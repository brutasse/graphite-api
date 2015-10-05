import os.path
from graphite_api._vendor import whisper

from . import TestCase, WHISPER_DIR


class MetricsTests(TestCase):
    def _create_dbs(self):
        for db in (
            ('test', 'foo.wsp'),
            ('test', 'wat', 'welp.wsp'),
            ('test', 'bar', 'baz.wsp'),
        ):
            db_path = os.path.join(WHISPER_DIR, *db)
            os.makedirs(os.path.dirname(db_path))
            whisper.create(db_path, [(1, 60)])

    def test_find(self):
        url = '/metrics/find'

        response = self.app.get(url)
        self.assertEqual(response.status_code, 400)

        response = self.app.get(url, query_string={'query': 'test'})
        self.assertJSON(response, [])

        response = self.app.get(url, query_string={'query': 'test',
                                                   'format': 'completer'})
        self.assertJSON(response, {'metrics': []})

        self._create_dbs()

        for _url in ['/metrics/find', '/metrics']:
            response = self.app.get(_url, query_string={'query': 'test.*',
                                                        'format': 'treejson'})
            self.assertJSON(response, [{
                'allowChildren': 1,
                'expandable': 1,
                'id': 'test.bar',
                'leaf': 0,
                'text': 'bar',
            }, {
                'allowChildren': 1,
                'expandable': 1,
                'id': 'test.wat',
                'leaf': 0,
                'text': 'wat',
            }, {
                'allowChildren': 0,
                'expandable': 0,
                'id': 'test.foo',
                'leaf': 1,
                'text': 'foo',
            }])

        response = self.app.get(url, query_string={'query': 'test.*',
                                                   'format': 'treejson',
                                                   'wildcards': 1})
        self.assertJSON(response, [{
            'text': '*',
            'expandable': 1,
            'leaf': 0,
            'id': 'test.*',
            'allowChildren': 1,
        }, {
            'allowChildren': 1,
            'expandable': 1,
            'id': 'test.bar',
            'leaf': 0,
            'text': 'bar',
        }, {
            'allowChildren': 1,
            'expandable': 1,
            'id': 'test.wat',
            'leaf': 0,
            'text': 'wat',
        }, {
            'allowChildren': 0,
            'expandable': 0,
            'id': 'test.foo',
            'leaf': 1,
            'text': 'foo',
        }])

        response = self.app.get(url, query_string={'query': 'test.*',
                                                   'format': 'completer'})
        self.assertJSON(response, {'metrics': [{
            'is_leaf': 0,
            'name': 'bar',
            'path': 'test.bar.',
        }, {
            'is_leaf': 1,
            'name': 'foo',
            'path': 'test.foo',
        }, {
            'is_leaf': 0,
            'name': 'wat',
            'path': 'test.wat.',
        }]})

        response = self.app.get(url, query_string={'query': 'test.*',
                                                   'wildcards': 1,
                                                   'format': 'completer'})
        self.assertJSON(response, {'metrics': [{
            'is_leaf': 0,
            'name': 'bar',
            'path': 'test.bar.',
        }, {
            'is_leaf': 1,
            'name': 'foo',
            'path': 'test.foo',
        }, {
            'is_leaf': 0,
            'name': 'wat',
            'path': 'test.wat.',
        }, {
            'name': '*',
        }]})

    def test_find_validation(self):
        url = '/metrics/find'
        response = self.app.get(url, query_string={'query': 'foo',
                                                   'wildcards': 'aaa'})
        self.assertJSON(response, {'errors': {'wildcards': 'must be 0 or 1.'}},
                        status_code=400)

        response = self.app.get(url, query_string={'query': 'foo',
                                                   'from': 'aaa',
                                                   'until': 'bbb'})
        self.assertJSON(response, {'errors': {
            'from': 'must be an epoch timestamp.',
            'until': 'must be an epoch timestamp.',
        }}, status_code=400)

        response = self.app.get(url, query_string={'query': 'foo',
                                                   'format': 'other'})
        self.assertJSON(response, {'errors': {
            'format': 'unrecognized format: "other".',
        }}, status_code=400)

    def test_expand(self):
        url = '/metrics/expand'

        response = self.app.get(url)
        self.assertJSON(response, {'errors':
                                   {'query': 'this parameter is required.'}},
                        status_code=400)

        response = self.app.get(url, query_string={'query': 'test'})
        self.assertJSON(response, {'results': []})

        self._create_dbs()
        response = self.app.get(url, query_string={'query': 'test'})
        self.assertJSON(response, {'results': ['test']})

        response = self.app.get(url, query_string={'query': 'test.*'})
        self.assertJSON(response, {'results': ['test.bar', 'test.foo',
                                               'test.wat']})

        response = self.app.get(url, query_string={'query': 'test.*',
                                                   'leavesOnly': 1})
        self.assertJSON(response, {'results': ['test.foo']})

        response = self.app.get(url, query_string={'query': 'test.*',
                                                   'groupByExpr': 1})
        self.assertJSON(response, {'results': {'test.*': ['test.bar',
                                                          'test.foo',
                                                          'test.wat']}})

    def test_expand_validation(self):
        url = '/metrics/expand'
        response = self.app.get(url, query_string={'query': 'foo',
                                                   'leavesOnly': 'bbb',
                                                   'groupByExpr': 'aaa'})
        self.assertJSON(response, {'errors': {
            'groupByExpr': 'must be 0 or 1.',
            'leavesOnly': 'must be 0 or 1.',
        }}, status_code=400)

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

    def test_index(self):
        parent = os.path.join(WHISPER_DIR, 'collectd')
        os.makedirs(parent)

        for metric in ['load', 'memory', 'cpu']:
            db = os.path.join(parent, '{0}.wsp'.format(metric))
            whisper.create(db, [(1, 60)])

        response = self.app.put('/index')
        self.assertJSON(response, {'success': True, 'entries': 3})

    def test_metrics_index(self):
        url = '/metrics/index.json'
        response = self.app.get(url)
        self.assertJSON(response, [])
        self.assertEqual(response.headers['Content-Type'], 'application/json')

        response = self.app.get(url, query_string={'jsonp': 'foo'})
        self.assertEqual(response.data, b'foo([])')
        self.assertEqual(response.headers['Content-Type'], 'text/javascript')

        parent = os.path.join(WHISPER_DIR, 'collectd')
        os.makedirs(parent)

        for metric in ['load', 'memory', 'cpu']:
            db = os.path.join(parent, '{0}.wsp'.format(metric))
            whisper.create(db, [(1, 60)])

        response = self.app.get(url)
        self.assertJSON(response, [
            u'collectd.cpu',
            u'collectd.load',
            u'collectd.memory',
        ])
        response = self.app.get(url, query_string={'jsonp': 'bar'})
        self.assertEqual(
            response.data,
            b'bar(["collectd.cpu", "collectd.load", "collectd.memory"])')
