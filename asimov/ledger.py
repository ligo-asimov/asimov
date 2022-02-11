"""
Code for the project ledger.
"""

import yaml
import asimov
from asimov.event import Event
from asimov import config

class Ledger:
    @classmethod
    def create(cls, engine=None, location=None):
        """
        Create a ledger.
        """

        if not engine:
            engine = config.get("ledger", "engine")

        if engine == "yamlfile":
            YAMLLedger.create(location)
        elif engine == "gitlab":
            raise NotImplementedError("This hasn't been ported to the new interface yet. Stay tuned!")
            
    pass

class YAMLLedger(Ledger):
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

    def update_event(self, event):
        """
        Update an event in the ledger with a changed event object.
        """
        self.events[event.name] = event.to_dict()
        self.save()
            
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

    def add_production(self, event, production):
        event.add_production(production)
        self.events[event.name] = event.to_dict()
        self.save()

        
    def get_event(self, event=None):
        if event:
            return Event(**self.events[event])
        else:
            return [Event(**self.events[event]) for event in self.events.keys()]

    def get_productions(self, event=None, filters=None):
        """Get a list of productions either for a single event or for all events.

        Parameters
        ----------
        event : str
           The name of the event to pull productions from.
           Optional; if no event is specified then all of the productions are
           returned.

        filters : dict
           A dictionary of parameters to filter on.

        Examples
        --------
        FIXME: Add docs.

        """

        if event:
            productions = self.get_event(event).productions
        else:
            productions = []
            for event_i in self.get_event():
                for production in event_i.productions:
                    productions.append(production)

        def apply_filter(productions, parameter, value):
            productions = filter(lambda x: x.meta[parameter] == value
                                 if (parameter in x.meta)
                                 else (getattr(x, parameter) == value
                                       if hasattr(x, parameter) else False),
                                 productions)
            return productions

        if filters:
            for parameter, value in filters.items():
                productions = apply_filter(productions, parameter, value)
        return list(productions)
