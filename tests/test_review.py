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
    review:
    - message: This is a review message.
      status: REJECTED
      timestamp: 2021-03-17 20:58:05
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
