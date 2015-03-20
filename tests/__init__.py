import json
import os
import shutil
import sys

os.environ.setdefault(
    'GRAPHITE_API_CONFIG',
    os.path.join(os.path.dirname(__file__), 'conf.yaml'))  # noqa

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from graphite_api.app import app
from graphite_api.finders.whisper import WhisperFinder
from graphite_api.search import IndexSearcher
from graphite_api.storage import Store
from graphite_api._vendor import whisper


DATA_DIR = '/tmp/graphite-api-data.{0}'.format(os.getpid())
WHISPER_DIR = os.path.join(DATA_DIR, 'whisper')
SEARCH_INDEX = os.path.join(DATA_DIR, 'index')

null_handler = 'logging.NullHandler'
if sys.version_info > (2, 7):
    from logging.config import dictConfig
else:
    from logutils.dictconfig import dictConfig

    class NullHandler(object):
        def emit(self, record):
            pass

        def setLevel(self, level):
            pass
    null_handler = 'tests.NullHandler'

dictConfig({
    'version': 1,
    'handlers': {
        'raw': {
            'level': 'DEBUG',
            'class': null_handler,
        },
    },
})


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

    def write_series(self, series, retentions=[(1, 180)]):
        file_name = os.path.join(
            WHISPER_DIR,
            '{0}.wsp'.format(series.pathExpression.replace('.', os.sep)))
        dir_name = os.path.dirname(file_name)
        if not os.path.isdir(dir_name):
            os.makedirs(dir_name)
        whisper.create(file_name, retentions)
        data = []
        for index, value in enumerate(series):
            if value is None:
                continue
            data.append((series.start + index * series.step, value))
        whisper.update_many(file_name, data)
