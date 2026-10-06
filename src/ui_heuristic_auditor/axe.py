"""Fetch the pinned axe-core release and verify it before it ever runs in a page."""

from __future__ import annotations

import base64
import hashlib
import io
import tarfile
import urllib.request
from pathlib import Path

AXE_VERSION = "4.13.0"
TARBALL_URL = f"https://registry.npmjs.org/axe-core/-/axe-core-{AXE_VERSION}.tgz"
# npm's published integrity for that exact tarball (Subresource Integrity format).
TARBALL_INTEGRITY = "sha512-UzGt8zg7Ny8djbYMhxl2zuEevVa7r2gJjYY5Lwr1xM7+XU2nd6CkIWFTVcCIbAP63vSz71NaVyyuSk9lHKcy0A=="
MEMBER = "package/axe.min.js"


class IntegrityError(RuntimeError):
    """The downloaded tarball does not match the pinned hash."""


def verify(tarball: bytes, integrity: str = TARBALL_INTEGRITY) -> None:
    """Raise IntegrityError unless the bytes match the npm integrity string."""
    algorithm, _, expected = integrity.partition("-")
    if algorithm != "sha512":
        raise IntegrityError(f"unsupported integrity algorithm {algorithm}")
    actual = base64.b64encode(hashlib.sha512(tarball).digest()).decode()
    if actual != expected:
        raise IntegrityError("axe-core tarball does not match the pinned sha512")


def extract_axe(tarball: bytes) -> bytes:
    """Read axe.min.js out of the package tarball without extracting anything else."""
    with tarfile.open(fileobj=io.BytesIO(tarball), mode="r:gz") as tar:
        member = tar.getmember(MEMBER)
        handle = tar.extractfile(member)
        if handle is None:
            raise IntegrityError(f"{MEMBER} is not a regular file")
        return handle.read()


def ensure_axe(cache_dir: Path) -> Path:
    """Path to a verified axe.min.js, downloading it once into cache_dir."""
    target = cache_dir / f"axe-{AXE_VERSION}.min.js"
    if target.exists():
        return target
    with urllib.request.urlopen(TARBALL_URL, timeout=60) as resp:
        tarball = resp.read()
    verify(tarball)
    cache_dir.mkdir(parents=True, exist_ok=True)
    target.write_bytes(extract_axe(tarball))
    return target
