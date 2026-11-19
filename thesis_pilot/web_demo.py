"""Local browser prototype. Every submitted question invokes live Modal models."""
import json
import secrets
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .live_cli import OUT, run
from .core import AGENTS,prompt

HERE = Path(__file__).resolve().parent
TOKEN = secrets.token_urlsafe(24)
JOBS = {}
LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def log_message(self,format,*args):
        if not self.path.startswith('/api/jobs/'):
            super().log_message(format,*args)

    def send(self, status, value, content_type='application/json; charset=utf-8'):
        body = value.encode() if isinstance(value, str) else json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/':
            return self.send(200, (HERE/'demo.html').read_text().replace('__TOKEN__', TOKEN), 'text/html; charset=utf-8')
        if self.path == '/api/cases':
            packet = json.loads((OUT/'packet_private.json').read_text())
            return self.send(200, packet['visible']['cases'])  # Public document inputs only.
        if self.path.startswith('/api/jobs/'):
            value = JOBS.get(self.path.rsplit('/', 1)[-1])
            return self.send(200 if value else 404, value or {'error': 'Unknown job'})
        self.send(404, {'error': 'Not found'})

    def do_POST(self):
        if self.path != '/api/jobs':
            return self.send(404, {'error': 'Not found'})
        if self.headers.get('X-Demo-Token') != TOKEN:
            return self.send(403, {'error': 'Open the local demo page first'})
        size = int(self.headers.get('Content-Length', '0'))
        if size < 1 or size > 262144:
            return self.send(400, {'error': 'Input must be 1–262144 bytes'})
        try:
            data = json.loads(self.rfile.read(size))
            index = int(data['case_index'])
            question = str(data['question']).strip()
            mode = data.get('mode', 'repguard')
            document = data.get('document')
            if not 0 <= index < 100 or not question or len(question) > 4000:
                raise ValueError('Invalid question or report index')
            if mode not in ['repguard', 'always_a', 'always_b','repaired_b','typed_b']:
                raise ValueError('Invalid mode')
            if document is not None:
                if not isinstance(document,dict):raise ValueError('Document must be a JSON object')
                prompt(document,AGENTS[0])  # Reject gold and unsupported runtime fields before any model call.
        except (KeyError, ValueError, TypeError) as error:
            return self.send(400, {'error': str(error)})
        if not LOCK.acquire(blocking=False):
            return self.send(409, {'error': 'A real inference job is already running'})
        job_id = uuid.uuid4().hex
        JOBS[job_id] = {'state': 'running'}
        def execute():
            try:
                result = run(index,question,'always_b' if mode in ['repaired_b','typed_b'] else mode,document,
                             'typed_tools' if mode=='typed_b' else 'schema_prompt' if mode=='repaired_b' else 'frozen')
                JOBS[job_id] = {'state': 'completed', 'result': result}
            except Exception as error:
                JOBS[job_id] = {'state': 'failed', 'error': type(error).__name__+': '+str(error)}
            finally:
                LOCK.release()
        threading.Thread(target=execute, daemon=True).start()
        self.send(202, {'job_id': job_id})


if __name__ == '__main__':
    print('Real inference demo: http://127.0.0.1:8765 (private local server)', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8765), Handler).serve_forever()
