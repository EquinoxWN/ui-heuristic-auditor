"""Helpers shared by test modules."""

from __future__ import annotations

from pathlib import Path

from ui_heuristic_auditor.axe import ensure_axe

CACHE = Path(__file__).resolve().parents[1] / ".tmp" / "cache"


def cached_axe_path() -> Path:
    """The verified axe.min.js (downloads it once if missing)."""
    return ensure_axe(CACHE)


def png_size(data: bytes) -> tuple[int, int]:
    """Width and height from a PNG header."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
