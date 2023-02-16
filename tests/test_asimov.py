"""Perform tests on the base asimov package."""

import unittest
from unittest.mock import patch
from importlib import reload
import asimov

from pkg_resources import DistributionNotFound

class TestAsimovBase(unittest.TestCase):

    @patch("pkg_resources.get_distribution",
           **{
               'side_effect': DistributionNotFound,#("Not found", "asimov"),
           })
    def testImports(self, blah):
        reload(asimov)

        self.assertEqual(asimov.__version__, "dev")
