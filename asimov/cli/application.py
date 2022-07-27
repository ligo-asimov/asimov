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
def apply(file):

    if file[:4] == "http":
        r = requests.get(file)
        if r.status_code == 200:
            data = r.text
    else:
        with open(file, "r") as apply_file:
            data = apply_file.read()

    quick_parse = yaml.safe_load(data) # Load as a dictionary so we can identify the object type it contains
        
    if quick_parse['kind'] == "event":
        event = asimov.event.Event.from_yaml(data)


    ledger.update_event(event)
