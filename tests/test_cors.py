from . import TestCase


class CorsTestCase(TestCase):
    def test_cors(self):
        response = self.app.options('/render')
        self.assertFalse(
            'Access-Control-Allow-Origin' in response.headers.keys())

        response = self.app.options('/render', headers=(
            ('Origin', 'https://example.com'),
        ))
        self.assertEqual(response.headers['Access-Control-Allow-Origin'],
                         'https://example.com')

        response = self.app.options('/render', headers=(
            ('Origin', 'http://foo.example.com:8888'),
        ))
        self.assertEqual(response.headers['Access-Control-Allow-Origin'],
                         'http://foo.example.com:8888')

        response = self.app.options('/', headers=(
            ('Origin', 'http://foo.example.com'),
        ))
        self.assertFalse(
            'Access-Control-Allow-Origin' in response.headers.keys())
