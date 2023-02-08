"""Tests for the Bilby interface."""

import unittest
import shutil
import os
import git

from click.testing import CliRunner
from asimov.pipelines.bilby import Bilby
from asimov.event import Event
from asimov.pipeline import PipelineException
from asimov import config
from asimov.cli import project
from asimov.cli import configuration
from asimov.cli import manage
from asimov.cli.application import apply_page
from asimov.ledger import YAMLLedger
import io
import contextlib

class BilbyTests(unittest.TestCase):
    """Test bilby interface"""

    @classmethod
    def setUpClass(cls):
        cls.cwd = os.getcwd()

    def setUp(self):
        os.makedirs(f"{self.cwd}/tests/tmp/project")
        os.chdir(f"{self.cwd}/tests/tmp/project")
        runner = CliRunner()
        result = runner.invoke(project.init,
                               ['Test Project', '--root', f"{self.cwd}/tests/tmp/project"])
        assert result.exit_code == 0
        assert result.output == '● New project created successfully!\n'
        self.ledger = YAMLLedger(f"ledger.yml")

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(f"{self.cwd}/tests/tmp/project/")

    @unittest.skip("I need to get this to work properly.")
    def test_build_cli(self):
        """Check that a bilby config file can be built."""
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe.yaml", event=None, ledger=self.ledger)
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe-priors.yaml", event=None, ledger=self.ledger)
        event = "GW150914_095045"
        pipeline = "bilby"
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{event}.yaml", event=None, ledger=self.ledger)
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{pipeline}.yaml", event=event, ledger=self.ledger)

        runner = CliRunner()
        result = runner.invoke(manage.build, "--dryrun")
        self.assertTrue("bilby_pipe" in result.output)

    def test_build_api(self):
        """Check that a bilby config file can be built."""
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe.yaml", event=None, ledger=self.ledger)
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe-priors.yaml", event=None, ledger=self.ledger)
        event = "GW150914_095045"
        pipeline = "bilby"
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{event}.yaml", event=None, ledger=self.ledger)
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{pipeline}.yaml", event=event, ledger=self.ledger)

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            self.ledger.get_event(event)[0].productions[0].pipeline.build_dag(dryrun=True)
            print(f.getvalue())
            self.assertTrue("bilby_pipe" in f.getvalue())
        
    def test_read_ini(self):
        """Check that a bilby ini file can be read correctly."""
        pass
