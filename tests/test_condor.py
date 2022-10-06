import unittest

import asimov
import asimov.condor

class CondorTests(unittest.TestCase):

# @classmethod
#     def setUpClass(cls):
#         cls.app = app = asimov.server.create_app()
#         app.config.update({
#         "TESTING": True,
#         })
#         cls.client = cls.app.test_client()


    def test_job_from_dict(self):
        """Check that a CondorJob object can be created from a dictionary."""

        dictionary = {"id": 450,
                      "command": "test.sh",
                      "hosts": "test.test.com",
                      "status": 1}

        job = asimov.condor.CondorJob.from_dict(dictionary)

        self.assertEqual(job.idno, 450)

    def test_status(self):
        """Check that status codes get translated to a human-readable string."""
        dictionary = {"id": 450,
                      "command": "test.sh",
                      "hosts": "test.test.com",
                      "status": 1}

        job = asimov.condor.CondorJob.from_dict(dictionary)

        self.assertEqual(job.status, "Idle")
