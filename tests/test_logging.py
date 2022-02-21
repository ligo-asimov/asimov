import unittest

import asimov
import asimov.server
import json

class LoggerHTTPTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.prefix = "/log"
        cls.app = app = asimov.server.create_app()
        app.config.update({
        "TESTING": True,
        })
        cls.client = cls.app.test_client()

        cls.client.post(cls.prefix+"/", json=       {
         "event":"GW150914",
         "level":"info",
         "message":"This is another test message.",
         "module":"sampling",
         "pipeline":"pycbc",
         "production":"ProdX10"
       })

    def test_list_events(self):
        landing = self.client.get(self.prefix+"/")
        data = json.loads(landing.data.decode())
        self.assertTrue("module" in data[0])

    def test_add_log_entry(self):
        resp = self.client.post(self.prefix+"/", json=       {
         "event":"GW150914",
         "level":"info",
         "message":"This is yet another test message.",
         "module":"sampling",
         "pipeline":"pycbc",
         "production":"ProdX10"
        })
        self.assertEqual(resp.data.decode().strip(), "{}")
        self.assertEqual(resp.status, "201 CREATED")
