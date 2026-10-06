"""A local fixture website (with a deliberately slow page) and one shared headless browser."""

from __future__ import annotations

import functools
import threading
import time
from collections.abc import Iterator
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from ui_heuristic_auditor.capture import Auditor

SITE = Path(__file__).parent / "fixtures" / "site"
CACHE = Path(__file__).resolve().parents[1] / ".tmp" / "cache"


class _Handler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/slow":
            time.sleep(5)
        super().do_GET()

    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.fixture(scope="session")
def site() -> Iterator[str]:
    """Base URL of the fixture site served from tests/fixtures/site."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Handler, directory=str(SITE)))
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


@pytest.fixture(scope="session")
def auditor() -> Iterator[Auditor]:
    """One headless Chromium for the whole session."""
    with Auditor(CACHE, timeout_ms=15_000) as a:
        yield a
