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
    - message: Second.
      status: APPROVED
      timestamp: 2021-03-17 21:58:05
    - message: This is a review message.
      status: REJECTED
      timestamp: 2021-03-17 20:58:05
    - message: Third.
      timestamp: 2021-03-18 20:58:05
"""
TEST_YAML_2 = """
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
class ReviewTests(unittest.TestCase):
    """All tests of the YAML event format."""
    @classmethod
    def setUpClass(cls):
        cls.cwd = os.getcwd()
        git.Repo.init(cls.cwd+"/tests/test_data/s000000xx/")
        
    def setUp(self):
        self.event = asimov.event.Event.from_yaml(TEST_YAML.format(self.cwd))
        self.event_no_review = asimov.event.Event.from_yaml(TEST_YAML_2.format(self.cwd))

    def tearDown(self):
        #shutil.rmtree(self.cwd+"/tests/tmp/")
        # shutil.rmtree("/tmp/S000000xx")
        pass

    
    def test_review_parsing(self):
        """Check that review messages get parsed correctly."""
        self.assertEqual(self.event.productions[0].review[0].status, "REJECTED")

    def test_empty_register_creation(self):
        """Check that productions initialise an empty register if no review information attached."""
        self.assertEqual(len(self.event_no_review.productions[0].review), 0)

    def test_review_message_sort(self):
        """Check that messages are correctly sorted."""
        self.assertEqual(self.event.productions[0].review[-1].message, "Third.")
        self.assertEqual(self.event.productions[0].review[1].message, "Second.")

    def test_gets_latest_status(self):
        """Ensure latest status is reported."""
        self.assertEqual(self.event.productions[0].review.status, "APPROVED")
        
    def test_outputs_to_dict(self):
        """Check that dictionary output works"""
        self.assertEqual(self.event.productions[0].review.to_dicts()[0]['status'], 'REJECTED')
