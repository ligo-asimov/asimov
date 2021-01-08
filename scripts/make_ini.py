"""
Script to add event data from an ini configuration file.
"""
import ast

import asimov

from asimov.event import Event, DescriptionException
from asimov import config
from asimov import gitlab



import numpy as np
from configparser import ConfigParser, NoOptionError

from git.exc import GitCommandError
import click
import collections.abc


server = gitlab.gitlab.Gitlab(config.get("gitlab", "url"), private_token=config.get("gitlab", "token"))
repository = server.projects.get(config.get("olivaw", "tracking_repository"))


@click.option("--event", "event", default=None, help="The event which the ledger should be returned for, optional.")
@click.option("--ini", "ini_data", default=None)
@click.command()
def add_data(event, ini_data=None):    
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

add_data()
