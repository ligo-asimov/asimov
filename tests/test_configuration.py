"""
Tests for general configuration variables.
"""

import unittest
import os
import shutil
from click.testing import CliRunner
from asimov import config
from asimov.cli import project
from asimov.cli import configuration
from asimov.cli import manage
from asimov.cli.application import apply_page
from asimov.ledger import YAMLLedger

class TestCategories(unittest.TestCase):
    """Test that categories, e.g. calibration epochs, are used correctly."""

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

    def tearDown(self):
        shutil.rmtree(f"{self.cwd}/tests/tmp/")

    def testCategoryUpdate(self):
        """Check that the category is updated in the config file."""
        runner = CliRunner()
        result = runner.invoke(configuration.update,
                               ['--general/calibration_directory', f"C00_offline"])
        assert result.exit_code == 0
        new_content = runner.invoke(configuration.show,
                               ['--key', 'general/calibration_directory',])
        assert new_content.output.strip() == f"C00_offline"

    def testCategoryDirectory(self):
        """Check that the category is used to create the directory in the git repo."""
        runner = CliRunner()
        result = runner.invoke(configuration.update,
                               ['--general/calibration_directory', f"C00_offline"])
        assert result.exit_code == 0
        self.ledger = YAMLLedger(f"ledger.yml")
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe.yaml", event=None, ledger=self.ledger)
        apply_page(file = "https://git.ligo.org/asimov/data/-/raw/main/defaults/production-pe-priors.yaml", event=None, ledger=self.ledger)
        event = "GW150914_095045"
        pipeline = "bayeswave"
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{event}.yaml", event=None, ledger=self.ledger)
        apply_page(file = f"https://git.ligo.org/asimov/data/-/raw/main/tests/{pipeline}.yaml", event=event, ledger=self.ledger)

        result = runner.invoke(manage.build)

        assert os.path.exists(os.path.join(config.get("project", "root"), "checkouts", event, config.get("general", "calibration_directory")))
        
