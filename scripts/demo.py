"""Serve the fixture site on a free port, audit the seeded page, then stop the server."""

from __future__ import annotations

import functools
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ui_heuristic_auditor.cli import main

SITE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "site"

if __name__ == "__main__":
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(SimpleHTTPRequestHandler, directory=str(SITE))
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        code = main(
            [f"http://127.0.0.1:{server.server_address[1]}/seeded.html", "--out", ".tmp/demo"]
        )
    finally:
        server.shutdown()
        server.server_close()
    sys.exit(code)
