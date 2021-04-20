"""
This module contains tools to log data from runs.
Unlike a conventional python process, processes run by asimov may wish to send information to a number of different locations, and store
information for review purposes.
"""

import logging
import os

from asimov import mattermost

from asimov import config
from .gitlab import EventIssue

class AsimovLogger():

    def __init__(self, event):
        """
        An object for logging asimov productions.

        Parameters
        ----------
        event : ``asimov.event.Event``
           The event which this logger is for.
        """

        self.event_object = event
        self.event_issue = event.issue_object
        self.mattermost = mattermost.Mattermost()
        if event.work_dir:
            log_dir = event.work_dir
        else:
            log_dir = os.getcwd()
        self.log_file = f"{log_dir}/asimov.log"
        self.file_logger = logging.basicConfig(filename=self.log_file, level=logging.DEBUG)
        
    def log(self, level, message, production=None, channels="file"):
        """
        Record a log message.

        Parameters
        ----------
        level : str, {DEBUG, INFO, WARNING, ERROR}
           The level of the logging message.
        production : ``asimov.event.Production``, optional
           The production this message is for.
        message : str
           The free-form message for the log message.
        channels : list, or str, {"file", "mattermost", "gitlab"}, optional
           The list of places where the log message should be sent.
           Defaults to file only.
        """

        logger_levels = {"debug": logging.DEBUG,
                         "info": logging.INFO,
                         "warning": logging.WARNING,
                         "error": logging.ERROR}

        if not production:
            production = ""
        
        if "file" in channels:
            logging.log(logger_levels[level.lower()],
                                 message)

        if "mattermost" in channels:
            self.mattermost.send_message(f":mega: {self.event_object.name} {production} {message} :robot:")

        if "gitlab" in channels:
            self.event_issue.add_note(message)
            
        
    def info(self, message, production=None, channels="file"):
        """
        Record an information message.

        Parameters
        ----------

        production : ``asimov.event.Production``, optional
           The production this message is for.
        message : str
           The free-form message for the log message.
        channels : list, or str, {"file", "mattermost", "gitlab"}, optional
           The list of places where the log message should be sent.
           Defaults to file only.
        """

        self.log("info", message, production, channels)

    def error(self, message, production=None, channels="file"):
        """
        Record an error message.

        Parameters
        ----------

        production : ``asimov.event.Production``, optional
           The production this message is for.
        message : str
           The free-form message for the log message.
        channels : list, or str, {"file", "mattermost", "gitlab"}, optional
           The list of places where the log message should be sent.
           Defaults to file only.
        """

        self.log("error", message, production, channels)

    def warning(self, message, production=None, channels="file"):
        """
        Record an warning message.

        Parameters
        ----------

        production : ``asimov.event.Production``, optional
           The production this message is for.
        message : str
           The free-form message for the log message.
        channels : list, or str, {"file", "mattermost", "gitlab"}, optional
           The list of places where the log message should be sent.
           Defaults to file only.
        """

        self.log("warning", message, production, channels)
