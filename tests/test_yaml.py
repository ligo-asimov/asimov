"""Test that yaml event formats are parsed and written correctly."""

import unittest
import asimov.event

TEST_YAML = """
name: S200311bg
repository: https://git.ligo.org/pe/O3/S200311bg
productions:
- Prod0:
    comment: PSD production
    status: wait

"""

BAD_YAML = """
repository: https://git.ligo.org/pe/O3/S200311bg
productions:
- Prod0:
    comment: PSD production
    status: wait

"""

BAD_YAML_2 = """
name: S200311bg
productions:
- Prod0:
    comment: PSD production
    status: wait

"""


class EventTests(unittest.TestCase):
    """All tests of the YAML event format."""

    def setUp(self):
        self.event = asimov.event.Event.from_yaml(TEST_YAML)

    def test_name(self):
        """Check the name is loaded correctly."""
        self.assertEqual(self.event.name, "S200311bg")

    def test_no_name_error(self):
        """Check an exception is raised if the event name is missing."""
        with self.assertRaises(asimov.event.DescriptionException):
            asimov.event.Event.from_yaml(BAD_YAML)

    def test_no_repository_error(self):
        """Check that an exception is raised if the event has no repository."""
        with self.assertRaises(asimov.event.DescriptionException):
            asimov.event.Event.from_yaml(BAD_YAML_2)

class ProductionTests(unittest.TestCase):
    """Tests of the YAML Production format."""

    def setUp(self):
        self.event = asimov.event.Event("S000000xx",
                                        "https://blah.com/repo.git")
    
    def test_missing_name(self):
        """Check that an exception is raised if the production has no name."""
        production = dict(status="wait", pipeline="lalinference")
        with self.assertRaises(asimov.event.DescriptionException):
            asimov.event.Production.from_dict(production, event=self.event)
        
    def test_missing_pipeline(self):
        """Check that an exception is raised if the production has no pipeline."""
        production = {"S000000x": dict(status="wait")}
        with self.assertRaises(asimov.event.DescriptionException):
            asimov.event.Production.from_dict(production, event=self.event)
        
    def test_missing_status(self):
        """Check that an exception is raised if the production has no status."""
        production = {"S000000x": dict(pipeline="lalinference")}
        with self.assertRaises(asimov.event.DescriptionException):
            asimov.event.Production.from_dict(production, event=self.event)
