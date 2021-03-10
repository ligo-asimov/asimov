"""Test that yaml event formats are parsed and written correctly."""

import unittest
import os
import shutil
import git
import asimov.event

TEST_YAML = """
name: S000000xx
working directory: {0}/tests/tmp/
repository: {0}/tests/test_data/s000000xx/
interferometers: 
- L1
calibration: 
  L1: Fake
quality: {{}}
productions:
- Prod0:
    pipeline: lalinference
    comment: PSD production
    status: wait

"""

BAD_YAML = """
repository: {0}/tests/test_data/s000000xx/
working directory: {0}/tests/tmp/
interferometers: [L1]
calibration:
  L1: Fake
quality: {{}}
productions:
- Prod0:
    comment: PSD production
    status: wait

"""

BAD_YAML_2 = """
name: S200311bg
interferometers: [L1]
calibration:
- L1: Fake
working directory: {0}/tests/tmp/
productions:
- Prod0:
    comment: PSD production
    status: wait

"""



class EventTests(unittest.TestCase):
    """All tests of the YAML event format."""
    @classmethod
    def setUpClass(cls):
        cls.cwd = os.getcwd()
        git.Repo.init(cls.cwd+"/tests/test_data/s000000xx/")
        
    def setUp(self):
        self.event = asimov.event.Event.from_yaml(TEST_YAML.format(self.cwd))

    def tearDown(self):
        #shutil.rmtree(self.cwd+"/tests/tmp/")
        # shutil.rmtree("/tmp/S000000xx")
        pass
        
    def test_name(self):
        """Check the name is loaded correctly."""
        self.assertEqual(self.event.name, "S000000xx")

    def test_no_name_error(self):
        """Check an exception is raised if the event name is missing."""
        with self.assertRaises(asimov.event.DescriptionException):
            asimov.event.Event.from_yaml(BAD_YAML.format(self.cwd))

    # def test_no_repository_error(self):
    #     """Check that an exception is raised if the event has no repository."""
    #     with self.assertRaises(asimov.event.DescriptionException):
    #         asimov.event.Event.from_yaml(BAD_YAML_2.format(self.cwd))

class ProductionTests(unittest.TestCase):
    """Tests of the YAML Production format."""
    @classmethod
    def setUpClass(cls):
        cls.cwd = os.getcwd()
        git.Repo.init(cls.cwd+"/tests/test_data/s000000xx/")

    @classmethod
    def tearDownClass(cls):
        """Destroy all the products of this test."""
        shutil.rmtree(cls.cwd+"/tests/test_data/s000000xx/.git")
            
    def setUp(self):
        self.event = asimov.event.Event("S000000xx",
                                        "{0}/tests/test_data/s000000xx/".format(self.cwd))

    def tearDown(self):
        #shutil.rmtree(self.cwd+"/tests/tmp/")
        #shutil.rmtree("/tmp/S000000xx")
        pass

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

    def test_production_prior_read(self):
            """Check that per-production priors get read."""
            YAML_WITH_PRODUCTION_PRIORS = """
            name: S200311bg
            interferometers: [L1]
            calibration: {{}}
            working directory: {0}/tests/tmp/
            priors:
              q: [0, 1]
            productions:
              - Prod0:
                  comment: PSD production
                  pipeline: lalinference
                  priors:
                    q: [0.0, 0.05]
                  status: wait
              - Prod1:
                  comment: PSD production
                  pipeline: lalinference
                  priors:
                    q: [0.0, 1.0]
                  status: wait
            """
            event = asimov.event.Event.from_yaml(
                YAML_WITH_PRODUCTION_PRIORS.format(self.cwd))
            prod0 = event.productions[0]
            prod1 = event.productions[1]
            self.assertEqual(prod0.priors['q'][1], 0.05)
            self.assertEqual(prod0.meta['priors']['q'][1], 0.05)
            self.assertEqual(prod1.priors['q'][1], 1.00)
            self.assertEqual(prod1.meta['priors']['q'][1], 1.00)

    def test_production_prior_preserved(self):
        """Check that per-production priors get preserved when saved to yaml."""
        YAML_WITH_PRODUCTION_PRIORS = """
        name: S200311bg
        interferometers: [L1]
        calibration: {{}}
        working directory: {0}/tests/tmp/
        priors:
          q: [0, 1]
        productions:
          - Prod0:
              comment: PSD production
              pipeline: lalinference
              priors:
                q: [0.0, 0.05]
              status: wait
          - Prod1:
              comment: PSD production
              pipeline: lalinference
              priors:
                q: [0.0, 1.0]
              status: wait
        """
        event = asimov.event.Event.from_yaml(
            YAML_WITH_PRODUCTION_PRIORS.format(self.cwd))

        event_YAML = event.to_yaml()
        event2 = asimov.event.Event.from_yaml(event_YAML)
        prod0 = event.productions[0]
        prod1 = event.productions[1]

        prod01 = event2.productions[0]
        prod11 = event2.productions[1]
        self.assertEqual(prod0.priors, prod01.priors)
        
