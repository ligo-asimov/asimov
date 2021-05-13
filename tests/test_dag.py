import os
import unittest
import asimov.event
import git

class DAGTests(unittest.TestCase):
    """All the tests to check production DAGs are generated successfully."""
    @classmethod
    def setUpClass(cls):
        cls.cwd = os.getcwd()
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
        
    def setUp(self):
        pass

    def test_simple_dag(self):
        """Check that all jobs are run when there are no dependencies specified."""
        TEST_YAML = """
name: S000000xx
repository: {0}/tests/test_data/s000000xx/
working_directory: {0}/tests/tmp/s000000xx/
webdir: ''
productions:
- Prod0:
    rundir: {0}/tests/tmp/s000000xx/Prod0
    pipeline: lalinference
    comment: PSD production
    status: ready
- Prod1:
    rundir: {0}/tests/tmp/s000000xx/Prod1
    pipeline: lalinference
    comment: PSD production
    status: ready
"""
        event = asimov.event.Event.from_yaml(TEST_YAML.format(self.cwd))
        self.assertEqual(len(event.get_all_latest()), 2)
    
    def test_linear_dag(self):
        """Check that all jobs are run when the dependencies are a chain."""
        TEST_YAML = """
name: S000000xx
repository: {0}/tests/test_data/s000000xx/
working_directory: {0}/tests/tmp/s000000xx/
webdir: ''
productions:
- Prod0:
    rundir: {0}/tests/tmp/s000000xx/Prod0
    pipeline: lalinference
    comment: PSD production
    status: ready
- Prod1:
    rundir: {0}/tests/tmp/s000000xx/Prod1
    pipeline: lalinference
    comment: PSD production
    status: ready
    needs: Prod0
"""
        event = asimov.event.Event.from_yaml(TEST_YAML.format(self.cwd))
        self.assertEqual(len(event.get_all_latest()), 1)

    def test_complex_dag(self):
        """Check that all jobs are run when the dependencies are not a chain."""
        TEST_YAML = """
name: S000000xx
repository: {0}/tests/test_data/s000000xx/
working_directory: {0}/tests/tmp/s000000xx/
webdir: ''
productions:
- Prod0:
    rundir: {0}/tests/tmp/s000000xx/Prod0
    pipeline: lalinference
    comment: PSD production
    status: finished
- Prod1:
    rundir: {0}/tests/tmp/s000000xx/Prod1
    pipeline: lalinference
    comment: PSD production
    status: wait
    needs: Prod0
- Prod2:
    rundir: {0}/tests/tmp/s000000xx/Prod2
    pipeline: lalinference
    comment: PSD production
    status: wait
    needs: Prod1
- Prod3:
    rundir: {0}/tests/tmp/s000000xx/Prod2
    pipeline: lalinference
    comment: PSD production
    status: wait
    needs: 
    - Prod0
- Prod4:
    rundir: {0}/tests/tmp/s000000xx/Prod2
    pipeline: lalinference
    comment: PSD production
    status: wait
    needs: 
       - Prod2
       - Prod3
- Prod5:
    rundir: {0}/tests/tmp/s000000xx/Prod2
    pipeline: lalinference
    comment: PSD production
    status: wait
"""
        event = asimov.event.Event.from_yaml(TEST_YAML.format(self.cwd))
        self.assertEqual(len(event.get_all_latest()), 2)
