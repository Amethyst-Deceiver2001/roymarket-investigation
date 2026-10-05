#!/usr/bin/env python3
"""Serve the internal status board, rebuilt from the registry on every page load.

  python3 exhibits/serve_status_board.py            # http://127.0.0.1:8765/
  python3 exhibits/serve_status_board.py --port 9000

Run it in its own terminal and refresh the browser tab: each load takes a fresh board
(about a second). It binds to 127.0.0.1 only, because the page carries slugs, ИНН and
open questions; do not pass --host 0.0.0.0 on a shared network. Local file processing,
no network calls; nothing is written to disk.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "exhibits"))
import build_status_board as bsb  # noqa: E402
import status_board as sb  # noqa: E402


def render() -> bytes:
    ss, dv = sb.default_path("weekly_scan_state.json"), sb.default_path("developments.json")
    board = sb.Board(date.today(),
                     json.loads(ss.read_text(encoding="utf-8")) if ss and ss.exists() else None,
                     json.loads(dv.read_text(encoding="utf-8")) if dv and dv.exists() else None).build()
    return bsb.build(board).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] not in ("/", "/index.html"):
            self.send_error(404)
            return
        t = time.time()
        try:
            body = render()
        except Exception as exc:  # show the failure in the tab instead of a blank page
            body = f"<pre>board build failed: {exc!r}</pre>".encode("utf-8")
            self.send_response(500)
        else:
            self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
        print(f"served board in {time.time() - t:.1f}s", flush=True)

    def log_message(self, *args):
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    print(f"status board at http://{a.host}:{a.port}/  (Ctrl-C to stop)", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
