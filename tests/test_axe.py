"""axe-core is pinned by version and npm integrity hash, and only axe.min.js is read."""

from __future__ import annotations

import io
import tarfile
import urllib.request
from pathlib import Path

import pytest
from tests_support import cached_axe_path

from ui_heuristic_auditor import axe
from ui_heuristic_auditor.axe import AXE_VERSION, IntegrityError, extract_axe, verify


def test_the_pinned_axe_core_was_verified_and_cached() -> None:
    path = cached_axe_path()
    assert path.name == f"axe-{AXE_VERSION}.min.js"
    assert path.read_text(encoding="utf-8").startswith(f"/*! axe v{AXE_VERSION}")


def test_a_tampered_tarball_is_rejected() -> None:
    with pytest.raises(IntegrityError, match="does not match"):
        verify(b"not the real tarball")
    with pytest.raises(IntegrityError, match="unsupported"):
        verify(b"x", "md5-abc")


def test_only_axe_min_js_is_read_from_the_package() -> None:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, data in [("package/axe.min.js", b"window.axe={}"), ("../evil.sh", b"rm -rf /")]:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    assert extract_axe(buf.getvalue()) == b"window.axe={}"


def test_a_crash_while_caching_never_leaves_a_partial_axe_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeResponse(io.BytesIO):
        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, *exc: object) -> None:
            return None

    monkeypatch.setattr(urllib.request, "urlopen", lambda url, timeout: FakeResponse(b"tgz"))
    monkeypatch.setattr(axe, "verify", lambda tarball: None)
    monkeypatch.setattr(axe, "extract_axe", lambda tarball: b"/*! axe */" * 100)
    real_write = Path.write_bytes

    def disk_full(self: Path, data: bytes) -> int:
        real_write(self, data[: len(data) // 2])
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_bytes", disk_full)
    with pytest.raises(OSError, match="disk full"):
        axe.ensure_axe(tmp_path)
    assert list(tmp_path.iterdir()) == [], "a half-written file would be trusted as the cache"
