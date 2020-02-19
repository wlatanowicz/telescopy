import http.server
import os
import posixpath
import socketserver
import threading
import urllib.parse
from http import HTTPStatus

from . import settings


class HttpServer:
    @classmethod
    def http_server(cls):
        class HttpHandler(http.server.SimpleHTTPRequestHandler):
            def translate_path(self, path):
                # abandon query parameters
                path = path.split("?", 1)[0]
                path = path.split("#", 1)[0]
                # Don't forget explicit trailing slash when normalizing. Issue17324
                trailing_slash = path.rstrip().endswith("/")
                try:
                    path = urllib.parse.unquote(path, errors="surrogatepass")
                except UnicodeDecodeError:
                    path = urllib.parse.unquote(path)
                path = posixpath.normpath(path)
                words = path.split("/")
                words = filter(None, words)

                path = settings.PUB_DIR

                for word in words:
                    if os.path.dirname(word) or word in (os.curdir, os.pardir):
                        # Ignore components that are not a simple file/directory name
                        continue
                    path = os.path.join(path, word)
                if trailing_slash:
                    path += "/"
                return path

            def do_DELETE(self):
                path = self.translate_path(self.path)
                if os.path.isfile(path):
                    try:
                        os.unlink(path)
                        self.send_response(HTTPStatus.OK)
                        self.end_headers()
                    except:
                        self.send_error(
                            HTTPStatus.INTERNAL_SERVER_ERROR, "Internal server error"
                        )
                else:
                    self.send_error(HTTPStatus.NOT_FOUND, "File not found")

        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", settings.HTTP_PORT), HttpHandler) as httpd:
            httpd.serve_forever()

    @classmethod
    def start(cls):
        if not os.path.exists(settings.PUB_DIR):
            os.makedirs(settings.PUB_DIR)

        http_th = threading.Thread(target=cls.http_server, daemon=True)
        http_th.start()
