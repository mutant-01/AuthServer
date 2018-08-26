from auth_server import config
from auth_server import create_app


class PrefixMiddleware:

    def __init__(self, application, prefix=''):
        self.app = application
        self.prefix = prefix

    def __call__(self, environ, start_response):

        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)
        else:
            start_response('404', [('Content-Type', 'text/plain')])
            return ["Resource not found".encode()]


app = create_app()
app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix=config.url_prefix)
