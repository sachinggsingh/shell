import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from dev_shell.core.errors import StreamDisconnected
from dev_shell.monitoring.reconnect import ReconnectPolicy
from dev_shell.monitoring.stream_client import MonitoringStreamClient


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = json.dumps({"status": "ok", "version": "0.1.0", "server_id": "server-1"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson")
            self.end_headers()
            events = [
                {
                    "type": "ready",
                    "version": 1,
                    "timestamp": "2026-09-29T09:30:01Z",
                    "server_id": "server-1",
                    "sequence": 1,
                    "data": {},
                },
                {
                    "type": "metric",
                    "version": 1,
                    "timestamp": "2026-09-29T09:30:02Z",
                    "server_id": "server-1",
                    "sequence": 3,
                    "data": {"name": "cpu.percent", "value": 11.0, "unit": "percent"},
                },
            ]
            for event in events:
                self.wfile.write((json.dumps(event) + "\n").encode())
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return


def test_health_and_stream_and_sequence_gap():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        client = MonitoringStreamClient(f"http://127.0.0.1:{port}")
        health = client.health()
        assert health["status"] == "ok"
        events = []
        try:
            for event in client.stream():
                events.append(event)
        except StreamDisconnected:
            pass
        assert events[0].event_type == "ready"
        assert events[1].event_type == "metric"
        assert 2 in client.sequence_gaps
    finally:
        server.shutdown()


def test_reconnect_backoff():
    policy = ReconnectPolicy()
    assert policy.next_delay() == 1
    assert policy.next_delay() == 2
    assert policy.next_delay() == 4
    policy.reset()
    assert policy.next_delay() == 1
    for _ in range(10):
        delay = policy.next_delay()
    assert delay == 30
