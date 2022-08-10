"""
Tools for adding data from JSON and YAML files.
Inspired by the kubectl apply approach from kubernetes.
"""

import yaml

import click
import requests

from asimov import current_ledger as ledger

import asimov.event

@click.command()
@click.option("--file", "-f", 
              help="Location of the file containing the ledger items.")
@click.option("--event", "-e",
              help="The event which the ledger items should be applied to (e.g. for analyses)",
              default=None)
def apply(file, event):

    if file[:4] == "http":
        r = requests.get(file)
        if r.status_code == 200:
            data = r.text
    else:
        with open(file, "r") as apply_file:
            data = apply_file.read()

    quick_parse = yaml.safe_load_all(data) # Load as a dictionary so we can identify the object type it contains

    for document in quick_parse:

        if document['kind'] == "event":
            document.pop("kind")
            event = asimov.event.Event.from_yaml(yaml.dump(document))
            ledger.update_event(event)

        if document['kind'] == "analysis":
            document.pop("kind")
            if not event:
                prompt = "Which event should these be applied to?"
                event = click.prompt(prompt)

            event = ledger.get_event(event)
            production = asimov.event.Production.from_dict(document, event=event)
            event.add_production(production)
            ledger.update_event(event)
