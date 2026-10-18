"""Throwaway local vision demo. Standard library only; private Tailscale Serve frontend."""
import base64
import concurrent.futures
from contextlib import contextmanager
import datetime
import json
import mimetypes
import os
import sqlite3
import threading
import time
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8766
# Public snapshot: inject private hostnames/IPs locally; never commit a device export.
TAILNET_HOST = os.environ.get('AGENT_EYES_HOST', '').strip().lower()
ALLOWED_HOSTS = {'127.0.0.1', 'localhost'} | ({TAILNET_HOST} if TAILNET_HOST else set())
ALLOWED_ORIGINS = {'http://127.0.0.1:8766', 'http://localhost:8766'}
if TAILNET_HOST:
    ALLOWED_ORIGINS.update({'https://' + TAILNET_HOST, 'http://' + TAILNET_HOST + ':8080'})

def ollama(path, payload=None, timeout=20):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request('http://127.0.0.1:11434' + path, data=data, headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)

def models():
    return [m['name'] for m in ollama('/api/tags')['models'] if 'vision' in m.get('capabilities', [])]

class Store:
    def __init__(self, root):
        self.root = root
        (root / 'photos').mkdir(parents=True, exist_ok=True)
        self.db = root / 'history.sqlite'
        with self.connect() as c:
            c.execute('CREATE TABLE IF NOT EXISTS captures (id TEXT PRIMARY KEY, created TEXT, model TEXT, prompt TEXT, photo TEXT, status TEXT, answer TEXT, error TEXT, seconds REAL)')
            c.execute("UPDATE captures SET status='error', error='Demo restarted before completion' WHERE status IN ('queued','running')")
    @contextmanager
    def connect(self):
        c = sqlite3.connect(self.db)
        c.row_factory = sqlite3.Row
        try:
            with c:
                yield c
        finally:
            c.close()
    def create(self, prompt, model, image, mime):
        ident = uuid.uuid4().hex
        ext = {'image/jpeg':'.jpg', 'image/png':'.png', 'image/webp':'.webp'}[mime]
        photo = 'photos/' + ident + ext
        (self.root / photo).write_bytes(image)
        with self.connect() as c:
            c.execute('INSERT INTO captures VALUES (?,?,?,?,?,?,?,?,?)', (ident, datetime.datetime.now().astimezone().isoformat(timespec='seconds'), model, prompt, photo, 'queued', '', None, None))
        return self.get(ident)
    def get(self, ident):
        with self.connect() as c:
            r = c.execute('SELECT * FROM captures WHERE id=?', (ident,)).fetchone()
            return dict(r) if r else None
    def recent(self):
        with self.connect() as c:
            return [dict(r) for r in c.execute('SELECT * FROM captures ORDER BY created DESC, rowid DESC LIMIT 30')]
    def finish(self, ident, answer, error, seconds=None):
        with self.connect() as c:
            c.execute('UPDATE captures SET status=?, answer=?, error=?, seconds=? WHERE id=?', ('error' if error else 'done', answer, error, seconds, ident))

store = None
pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)

def process(ident):
    started = time.monotonic()
    record = store.get(ident)
    with store.connect() as c:
        c.execute("UPDATE captures SET status='running' WHERE id=?", (ident,))
    try:
        image = base64.b64encode((store.root / record['photo']).read_bytes()).decode()
        result = ollama('/api/chat', {'model':record['model'], 'messages':[{'role':'user', 'content':record['prompt'], 'images':[image]}], 'stream':False, 'think':False, 'keep_alive':'2m', 'options':{'num_ctx':4096, 'num_predict':512}}, timeout=900)
        answer = result['message']['content'].strip()
        if not answer:
            raise ValueError('Model returned no answer. Try another installed model.')
        store.finish(ident, answer, None, round(time.monotonic()-started, 2))
    except Exception as exc:
        store.finish(ident, '', str(exc), round(time.monotonic()-started, 2))

class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data, mime='application/json'):
        if mime == 'application/json': data = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.end_headers()
        self.wfile.write(data)
    def valid_host(self):
        return self.headers.get('Host', '').split(':')[0].lower() in ALLOWED_HOSTS
    def do_GET(self):
        if not self.valid_host(): return self.reply(403, {'error':'Host not allowed'})
        path = self.path.split('?')[0]
        try:
            if path == '/': return self.reply(200, (ROOT/'index.html').read_bytes(), 'text/html; charset=utf-8')
            if path == '/api/models': return self.reply(200, {'models':models()})
            if path == '/api/history': return self.reply(200, store.recent())
            if path.startswith('/api/jobs/'):
                record = store.get(path.rsplit('/',1)[-1])
                return self.reply(200 if record else 404, record or {'error':'Not found'})
            if path.startswith('/photos/'):
                target = (store.root / path.lstrip('/')).resolve()
                if target.parent != (store.root/'photos').resolve(): return self.reply(403, {'error':'Forbidden'})
                return self.reply(200, target.read_bytes(), mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
            return self.reply(404, {'error':'Not found'})
        except FileNotFoundError: self.reply(404, {'error':'Not found'})
        except Exception as exc: self.reply(503, {'error':str(exc)})
    def do_POST(self):
        if not self.valid_host(): return self.reply(403, {'error':'Host not allowed'})
        origin = self.headers.get('Origin')
        if origin and origin not in ALLOWED_ORIGINS:
            return self.reply(403, {'error':'Origin not allowed'})
        if self.path != '/api/captures': return self.reply(404, {'error':'Not found'})
        try:
            length = int(self.headers.get('Content-Length',0))
            if not 0 < length <= 22000000: return self.reply(413, {'error':'Image request too large (limit 22 MB)'})
            if not self.headers.get('Content-Type','').startswith('application/json'): return self.reply(415, {'error':'JSON required'})
            obj = json.loads(self.rfile.read(length))
            prompt = obj.get('prompt','').strip()
            if not prompt or len(prompt)>12000: raise ValueError('Enter a prompt (up to 12000 characters)')
            if obj.get('model') not in models(): raise ValueError('Select an installed vision model')
            mime = obj.get('mime')
            if mime not in ('image/jpeg','image/png','image/webp'): raise ValueError('Use a JPEG, PNG or WebP photo')
            image = base64.b64decode(obj.get('image',''), validate=True)
            signature_ok = (mime=='image/jpeg' and image.startswith(b'\xff\xd8\xff')) or (mime=='image/png' and image.startswith(b'\x89PNG\r\n\x1a\n')) or (mime=='image/webp' and image.startswith(b'RIFF') and image[8:12]==b'WEBP')
            if not signature_ok: raise ValueError('Invalid image format')
            if sum(r['status'] in ('queued','running') for r in store.recent()) >= 3:
                return self.reply(429, {'error':'Queue full; wait for a request to finish'})
            record = store.create(prompt, obj['model'], image, mime)
            pool.submit(process, record['id'])
            self.reply(202, record)
        except (ValueError, TypeError, KeyError) as exc: self.reply(400, {'error':str(exc)})
        except Exception as exc: self.reply(503, {'error':str(exc)})

if __name__ == '__main__':
    store = Store(ROOT/'data')
    print(f'Agent Eyes demo listening on http://127.0.0.1:{PORT}', flush=True)
    ThreadingHTTPServer(('127.0.0.1',PORT),Handler).serve_forever()
