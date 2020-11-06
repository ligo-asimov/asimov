"""
Make the event issues on the gitlab issue tracker from gracedb.
"""
import os

import asimov
from asimov.event import Event, DescriptionException
from asimov import config

from asimov import gitlab
from asimov import config

import numpy as np
import yaml


import click


server = gitlab.gitlab.Gitlab(config.get("gitlab", "url"), private_token=config.get("gitlab", "token"))
repository = server.projects.get(config.get("olivaw", "tracking_repository"))



def find_calibrations(time):
    with open("LLO_calibs.txt") as llo_file:
        data_llo = llo_file.read().split("\n")
        data_llo = [datum for datum in data_llo if datum[-16:]=="FinalResults.txt"]
        times_llo = {int(datum.split("GPSTime_")[1].split("_C01")[0]): datum for datum in data_llo}
    
    with open("LHO_calibs.txt") as llo_file:
        data_lho = llo_file.read().split("\n")
        data_lho = [datum for datum in data_lho if datum[-16:]=="FinalResults.txt"]
        times_lho = {int(datum.split("GPSTime_")[1].split("_C01")[0]): datum for datum in data_lho}
        
    keys_llo = np.array(list(times_llo.keys())) 
    keys_lho = np.array(list(times_lho.keys())) 
    return {"H1": times_lho[keys_lho[np.argmin(np.abs(keys_lho - time))]], "L1": times_llo[keys_llo[np.argmin(np.abs(keys_llo - time))]]}


@click.group()
def olivaw():
    """
    This is the main olivaw program which runs the DAGs for each event issue.
    """
    click.echo("Running olivaw")

    global rundir
    rundir = os.getcwd()

@click.option("--event", "event", default=None, help="The event which the ledger should be returned for, optional.")
@olivaw.command()
def notes(event):
    gitlab_events = gitlab.find_events(repository, subset=event)
    # Update existing events
    delete_list = []
    for event in gitlab_events:
        for note in event.issue_object.notes.list():
            if "error was detected" in note.body:
                delete_list.append(note)
        for note in delete_list:
            note.delete()

olivaw()
