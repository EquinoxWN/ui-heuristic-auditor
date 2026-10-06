"""Capture a page at several viewports and audit it for accessibility problems."""

from ui_heuristic_auditor.capture import Auditor, CaptureError, PageCapture
from ui_heuristic_auditor.findings import Finding, merge
from ui_heuristic_auditor.viewports import VIEWPORTS, Viewport

__all__ = ["VIEWPORTS", "Auditor", "CaptureError", "Finding", "PageCapture", "Viewport", "merge"]
