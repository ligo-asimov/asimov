"""
These tests are designed to ensure that all classes of data in the
yaml 'blueprints' are correctly applied to the asimov ledger, and are
then correctly used to make config files.
"""

import os
import unittest
import shutil
import git
import asimov.event
from asimov.cli.project import make_project
from asimov.cli.application import apply_page
from asimov.ledger import YAMLLedger
from asimov.testing import AsimovTestCase


class DetcharTests(AsimovTestCase):
    """Tests to ensure that various detector characterisation related
    data are handled correctly.
    These should include:
    - minimum frequencies
    - maximum frequencies
    - data channels
    - frame types"""

    def test_event_non_standard_fmin(self):
        """Check event-specific fmin overwrites project default."""
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

        event = self.ledger.get_event("Nonstandard fmin")[0]

        self.assertEqual(event.meta["quality"]["minimum frequency"]["H1"], 62)
        self.assertEqual(event.meta["quality"]["minimum frequency"]["L1"], 92)
        self.assertEqual(event.meta["quality"]["minimum frequency"]["V1"], 62)

    def test_event_non_standard_channels(self):
        """Check event-specific channel overwrites project default."""
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

        event = self.ledger.get_event("Nonstandard fmin")[0]

        self.assertEqual(event.meta["data"]["channels"]["L1"], "L1:WeirdChannel")
        self.assertEqual(event.meta["data"]["channels"]["H1"], "H1:WeirdChannel")
        self.assertEqual(event.meta["data"]["channels"]["V1"], "V1:OddChannel")

    def test_event_non_standard_frames(self):
        """Check event-specific frame-type overwrites project default."""
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

        event = self.ledger.get_event("Nonstandard fmin")[0]

        self.assertEqual(event.meta["data"]["frame types"]["L1"], "NonstandardFrameL1")
        self.assertEqual(event.meta["data"]["frame types"]["H1"], "NonstandardFrame")
        self.assertEqual(event.meta["data"]["frame types"]["V1"], "UnusualFrameType")
