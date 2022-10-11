import json
from math import floor
import click


@click.option("--event", "event", default=None, help="The event which will be updated")
@click.option("--json", "json_data", default=None)
@click.command(help="Add data from the configurator.")
def configurator(event, json_data=None):
    """
    Add data from the PEConfigurator script to an event.
    """

    if json_data:
        with open(json_data, "r") as datafile:
            data = json.load(datafile)

    new_data = {"quality": {}, "priors": {}}
    new_data["quality"]["sample-rate"] = data["srate"]
    new_data["quality"]["lower-frequency"] = {}
    new_data["quality"]["upper-frequency"] = int(0.875 * data["srate"] / 2)
    new_data["quality"]["start-frequency"] = data["f_start"]
    new_data["quality"]["segment-length"] = data["seglen"]
    new_data["quality"]["window-length"] = data["seglen"]
    new_data["quality"]["psd-length"] = data["seglen"]

    def decide_fref(freq):
        if (freq >= 5) and (freq < 10):
            return 5
        else:
            return floor(freq / 10) * 10

    new_data["quality"]["reference-frequency"] = decide_fref(data["f_ref"])

    new_data["priors"]["amp order"] = data["amp_order"]
    new_data["priors"]["chirp-mass"] = [data["chirpmass_min"], data["chirpmass_max"]]
