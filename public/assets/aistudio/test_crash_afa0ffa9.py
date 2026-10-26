import http.server
class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        raise Exception('Crash!')
http.server.HTTPServer(('127.0.0.1', 8090), Handler).handle_request()
