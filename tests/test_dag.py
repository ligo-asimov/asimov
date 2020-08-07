import os
import unittest
import asimov.event

class DAGTests(unittest.TestCase):
    """All the tests to check production DAGs are generated successfully."""
    @classmethod
    def setUpClass(cls):
        cls.cwd = os.getcwd()
        
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
        self.assertEqual(len(event.get_all_latest()), 3)
