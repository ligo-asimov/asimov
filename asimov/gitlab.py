"""
Code for interacting with a gitlab instance.
"""
import yaml

from .event import Event
from . import config
import gitlab

import re
import datetime

from liquid import Liquid

STATE_PREFIX = "C01"

def find_events(repository, milestone=None, subset=None):
    """
    Search through a repository's issues and find all of the ones
    for events.
    """

    event_label = config.get("gitlab", "event_label")
    issues = repository.issues.list(labels=[event_label], 
                                    milestone=milestone,
                                    per_page=1000)
    if subset:
        return [EventIssue(issue, repository) for issue in issues if issue.title in subset]
    else:
        return [EventIssue(issue, repository) for issue in issues]

class EventIssue(object):
    """
    Use an issue on the gitlab issue tracker to 
    hold variable data for the program.

    Parameters
    ----------
    issue : `gitlab.issue`
       The issue which represents the event.
    """

    def __init__(self, issue, repository):
        print(issue.title)
        self.issue_object = issue
        print(issue.title)
        self.title = issue.title
        self.text = issue.description
        
        self.issue_id = issue.id
        self.labels = issue.labels
        self.data = self.parse_notes()
        self.repository = repository
        self.event_object=None
        self.event_object = Event.from_issue(self)
        

    def _refresh(self):
        self.issue_object = self.repository.issues.get(self.issue_object.iid)
        if self.event_object:
            self.event_object.text = self.issue_object.description.split("---")

    @classmethod
    def create_issue(cls, repository, event_object, issue_template=None):
        """
        Create an issue for an event.
        """

        if issue_template:
            with open(issue_template, "r") as template_file:
                liq = Liquid(template_file.read())
                rendered = liq.render(event_object=event_object, yaml = event_object.to_yaml())
        else:
            rendered = event_object.to_yaml()
            
        repository.issues.create({'title': event_object.name,
                                       'description': rendered})
            
    @property
    def productions(self):
        """List the productions on this event."""
        return self.event_object.productions
        
    @property
    def state(self):
        """
        Get the state of the event's runs.
        """
        for label in self.issue_object.labels:
            if f"{STATE_PREFIX}::" in label:
                return label[len(STATE_PREFIX)+2:]
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
        self.issue_object.notes.create({"body": header+text+footer})
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
        keyval = r"([\w]+):[\s]*([ \w\#\/\,\.-]+)"
        notes = self.issue_object.notes.list(per_page=200)
        note_data = []
        for note in reversed(notes):
            if "---\n" in note.body:
                data = note.body.split("---")
                if len(data)>0: 
                    data=data[1]
                else: 
                    continue
                data = yaml.safe_load(data)
                note_data.append(data)
        return data
