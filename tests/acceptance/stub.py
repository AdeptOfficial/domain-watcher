"""Scripted RDAP/Discord peers. Control API exists only inside the test network."""
import json
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

lock = threading.Lock()
state = dict(rdap={}, discord=deque(), requests=[], unexpected=[], attempts=[], accepted=[])


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, body=None, raw=None):
        data = raw.encode() if raw is not None else json.dumps({} if body is None else body).encode()
        try:
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass  # expected during scripted timeout

    def do_GET(self):
        if self.path == '/healthz':
            return self.reply(200)
        if self.path == '/state':
            with lock:
                result = {k: state[k] for k in ('requests', 'unexpected', 'attempts', 'accepted')}
                result = json.loads(json.dumps(result))
                result['pending_rdap'] = {k: len(v) for k, v in state['rdap'].items() if v}
                result['pending_discord'] = len(state['discord'])
            return self.reply(200, result)
        if self.path.startswith('/domain/'):
            domain = unquote(self.path[len('/domain/'):])
            with lock:
                state['requests'].append(domain)
                queue = state['rdap'].get(domain)
                if queue:
                    response = queue.popleft()
                else:
                    state['unexpected'].append('rdap ' + domain)
                    response = {'status': 500}
            time.sleep(response.get('delay', 0))
            return self.reply(response.get('status', 200), response.get('body'), response.get('raw'))
        return self.reply(404)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
        if self.path == '/script':
            with lock:
                for domain, responses in body.get('rdap', {}).items():
                    if state['rdap'].get(domain):
                        state['unexpected'].append('overwritten pending script ' + domain)
                    state['rdap'][domain] = deque(responses)
                state['discord'].extend(body.get('discord', []))
            return self.reply(200)
        if self.path == '/webhook':
            with lock:
                state['attempts'].append(body)
                if state['discord']:
                    response = state['discord'].popleft()
                else:
                    state['unexpected'].append('discord without script')
                    response = {'status': 500}
                if 200 <= response.get('status', 204) < 300:
                    state['accepted'].append(body)
            return self.reply(response.get('status', 204), response.get('body'))
        return self.reply(404)


ThreadingHTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
