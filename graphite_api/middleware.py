from six.moves.urllib.parse import urlparse


class CORS(object):
    """
    Simple middleware that adds CORS headers.
    """
    def __init__(self, app, origins=None):
        self.app = app
        self.origins = origins

    def __call__(self, environ, start_response):
        origin = environ.get('HTTP_ORIGIN')
        if origin is None or self.origins is None:
            return self.app(environ, start_response)

        netloc = urlparse(origin).netloc
        if netloc in self.origins:
            allow_origin = [
                ('Access-Control-Allow-Origin', origin),
                ('Access-Control-Allow-Credentials', 'true'),
            ]
            if environ['REQUEST_METHOD'] == 'OPTIONS':
                start_response('204 No Content', allow_origin)
                return []

            def custom_start_response(status, headers, exc_info=None):
                headers.extend(allow_origin)
                return start_response(status, headers, exc_info)
        else:
            custom_start_response = start_response
        return self.app(environ, custom_start_response)
