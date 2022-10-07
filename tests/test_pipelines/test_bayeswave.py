"""Tests for the LALInference interface."""

import unittest
import shutil
import os
import git

import io
import contextlib


from click.testing import CliRunner

from asimov.utils import set_directory
from asimov import config

from asimov.cli import project, manage
from asimov.cli import configuration
from asimov.cli.application import apply_page
from asimov.ledger import YAMLLedger
from asimov.event import Event
from asimov.pipeline import PipelineException
from asimov.pipelines.bayeswave import BayesWave
from asimov.event import Event
from asimov.pipeline import PipelineException

TEST_YAML = """
name: S000000xx
repository: {0}/tests/test_data/s000000xx/
working_directory: {0}/tests/tmp/s000000xx/
webdir: ''
productions:
- Prod1:
    rundir: {0}/tests/tmp/s000000xx/C01_offline/Prod1
    pipeline: bayeswave
    comment: PSD production
    status: wait

"""

class BayeswaveTests(unittest.TestCase):
    """Test bayeswave interface.

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
        pipeline = "bayeswave"
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{event}.yaml", event=None, ledger=self.ledger)
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{pipeline}.yaml", event=event, ledger=self.ledger)

        runner = CliRunner()
        result = runner.invoke(manage.build, "--dryrun")
        self.assertTrue("util_RIFT_pseudo_pipe.py" in result.output)

    def test_make_ini(self):
        """Check that a bayeswave config file can be built."""
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe.yaml", event=None, ledger=self.ledger)
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe-priors.yaml", event=None, ledger=self.ledger)
        event = "GW150914_095045"
        pipeline = "bayeswave"
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{event}.yaml", event=None, ledger=self.ledger)
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{pipeline}.yaml", event=event, ledger=self.ledger)

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            production = self.ledger.get_event(event)[0].productions[0]
            with set_directory(os.path.join("checkouts", event, config.get("general", "calibration_directory"))):
                production.make_config(f"{production.name}.ini")
            self.assertTrue(os.path.exists(os.path.join(config.get("project", "root"),
                                                        "checkouts",
                                                        event,
                                                        config.get("general", "calibration_directory"),
                                                        f"{production.name}.ini")))

        
    def test_build_api(self):
        """Check that a bayeswave DAG can be built."""
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe.yaml", event=None, ledger=self.ledger)
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe-priors.yaml", event=None, ledger=self.ledger)
        event = "GW150914_095045"
        pipeline = "bayeswave"
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{event}.yaml", event=None, ledger=self.ledger)
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{pipeline}.yaml", event=event, ledger=self.ledger)

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            production = self.ledger.get_event(event)[0].productions[0]
            with set_directory(os.path.join("checkouts", event, config.get("general", "calibration_directory"))):
                production.make_config(f"{production.name}.ini")
            production.pipeline.build_dag(dryrun=True)
            self.assertTrue("bayeswave_pipe" in f.getvalue())

    @unittest.skipIf(not os.path.exists(os.path.join(config.get("pipelines", "environment"), "bin", "bayeswave_pipe")),
                     "Bayeswave Pipe isnt installed on the test system")
    def test_submit_api(self):
        """Check that a RIFT config file can be built."""
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe.yaml", event=None, ledger=self.ledger)
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe-priors.yaml", event=None, ledger=self.ledger)
        event = "GW150914_095045"
        pipeline = "bayeswave"
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{event}.yaml", event=None, ledger=self.ledger)
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{pipeline}.yaml", event=event, ledger=self.ledger)

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            production = self.ledger.get_event(event)[0].productions[0]
            with set_directory(os.path.join("checkouts", event, config.get("general", "calibration_directory"))):
                production.make_config(f"{production.name}.ini")
            production.pipeline.build_dag(dryrun=False)

        with contextlib.redirect_stdout(f):
            production.pipeline.submit_dag(dryrun=True)
            self.assertTrue("bayeswave_pipe" in f.getvalue())

    def test_presubmit_mocked(self):
        """Check that a bayeswave submit file should be altered"""
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe.yaml", event=None, ledger=self.ledger)
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe-priors.yaml", event=None, ledger=self.ledger)
        event = "GW150914_095045"
        pipeline = "bayeswave"
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{event}.yaml", event=None, ledger=self.ledger)
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{pipeline}.yaml", event=event, ledger=self.ledger)

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            production = self.ledger.get_event(event)[0].productions[0]
            with set_directory(os.path.join("checkouts", event, config.get("general", "calibration_directory"))):
                production.make_config(f"{production.name}.ini")
            production.pipeline.build_dag(dryrun=True)
            self.assertTrue("bayeswave_pipe" in f.getvalue())
        os.makedirs(os.path.join(config.get("general", "rundir_default"), event, production.name))
        with set_directory(os.path.join(config.get("general", "rundir_default"), event, production.name)):
            with open("bayeswave_post.sub", "w") as submit_file:
                submit_file.write("This is some test text and is just garbage")

        production.pipeline.before_submit()

        with set_directory(os.path.join(config.get("general", "rundir_default"), event, production.name)):
            with open("bayeswave_post.sub", "r") as submit_file:
                self.assertTrue("request_disk" in submit_file.read())
