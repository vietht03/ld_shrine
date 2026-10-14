#!/usr/bin/env python3
"""
shop_server.py
==============
Lightweight HTTP server that:
  1. Serves  upgrade_shop.html  (and any static files in the game root)
     at  http://127.0.0.1:55234/
  2. Accepts  POST /save  with JSON body  → writes  shop_state.json
  3. Serves  shop_state.json  for GET requests (CORS-enabled)

Run automatically by the game when the player opens the Skill Shop.
Port: 55234 (fixed, unlikely to conflict).

Usage:
    python3 shop_server.py          # run directly
    # or imported and called:
    from shop_server import start_shop_server, open_shop
    start_shop_server()   # starts background thread
    open_shop()           # opens browser
"""
from __future__ import annotations
import json
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PORT        = 55234
GAME_ROOT   = Path(__file__).parent
STATE_FILE  = GAME_ROOT / "shop_state.json"
HTML_FILE   = GAME_ROOT / "upgrade_shop.html"

_server_thread: threading.Thread | None = None
_httpd: HTTPServer | None = None


class _Handler(BaseHTTPRequestHandler):
    """Simple handler: serve static files + accept POST /save."""

    def log_message(self, fmt, *args):          # suppress console noise
        pass

    # ── CORS pre-flight ─────────────────────────────────────────────────────
    def do_OPTIONS(self):
        self._send_cors(200)

    # ── GET: serve shop HTML / shop_state.json / other files ────────────────
    def do_GET(self):
        path = self.path.split("?")[0].lstrip("/")
        if path == "" or path == "upgrade_shop.html":
            self._serve_file(HTML_FILE, "text/html; charset=utf-8")
        elif path == "shop_state.json":
            self._serve_file(STATE_FILE, "application/json")
        else:
            # Try serving from game root
            fp = GAME_ROOT / path
            if fp.exists() and fp.is_file():
                ct = "application/octet-stream"
                self._serve_file(fp, ct)
            else:
                self._send_cors(404)
                self.wfile.write(b"Not found")

    # ── POST /save: receive JSON from browser, write shop_state.json ─────────
    def do_POST(self):
        if self.path != "/save":
            self._send_cors(404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            data   = json.loads(body)
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self._send_cors(200)
            self.wfile.write(b'{"ok":true}')
        except Exception as e:
            self._send_cors(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _send_cors(self, code: int, content_type: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def _serve_file(self, fp: Path, content_type: str) -> None:
        if not fp.exists():
            self._send_cors(404)
            self.wfile.write(b"Not found")
            return
        data = fp.read_bytes()
        self._send_cors(200, content_type)
        self.wfile.write(data)


def start_shop_server() -> None:
    """Start the save-server in a daemon background thread (call once)."""
    global _httpd, _server_thread
    if _server_thread and _server_thread.is_alive():
        return   # already running

    _httpd = HTTPServer(("127.0.0.1", PORT), _Handler)

    def _run():
        _httpd.serve_forever()

    _server_thread = threading.Thread(target=_run, daemon=True)
    _server_thread.start()
    print(f"[ShopServer] Listening on http://127.0.0.1:{PORT}/")


def open_shop() -> None:
    """Open the upgrade shop in the system default browser."""
    start_shop_server()
    url = f"http://127.0.0.1:{PORT}/upgrade_shop.html"
    webbrowser.open(url)
    print(f"[ShopServer] Opened shop at {url}")


if __name__ == "__main__":
    # Run standalone: start server + open browser
    open_shop()
    print("Press Ctrl+C to stop.")
    try:
        _server_thread.join()
    except KeyboardInterrupt:
        if _httpd:
            _httpd.shutdown()
