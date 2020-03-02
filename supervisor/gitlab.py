"""
Code for interacting with a gitlab instance.
"""

from . import config
import gitlab

import re

STATE_PREFIX = "C01"

def find_events(repository, milestone=None):
    """
    Search through a repository's issues and find all of the ones
    for events.
    """

    event_label = config.get("gitlab", "event_label")
    issues = repository.issues.list(labels=[event_label], 
                                    milestone=milestone,
                                    per_page=1000)

    return [EventIssue(issue) for issue in issues]


class EventIssue(object):
    """
    Use an issue on the gitlab issue tracker to 
    hold variable data for the program.

    Parameters
    ----------
    issue : `gitlab.issue`
       The issue which represents the event.
    """

    def __init__(self, issue):
        self.issue_object = issue
        self.title = issue.title
        self.issue_id = issue.id
        self.labels = issue.labels
        self.data = self.parse_notes()

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
        self.issue_object.labels += ["{}::{}".format(STATE_PREFIX, state)]
        self.issue_object.save()

    def update_data(self):
        """
        Store event data in the comments on the event repository.
        """

        notes = self.issue_object.notes.list(per_page=200)
        for note in reversed(notes):
            if "# Run information" in note.body:
                try:
                    note.delete()
                except:
                    pass

        message = ""
        header = "# Run information\nAdded by the run supervising robot :robot:.\n```\n"
        for key, val in self.data.items():
            message += f"{key}: {val}\n"
        footer = "```"
        self.issue_object.notes.create({"body": header+message+footer})
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
        keyval = r"([\w]+):[\s]*([\w\/\.-]+)"
        notes = self.issue_object.notes.list(per_page=200)
        for note in reversed(notes):
            if "# Run information" in note.body:
                for match in re.finditer(keyval, note.body):
                    key, val = match.groups()
                    data[key] = val
        self.data = data
        return data
