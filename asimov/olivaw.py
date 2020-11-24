import os


import click

from datetime import datetime
import pytz

tz = pytz.timezone('Europe/London')

from asimov import gitlab
from asimov.event import DescriptionException
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

ACTIVE_STATES = {"running", "stuck", "finished", "processing"}

known_pipelines = {"bayeswave": BayesWave,
                   "bilby": Bilby,
                   "rift": Rift,
                   "lalinference": LALInference}

server = gitlab.gitlab.Gitlab('https://git.ligo.org',
                              private_token=config.get("gitlab", "token"))
repository = server.projects.get(config.get("olivaw", "tracking_repository"))

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
    events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"), subset=[event])

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

    if not webdir:
        webdir = "./"
    if event:
        events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"), subset=[event])
    else:
        events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"))
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
            
            status_map = {"finished": "success", "uploaded": "success", "processing": "primary",  "running": "primary", "stuck": "warning", "restart": "secondary", "ready": "secondary", "wait": "light"}
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

    if event:
        events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"), subset=[event])
    else:
        events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"))
    
    for event in events:
        click.echo(f"Working on {event.title}")
        logger = logging.AsimovLogger(event=event.event_object)
        ready_productions = event.event_object.get_all_latest()
        print(event.productions)
        for production in ready_productions:
            click.echo(f"\tWorking on production {production.name}")
            if production.status in {"running", "stuck", "wait"}: continue
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
@olivaw.command()
def submit(event):
    """
    Submit the run configuration files for a given event for jobs which are ready to run.
    If no event is specified then all of the events will be processed.
    """
    if event:
        events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"), subset=[event])
    else:
        events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"))

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
@olivaw.command()
def monitor(event):
    """
    Monitor condor jobs' status, and collect logging information.
    """

    if event:
        events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"), subset=[event])
    else:
        events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"))

    for event in events:
        click.echo(f"Checking {event.title}")
        on_deck = [production for production in event.productions if production.status in ACTIVE_STATES]
        for production in on_deck:

            click.echo(f"Checking {production.name}")
            logger = logging.AsimovLogger(event=event.event_object)
            # Get the condor jobs
            try:
                job = condor.CondorJob(production.meta['job id'])
                print(f"{event.event_object.name}\t{production.name}\t{job.status}")
                if event.state == "running" and job.status.lower() == "stuck":
                    event.state = "stuck"
                    production.status = "stuck"
                    production.meta['stage'] = 'production'
                elif event.state == "processing" and job.status.lower() == "stuck":
                    production.status = "stuck"
                    production.meta['stage'] = "post"
            except ValueError as e:
                click.echo(production.status.lower())
                if production.pipeline.lower() in known_pipelines:
                    
                    pipe = known_pipelines[production.pipeline.lower()](production, "C01_offline")

                    if production.status.lower() == "processing":
                    # Need to check the upload has completed
                        try:
                            pipe.after_processing()
                        except ValueError as e:
                            click.echo(e)
                            production.status = "stuck"
                            production.meta['stage'] = "after processing"

                    elif pipe.detect_completion() and production.status.lower() == "running":
                        # The job has been completed, collect its assets
                        production.meta['job id'] = None
                        production.status = "finished"
                        pipe.after_completion()
                        
                    else:
                        # It looks like the job has been evicted from the cluster
                        event.state = "stuck"
                        production.status = "stuck"
                        production.meta['stage'] = 'production'
                        pipe.resurrect()

                if production.status == "stuck":
                    event.state = "stuck"
