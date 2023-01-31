"""These tests are designed to be run on all pipelines to ensure that
they are generally compliant within asimov's specifications.  They can
include checking that ini files have the correct information and that
the pipelines report information as expected.
"""

import os
import io
import unittest
import shutil
import git
import contextlib

import asimov.event
from asimov.cli.project import make_project
from asimov.cli.application import apply_page
from asimov.ledger import YAMLLedger

from . import AsimovTestCase
from asimov import config
from asimov.utils import set_directory


class TestIniFileHandling(AsimovTestCase):
    """Test that for all pipelines the information in the ini file is
    correctly substituted."""

    def test_detchar_substitution(self):
        event = "Nonstandard fmin"
        apply_page(
            f"{self.cwd}/tests/test_data/testing_pe.yaml",
            event=None,
            ledger=self.ledger,
        )
        apply_page(
            f"{self.cwd}/tests/test_data/event_non_standard_settings.yaml",
            event=None,
            ledger=self.ledger,
        )
        apply_page(
            f"{self.cwd}/tests/test_data/bayeswave_settings_nodeps.yaml",
            event=event,
            ledger=self.ledger,
        )

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            production = self.ledger.get_event(event)[0].productions[0]
            with set_directory(
                os.path.join(
                    "checkouts", event, config.get("general", "calibration_directory")
                )
            ):
                production.make_config(f"{production.name}.ini")

        ini_location = os.path.join(
            config.get("project", "root"),
            "checkouts",
            event,
            config.get("general", "calibration_directory"),
            f"{production.name}.ini",
        )
        self.assertTrue(
            os.path.exists(ini_location)
        )

        # Read the ini file and convert it to a dictionary for easy access

        import configparser

        pipeline_config = configparser.ConfigParser()
        pipeline_config.read(ini_location)
        pipeline_config = {s:dict(pipeline_config.items(s)) for s in pipeline_config.sections()}
        # print(pipeline_config)
        # Test fmin
        self.assertEqual(pipeline_config['input']['flow'], "{ 'H1':62,'L1':92,'V1':62, }")
        # Test segment length
        self.assertEqual(pipeline_config['input']['seglen'], '4')
        # Test segment length
        self.assertEqual(pipeline_config['input']['window'], '71')
        # PSD Length
        self.assertEqual(pipeline_config['input']['psdlength'], '108.6')
        # IFOs
        self.assertEqual(pipeline_config['input']['ifo-list'], "['H1', 'L1', 'V1']")
        # Segment start
        self.assertEqual(pipeline_config['input']['segment-start'], '2')

        ## DATA
        # Channel lists
        self.assertEqual(pipeline_config['datafind']['channel-list'],  "{ 'H1':'H1:WeirdChannel','L1':'L1:WeirdChannel','V1':'V1:OddChannel', }")    
        # Frame types
        self.assertEqual(pipeline_config['datafind']['frtype-list'], "{ 'H1':'NonstandardFrame','L1':'NonstandardFrameL1','V1':'UnusualFrameType', }")    
