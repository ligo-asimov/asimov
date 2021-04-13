""" 
Olivaw management commands
"""
import os

import click

from asimov.cli import connect_gitlab, known_pipelines
from asimov import logging
from asimov import config
from asimov import gitlab
from asimov.event import Event, DescriptionException, Production
from asimov.pipeline import PipelineException

@click.group()
def manage():
    pass


@click.option("--event", "event", default=None, help="The event which the ledger should be returned for, optional.")
@manage.command()
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
        for production in ready_productions:
            click.echo(f"\tWorking on production {production.name}")
            if production.status in {"running", "stuck", "wait", "finished", "uploaded"}: continue
            try:
                configuration = production.get_configuration()
            except ValueError:
                try:
                    rundir = config.get("general", "rundir_default")
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
@manage.command()
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
