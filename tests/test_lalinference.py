"""Tests for the LALInference interface."""

import unittest
import shutil
import os
import git

from asimov.pipelines.lalinference import LALInference
from asimov.event import Event
from asimov.pipeline import PipelineException

TEST_YAML = """
name: S000000xx
repository: {0}/tests/test_data/s000000xx/
working_directory: {0}/tests/tmp/s000000xx/
webdir: ''
productions:
- Prod0:
    rundir: {0}/tests/tmp/s000000xx/C01_offline/Prod0
    pipeline: lalinference
    comment: PSD production
    status: wait

"""


class LALInferenceTests(unittest.TestCase):
    """Test lalinference interface"""

    @classmethod
    def setUpClass(cls):
        cls.cwd = os.getcwd()
        repo = git.Repo.init(cls.cwd+"/tests/test_data/s000000xx/")
        os.chdir(cls.cwd+"/tests/test_data/s000000xx/")
        os.system("git add C01_offline/Prod0_test.ini C01_offline/s000000xx_gpsTime.txt")
        os.system("git commit -m 'test'")


    @classmethod
    def tearDownClass(cls):
        """Destroy all the products of this test."""
        os.system(f"{cls.cwd}/tests/tmp/-rf")
        os.system(f"{cls.cwd}/tests/test_data/s000000xx/.git -rf")
        try:
            shutil.rmtree("/tmp/S000000xx")
        except:
            pass

    def tearDown(self):
        os.system(f"{self.cwd}/tests/tmp/-rf")
        
    def setUp(self):
        """Create a pipeline."""
        self.event = Event.from_yaml(TEST_YAML.format(self.cwd))
        self.pipeline = LALInference(self.event.productions[0])
        out = self.pipeline.build_dag()

    def test_dag(self):
        """Check that a DAG is actually produced."""
        print(f"{self.cwd}/tests/tmp/s000000xx/C01_offline/Prod0/lalinference_1248617392-1248617397.dag")
        self.assertEqual(os.path.exists(f"{self.cwd}/tests/tmp/s000000xx/C01_offline/Prod0/lalinference_1248617392-1248617397.dag"), 1)
