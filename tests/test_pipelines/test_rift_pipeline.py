"""Tests for the RIFT interface."""

import unittest
import shutil
import os
import git

import io
import contextlib

from click.testing import CliRunner

from asimov.cli import project, manage
from asimov.cli import configuration
from asimov.cli.application import apply_page
from asimov.ledger import YAMLLedger
from asimov.pipelines.rift import Rift
from asimov.event import Event
from asimov.pipeline import PipelineException


# @unittest.skip("Skipped until RIFT is added to the testing environment correctly.")
class RiftTests(unittest.TestCase):
    """Test RIFT interface.

    TODO
    ----
    Right now these feel a bit more like an expression of intention than actual tests, as we'll need to set the testing environment up better to make this work.

    The test_dag method will need to be updated.
"""

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

    @unittest.skip("Skipped temporarily while RIFT is updated")
    def test_build_cli(self):
        """Check that a RIFT config file can be built."""
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe.yaml", event=None, ledger=self.ledger)
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe-priors.yaml", event=None, ledger=self.ledger)
        event = "GW150914_095045"
        pipeline = "rift"
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{event}.yaml", event=None, ledger=self.ledger)
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{pipeline}.yaml", event=event, ledger=self.ledger)

        runner = CliRunner()
        result = runner.invoke(manage.build, "--dryrun")
        self.assertTrue("util_RIFT_pseudo_pipe.py" in result.output)

    def test_build_api(self):
        """Check that a RIFT config file can be built."""
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe.yaml", event=None, ledger=self.ledger)
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe-priors.yaml", event=None, ledger=self.ledger)
        event = "GW150914_095045"
        pipeline = "rift"
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{event}.yaml", event=None, ledger=self.ledger)
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{pipeline}.yaml", event=event, ledger=self.ledger)

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            self.ledger.get_event(event)[0].productions[0].pipeline.build_dag(dryrun=True)
            self.assertTrue("util_RIFT_pseudo_pipe.py --use-coinc COINC MISSING --l-max 4 --calibration C01 --add-extrinsic --approx SEOBNRv4PHM --cip-explode-jobs 3 --use-rundir working/GW150914_095045/RIFT0 --ile-force-gpu --use-ini INI MISSING" in f.getvalue())
        

    def test_build_api_non_default_calibration(self):
        """Check that a RIFT correctly picks up non C01 calibration."""

        runner = CliRunner()
        result = runner.invoke(configuration.update,
                               ['--general/calibration_directory', f"C00_offline"])
        assert result.exit_code == 0
        result = runner.invoke(configuration.update,
                               ['--general/calibration', f"C00"])
        assert result.exit_code == 0

        
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe.yaml", event=None, ledger=self.ledger)
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe-priors.yaml", event=None, ledger=self.ledger)
        event = "GW150914_095045"
        pipeline = "rift"
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{event}.yaml", event=None, ledger=self.ledger)
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{pipeline}.yaml", event=event, ledger=self.ledger)

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            self.ledger.get_event(event)[0].productions[0].pipeline.build_dag(dryrun=True)
            self.assertTrue("util_RIFT_pseudo_pipe.py --use-coinc COINC MISSING --l-max 4 --calibration C00 --add-extrinsic --approx SEOBNRv4PHM --cip-explode-jobs 3 --use-rundir working/GW150914_095045/RIFT0 --ile-force-gpu --use-ini INI MISSING" in f.getvalue())

