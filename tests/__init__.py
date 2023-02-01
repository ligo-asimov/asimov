"""
This module contains the factory classes for other asimov tests.
"""

import os
import unittest
import shutil
import git
from asimov.cli.project import make_project
from asimov.ledger import YAMLLedger


class AsimovTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cwd = os.getcwd()
        git.Repo.init(cls.cwd + "/tests/test_data/s000000xx/")

    def setUp(self):
        os.makedirs(f"{self.cwd}/tests/tmp/project")
        os.chdir(f"{self.cwd}/tests/tmp/project")
        make_project(name="Test project", root=f"{self.cwd}/tests/tmp/project")
        self.ledger = YAMLLedger(f"ledger.yml")

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(f"{self.cwd}/tests/tmp/")
