import unittest

import asimov
import asimov.server

class ServerTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = app = asimov.server.create_app()
        app.config.update({
        "TESTING": True,
        })
        cls.client = cls.app.test_client()

    def test_landing(self):
        EXPECT = '"asimov"'
        landing = self.client.get("/")
        html = landing.data.decode().strip()

        self.assertEqual(EXPECT, html)

    def test_version(self):
        EXPECT = f'"{asimov.__version__}"'
        landing = self.client.get("/version")
        html = landing.data.decode().strip()

        self.assertEqual(EXPECT, html)
