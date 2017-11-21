import os
import unittest

os.environ['GRAPHITE_API_CONFIG'] = os.path.join(
    os.path.dirname(__file__), 'no_finders_conf.yaml')  # noqa

from graphite_api.app import app
from graphite_api.config import configure


class NoFindersTest(unittest.TestCase):

    def test_app_no_finders(self):
        configure(app)
        self.assertTrue(app is not None)
