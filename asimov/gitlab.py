"""
Code for interacting with a gitlab instance.
"""
import datetime
import time
import configparser

import gitlab
import yaml
from liquid import Liquid

from asimov import config

from .event import Event
from .ledger import Ledger

STATE_PREFIX = "C01"


class GitlabLedger(Ledger):
    """
    Connect to a gitlab-based issue tracker.
    """

    def __init__(
        self, configs, milestone=None, subset=None, update=False, repo=True, label=None
    ):
        """
        Search through a repository's issues and find all of the ones
        for events.
        """

        _, self.repository = self._connect_gitlab()

        if subset == [None]:
            subset = None
        if not label:
            event_label = config.get("gitlab", "event_label")
        else:
            event_label = label
        try:
            sleep_time = int(config.get("gitlab", "rest_time"))
        except configparser.NoOptionError:
            sleep_time = 30
        issues = self.repository.issues.list(labels=[event_label], per_page=1000)
        output = []
        if subset:
            for issue in issues:
                if issue.title in subset:
                    output += [EventIssue(issue, self.repository, update, repo=repo)]
                    if update:
                        time.sleep(sleep_time)
        else:
            for issue in issues:
                output += [EventIssue(issue, self.repository, update, repo=repo)]
                if update:
                    time.sleep(sleep_time)

        self.data["events"] = output
        self.events = {ev["name"]: ev for ev in self.data["events"]}

    def _connect_gitlab(self):
        """
        Connect to the gitlab server.

        Returns
        -------
        server : `Gitlab`
           The gitlab server.
        repository: `Gitlab.project`
           The gitlab project.
        """
        server = gitlab.gitlab.Gitlab(
            config.get("gitlab", "server"), private_token=config.get("gitlab", "token")
        )
        repository = server.projects.get(config.get("gitlab", "tracking_repository"))
        return server, repository

    def get_event(self, event=None):
        if event:
            return self.events[event]
        else:
            return self.events.values()

    @classmethod
    def add_event(self, event_object, issue_template=None):
        """
        Create an issue for an event.
        """

        if not issue_template:
            from pkg_resources import resource_filename

            issue_template = resource_filename("asimov", "gitlabissue.md")

        with open(issue_template, "r") as template_file:
            liq = Liquid(template_file.read())
            rendered = liq.render(
                event_object=event_object, yaml=event_object.to_yaml()
            )

        self.repository.issues.create(
            {"title": event_object.name, "description": rendered}
        )

    def update_event(self, event):
        event.update_data()

    def save(self):
        pass

    @classmethod
    def create(cls):
        raise NotImplementedError(
            "You must create a gitlab issue tracker manually first."
        )

    pass


class EventIssue(Event):
    """
    Use an issue on the gitlab issue tracker to
    hold variable data for the program.

    Parameters
    ----------
    issue : `gitlab.issue`
       The issue which represents the event.
    update : bool
       Flag to determine if the git repository is updated
       when it is loaded. Defaults to False to prevent
       excessive load on the git server.
    """

    def __init__(self, issue, repository, update=False, repo=True):

        self.from_issue(self, issue, update, repo)

        self.issue_object = issue
        self.title = issue.title
        self.text = issue.description

        self.issue_id = issue.id
        self.labels = issue.labels
        self.data = self.parse_notes()

    def from_issue(self, issue, update=False, repo=True):
        """
        Parse an issue description to generate this event.


        Parameters
        ----------
        update : bool
           Flag to determine if the repository is updated when loaded.
           Defaults to False.
        """

        text = issue.text.split("---")

        event = self.from_yaml(text[1], issue, update=update, repo=repo)
        event.text = text
        # event.from_notes()

        return event

    def _refresh(self):
        if self.repository:
            self.issue_object = self.repository.issues.get(self.issue_object.iid)
            self.text = self.issue_object.description.split("---")
        else:
            pass

    @property
    def state(self):
        """
        Get the state of the event's runs.
        """
        for label in self.issue_object.labels:
            if f"{STATE_PREFIX}::" in label:
                return label[len(STATE_PREFIX) + 2:]
        return None

    @state.setter
    def state(self, state):
        """
        Set the event state.
        """
        self._refresh()
        for label in self.issue_object.labels:
            if f"{STATE_PREFIX}::" in label:
                # Need to remove all of the other scoped labels first.
                self.issue_object.labels.remove(label)
        self.issue_object.labels += ["{}::{}".format(STATE_PREFIX, state)]
        self.issue_object.save()

    def add_note(self, text):
        """
        Add a comment to the event issue.
        A footer will be added to identify this as being created by the
        supervisor and not the user.
        """
        self._refresh()
        now = datetime.datetime.now()
        header = """"""
        footer = f"""\nAdded at {now:%H}:{now:%M}, {now:%Y}-{now:%m}-{now:%d} by the run supervision robot :robot:."""
        self.issue_object.notes.create({"body": header + text + footer})
        self.issue_object.save()

    def add_label(self, label, state=True):
        """
        Add a new label to an event issue.

        Parameters
        ----------
        label : str
           The name of the label.
        """
        self._refresh()
        if state:
            self.issue_object.labels += [f"{STATE_PREFIX}:{label}"]
        else:
            self.issue_object.labels += [f"{label}"]

        self.issue_object.save()

    def update_data(self):
        """
        Store event data in the comments on the event repository.
        """
        self._refresh()

        self.issue_object.description = self.event_object.to_issue()

        self.issue_object.save()

    def parse_notes(self):
        """
        Read issue information from the comments on the issue.

        Only notes which start
        ```
        # Run information
        ```
        will be parsed.
        """
        data = {}
        notes = self.issue_object.notes.list(per_page=200)
        note_data = []
        for note in reversed(notes):
            if "---\n" in note.body:
                data = note.body.split("---")
                if len(data) > 0:
                    data = data[1]
                else:
                    continue
                data = yaml.safe_load(data)
                note_data.append(data)
        return note_data
