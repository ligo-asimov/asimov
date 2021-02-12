import os
import collections
import json

from math import floor

import click

from datetime import datetime
import pytz

tz = pytz.timezone('Europe/London')

import numpy as np

from asimov import gitlab
from asimov.event import Event, DescriptionException, Production
from asimov import config
from asimov import logging
from asimov.pipeline import PipelineException
from asimov import condor
import asimov.pipelines
from asimov.pipelines.bayeswave import BayesWave
from asimov.pipelines.lalinference import LALInference                    
from asimov.pipelines.rift import Rift
from asimov.pipelines.bilby import Bilby

# Replace this with a better logfile handling module please
from glob import glob

import yaml

import otter
import otter.bootstrap as bt

from git.exc import GitCommandError

state_vector_channel = {"L1": "L1:DCS-CALIB_STATE_VECTOR_C01",
                        "H1": "H1:DCS-CALIB_STATE_VECTOR_C01",
                        "V1": "V1:DQ_ANALYSIS_STATE_VECTOR"}

frametypes= {"L1": "L1_HOFT_CLEAN_SUB60HZ_C01",
             "H1": "H1_HOFT_CLEAN_SUB60HZ_C01",
             "V1": "V1Online"}

CALIBRATION_NOTE = """
## Calibration envelopes
The following calibration envelopes have been found.
```yaml
---
{}
---
```
"""


ACTIVE_STATES = {"running", "stuck", "finished", "processing", "stop"}

known_pipelines = {"bayeswave": BayesWave,
                   "bilby": Bilby,
                   "rift": Rift,
                   "lalinference": LALInference}


def connect_gitlab():
    """
    Connect to the gitlab server.

    Returns
    -------
    server : `Gitlab`
       The gitlab server.
    repository: `Gitlab.project`
       The gitlab project.
    """
    server = gitlab.gitlab.Gitlab('https://git.ligo.org',
                              private_token=config.get("gitlab", "token"))
    repository = server.projects.get(config.get("olivaw", "tracking_repository"))
    return server, repository

@click.group()
def olivaw():
    """
    This is the main olivaw program which runs the DAGs for each event issue.
    """
    click.echo("Running olivaw")

    global rundir
    rundir = os.getcwd()

@click.option("--yaml", "yaml_f", default=None, help="A YAML file to save the ledger to.")
@click.option("--event", "event", default=None, help="The event which the ledger should be returned for, optional.")
@olivaw.command()
def ledger(event, yaml_f):
    """
    Return the ledger for a given event.
    If no event is specified then the entire production ledger is returned.
    """

    server, repository = connect_gitlab()
    
    events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"), subset=[event], update=False)

    if event:
        events = [event_i for event_i in events if event_i.title == event]

    total = []
    for event in events:
        total.append(yaml.safe_load(event.event_object.to_yaml()))
        click.echo(f"{event.title:30}")
        click.echo("-"*45)
        if len(event.event_object.meta['productions'])>0:
            for production in event.event_object.meta['productions']:
                click.echo(f"{production}")
            click.echo("-"*45)
        if len(event.event_object.get_all_latest())>0:
            click.echo("Jobs waiting")
            click.echo("-"*45)
            click.echo(event.event_object.get_all_latest())

    if yaml_f:
        with open(yaml_f, "w") as f:
            f.write(yaml.dump(total))


@click.option("--location", "webdir", default=None, help="The place to save the report to")
@click.option("--event", "event", default=None, help="The event which the report should be returned for, optional.")
@olivaw.command()
def report(event, webdir):
    """
    Return the ledger for a given event.
    If no event is specified then the entire production ledger is returned.
    """
    server, repository = connect_gitlab()
    if not webdir:
        webdir = "./"

    events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"), subset=[event], update=False)
    report = otter.Otter(f"{webdir}/index.html", 
                         author="Olivaw", 
                         title="Olivaw PE Report", 
                         author_email="daniel.williams@ligo.org", 
                         config_file="asimov.conf")

    with report:
        navbar = bt.Navbar("Asimov", background="navbar-dark bg-primary")
        report + navbar

    with report:
        time = bt.Container()

        time + f"Report generated at {str(datetime.now(tz))}"
        report + time

    cards = []
    container = bt.Container()
    container + "# All PE Productions"
    for event in events:

        event_report =  otter.Otter(f"{webdir}/{event.title}.html", 
                         author="Olivaw", 
                         title=f"Olivaw PE Report | {event.title}", 
                         author_email="daniel.williams@ligo.org", 
                         config_file="asimov.conf")

        card = bt.Card(title=f"<a href='{event.title}.html'>{event.title}</a>")

        toc = bt.Container()

        for production in event.productions:
            toc + f"[{production.name}](#{production.name})"

        with event_report:
            event_report + f"#{event.title}"
            event_report + toc

        production_list = bt.ListGroup()
        for production in event.productions:

            event_log =  otter.Otter(f"{webdir}/{event.title}-{production.name}.html", 
                                     author="Olivaw", 
                                     title=f"Olivaw PE Report | {event.title} | {production.name}", 
                                     author_email="daniel.williams@ligo.org", 
                                     config_file="asimov.conf")

            

            pipe = known_pipelines[production.pipeline.lower()](production, "C01_offline")
            
            status_map = {"cancelled": "light",
                          "finished": "success",
                          "uploaded": "success",
                          "processing": "primary",
                          "running": "primary",
                          "stuck": "warning",
                          "restart": "secondary",
                          "ready": "secondary",
                          "wait": "light",
                          "stop": "danger",
                          "manual": "light",
                          "stopped": "light"}
            production_list.add_item(f"{production.name}" + str(bt.Badge(f"{production.pipeline}", "info")) + str(bt.Badge(f"{production.status}")), 
                                     context=status_map[production.status])

            with event_report:
                container = bt.Container()
                container + f"## {production.name}"
                container + f"<a id='{production.name}'/>"
                container + "### Ledger"
                container + production.meta



            logs = pipe.collect_logs()
            container + f"### Log files"
            container + f"<a href='{event.title}-{production.name}.html'>Log file page</a>"
            with event_log:

                for log, message in logs.items():
                    log_card = bt.Card(title=f"{log}")
                    log_card.add_content("<div class='card-body'><pre>"+message+"</pre></div>")
                    event_log + log_card

            with event_report:
                event_report + container

        card.add_content(production_list)
        cards.append(card)



    with report:
        if len(cards) == 1:
            report + card
        else:
            for i, card in enumerate(cards):
                if i%2==0:
                    deck = bt.CardDeck()
                deck + card
                if i%2==1:
                    report + deck

            
@click.option("--event", "event", default=None, help="The event which the ledger should be returned for, optional.")
@olivaw.command()
def build(event):
    """
    Create the run configuration files for a given event for jobs which are ready to run.
    If no event is specified then all of the events will be processed.
    """
    server, repository = connect_gitlab()
    events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"), subset=[event], update=True)    
    for event in events:
        click.echo(f"Working on {event.title}")
        logger = logging.AsimovLogger(event=event.event_object)
        ready_productions = event.event_object.get_all_latest()
        print(event.productions)
        for production in ready_productions:
            click.echo(f"\tWorking on production {production.name}")
            if production.status in {"running", "stuck", "wait", "finished", "uploaded"}: continue
            try:
               configuration = production.get_configuration()
            except ValueError:
               try:
                   templates = os.path.join(rundir, config.get("templating", "directory"))
                   production.make_config(f"{production.name}.ini", template_directory=templates)
                   click.echo(f"Production config {production.name} created.")
                   logger.info("Run configuration created.", production=production)

                   try:
                       event.event_object.repository.add_file(f"{production.name}.ini",
                                                              os.path.join(f"{production.category}",
                                                                           f"{production.name}.ini"))
                       logger.info("Configuration committed to event repository.",
                                   production=production)
                   except Exception as e:
                       logger.error(f"Configuration could not be committed to repository.\n{e}",
                                    production=production)
                   
               except DescriptionException as e:
                   logger.error("Run configuration failed", production=production, channels=["file", "mattermost"])


@click.option("--event", "event", default=None, help="The event which the ledger should be returned for, optional.")
@click.option("--update", "update", default=False, help="Force the git repos to be pulled before submission occurs.")
@olivaw.command()
def submit(event, update):
    """
    Submit the run configuration files for a given event for jobs which are ready to run.
    If no event is specified then all of the events will be processed.
    """
    server, repository = connect_gitlab()
    events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"), subset=[event], update=update)
    for event in events:
        logger = logging.AsimovLogger(event=event.event_object)
        ready_productions = event.event_object.get_all_latest()
        print(ready_productions)
        for production in ready_productions:
            if production.status.lower() in {"running", "stuck", "wait", "processing", "uploaded", "finished"}: continue
            if production.status.lower() == "restart":
                if production.pipeline.lower() in known_pipelines:
                    pipe = known_pipelines[production.pipeline.lower()](production, "C01_offline")
                    pipe.clean()
                    pipe.submit_dag()
            else:
                try:
                    configuration = production.get_configuration()
                except ValueError as e:
                    #build(event)
                    logger.error(f"Error while trying to submit a configuration. {e}", production=production, channels="gitlab")
                if production.pipeline.lower() in known_pipelines:
                    pipe = known_pipelines[production.pipeline.lower()](production, "C01_offline")
                    try:
                        pipe.build_dag()
                    except PipelineException:
                        logger.error("The pipeline failed to build a DAG file.",
                                     production=production)
                    try:
                        pipe.submit_dag()
                        production.status = "running"

                    except PipelineException as e:
                        production.status = "stuck"
                        logger.error(f"The pipeline failed to submit the DAG file to the cluster. {e}",
                                     production=production)
                

@click.option("--event", "event", default=None, help="The event which the ledger should be returned for, optional.")
@click.option("--update", "update", default=False, help="Force the git repos to be pulled before submission occurs.")
@olivaw.command()
def monitor(event, update):
    """
    Monitor condor jobs' status, and collect logging information.
    """
    server, repository = connect_gitlab()
    events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"), subset=[event], update=update)
    for event in events:
        stuck = 0
        running = 0
        ready = 0
        finish = 0
        click.echo(f"Checking {event.title}")
        on_deck = [production for production in event.productions if production.status in ACTIVE_STATES]
        for production in on_deck:

            click.echo(f"Checking {production.name}")
            logger = logging.AsimovLogger(event=event.event_object)

            # Deal with jobs which need to be stopped first
            if production.status.lower() == "stop":
                pipe = known_pipelines[production.pipeline.lower()](production, "C01_offline")
                pipe.eject_job()
                production.status = "stopped"
                click.echo(f"{production.name} stopped")
                continue

            # Get the condor jobs
            try:
                if "job id" in production.meta:
                    job = condor.CondorJob(production.meta['job id'])
                else:
                    raise ValueError
                click.echo(f"{event.event_object.name}\t{event.state}\t{production.name}\t{job.status}")

                if event.state == "running" and job.status.lower() == "stuck":
                    click.echo("Job is stuck on condor")
                    event.state = "stuck"
                    production.status = "stuck"
                    stuck += 1
                    production.meta['stage'] = 'production'
                elif event.state == "processing" and job.status.lower() == "stuck":
                    production.status = "stuck"
                    stuck += 1
                    production.meta['stage'] = "post"
                    
                else:
                    running += 1
            except ValueError as e:
                click.echo(production.status.lower())
                if production.pipeline.lower() in known_pipelines:
                    click.echo("Investigating...")
                    pipe = known_pipelines[production.pipeline.lower()](production, "C01_offline")

                    if production.status.lower() == "stop":
                        pipe.eject_job()
                        production.status = "stopped"

                    if production.status.lower() == "processing":
                    # Need to check the upload has completed
                        try:
                            pipe.after_processing()
                        except ValueError as e:
                            click.echo(e)
                            production.status = "stuck"
                            stuck += 1
                            production.meta['stage'] = "after processing"

                    elif pipe.detect_completion() and production.status.lower() == "running":
                        # The job has been completed, collect its assets
                        production.meta['job id'] = None
                        finish += 1
                        production.status = "finished"
                        pipe.after_completion()
                        
                    else:
                        # It looks like the job has been evicted from the cluster
                        click.echo(f"Attempting to rescue {production.name}")
                        #event.state = "stuck"
                        #production.status = "stuck"
                        #production.meta['stage'] = 'production'
                        pipe.resurrect()

                if production.status == "stuck":
                    event.state = "stuck"

            if (running > 0) and (stuck == 0):
                event.state = "running"
            elif (stuck == 0) and (running == 0) and (finish > 0):
                event.state = "finished"

@click.option("--event", "event", default=None, help="The event which will be updated")
@click.option("--pipeline", "pipeline", default=None, help="The pipeline which the job should use")
@click.option("--family", "family", default=None, help="The family name of the production, e.g. `prod`.")
@click.option("--comment", "comment", default=None, help="A comment to attach to the production")
@click.option("--needs", "needs", default=None, help="A list of productions which are requirements")
@click.option("--template", "template", default=None, help="The configuration template for the production.")
@click.option("--status", "status", default=None, help="The initial status of the production.")
@olivaw.command(help="Add a new production to an event")
def production(event, pipeline, family, comment, needs, template, status):
    """
    Add a new production to an event.

    """
    server, repository = connect_gitlab()
    gitlab_event = gitlab.find_events(repository, subset=event)
    event = gitlab_event[0].event_object
    #
    event_prods = event.productions
    names = [production.name for production in event_prods]
    family_entries = [int(name.split(family)[1]) for name in names if family in name]
    #
    if "bayeswave" in needs:
        bw_entries = [production.name for production in event_prods if "bayeswave" in production.pipeline.lower()]
        needs = bw_entries
    #
    production = {"comment": comment, "pipeline": pipeline, "status": status}
    if needs:
        production['needs'] = needs
    if template:
        production['template'] = template
    number = max(family_entries)+1
    production_dict = {f"{family}{number}": production}
    production = Production.from_dict(production_dict, event=event)
    #
    click.echo(production)
    event.add_production(production)
    gitlab_event[0].update_data()
    


@click.option("--event", "event", default=None, help="The event which will be updated")
@click.option("--json", "json_data", default=None)
@olivaw.command(help="Add data from the configurator.")
def configurator(event, json_data=None):    
    gitlab_event = gitlab.find_events(repository, subset=event)
    def update(d, u):
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

   
    if json_data:
        with open(json_data, "r") as datafile:
            data = json.load(datafile)

    new_data = {"quality": {}, "priors": {}}
    new_data["quality"]["sample-rate"] = data["srate"]
    new_data["quality"]["lower-frequency"] = {}
    new_data["quality"]["upper-frequency"] = int(0.875 * data["srate"]/2)
    new_data["quality"]["start-frequency"] = data['f_start']
    new_data["quality"]["segment-length"] = data['seglen']
    new_data["quality"]["window-length"] = data['seglen']
    new_data["quality"]["psd-length"] = data['seglen']

    def decide_fref(freq):
        if (freq >= 5) and (freq < 10):
            return 5
        else:
            return floor(freq/10)*10

    new_data["quality"]["reference-frequency"] = decide_fref(data['f_ref'])

    new_data["priors"]["amp order"] = data['amp_order']
    new_data["priors"]["chirp-mass"] = [data["chirpmass_min"], data["chirpmass_max"]]

    update(gitlab_event[0].event_object.meta, new_data)
    print(gitlab_event[0].event_object.meta)
    gitlab_event[0].update_data()


#@click.option("--event", "event", default=None, help="The event which the ledger should be returned for, optional.")
#@olivaw.command()
def checkifo(event):
    server, repository = connect_gitlab()
    gitlab_events = gitlab.find_events(repository, subset=event)

    for event in gitlab_events:
        if "event time" not in event.event_object.meta:
            print(f"Time not found {event.event_object.name}")
        time = event.event_object.meta['event time']
        gpsstart=time-600
        gpsend=time+600
        bits = ['Bit 0', 'Bit 1', 'Bit 2']

        active_ifo = []
        for ifo in ["L1", "H1", "V1"]:
    
            urls = find_urls(site=f"{ifo[0]}", frametype=frametypes[ifo], gpsstart=gpsstart, gpsend=gpsend)
            datacache = Cache.from_urls(urls)
            if len(datacache) == 0:
                print(f"No {ifo} data found.")
                continue
            state = gwpy.timeseries.StateVector.read(
                datacache, state_vector_channel[ifo], start=gpsstart, end=gpsend,
                pad=0  # padding data so that errors are not raised even if found data are not continuous.
            )
            if not np.issubdtype(state.dtype, np.unsignedinteger):
                # if data are not unsigned integers, cast to them now so that
                # we can determine the bit content for the flags
                state = state.astype(
                    "uint32",
                    casting="unsafe",
                    subok=True,
                    copy=False,
                )
            flags = state.to_dqflags()

            segments = flags[bits[0]].active
            for bit in bits:
                segments -= ~flags[bit].active

            if len(segments)>0: active_ifo += [ifo]
        print(event.event_object.name)
        if event.event_object.meta['interferometers'] != active_ifo:
            print(f"Gitlab data\t{event.event_object.meta['interferometers']}")
            print(f"Recommended IFOS\t{active_ifo}")
        event.event_object.meta['interferometers'] = active_ifo
        event.update_data()

@click.option("--event", "event", help="The event to be populated.")
@click.option("--yaml", "yaml", default=None)
@click.option("--ini", "ini", default=None)
@olivaw.command()
def populate(event, yaml, ini):
    """
    Populate an event ledger with data from ini or yaml files.
    """
    server, repository = connect_gitlab()
    gitlab_events = gitlab.find_events(repository, subset=[event])
    event = gitlab_events[0]
    event_o = event.event_object
    # Check the calibration files for this event
    click.echo("Check the calibration.")
    calibration(event_o.name)
    # Check the IFOs for this event
    click.echo("Check the IFO list")
    try:
        checkifo(event_o.name)
    except:
        pass

    # Add default data
    click.echo("Add in default channel data.")
    if yaml:
        add_data(event_o.name, yaml)

@click.option("--namefile", "names", default=None, help="The mapping between old and new names for events.")
@click.argument("name")
@click.argument("superevent")
@olivaw.command()
def create(superevent, name, names=None):
    """
    Create a new event record on the git issue tracker from the GraceDB dev server.

    Parameters
    ----------
    superevent : str
       The ID of the superevent to be used from GraceDB
    name : str
       The name of the event to be recorded in the issue tracker
    """
    server, repository = connect_gitlab()
    from ligo.gracedb.rest import GraceDb, HTTPError 
    client = GraceDb(service_url=config.get("gracedb", "url"))
    r = client.ping()
    data = client.superevent(superevent).json()
    event_data = client.event(data['preferred_event']).json()

    if names:
        with open(names, "r") as datafile:
            names = json.load(datafile)
        old_superevent = names['SNAME'][name]
    else:
        old_superevent = superevent
        
    event_url = f"https://catalog-dev.ligo.org/events/{data['preferred_event']}/view/"
    event = Event(name=name,
                  repository=f"git@git.ligo.org:pe/O3/{old_superevent}",
                  #gid=data['preferred_event'],
                  #gid_url=event_url,
                  calibration = {},
                  interferometers=event_data['instruments'].split(","),
    )
    event.meta['old superevent'] = old_superevent
    event.meta['event time'] = event_data['gpstime']
    event.meta['working directory'] = f"{config.get('general', 'rundir_default')}/{name}"
    gitlab.EventIssue.create_issue(repository, event, issue_template="/home/daniel.williams/repositories/asimov/scripts/outline.md")

@click.option("--event", "event", default=None, help="The event which will be updated")
@click.option("--json", "json_data", default=None)
@olivaw.command(help="Add data from the configurator.")
def configurator(event, json_data=None):
    """
    Add data from the PEConfigurator script to an event.
    """
    server, repository = connect_gitlab()
    gitlab_event = gitlab.find_events(repository, subset=event)
    def update(d, u):
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    if json_data:
        with open(json_data, "r") as datafile:
            data = json.load(datafile)

    new_data = {"quality": {}, "priors": {}}
    new_data["quality"]["sample-rate"] = data["srate"]
    new_data["quality"]["lower-frequency"] = {}
    new_data["quality"]["upper-frequency"] = int(0.875 * data["srate"]/2)
    new_data["quality"]["start-frequency"] = data['f_start']
    new_data["quality"]["segment-length"] = data['seglen']
    new_data["quality"]["window-length"] = data['seglen']
    new_data["quality"]["psd-length"] = data['seglen']

    def decide_fref(freq):
        if (freq >= 5) and (freq < 10):
            return 5
        else:
            return floor(freq/10)*10

    new_data["quality"]["reference-frequency"] = decide_fref(data['f_ref'])

    new_data["priors"]["amp order"] = data['amp_order']
    new_data["priors"]["chirp-mass"] = [data["chirpmass_min"], data["chirpmass_max"]]

    update(gitlab_event[0].event_object.meta, new_data)
    print(gitlab_event[0].event_object.meta)
    gitlab_event[0].update_data()
        
def find_calibrations(time):
    with open("/home/daniel.williams/repositories/asimov/scripts/LLO_calibs.txt") as llo_file:
        data_llo = llo_file.read().split("\n")
        data_llo = [datum for datum in data_llo if datum[-16:]=="FinalResults.txt"]
        times_llo = {int(datum.split("GPSTime_")[1].split("_C01")[0]): datum for datum in data_llo}
    
    with open("/home/daniel.williams/repositories/asimov/scripts/LHO_calibs.txt") as llo_file:
        data_lho = llo_file.read().split("\n")
        data_lho = [datum for datum in data_lho if datum[-16:]=="FinalResults.txt"]
        times_lho = {int(datum.split("GPSTime_")[1].split("_C01")[0]): datum for datum in data_lho}
        
    keys_llo = np.array(list(times_llo.keys())) 
    keys_lho = np.array(list(times_lho.keys())) 

    return {"H1": times_lho[keys_lho[np.argmin(np.abs(keys_lho - time))]], "L1": times_llo[keys_llo[np.argmin(np.abs(keys_llo - time))]], "V1": "/home/cbc/pe/O3/calibrationenvelopes/Virgo/V_O3a_calibrationUncertaintyEnvelope_magnitude5percent_phase35milliradians10microseconds.txt"}

def calibration(event):
    server, repository = connect_gitlab()
    gitlab_events = gitlab.find_events(repository, subset=event)
    # Update existing events
    for event in gitlab_events:
        if "disable_repo" in event.event_object.meta:
            if event.event_object.meta['disable_repo'] == True:
                continue
        try:
            event.event_object._check_calibration()
        except DescriptionException:
            print(event.title)
            time = event.event_object.meta['event time'] 

            calibrations = find_calibrations(time)
            print(calibrations)
            # try:
            for ifo, envelope in calibrations.items():
                description = f"Added calibration {envelope} for {ifo}."
                try:
                    event.event_object.repository.add_file(os.path.join(f"/home/cal/public_html/uncertainty/O3C01/{ifo}", envelope), f"C01_offline/calibration/{ifo}.dat", 
                                                       commit_message=description)
                except GitCommandError as e:
                    if "nothing to commit," in e.stderr:
                        pass
                calibrations[ifo] = f"C01_offline/calibration/{ifo}.dat"
            envelopes = yaml.dump({"calibration": calibrations})
            event.add_note(CALIBRATION_NOTE.format(envelopes))


def add_data(event, yaml_data, json_data=None):
    server, repository = connect_gitlab()
    gitlab_event = gitlab.find_events(repository, subset=event)
    def update(d, u):
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

   
    if yaml_data:
        with open(yaml_data, "r") as datafile:
            data = yaml.safe_load(datafile.read())

        gitlab_event[0].event_object.meta = update(gitlab_event[0].event_object.meta, data)
        gitlab_event[0].update_data()
        print(gitlab_event[0].event_object.meta)

        
