"""Screen sizes the auditor captures."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Viewport:
    """A device profile: CSS size in pixels and whether it behaves like a phone."""

    name: str
    width: int
    height: int
    mobile: bool


VIEWPORTS: dict[str, Viewport] = {
    "mobile": Viewport("mobile", 390, 844, mobile=True),
    "desktop": Viewport("desktop", 1440, 900, mobile=False),
}
