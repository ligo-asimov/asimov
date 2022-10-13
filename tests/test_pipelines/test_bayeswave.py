"""Tests for the LALInference interface."""

import unittest
from unittest.mock import Mock, patch

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

#    @unittest.skipIf(not os.path.exists(os.path.join(config.get("pipelines", "environment"), "bin", "bayeswave_pipe")),
#                    "Bayeswave Pipe isnt installed on the test system")
    @patch('subprocess.Popen')
    def test_submit_api(self, mock_popen):
        """Check that a bayeswave config file can be submitted."""
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
            # We need to make the workdir as this ought to be done by bayeswave_pipe
            os.makedirs(os.path.join("working", event, production.name))

            mock_popen.returncode=0
            mock_popen.return_value.communicate.return_value=(b"Blah blah blah To submit: just run this", b"Lots of stuff on stderr")

            production.pipeline.build_dag(dryrun=False)

        with contextlib.redirect_stdout(f):

            mock_popen.returncode=0
            mock_popen.return_value.communicate.return_value=(b"submitted to cluster 999", b"Lots of stuff on stderr")

            
            production.pipeline.submit_dag(dryrun=False)
            self.ledger.update_event(production.event)
        
        self.assertEqual(production.job_id, 999)
        self.assertEqual(self.ledger.get_event(event)[0].productions[0].job_id, 999)

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
        # We need to make the workdir as this ought to be done by bayeswave_pipe
        os.makedirs(os.path.join("working", event, production.name))
        with set_directory(os.path.join(config.get("general", "rundir_default"), event, production.name)):
            with open("bayeswave_post.sub", "w") as submit_file:
                submit_file.write("This is some test text and is just garbage")

        production.pipeline.before_submit()

        with set_directory(os.path.join(config.get("general", "rundir_default"), event, production.name)):
            with open("bayeswave_post.sub", "r") as submit_file:
                self.assertTrue("request_disk" in submit_file.read())

    @patch('subprocess.Popen.communicate')
    @patch('subprocess.Popen')
    def test_bad_dag_build(self, mock_popen, mock_pcomm):
        """Check that things behave as expected if the DAG file can't be build."""
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe.yaml", event=None, ledger=self.ledger)
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe-priors.yaml", event=None, ledger=self.ledger)
        event = "GW150914_095045"
        pipeline = "bayeswave"
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{event}.yaml", event=None, ledger=self.ledger)
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{pipeline}.yaml", event=event, ledger=self.ledger)

        mock_popen.returncode=1 #"Could not build the DAG file"
        mock_popen.return_value.communicate.return_value=(b"Could not be created", b"Lots of stuff on stderr")
        
        production = self.ledger.get_event(event)[0].productions[0]
        with set_directory(os.path.join("checkouts", event, config.get("general", "calibration_directory"))):
            production.make_config(f"{production.name}.ini")
        
        with self.assertRaises(PipelineException):
            production.pipeline.build_dag(dryrun=False)
