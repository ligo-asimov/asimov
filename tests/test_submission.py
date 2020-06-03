"""Tests of asimov's ability to run pipeline generation tools to produce submission files."""

import hashlib
import unittest
import shutil, os
import git
import asimov.git

class LALInferenceTests(unittest.TestCase):
    """Test lalinference_pipe related jobs."""

    @classmethod
    def setUpClass(self):
        git.Repo.init("test_data/s000000xx/")
    
    def setUp(self):
        self.repo = repo = asimov.git.EventRepo("test_data/s000000xx/")
        self.cwd = os.getcwd()
        self.sample_hashes = {
            "lalinference_dag": self._get_hash("test_data/sample_files/lalinference_1248617392-1248617397.dag")
            }

    def _get_hash(self, filename):
        with open(filename, "r") as handle:
            return hashlib.md5(handle.read().encode()).hexdigest()
        
    def test_pipe_build(self):
        """Test that the lalinference_pipe builds the submission file."""
        self.repo.build_dag("C01_offline", "Prod0")

    def test_lalinference_dag(self):
        """Check that the generated lalinference DAG is correct."""
        self.repo.build_dag("C01_offline", "Prod0")
        os.chdir(self.cwd)
        self.assertEqual(self.sample_hashes["lalinference_dag"],
self._get_hash("test_data/s000000xx/C01_offline/Prod0/lalinference_1248617392-1248617397.dag"))

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree("test_data/s000000xx/C01_offline/Prod0/")
        
    @classmethod
    def tearDownClass(self):
        """Destroy all the products of this test."""
        
        shutil.rmtree("test_data/s000000xx/.git")
