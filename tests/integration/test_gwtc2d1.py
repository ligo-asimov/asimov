"""
Test that an O3a final event is pushed-through all of the steps of
ini and DAG creation.
"""

import unittest

import asimov.event



class EventTests(unittest.TestCase):
    """All tests of the YAML event format."""
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        with open("GW190426190642.yaml", "r") as f:
            TEST_YAML = f.read()
        self.event = asimov.event.Event.from_yaml(TEST_YAML, repo=False)

    def test_ini_generation(self):
        """Check that the ini file is correctly generated."""

        for production in self.event.productions:
            print(f"Production {production.name}")
            production.make_config(f"{self.event.name}_{production.name}.ini",
                                   template_directory="test_templates")


if __name__ == '__main__':
    unittest.main()
