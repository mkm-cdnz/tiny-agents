"""HTTP checks exercise the snapshot without loading a model or touching live data."""
import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
import server

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        server.store = server.Store(Path(self.temp.name))
        self.http = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
    def tearDown(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join()
        self.temp.cleanup()
    def request(self, method, path, payload=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.http.server_port)
        try:
            h = {'Content-Type':'application/json'}
            h.update(headers or {})
            conn.request(method, path, json.dumps(payload) if payload is not None else None, h)
            response = conn.getresponse()
            return response.status, response.read()
        finally:
            conn.close()
    def test_page_loads(self):
        status, body = self.request('GET', '/')
        self.assertEqual(status, 200)
        self.assertIn(b'Agent Eyes', body)
    def test_unknown_host_rejected(self):
        self.assertEqual(self.request('GET', '/', headers={'Host':'untrusted.invalid'})[0], 403)
    def test_cross_origin_submission_rejected(self):
        self.assertEqual(self.request('POST','/api/captures',{}, {'Origin':'https://untrusted.invalid'})[0],403)
    def test_blank_prompt_rejected(self):
        self.assertEqual(self.request('POST','/api/captures',{'prompt':''})[0],400)
    def test_photo_path_traversal_rejected(self):
        self.assertEqual(self.request('GET','/photos/../../server.py')[0],403)
    def test_private_history_starts_empty(self):
        status, body = self.request('GET','/api/history')
        self.assertEqual(status,200)
        self.assertEqual(json.loads(body),[])

if __name__ == '__main__': unittest.main()
