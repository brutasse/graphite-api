import json
import os
import shutil

os.environ.setdefault('GRAPHITE_API_CONFIG',
                      os.path.join(os.path.dirname(__file__), 'conf.yaml'))

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from graphite_api.app import app
from graphite_api.finders.whisper import WhisperFinder
from graphite_api.search import IndexSearcher
from graphite_api.storage import Store

DATA_DIR = '/tmp/graphite-api-data.{0}'.format(os.getpid())
WHISPER_DIR = os.path.join(DATA_DIR, 'whisper')
SEARCH_INDEX = os.path.join(DATA_DIR, 'index')


class TestCase(unittest.TestCase):
    def _cleanup(self):
        shutil.rmtree(DATA_DIR, ignore_errors=True)

    def setUp(self):
        self._cleanup()
        os.makedirs(WHISPER_DIR)
        app.config['TESTING'] = True
        whisper_conf = {'whisper': {'directories': [WHISPER_DIR]}}
        app.config['GRAPHITE']['store'] = Store([WhisperFinder(whisper_conf)])
        app.config['GRAPHITE']['searcher'] = IndexSearcher(SEARCH_INDEX)
        self.app = app.test_client()

    def tearDown(self):
        self._cleanup()

    def assertJSON(self, response, data, status_code=200):
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(json.loads(response.data.decode('utf-8')), data)
