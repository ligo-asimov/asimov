import os
import collections
import yaml
import json
from math import floor
import ligo.gracedb
import gwpy

import click

from git import GitCommandError

from asimov import config
from asimov.ledger import Ledger
from asimov.storage import Store
from asimov.event import Production, Event,  DescriptionException
from asimov import gitlab
from asimov.cli import connect_gitlab

@click.group()
def production():
    """
    Commands to handle productions.
    """
    pass


@click.argument("pipeline")
@click.argument("event")
@click.option("--family", "family", default="Prod", help="The family name of the production, e.g. `prod`.")
@click.option("--comment", "comment", default=None, help="A comment to attach to the production")
@click.option("--needs", "needs", multiple=True, default=[], help="A list of productions which are requirements")
@click.option("--template", "template", default=None, help="The configuration template for the production.")
@click.option("--status", "status", default="wait", help="The initial status of the production.")
@click.option("--approximant", "approximant", default=None, help="The waveform approximant to be used in the production.")
@production.command(help="Add a new production to an event")
def create(event, pipeline, family, comment, needs, template, status, approximant):
    """
    Add a new production to an event.

    """
    if config.get("ledger", "engine") == "gitlab":
        _, repository = connect_gitlab()
        gitlab_event = gitlab.find_events(repository, subset=event)
        event = gitlab_event[0].event_object
    elif config.get("ledger", "engine") == "yamlfile":
        ledger = Ledger(config.get("ledger", "location"))
        event = ledger.get_event(event)
    #
    event_prods = event.productions
    names = [production.name for production in event_prods]
    family_entries = [int(name.split(family)[1]) for name in names if family in name]
    #
    if "bayeswave" in needs:
        bw_entries = [production.name for production in event_prods 
                      if ("bayeswave" in production.pipeline.lower())
                      and (production.review.status not in {"REJECTED", "DEPRECATED"})]
        needs = bw_entries
    #
    production = {"comment": comment, "pipeline": pipeline, "status": status}
    if needs:
        production['needs'] = needs
    if template:
        production['template'] = template
    if approximant:
        production['approximant'] = approximant
    if len(family_entries)>0:
        number = max(family_entries)+1
    else:
        number = 0
    production_dict = {f"{family}{number}": production}
    production = Production.from_dict(production_dict, event=event)
    #
    click.echo(production)
    event.add_production(production)

    if config.get("ledger", "engine") == "gitlab":
        gitlab_event[0].update_data()
    elif config.get("ledger", "engine") == "yamlfile":
        ledger.events[event.name] = event.to_dict()
        ledger.save()

@click.option("--file", "file", default=None)
@click.argument("production")
@click.argument("event")
@production.command()
def results(event, production, file, hash=None):
    """
    Fetch or list the results of a production.
    """
    if config.get("ledger", "engine") == "gitlab":
        _, repository = connect_gitlab()
        gitlab_event = gitlab.find_events(repository, subset=event)
        event = gitlab_event[0].event_object
    elif config.get("ledger", "engine") == "yamlfile":
        ledger = Ledger(config.get("ledger", "location"))
        event = ledger.get_event(event)
    production = [production_o for production_o in event.productions if production_o.name == production][0]
    store = Store(root=config.get("storage", "results_store"))

    if not file:
        try:
            items = store.manifest.list_resources(event.name, production.name).items()
            click.secho(f"{'Resource':30} {'Hash':32} {'UUID':32}")
            click.secho("-"*96)
            for resource, details in items:
                click.secho(f"{resource:30} {details['hash']:32} {details['uuid']:32}")
        except KeyError:
            click.secho("There are no results for this production.")
    else:
        try:
            click.echo(store.fetch_file(event, production, file, hash))
        except FileNotFoundError:
            click.secho(f"{file} could not be found for this production.")
