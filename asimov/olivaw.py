import os

import click

from asimov import gitlab
from asimov.event import DescriptionException
from asimov import config, config_locations
from asimov import logging

import yaml


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
    events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"))

    if event:
        events = [event_i for event_i in events if event_i.title == event]

    total = []
    for event in events:
        total.append(yaml.safe_load(event.event_object.to_yaml()))
        click.echo(f"{event.title:30}")
        click.echo("-"*45)
        if len(event.event_object.meta['productions'])>0:
            click.echo(event.event_object.meta['productions'])
            click.echo("-"*45)
        if len(event.event_object.get_all_latest())>0:
            click.echo("Jobs waiting")
            click.echo("-"*45)
            click.echo(event.event_object.get_all_latest())

    if yaml_f:
        with open(yaml_f, "w") as f:
            f.write(yaml.dump(total))

            
@click.option("--event", "event", default=None, help="The event which the ledger should be returned for, optional.")
@olivaw.command()
def build(event):
    """
    Create the run configuration files for a given event for jobs which are ready to run.
    If no event is specified then all of the events will be processed.
    """
    events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"))

    if event:
        events = [event_i for event_i in events if event_i.title == event]

    for event in events:
        logger = logging.AsimovLogger(event=event.event_object)
        ready_productions = event.event_object.get_all_latest()

        for production in ready_productions:
            try:
                configuration = production.get_configuration()
            except ValueError:
                try:
                    templates = os.path.join(rundir, config.get("templating", "directory"))
                    production.make_config(f"{production.name}.ini", template_directory=templates)
                    click.echo(f"Production config {production.name} created.")
                    logger.info("Run configuration created.", production=production)

                    #try:
                    event.event_object.repository.add_file(f"{production.name}.ini",
                                                               os.path.join(f"{production.category}",
                                                                            f"{production.name}.ini"))
                    #logger.info("Configuration committed to event repository.",
                    #                production=production)
                    #except Exception as e:
                    #    logger.error(f"Configuration could not be committed to repository.\n{e}",
                    #                 production=production)
                    
                except DescriptionException:
                    logger.error("Run configuration failed", production=production, channels=["file", "mattermost"])


@click.option("--event", "event", default=None, help="The event which the ledger should be returned for, optional.")
@olivaw.command()
def submit(event):
    """
    Submit the run configuration files for a given event for jobs which are ready to run.
    If no event is specified then all of the events will be processed.
    """
    events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"))

    if event:
        events = [event_i for event_i in events if event_i.title == event]

    for event in events:
        logger = logging.AsimovLogger(event=event.event_object)
        ready_productions = event.event_object.get_all_latest()

        for production in ready_productions:
            try:
                configuration = production.get_configuration()
            except ValueError:
                build(event)

            if production.pipeline.lower() == "bayeswave":
                from asimov.pipelines.bayeswave import BayesWave
                pipe = BayesWave(production, "C01_offline")
                pipe.build_dag()
                
