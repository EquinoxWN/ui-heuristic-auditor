"""axe-core is pinned by version and npm integrity hash, and only axe.min.js is read."""

from __future__ import annotations

import io
import tarfile

import pytest
from tests_support import cached_axe_path

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
