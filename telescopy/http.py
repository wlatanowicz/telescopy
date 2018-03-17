import threading
import http.server
import socketserver
import os
import posixpath
import urllib.parse

from . import settings


class HttpServer:
    @classmethod
    def http_server(cls):
        class HttpHandler(http.server.SimpleHTTPRequestHandler):
            def translate_path(self, path):
                # abandon query parameters
                path = path.split('?', 1)[0]
                path = path.split('#', 1)[0]
                # Don't forget explicit trailing slash when normalizing. Issue17324
                trailing_slash = path.rstrip().endswith('/')
                try:
                    path = urllib.parse.unquote(path, errors='surrogatepass')
                except UnicodeDecodeError:
                    path = urllib.parse.unquote(path)
                path = posixpath.normpath(path)
                words = path.split('/')
                words = filter(None, words)

                path = settings.PUB_DIR

                for word in words:
                    if os.path.dirname(word) or word in (os.curdir, os.pardir):
                        # Ignore components that are not a simple file/directory name
                        continue
                    path = os.path.join(path, word)
                if trailing_slash:
                    path += '/'
                return path

        with socketserver.TCPServer(("", settings.HTTP_PORT), HttpHandler) as httpd:
            httpd.serve_forever()

    @classmethod
    def start(cls):
        if not os.path.exists(settings.PUB_DIR):
            os.makedirs(settings.PUB_DIR)

        http_th = threading.Thread(target=cls.http_server)
        http_th.start()
