from . import TestCase


class MetricsTests(TestCase):
    def test_find(self):
        url = '/metrics/find'

        response = self.app.get(url)
        self.assertEqual(response.status_code, 400)

        response = self.app.get(url, query_string={'query': 'test'})
        self.assertJSON(response, [])

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
