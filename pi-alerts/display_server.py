#!/usr/bin/env python3
import html, json, os, sqlite3, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
DB=os.environ.get('HERMES_PI_ALERT_DB','/var/lib/hermes-pi-alerts/alerts.db')
def current():
    try:
        db=sqlite3.connect(DB); row=db.execute("SELECT payload FROM alerts WHERE status='queued' ORDER BY created_at LIMIT 1").fetchone(); db.close()
        return json.loads(row[0]) if row else None
    except Exception: return None
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        p=current(); blocks=[]
        for b in (p or {}).get('content', []):
            kind=b.get('type'); value=str(b.get('value',''))
            if kind == 'text': blocks.append('<p>'+html.escape(value)+'</p>')
            elif kind == 'image' and urllib.parse.urlparse(value).scheme in ('https',): blocks.append('<img src="'+html.escape(value, quote=True)+'">')
            elif kind in ('youtube','map') and urllib.parse.urlparse(value).scheme in ('https',): blocks.append('<p><a href="'+html.escape(value, quote=True)+'">Open '+kind+'</a></p>')
            elif kind == 'qr': blocks.append('<p class="qr">QR target: '+html.escape(value)+'</p>')
        extra=''.join(blocks)
        p=current(); title=html.escape(p.get('title','')) if p else 'Hermes Pi Display'; body=html.escape(p.get('body','')) if p else 'Waiting for alerts.'
        data=f'''<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><style>html,body{{margin:0;background:#101820;color:#fff;font-family:sans-serif}}main{{padding:6vw}}h1{{font-size:7vw;margin:0 0 3vw}}p{{font-size:4vw;white-space:pre-wrap}}img{{max-width:90vw;max-height:55vh}}a{{color:#7dd3fc;font-size:3vw}}</style><main><h1>{title}</h1><p>{body}</p>{extra}</main><script>setTimeout(()=>location.reload(),2000)</script>'''.encode()
        self.send_response(200); self.send_header('Content-Type','text/html'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def log_message(self,*a): pass
ThreadingHTTPServer(('127.0.0.1',8788),Handler).serve_forever()
