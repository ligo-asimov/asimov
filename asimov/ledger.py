"""
Code for the project ledger.
"""

import yaml
import asimov
from asimov.event import Event

class Ledger:
    def __init__(self, location="ledger.yml"):
        self.location = location
        with open(location, "r") as ledger_file:
            self.data = yaml.safe_load(ledger_file)

        
        self.events = {ev['name']: ev for ev in self.data['events']}
        self.data.pop("events")

    @classmethod
    def create(cls, location="ledger.yml"):

        data = {}
        data['asimov'] = asimov.__version__
        data['events'] = []

        with open(location, "w") as ledger_file:
            ledger_file.write(
                yaml.dump(data, default_flow_style=False))

    def save(self):
        self.data['events'] = list(self.events.values())
        with open(self.location, "w") as ledger_file:
            ledger_file.write(
                yaml.dump(self.data, default_flow_style=False))
            
    def add_event(self, event):
        if "events" not in self.data:
            self.data['events'] = []

        self.events[event.name] = event.to_dict()
        self.save()

    def get_event(self, event=None):
        if event:
            return Event(**self.events[event])
        else:
            return [Event(**self.events[event]) for event in self.events.keys()]
