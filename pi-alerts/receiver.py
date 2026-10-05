#!/usr/bin/env python3
import argparse, hashlib, hmac, json, os, sqlite3, subprocess, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SCHEMA = """CREATE TABLE IF NOT EXISTS alerts (
 id TEXT PRIMARY KEY, payload TEXT NOT NULL, status TEXT NOT NULL,
 created_at REAL NOT NULL, expires_at REAL, delivered_at REAL
)"""

def now(): return time.time()

def tv_power():
    if os.environ.get('HERMES_PI_TV_CONTROL') != 'on': return 'unknown'
    try:
        out=subprocess.run("printf 'pow 0\\n' | cec-client -s -d 1 /dev/cec1",shell=True,capture_output=True,text=True,timeout=4).stdout.lower()
        return 'on' if 'power status: on' in out else ('off' if 'power status: standby' in out else 'unknown')
    except (OSError, subprocess.TimeoutExpired): return 'unknown'

def maybe_wake_tv(payload):
    if payload.get('tv_policy') != 'wake_if_off' or os.environ.get('HERMES_PI_TV_CONTROL') != 'on': return
    if tv_power() == 'off':
        try: subprocess.run("printf 'on 0\\n' | cec-client -s -d 1 /dev/cec1",shell=True,timeout=4,check=False)
        except (OSError, subprocess.TimeoutExpired): pass

def validate(p):
    if not isinstance(p, dict): raise ValueError("payload must be an object")
    for key in ("id", "title", "body"):
        if not isinstance(p.get(key), str) or not p[key].strip(): raise ValueError(f"missing {key}")
    if len(p["id"]) > 160 or len(p["title"]) > 240 or len(p["body"]) > 20000: raise ValueError("field too large")
    if p.get("priority", "normal") not in {"low", "normal", "high", "critical"}: raise ValueError("invalid priority")
    return p

class App:
    def __init__(self, db, token):
        self.db = sqlite3.connect(db, check_same_thread=False)
        self.db.execute(SCHEMA); self.db.commit(); self.token = token.encode()
    def auth(self, value):
        return bool(value) and hmac.compare_digest(value.encode(), self.token)
    def enqueue(self, p):
        raw = json.dumps(p, sort_keys=True, separators=(",", ":"))
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO alerts VALUES (?, ?, 'queued', ?, ?, NULL)", (p["id"], raw, now(), p.get("expires_at")))
        row = self.db.execute("SELECT status FROM alerts WHERE id=?", (p["id"],)).fetchone()
        return row[0]
    def get(self, ident):
        row = self.db.execute("SELECT id,payload,status,created_at,expires_at,delivered_at FROM alerts WHERE id=?", (ident,)).fetchone()
        if not row: return None
        return dict(zip(("id","payload","status","created_at","expires_at","delivered_at"), row))
    def dispatch_once(self):
        row=self.db.execute("SELECT id,payload FROM alerts WHERE status='queued' ORDER BY created_at LIMIT 1").fetchone()
        if not row: return False
        ident, raw=row
        command=os.environ.get("HERMES_PI_DISPLAY_COMMAND")
        ok=False
        if command:
            try:
                result=subprocess.run(command, input=raw.encode(), shell=True, timeout=15, check=False)
                ok=result.returncode == 0
            except (OSError, subprocess.TimeoutExpired): ok=False
        if ok:
            with self.db: self.db.execute("UPDATE alerts SET status='delivered',delivered_at=? WHERE id=?",(now(),ident))
        return True

class Handler(BaseHTTPRequestHandler):
    server_version = "HermesPiAlerts/0.1"
    def send_json(self, code, value):
        data=json.dumps(value).encode(); self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        if self.path == "/health": return self.send_json(200, {"status":"ok"})
        if self.path.startswith("/v1/alerts/") and self.server.app.auth(self.headers.get("Authorization", "").removeprefix("Bearer ")):
            row=self.server.app.get(self.path.rsplit("/",1)[-1]); return self.send_json(200,row or {"error":"not found"}) if row else self.send_json(404,{"error":"not found"})
        self.send_json(401,{"error":"unauthorized"})
    def do_POST(self):
        if self.path != "/v1/alerts": return self.send_json(404,{"error":"not found"})
        token=self.headers.get("Authorization", "").removeprefix("Bearer ")
        if not self.server.app.auth(token): return self.send_json(401,{"error":"unauthorized"})
        try:
            p=validate(json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0")))))
            status=self.server.app.enqueue(p); self.send_json(202,{"id":p["id"],"status":status})
        except (ValueError, json.JSONDecodeError) as e: self.send_json(400,{"error":str(e)})
    def log_message(self, *_): pass

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--host",default="127.0.0.1"); ap.add_argument("--port",type=int,default=8787); ap.add_argument("--db",default="alerts.db"); args=ap.parse_args()
    token=os.environ.get("HERMES_PI_TOKEN");
    if not token: raise SystemExit("HERMES_PI_TOKEN is required")
    server=ThreadingHTTPServer((args.host,args.port),Handler); server.app=App(args.db,token)
    def worker():
        while True:
            server.app.dispatch_once(); time.sleep(1)
    threading.Thread(target=worker,daemon=True).start(); server.serve_forever()
if __name__ == "__main__": main()

