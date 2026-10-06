"""Real headless Chromium against the fixture site: screenshots, DOM and axe-core results."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests_support import png_size

from ui_heuristic_auditor.capture import Auditor, CaptureError, check_url
from ui_heuristic_auditor.findings import at_least, merge
from ui_heuristic_auditor.viewports import VIEWPORTS

BOTH = [VIEWPORTS["mobile"], VIEWPORTS["desktop"]]
SEEDED = {"image-alt", "label", "button-name", "link-name", "color-contrast", "html-has-lang"}


def test_each_viewport_gets_a_screenshot_of_its_width_and_the_dom(
    auditor: Auditor, site: str, tmp_path: Path
) -> None:
    capture = auditor.capture(f"{site}/responsive.html", tmp_path, BOTH)
    assert capture.title == "Responsive page"
    for vc in capture.viewports:
        width, height = png_size(vc.screenshot.read_bytes())
        assert width == vc.viewport.width
        assert height == vc.page_height > vc.viewport.height, "full-page screenshot"
        assert "Catalogue" in vc.dom.read_text(encoding="utf-8")
        assert (tmp_path / f"axe-{vc.viewport.name}.json").exists()


def test_a_clean_page_has_no_findings(auditor: Auditor, site: str, tmp_path: Path) -> None:
    assert merge(auditor.capture(f"{site}/clean.html", tmp_path, BOTH)) == []


def test_every_seeded_problem_is_found_on_the_seeded_page(
    auditor: Auditor, site: str, tmp_path: Path
) -> None:
    findings = merge(auditor.capture(f"{site}/seeded.html", tmp_path, BOTH))
    assert {f.rule for f in findings} == SEEDED
    by_rule = {f.rule: f for f in findings}
    assert by_rule["image-alt"].selector == "#hero"
    assert by_rule["label"].selector == "#coupon"
    assert by_rule["button-name"].selector == "#close"
    assert by_rule["link-name"].selector == "#empty-link"
    assert by_rule["color-contrast"].selector == "#faint"
    for f in findings:
        assert f.viewports == ["mobile", "desktop"], f.rule
        assert f.fix, f"{f.rule} has a suggested fix"
        assert f.help_url.startswith("https://dequeuniversity.com/rules/axe/")
        assert any(t.startswith("wcag") for t in f.wcag)


def test_problems_that_exist_at_only_one_size_are_attributed_to_that_size(
    auditor: Auditor, site: str, tmp_path: Path
) -> None:
    findings = {
        f.selector: f for f in merge(auditor.capture(f"{site}/responsive.html", tmp_path, BOTH))
    }
    assert findings["#menu-toggle"].rule == "button-name"
    assert findings["#menu-toggle"].viewports == ["mobile"]
    assert findings["#sidebar-search"].rule == "label"
    assert findings["#sidebar-search"].viewports == ["desktop"]
    assert len(findings) == 2


def test_findings_carry_boxes_inside_the_screenshot(
    auditor: Auditor, site: str, tmp_path: Path
) -> None:
    capture = auditor.capture(f"{site}/seeded.html", tmp_path, BOTH)
    heights = {vc.viewport.name: vc.page_height for vc in capture.viewports}
    for f in merge(capture):
        for name, box in f.boxes.items():
            vp = VIEWPORTS[name]
            assert box["x"] >= 0, (f.rule, name, box)
            assert box["x"] + box["width"] <= vp.width, (f.rule, name, box)
            assert box["y"] >= 0, (f.rule, name, box)
            assert box["y"] + box["height"] <= heights[name], (f.rule, name, box)


def test_impact_threshold_filtering(auditor: Auditor, site: str, tmp_path: Path) -> None:
    findings = merge(auditor.capture(f"{site}/seeded.html", tmp_path, [VIEWPORTS["desktop"]]))
    critical = at_least(findings, "critical")
    assert {f.rule for f in critical} <= {f.rule for f in at_least(findings, "minor")}
    assert at_least(findings, "minor") == findings
    impacts = [f.impact for f in findings]
    assert impacts == sorted(impacts, key=["critical", "serious", "moderate", "minor"].index), (
        "worst first"
    )


@pytest.mark.parametrize(
    "url", ["file:///etc/passwd", "javascript:alert(1)", "ftp://example.com", "http://"]
)
def test_only_http_urls_are_audited(url: str) -> None:
    with pytest.raises(CaptureError, match="only http"):
        check_url(url)


def test_a_page_that_does_not_load_in_time_is_an_error(
    auditor: Auditor, site: str, tmp_path: Path
) -> None:
    with pytest.raises(CaptureError, match="could not load"):
        auditor.capture(f"{site}/slow", tmp_path, [VIEWPORTS["desktop"]], timeout_ms=1_000)
