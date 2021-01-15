import os
import ast
import asimov
from asimov.event import Event, DescriptionException, Production
from asimov import config
from configparser import ConfigParser, NoOptionError
from asimov import gitlab
from asimov import config

import numpy as np
import yaml
import json

from git.exc import GitCommandError
import click

import gwpy
import gwpy.timeseries
import gwpy.segments
from gwpy.segments import DataQualityFlag
from gwdatafind import find_urls
from glue.lal import Cache

import collections.abc

state_vector_channel = {"L1": "L1:DCS-CALIB_STATE_VECTOR_C01",
                        "H1": "H1:DCS-CALIB_STATE_VECTOR_C01",
                        "V1": "V1:DQ_ANALYSIS_STATE_VECTOR"}

frametypes= {"L1": "L1_HOFT_CLEAN_SUB60HZ_C01",
             "H1": "H1_HOFT_CLEAN_SUB60HZ_C01",
             "V1": "V1Online"}

server = gitlab.gitlab.Gitlab(config.get("gitlab", "url"), private_token=config.get("gitlab", "token"))
repository = server.projects.get(config.get("olivaw", "tracking_repository"))

#
# Get GraceDB stuff
#
from ligo.gracedb.rest import GraceDb, HTTPError 
client = GraceDb(service_url=config.get("gracedb", "url"))
r = client.ping()

#superevent_iterator = client.superevents('O3B_CBC_CATALOG')
#superevent_ids = [superevent['superevent_id'] for superevent in superevent_iterator]


CALIBRATION_NOTE = """
## Calibration envelopes
The following calibration envelopes have been found.
```yaml
---
{}
---
```
"""

@click.group()
def olivaw():
    """
    This is the main olivaw program which runs the DAGs for each event issue.
    """
    click.echo("Running olivaw")

    global rundir
    rundir = os.getcwd()

@click.argument("name")
@click.argument("superevent")
@olivaw.command()
def create(superevent, name):
    data = client.superevent(name).json()
    event_data = client.event(data['preferred_event']).json()

    event_url = f"https://catalog-dev.ligo.org/events/{data['preferred_event']}/view/"
    
    event = Event(name=name,
                  repository=f"git@git.ligo.org:pe/O3/{superevent}",
                  gid=data['preferred_event'],
                  gid_url=event_url,
                  calibration = {},
                  interferometers=event_data['instruments'].split(","),
    )
    event.meta['old superevent'] = superevent
    event.meta['event time'] = event_data['gpstime']
    gitlab.EventIssue.create_issue(repository, event, issue_template="/home/daniel.williams/repositories/asimov/scripts/outline.md")



@click.option("--event", "event", help="The event which the ledger should be returned for.")
@click.option("--yaml", "yaml", default=None)
@click.option("--ini", "ini", default=None)
@olivaw.command()
def populate(event, yaml, ini):

    gitlab_events = gitlab.find_events(repository, subset=event)
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

    if ini:
        click.echo("Adding in data from ini file")
        try:
            add_ini(event_o.name, ini)
        except Exception as e:
            click.echo(e)

    # Add default data
    click.echo("Add in default channel data.")
    if yaml:
        add_data(event_o.name, yaml)

    # Add a Bayeswave job
    gitlab_events = gitlab.find_events(repository, subset=event_o.name)
    event = gitlab_events[0]
    event_o = event.event_object
    
    if "ProdF0" not in [p['name'] for p in event_o.productions]:
        job = Production(name="ProdF0", status="Ready", pipeline="Bayeswave", comment="PSD Production", event = event_o)
        event_o.add_production(job)
    event.update_data()




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
    for ifo in gitlab_event[0].event_object.meta['interferometers']:
        new_data["quality"]["lower-frequency"][ifo] = data['f_start']
    new_data["quality"]["segment-length"] = data['seglen']
    new_data["quality"]["window-length"] = data['seglen']
    new_data["quality"]["psd-length"] = data['seglen']
    new_data["quality"]["reference-frequency"] = data['f_ref']

    new_data["priors"]["amp order"] = data['amp_order']
    new_data["priors"]["chirp-mass"] = [data["chirpmass_min"], data["chirpmass_max"]]

    update(gitlab_event[0].event_object.meta, new_data)
    print(gitlab_event[0].event_object.meta)
    gitlab_event[0].update_data()


#@click.option("--event", "event", default=None, help="The event which the ledger should be returned for, optional.")
#@olivaw.command()
def checkifo(event):
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

#@click.option("--event", "event", default=None, help="The event which the ledger should be returned for, optional.")
#@click.option("--yaml", "yaml_data", default=None)
#@click.option("--json", "json_data", default=None)
#@olivaw.command()
def add_data(event, yaml_data, json_data=None):    
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

    

#@click.option("--event", "event", default=None, help="The event which the ledger should be returned for, optional.")
#@olivaw.command()
def calibration(event):    
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

def add_ini(event, ini_data=None):    
    gitlab_event = gitlab.find_events(repository, subset=event)
    def update(d, u):
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    ini = ConfigParser()
    ini.optionxform=str

    ini.read(ini_data)

    new_data = {"quality": {}, "priors": {}}
    new_data["quality"]["sample-rate"] = int(ini.get("engine", "srate"))
    new_data["quality"]["lower-frequency"] = ast.literal_eval(ini.get("lalinference", "flow"))
    new_data["quality"]["segment-length"] = float(ini.get("engine", "seglen"))
    new_data["quality"]["window-length"] = float(ini.get("engine", "seglen"))
    new_data["quality"]["psd-length"] = float(ini.get("engine", "seglen"))
    new_data["quality"]["reference-frequency"] = float(ini.get("engine", "fref"))

    # new_data["priors"]["amp order"] = data['amp_order']
    try: 
        ini.get("engine", "comp-max")
        new_data["priors"]["component"] = [float(ini.get("engine", "comp-min")), 
                                           float(ini.get("engine", "comp-max"))]
    except:
        pass
        #new_data["priors"]["component"] = [float(ini.get("engine", "comp-min")), 
        #                                   None]

    try:
        new_data["priors"]["chirp-mass"] = [float(ini.get("engine", "chirpmass-min")), 
                                            float(ini.get("engine", "chirpmass-max"))]
        new_data["priors"]["chirp-mass"] = [None, ini.get("engine", "distance-max")]
    except:
        pass
    new_data["priors"]["q"] = [float(ini.get("engine", "q-min")), 1.0]


    update(gitlab_event[0].event_object.meta, new_data)
    print(gitlab_event[0].event_object.meta)
    gitlab_event[0].update_data()


olivaw()
