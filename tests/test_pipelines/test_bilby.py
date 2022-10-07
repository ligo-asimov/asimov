"""Tests for the Bilby interface."""

import unittest
import shutil
import os
import git

from asimov.pipelines.bilby import Bilby
from asimov.event import Event
from asimov.pipeline import PipelineException

TEST_YAML = """
name: S000000xx
repository: {0}/tests/test_data/s000000xx
working directory: {0}/tests/tmp/s000000xx/
webdir: ''
productions:
- Prod3:
    pipeline: bilby
    comment: PSD production
    status: wait
quality:
  high-frequency: 1792
  lower-frequency:
    H1: 20
    L1: 20
    V1: 20
  psd-length: 16.0
  reference-frequency: 20
  sample-rate: 4096
  segment-length: 16.0
  start-frequency: 13.333333333333334
  supress:
    V1:
      lower: 49.5
      upper: 50.5
  upper-frequency: 1792
  window-length: 16.0
priors:
  amp order: 1
  chirp-mass:
  - 7.749135771186385
  - 12.237756554005374
  component:
  - 1
  - 1000
  distance:
  - 100
  - 10000
  q:
  - 0.05
  - 1.0

"""

from asimov import config

class BilbyTests(unittest.TestCase):
    """Test bilby interface"""

    @classmethod
    def setUpClass(cls):
        cls.cwd = os.getcwd()

        config.set("bilby", "priors", f"{cls.cwd}/tests/test_data/priors")
        repo = git.Repo.init(cls.cwd+"/tests/test_data/s000000xx/")
        os.chdir(cls.cwd+"/tests/test_data/s000000xx/")
        os.system("git add C01_offline/Prod3_test.ini C01_offline/s000000xx_gpsTime.txt")
        os.system("git commit -m 'test'")
        os.chdir(cls.cwd)

    @classmethod
    def tearDownClass(cls):
        """Destroy all the products of this test."""
        os.system("rm asimov.conf")
        os.system(f"rm -rf {cls.cwd}/tests/tmp/")
        os.system(f"rm -rf {cls.cwd}/tests/test_data/s000000xx/.git")
        try:
            shutil.rmtree("/tmp/S000000xx")
        except:
            pass

    def tearDown(self):
        os.chdir(self.cwd+"/tests/test_data/s000000xx/")
        os.system("git rm -f C01_offline/Prod3.prior")
        os.chdir(self.cwd)
        pass
        
    def setUp(self):
        """Create a pipeline."""
        self.event = Event.from_yaml(TEST_YAML.format(self.cwd))
        self.pipeline = Bilby(self.event.productions[0])
        out = self.pipeline.build_dag()

    def test_dag(self):
        """Check that a DAG is actually produced."""
        outdir = "outdir_from_config"
        label = "job_label_from_config"
        dagfile = f"submit/dag_Prod3.submit"
        
        print(f"{self.cwd}/tests/tmp/s000000xx/C01_offline/Prod3/{dagfile}")
        self.assertEqual(os.path.exists(f"{self.cwd}/tests/tmp/s000000xx/Prod3/{dagfile}"), 1)

    def test_read_ini(self):
        """Check that a bilby ini file can be read correctly."""
        pass
