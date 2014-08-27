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
        if netloc in self.origins or '*' in self.origins:
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


class TrailingSlash(object):
    """
    Middleware that strips trailing slashes from URLs.
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        path_info = environ['PATH_INFO']
        if len(path_info) > 1 and path_info.endswith('/'):
            environ['PATH_INFO'] = path_info.rstrip('/')
        return self.app(environ, start_response)
