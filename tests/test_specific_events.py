"""
These tests are designed to verify that specific tests produce specific 
outputs for each pipeline.
"""
import os
import unittest
import shutil
import git
import asimov.event
from asimov.cli.project import make_project
from asimov.cli.application import apply_page
from asimov.ledger import YAMLLedger

pipelines = {"bayeswave", "bilby", "rift"}
EVENTS = {"GW150914_095045", "GW190924_021846", "GW190929_012149", "GW191109_010717"}

class TestGravitationalWaveEvents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cwd = os.getcwd()
        git.Repo.init(cls.cwd+"/tests/test_data/s000000xx/")
        
    def setUp(self):
        os.makedirs(f"{self.cwd}/tests/tmp/project")
        os.chdir(f"{self.cwd}/tests/tmp/project")
        make_project(name="Test project", root=f"{self.cwd}/tests/tmp/project")
        self.ledger = YAMLLedger(f"ledger.yml")
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe.yaml", event=None, ledger=self.ledger)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(f"{self.cwd}/tests/tmp/")

    def test_fiducial_events(self):
        for event in EVENTS:
            for pipeline in pipelines:
                with self.subTest(event=event, pipeline=pipeline):
                    apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{event}.yaml", event=None, ledger=self.ledger)
                    apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{pipeline}.yaml", event=event, ledger=self.ledger)

                    event_o = self.ledger.get_event(event)[0]
                    production = event_o.productions[0]
                    production.make_config(f"{self.cwd}/tests/tmp/test_config.ini")
