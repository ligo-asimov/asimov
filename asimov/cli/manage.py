""" 
Olivaw management commands
"""
import os

import pathlib
import click

from asimov.cli import known_pipelines
from asimov import config, logger
from asimov import current_ledger as ledger

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
    for event in ledger.get_event(event):
        click.echo(f"Working on {event.name}")
        ready_productions = event.get_all_latest()
        for production in ready_productions:
            click.echo(f"\tWorking on production {production.name}")
            if production.status in {"running", "stuck", "wait", "finished", "uploaded", "cancelled", "stopped"}: continue
            try:
                configuration = production.get_configuration()
            except ValueError:
                try:

                    if production.rundir:
                        path = pathlib.Path(production.rundir)
                    else:
                        path = pathlib.Path(config.get("general", "rundir_default"))
                    path.mkdir(parents=True, exist_ok=True)
                    config_loc = os.path.join(path, f"{production.name}.ini")
                    production.make_config(config_loc)
                    click.echo(f"Production config {production.name} created.")
                    logger.info("Run configuration created.", production=production)

                    try:
                        event.repository.add_file(config_loc,
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
@click.option("--dryrun", "-d", "dryrun", default=False, help="Print all commands which will be executed without running them")
@manage.command()
def submit(event, update, dryrun):
    """
    Submit the run configuration files for a given event for jobs which are ready to run.
    If no event is specified then all of the events will be processed.
    """
    for event in ledger.get_event(event):
        ready_productions = event.get_all_latest()
        for production in ready_productions:
            if production.status.lower() in {"running", "stuck", "wait", "processing", "uploaded", "finished", "manual", "cancelled", "stopped"}: continue
            if production.status.lower() == "restart":
                if production.pipeline.lower() in known_pipelines:
                    pipe = known_pipelines[production.pipeline.lower()](production, "C01_offline")
                    pipe.clean()
                    pipe.submit_dag()
            else:
                #try:
                #    configuration = production.get_configuration()
                #except ValueError as e:
                #    #build(event)
                #    logger.error(f"Error while trying to submit a configuration. {e}", production=production, channels="gitlab")
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
@manage.command()
def results(event, update):
    """
    Find all available results for a given event.
    """
    for event in ledger.get_event(event):
        click.secho(f"{event.title}")
        for production in event.productions:
            try:
                for result, meta in production.results().items():
                    print(f"{production.event.name}/{production.name}/{result}, {production.results(result)}")
            except:
                pass
            # print(production.results())

@click.option("--event", "event", default=None, help="The event which the ledger should be returned for, optional.")
@click.option("--update", "update", default=False, help="Force the git repos to be pulled before submission occurs.")
@click.option("--root", "root")
@manage.command()
def resultslinks(event, update, root):
    """
    Find all available results for a given event.
    """
    server, repository = connect_gitlab()
    events = gitlab.find_events(repository, milestone=config.get("olivaw", "milestone"), subset=[event], update=update, repo=False)
    for event in events:
        click.secho(f"{event.title}")
        for production in event.productions:
            try:
                for result, meta in production.results().items():
                    print(f"{production.event.name}/{production.name}/{result}, {production.results(result)}")
                    pathlib.Path(os.path.join(root, production.event.name, production.name)).mkdir(parents=True, exist_ok=True)
                    os.symlink(f"{production.results(result)}", f"{root}/{production.event.name}/{production.name}/{result.split('/')[-1]}")
            except AttributeError:
                pass
            # print(production.results())
