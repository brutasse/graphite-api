import os
import whisper

from . import TestCase, WHISPER_DIR


class MetricsTests(TestCase):
    def test_find(self):
        url = '/metrics/find'

        response = self.app.get(url)
        self.assertEqual(response.status_code, 400)

        response = self.app.get(url, query_string={'query': 'test'})
        self.assertJSON(response, [])

        response = self.app.get(url, query_string={'query': 'test',
                                                   'format': 'completer'})
        self.assertJSON(response, {'metrics': []})

    def test_expand(self):
        url = '/metrics/expand'

        response = self.app.get(url)
        self.assertJSON(response, {'errors':
                                   {'query': 'this parameter is required.'}},
                        status_code=400)

        response = self.app.get(url, query_string={'query': 'test'})
        self.assertJSON(response, {'results': []})

    def test_noop(self):
        url = '/dashboard/find'
        response = self.app.get(url)
        self.assertJSON(response, {'dashboards': []})

        url = '/dashboard/load/foo'
        response = self.app.get(url)
        self.assertJSON(response, {'error': "Dashboard 'foo' does not exist."},
                        status_code=404)

        url = '/events/get_data'
        response = self.app.get(url)
        self.assertJSON(response, [])

    def test_search(self):
        url = '/metrics/search'
        response = self.app.get(url, query_string={'max_results': 'a'})
        self.assertJSON(response, {'errors': {
            'max_results': 'must be an integer.',
            'query': 'this parameter is required.'}}, status_code=400)

        response = self.app.get(url, query_string={'query': 'test'})
        self.assertJSON(response, {'metrics': []})

    def test_search_index(self):
        response = self.app.get('/metrics/search',
                                query_string={'query': 'collectd.*'})
        self.assertJSON(response, {'metrics': []})
        parent = os.path.join(WHISPER_DIR, 'collectd')
        os.makedirs(parent)

        for metric in ['load', 'memory', 'cpu']:
            db = os.path.join(parent, '{0}.wsp'.format(metric))
            whisper.create(db, [(1, 60)])

        response = self.app.put('/index')
        self.assertJSON(response, {'success': True, 'entries': 3})

        response = self.app.get('/metrics/search',
                                query_string={'query': 'collectd.*'})
        self.assertJSON(response, {'metrics': [
            {'is_leaf': False, 'path': None},
            {'is_leaf': True, 'path': 'collectd.cpu'},
            {'is_leaf': True, 'path': 'collectd.load'},
            {'is_leaf': True, 'path': 'collectd.memory'},
        ]})
