from . import TestCase


class HttpTestCase(TestCase):
    def test_cors(self):
        response = self.app.options("/render")
        self.assertFalse("Access-Control-Allow-Origin" in response.headers)

        response = self.app.options(
            "/render", headers=(("Origin", "https://example.com"),)
        )
        self.assertEqual(
            response.headers["Access-Control-Allow-Origin"],
            "https://example.com",
        )

        response = self.app.options(
            "/render", headers=(("Origin", "http://foo.example.com:8888"),)
        )
        self.assertEqual(
            response.headers["Access-Control-Allow-Origin"],
            "http://foo.example.com:8888",
        )

        response = self.app.options(
            "/", headers=(("Origin", "http://foo.example.com"),)
        )
        self.assertFalse("Access-Control-Allow-Origin" in response.headers)

    def test_trailing_slash(self):
        response = self.app.get("/render?target=foo")
        self.assertEqual(response.status_code, 200)

        response = self.app.get("/render/?target=foo")
        self.assertEqual(response.status_code, 200)
