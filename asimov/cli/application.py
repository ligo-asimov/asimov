"""
Tools for adding data from JSON and YAML files.
Inspired by the kubectl apply approach from kubernetes.
"""

import yaml

import click
import requests

from asimov import current_ledger as ledger
from asimov.utils import update
import asimov.event


def apply_page(file, event, ledger=ledger):
    if file[:4] == "http":
        r = requests.get(file)
        if r.status_code == 200:
            data = r.text
        else:
            raise ValueError(f"Could not download this file: {file}")
    else:
        with open(file, "r") as apply_file:
            data = apply_file.read()

    quick_parse = yaml.safe_load_all(data) # Load as a dictionary so we can identify the object type it contains

    for document in quick_parse:

        if document['kind'] == "event":
            document.pop("kind")
            event = asimov.event.Event.from_yaml(yaml.dump(document))
            ledger.update_event(event)
            click.echo(click.style("●", fg="green") + f" Successfully applied {event.name}")

        elif document['kind'] == "analysis":
            document.pop("kind")
            if not event:
                prompt = "Which event should these be applied to?"
                event = str(click.prompt(prompt))

            event_o = ledger.get_event(event)[0]
            production = asimov.event.Production.from_dict(document, event=event_o)
            try:
                event_o.add_production(production)
                ledger.update_event(event_o)
                click.echo(click.style("●", fg="green") + f" Successfully applied {production.name} to {event_o.name}")
            except ValueError:
                click.echo(click.style("●", fg="red") + f" Could not apply {production.name} to {event_o.name} as an analysis already exists with this name")

        elif document['kind'] == "configuration":
            document.pop("kind")
            update(ledger.data, document)
            ledger.save()
            click.echo(click.style("●", fg="green") + f" Successfully applied a configuration update")


@click.command()
@click.option("--file", "-f", 
              help="Location of the file containing the ledger items.")
@click.option("--event", "-e",
              help="The event which the ledger items should be applied to (e.g. for analyses)",
              default=None)
def apply(file, event):
    apply_page(file, event)
