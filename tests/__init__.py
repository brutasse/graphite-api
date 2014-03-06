import json
import os

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from graphite_api.app import app
from graphite_api.finders.whisper import WhisperFinder
from graphite_api.storage import Store

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))


class TestCase(unittest.TestCase):
    def setUp(self):
        whisper_conf = {'whisper': {'directories': [DATA_DIR]}}
        app.config['TESTING'] = True
        app.config['GRAPHITE']['store'] = Store([WhisperFinder(whisper_conf)])
        self.app = app.test_client()

    def assertJSON(self, response, data, status_code=200):
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(json.loads(response.data.decode('utf-8')), data)
