"""
Review functions for asimov events.
"""
import os

import click

from asimov.cli import connect_gitlab, known_pipelines
from asimov import gitlab
from asimov import config

@click.group()
def review():
    pass

@click.argument("event", required=True)
@click.argument("production", required=True)
@click.argument("status", required=False, default=None)
@click.option("--message", "-m", "message", default=None)
@review.command()
def add(event, production, status, message):
    """
    Add a review signoff or rejection to an event.
    """
    server, repository = connect_gitlab()
    gitlab_events = gitlab.find_events(repository,
                                      subset=[event],
                                      update=False,
                                      repo=False)
    for event in gitlab_events:
        production = [production_o
                      for production_o in event.productions
                      if production_o.name == production][0]
        click.secho(event.title, bold=True)
        message_o = ReviewMessage(message = message,
                                production = production,
                                status=status)
        production.review.add(message_o)
    
    if hasattr(event, "issue_object"):
        event.issue_object.update_data()

@click.argument("production", default=None, required=False)
@click.argument("event", default=None, required=False)
@review.command()
def status(event, production):
    """
    Show the review status of an event.
    """
    if isinstance(event, str):
        event = [event]
    server, repository = connect_gitlab()
    gitlab_events = gitlab.find_events(repository,
                                      subset=event,
                                      update=False,
                                      repo=False)
    for event in gitlab_events:
        click.secho(event.title, bold=True)
        if production:
            productions = [prod for prod in event.productions if prod.name == production]
        else:
            productions = event.productions

        for production in productions:
            click.secho(f"\t{production.name}", bold=True)
            if "review" in production.meta:
                click.echo(production.meta['review'])
            else:
                click.secho("\t\tNo review information exists for this production.")


@click.argument("event", default=None, required=False)
@review.command()
def audit(event):
    """
    Conduct an audit of the contents of production ini files
    against the production ledger.

    Parameters
    ----------
    event : str, optional
       The event to be checked.
       Optional; if the event isn't provided all events will be audited.
    """
    if isinstance(event, str):
        event = [event]
    _, repository = connect_gitlab()
    gitlab_events = gitlab.find_events(repository,
                                       subset=event,
                                       update=False,
                                       repo=True)

    for production in gitlab_events[0].productions:
        category = config.get("general", "calibration_directory")
        config_file = os.path.join(production.event.repository.directory,
                                   category,
                                   f"{production.name}.ini")
        pipe = known_pipelines[production.pipeline.lower()](production,
                                                            category)
        click.echo(pipe.read_ini(config_file))
