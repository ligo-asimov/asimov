"""
Tools for adding data from JSON and YAML files.
Inspired by the kubectl apply approach from kubernetes.
"""

import click
import requests
import yaml

from asimov import LOGGER_LEVEL, logger
import asimov.event
from asimov.analysis import ProjectAnalysis
from asimov import current_ledger as ledger
from asimov.ledger import Ledger
from asimov.utils import update

import sys

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


logger = logger.getChild("cli").getChild("apply")
logger.setLevel(LOGGER_LEVEL)


def apply_page(file, event=None, ledger=ledger):
    if file[:4] == "http":
        r = requests.get(file)
        if r.status_code == 200:
            data = r.text
            logger.info(f"Downloaded {file}")
        else:
            raise ValueError(f"Could not download this file: {file}")
    else:
        with open(file, "r") as apply_file:
            data = apply_file.read()

    quick_parse = yaml.safe_load_all(
        data
    )  # Load as a dictionary so we can identify the object type it contains

    for document in quick_parse:
        if document["kind"] == "event":
            logger.info("Found an event")
            document.pop("kind")
            event = asimov.event.Event.from_yaml(yaml.dump(document))
            ledger.update_event(event)
            click.echo(
                click.style("●", fg="green") + f" Successfully applied {event.name}"
            )
            logger.info(f"Added {event.name} to project")

        elif document["kind"] == "analysis":
            logger.info("Found an analysis")
            document.pop("kind")
            if event:
                event_s = event
            else:
                if "event" in document:
                    event_s = document["event"]
                else:
                    prompt = "Which event should these be applied to?"
                    event_s = str(click.prompt(prompt))
            try:
                event_o = ledger.get_event(event_s)[0]
            except KeyError as e:
                click.echo(
                    click.style("●", fg="red")
                    + f" Could not apply a production, couldn't find the event {event}"
                )
                logger.exception(e)
            production = asimov.event.Production.from_dict(document, subject=event_o)
            try:
                ledger.add_analysis(production, event=event_o)
                click.echo(
                    click.style("●", fg="green")
                    + f" Successfully applied {production.name} to {event_o.name}"
                )
                logger.info(f"Added {production.name} to {event_o.name}")
            except ValueError as e:
                click.echo(
                    click.style("●", fg="red")
                    + f" Could not apply {production.name} to {event_o.name} as "
                    + "an analysis already exists with this name"
                )
                logger.exception(e)

        elif document["kind"].lower() == "postprocessing":
            # Handle a project analysis
            logger.info("Found a postprocessing description")
            document.pop("kind")
            if event:
                event_s = event

            if event:
                try:
                    event_o = ledger.get_event(event_s)[0]
                    level = event_o
                except KeyError as e:
                    click.echo(
                        click.style("●", fg="red")
                        + f" Could not apply postprocessing, couldn't find the event {event}"
                    )
                    logger.exception(e)
            else:
                level = ledger
            try:
                if document["name"] in level.data["postprocessing"]:
                    click.echo(
                        click.style("●", fg="red")
                        + f" Could not apply postprocessing, as {document['name']} is already in the ledger."
                    )
                    logger.error(
                        f" Could not apply postprocessing, as {document['name']} is already in the ledger."
                    )
                else:
                    if isinstance(level, asimov.event.Event):
                        level.meta["postprocessing"][document["name"]] = document
                    elif isinstance(level, Ledger):
                        level.data["postprocessing"][document["name"]] = document
                        level.name = "the project"
                    ledger.save()
                    click.echo(
                        click.style("●", fg="green")
                        + f" Successfully added {document['name']} to {level.name}."
                    )
                    logger.info(f"Added {document['name']}")
            except ValueError as e:
                click.echo(
                    click.style("●", fg="red")
                    + f" Could not apply {document['name']} to project as "
                    + "a post-process already exists with this name"
                )
                logger.exception(e)

        elif document["kind"].lower() == "projectanalysis":
            # Handle a project analysis
            logger.info("Found a project analysis")
            document.pop("kind")
            analysis = ProjectAnalysis.from_dict(document, ledger=ledger)

            try:
                ledger.add_analysis(analysis)
                click.echo(
                    click.style("●", fg="green")
                    + f" Successfully added {analysis.name} to this project."
                )
                ledger.save()
                logger.info(f"Added {analysis.name}")
            except ValueError as e:
                click.echo(
                    click.style("●", fg="red")
                    + f" Could not apply {analysis.name} to project as "
                    + "an analysis already exists with this name"
                )
                logger.exception(e)

        elif document["kind"] == "configuration":
            logger.info("Found configurations")
            document.pop("kind")
            update(ledger.data, document)
            ledger.save()
            click.echo(
                click.style("●", fg="green")
                + " Successfully applied a configuration update"
            )


def apply_via_plugin(event, hookname, **kwargs):
    discovered_hooks = entry_points(group="asimov.hooks.applicator")
    for hook in discovered_hooks:
        if hook.name in hookname:
            hook.load()(ledger).run(event)


@click.command()
@click.option("--file", "-f", help="Location of the file containing the ledger items.")
@click.option(
    "--event",
    "-e",
    help="The event which the ledger items should be applied to (e.g. for analyses)",
    default=None,
)
@click.option(
    "--plugin", "-p", help="The plugin to use to apply this data", default=None
)
def apply(file, event, plugin):
    if plugin:
        apply_via_plugin(event, hookname=plugin)
    elif file:
        apply_page(file, event)
