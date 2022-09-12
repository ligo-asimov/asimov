import os
import shutil
import unittest

import click

import asimov.event
from asimov.ledger import YAMLLedger
from asimov.cli.project import make_project
from asimov.cli.application import apply_page
import git


TEST_LEDGER = """

"""

class DAGTests(unittest.TestCase):
    """All the tests to check production DAGs are generated successfully."""
    @classmethod
    def setUpClass(cls):
        cls.cwd = os.getcwd()
        # repo = git.Repo.init(cls.cwd+"/tests/test_data/s000000xx/")
        # os.chdir(cls.cwd+"/tests/test_data/s000000xx/")
        # os.system("git add C01_offline/Prod3_test.ini C01_offline/s000000xx_gpsTime.txt")
        # os.system("git commit -m 'test'")
        # os.chdir(cls.cwd)
    
    @classmethod
    def tearDownClass(cls):
        """Destroy all the products of this test."""
        # os.system("rm asimov.conf")
        # os.system(f"rm -rf {cls.cwd}/tests/tmp/")
        # os.system(f"rm -rf {cls.cwd}/tests/test_data/s000000xx/.git")
        # try:
        #     shutil.rmtree("/tmp/S000000xx")
        # except:
        #     pass

    #
    def setUp(self):
        os.makedirs(f"{self.cwd}/tests/tmp/project")
        os.chdir(f"{self.cwd}/tests/tmp/project")
        make_project(name="Test project", root=f"{self.cwd}/tests/tmp/project")
        self.ledger = YAMLLedger(f"ledger.yml")
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe.yaml", event=None, ledger=self.ledger)
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/events/gwtc-2-1/GW150914_095045.yaml", event=None, ledger=self.ledger)
        
    def tearDown(self):
        shutil.rmtree(f"{self.cwd}/tests/tmp/")
    
    def test_simple_dag(self):
        """Check that all jobs are run when there are no dependencies specified."""
        apply_page(file = f"{self.cwd}/tests/test_data/test_simple_dag.yaml", event='GW150914_095045', ledger=self.ledger)
        event = self.ledger.get_event('GW150914_095045')[0]
        self.assertEqual(len(event.get_all_latest()), 2)
    
    def test_linear_dag(self):
        """Check that all jobs are run when the dependencies are a chain."""
        apply_page(file = f"{self.cwd}/tests/test_data/test_linear_dag.yaml", event='GW150914_095045', ledger=self.ledger)
        event = self.ledger.get_event('GW150914_095045')[0]
        self.assertEqual(len(event.get_all_latest()), 1)
        

    def test_complex_dag(self):
        """Check that all jobs are run when the dependencies are not a chain."""

        apply_page(file = f"{self.cwd}/tests/test_data/test_complex_dag.yaml", event='GW150914_095045', ledger=self.ledger)
        event = self.ledger.get_event('GW150914_095045')[0]

        self.assertEqual(len(event.get_all_latest()), 2)
