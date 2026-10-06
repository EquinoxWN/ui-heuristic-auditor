"""Open a page in headless Chromium at each viewport: screenshot, DOM and axe-core results."""

from __future__ import annotations

import json
import urllib.parse
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import Any

from playwright.sync_api import Browser, Error, Playwright, sync_playwright

from ui_heuristic_auditor.axe import ensure_axe
from ui_heuristic_auditor.viewports import Viewport

# WCAG A and AA rules only: deterministic, standard-backed checks (best practices are excluded).
WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]

_RUN_AXE = """async (tags) => {
  const results = await axe.run(document, { runOnly: { type: 'tag', values: tags }, resultTypes: ['violations'] });
  return results.violations.map((v) => ({
    rule: v.id, impact: v.impact, help: v.help, helpUrl: v.helpUrl,
    tags: v.tags.filter((t) => t.startsWith('wcag')),
    nodes: v.nodes.map((n) => {
      const target = n.target.map((t) => Array.isArray(t) ? t.join(' >>> ') : t).join(' ');
      let box = null;
      try {
        const el = document.querySelector(n.target[n.target.length - 1]);
        if (el) {
          const r = el.getBoundingClientRect();
          box = { x: r.x + window.scrollX, y: r.y + window.scrollY, width: r.width, height: r.height };
        }
      } catch (e) { box = null; }
      return { target, html: n.html.slice(0, 500), summary: n.failureSummary || '', box };
    }),
  }));
}"""


class CaptureError(RuntimeError):
    """The page could not be loaded or audited."""


@dataclass(frozen=True)
class ViewportCapture:
    """What one viewport produced."""

    viewport: Viewport
    screenshot: Path
    dom: Path
    page_height: int
    violations: list[dict[str, Any]]


@dataclass(frozen=True)
class PageCapture:
    """A page captured at every requested viewport."""

    url: str
    title: str
    viewports: list[ViewportCapture] = field(default_factory=list)


def check_url(url: str) -> str:
    """Return the URL if it is http(s) with a host; refuse file:, javascript: and others."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise CaptureError(f"only http(s) URLs can be audited, got {url!r}")
    return url


class Auditor:
    """Owns one headless browser; use as a context manager and call capture() per page."""

    def __init__(self, cache_dir: Path, timeout_ms: int = 30_000) -> None:
        self._axe = ensure_axe(cache_dir).read_text(encoding="utf-8")
        self._timeout_ms = timeout_ms
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    def __enter__(self) -> Auditor:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def capture(
        self, url: str, out_dir: Path, viewports: Sequence[Viewport], timeout_ms: int | None = None
    ) -> PageCapture:
        """Load url at each viewport, save screenshot and DOM, and run axe-core."""
        timeout = timeout_ms or self._timeout_ms
        if self._browser is None:
            raise CaptureError("use Auditor as a context manager")
        check_url(url)
        out_dir.mkdir(parents=True, exist_ok=True)
        captures: list[ViewportCapture] = []
        title = ""
        for vp in viewports:
            context = self._browser.new_context(
                viewport={"width": vp.width, "height": vp.height},
                is_mobile=vp.mobile,
                has_touch=vp.mobile,
                device_scale_factor=1,
            )
            try:
                page = context.new_page()
                page.set_default_timeout(timeout)
                try:
                    page.goto(url, wait_until="load", timeout=timeout)
                except Error as e:
                    raise CaptureError(
                        f"could not load {url} at {vp.name}: {e.message.splitlines()[0]}"
                    ) from e
                title = page.title()
                shot = out_dir / f"screenshot-{vp.name}.png"
                page.screenshot(path=str(shot), full_page=True)
                dom = out_dir / f"dom-{vp.name}.html"
                dom.write_text(page.content(), encoding="utf-8")
                page.add_script_tag(content=self._axe)
                violations: list[dict[str, Any]] = page.evaluate(_RUN_AXE, WCAG_TAGS)
                height = int(page.evaluate("() => document.documentElement.scrollHeight"))
                (out_dir / f"axe-{vp.name}.json").write_text(
                    json.dumps(violations, indent=2), encoding="utf-8"
                )
                captures.append(ViewportCapture(vp, shot, dom, height, violations))
            finally:
                context.close()
        return PageCapture(url, title, captures)
