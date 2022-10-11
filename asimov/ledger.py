"""
Code for the project ledger.
"""
from copy import deepcopy
from functools import reduce

import yaml

import asimov
import asimov.database
from asimov import config
from asimov.event import Event, Production
from asimov.utils import update


class Ledger:
    @classmethod
    def create(cls, name=None, engine=None, location=None):
        """
        Create a ledger.
        """

        if not engine:
            engine = config.get("ledger", "engine")

        if engine == "yamlfile":
            YAMLLedger.create(location=location, name=name)

        elif engine in {"tinydb", "mongodb"}:
            DatabaseLedger.create()
        elif engine == "gitlab":
            raise NotImplementedError(
                "This hasn't been ported to the new interface yet. Stay tuned!"
            )

        elif engine == "gitlab":
            raise NotImplementedError(
                "This hasn't been ported to the new interface yet. Stay tuned!"
            )


class YAMLLedger(Ledger):
    def __init__(self, location="ledger.yml"):
        self.location = location
        with open(location, "r") as ledger_file:
            self.data = yaml.safe_load(ledger_file)

        self.data["events"] = [
            update(self.get_defaults(), event, inplace=False)
            for event in self.data["events"]
        ]
        self.events = {ev["name"]: ev for ev in self.data["events"]}
        self.data.pop("events")

    @classmethod
    def create(cls, name, location="ledger.yml"):

        data = {}
        data["asimov"] = {}
        data["asimov"]["version"] = asimov.__version__
        data["events"] = []
        data["project"] = {}
        data["project"]["name"] = name
        with open(location, "w") as ledger_file:
            ledger_file.write(yaml.dump(data, default_flow_style=False))

    def update_event(self, event):
        """
        Update an event in the ledger with a changed event object.
        """
        self.events[event.name] = event.to_dict()
        self.save()

    def delete_event(self, event_name):
        """
        Remove an event from the ledger.

        Parameters
        ----------
        event_name : str
           The name of the event to remove from the ledger.
        """
        event = self.events.pop(event_name)
        if "trash" not in self.data:
            self.data["trash"] = {}
        if "events" not in self.data["trash"]:
            self.data["trash"]["events"] = {}
        self.data["trash"]["events"][event_name] = event
        self.save()

    def save(self):
        """
        Update the ledger YAML file with the data from the various events.

        Notes
        -----
        The save function checks the difference between the default values for each production and event
        before saving them, in order to attempt to reduce the duplication within the ledger.


        """
        self.data["events"] = list(self.events.values())

        categories = {"priors", "sampler", "likelihood", "quality", "data", "scheduler"}
        for category in categories:
            for i, event in enumerate(self.data["events"]):
                overloaded = {}
                if category in event.keys():
                    event_data = self.data["events"][i].pop(category)
                    for prior, values in event_data.items():
                        if category in self.data:
                            inherited = self.data[category]
                            if isinstance(values, dict):
                                overload_inner = {}
                                for key, value in values.items():
                                    if value != inherited[prior][key]:
                                        overload_inner[key] = value
                                if len(overload_inner) > 0:
                                    overloaded[prior] = overload_inner
                                    # print(overloaded)
                            elif values != inherited[prior]:
                                overloaded[prior] = values
                        else:
                            overloaded = event_data
                        if len(overloaded) > 0:
                            if category not in self.data["events"][i]:
                                self.data["events"][i][category] = {}
                            self.data["events"][i][category] = update(
                                deepcopy(self.data["events"][i][category]),
                                overloaded,
                                inplace=False,
                            )

        for category in categories:
            for i, event in enumerate(self.data["events"]):
                for prod_i, production in enumerate(event["productions"]):
                    prod_name = list(production.keys())[0]
                    overloaded = {}
                    inherited = {}
                    if category in event["productions"][prod_i][prod_name].keys():
                        production_data = self.data["events"][i]["productions"][prod_i][
                            prod_name
                        ].pop(category)
                        for prior, values in production_data.items():
                            if "pipeline" in production[prod_name]:
                                if (
                                    production[prod_name]["pipeline"]
                                    in self.data["pipelines"]
                                ):
                                    if (
                                        category
                                        in self.data["pipelines"][
                                            production[prod_name]["pipeline"]
                                        ]
                                    ):
                                        inherited = update(
                                            inherited,
                                            self.data["pipelines"][
                                                production[prod_name]["pipeline"]
                                            ][category],
                                            inplace=False,
                                        )
                            if category in self.data:
                                inherited = update(
                                    inherited, self.data[category], inplace=False
                                )
                            if category in self.data["events"][i]:
                                inherited = update(
                                    inherited,
                                    self.data["events"][i][category],
                                    inplace=False,
                                )

                            if isinstance(values, dict):
                                overload_inner = {}
                                for key, value in values.items():
                                    if prior in inherited:
                                        if value != inherited[prior][key]:
                                            overload_inner[key] = value
                                    else:
                                        overload_inner[key] = value
                                if len(overload_inner) > 0:
                                    overloaded[prior] = overload_inner
                            elif values != inherited[prior]:
                                overloaded[prior] = values
                        else:
                            overloaded = production_data
                        if len(overloaded) > 0:
                            if (
                                category
                                not in self.data["events"][i]["productions"][prod_i][
                                    prod_name
                                ]
                            ):
                                self.data["events"][i]["productions"][prod_i][
                                    prod_name
                                ][category] = {}
                            self.data["events"][i]["productions"][prod_i][prod_name][
                                category
                            ] = update(
                                self.data["events"][i]["productions"][prod_i][
                                    prod_name
                                ][category],
                                overloaded,
                                inplace=False,
                            )

        with open(self.location, "w") as ledger_file:
            ledger_file.write(yaml.dump(self.data, default_flow_style=False))

    def add_event(self, event):
        if "events" not in self.data:
            self.data["events"] = []

        self.events[event.name] = event.to_dict()
        self.save()

    def add_production(self, event, production):
        event.add_production(production)
        self.events[event.name] = event.to_dict()
        self.save()

    def get_defaults(self):
        """
        Gather project-level defaults from the ledger.

        At present data, quality, priors, and likelihood settings can all be set at a project level as defaults.
        """
        defaults = {}
        if "data" in self.data:
            defaults["data"] = self.data["data"]
        if "priors" in self.data:
            defaults["priors"] = self.data["priors"]
        if "quality" in self.data:
            defaults["quality"] = self.data["quality"]
        if "likelihood" in self.data:
            defaults["likelihood"] = self.data["likelihood"]
        if "scheduler" in self.data:
            defaults["scheduler"] = self.data["scheduler"]
        return defaults

    def get_event(self, event=None):
        if event:
            return [Event(**self.events[event], ledger=self)]
        else:
            return [
                Event(**self.events[event], ledger=self) for event in self.events.keys()
            ]

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
            productions = filter(
                lambda x: x.meta[parameter] == value
                if (parameter in x.meta)
                else (
                    getattr(x, parameter) == value if hasattr(x, parameter) else False
                ),
                productions,
            )
            return productions

        if filters:
            for parameter, value in filters.items():
                productions = apply_filter(productions, parameter, value)
        return list(productions)


class DatabaseLedger(Ledger):
    """
    Use a document database to store the ledger.
    """

    def __init__(self):
        if config.get("ledger", "engine") == "tinydb":
            self.db = asimov.database.AsimovTinyDatabase()
        else:
            self.db = asimov.database.AsimovTinyDatabase()

    @classmethod
    def create(cls):
        ledger = cls()
        ledger.db._create()
        return ledger

    def _insert(self, payload):
        """
        Store the payload in the correct database table.
        """

        if isinstance(payload, Event):
            id_number = self.db.insert("event", payload.to_dict(productions=False))
        elif isinstance(payload, Production):
            id_number = self.db.insert("production", payload.to_dict(event=False))

        return id_number

    @property
    def events(self):
        """
        Return all of the events in the ledger.
        """
        return [Event.from_dict(page) for page in self.db.tables["event"].all()]

    def get_defaults(self):
        raise NotImplementedError

    def get_event(self, event=None):
        """
        Find a specific event in the ledger and return it.
        """
        event_dict = self.db.query("event", "name", event)[0]
        return Event.from_dict(event_dict)

    def get_productions(self, event, filters=None, query=None):
        """
        Get all of the productions for a given event.
        """

        if not filters and not query:
            productions = self.db.query("production", "event", event)

        else:
            queries_1 = self.db.Q["event"] == event
            queries = [
                self.db.Q[parameter] == value for parameter, value in filters.items()
            ]
            productions = self.db.tables["production"].search(
                queries_1 & reduce(lambda x, y: x & y, queries)
            )

        event = self.get_event(event)
        return [
            Production.from_dict(dict(production), event) for production in productions
        ]

    def add_event(self, event):
        self._insert(event)

    def add_production(self, production):
        self._insert(production)
