"""
This file contains code to allow unittests to be written with
Asimov so that productions can be tested with minimal boilerplate.
"""
from asimov.gitlab import find_events
from asimov import gitlab
from asimov import config
from asimov.cli import connect_gitlab


_, repository = connect_gitlab()

import unittest


class AsimovTest(unittest.TestCase):
    """
    Overloads the unittest.TestCase code.
    Simply makes `self.events` available to the test case.
    """
    @classmethod
    def setUpClass(cls):
        _, repository = connect_gitlab()
        cls.events = gitlab.find_events(repository)
