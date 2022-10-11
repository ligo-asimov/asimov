"""
This file contains code to allow unittests to be written with
Asimov so that productions can be tested with minimal boilerplate.
"""
import unittest
from asimov import current_ledger as ledger


class AsimovTest(unittest.TestCase):
    """
    Overloads the unittest.TestCase code.
    Simply makes `self.events` available to the test case.
    """

    @classmethod
    def setUpClass(cls):
        cls.events = ledger.get_event()
