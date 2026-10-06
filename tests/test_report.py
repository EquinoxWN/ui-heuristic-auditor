"""The Markdown summary stays inert whatever the audited page puts in its title or markup."""

from __future__ import annotations

from pathlib import Path

from ui_heuristic_auditor.capture import PageCapture
from ui_heuristic_auditor.findings import Finding
from ui_heuristic_auditor.report import md_code, write_report

EVIL_TITLE = "Shop</h1><img src=x onerror=alert(1)>\n# injected [click](javascript:alert(1))"


def finding(selector: str, help_url: str) -> Finding:
    """A finding whose page-controlled fields are hostile."""
    return Finding(
        rule="color-contrast",
        impact="serious",
        summary="Elements must meet minimum color contrast ratio thresholds",
        help_url=help_url,
        wcag=["wcag2aa"],
        selector=selector,
        html="<a>",
        fix="Fix any of the following:\n| broken | table |",
        viewports=["desktop"],
    )


def unescaped_pipes(row: str) -> int:
    """Pipes that a GitHub table would treat as cell borders."""
    return row.count("|") - row.count("\\|")


def test_a_hostile_title_and_selector_cannot_inject_html_or_markdown(tmp_path: Path) -> None:
    good = finding("a`b|c", "https://dequeuniversity.com/rules/axe/4.13/color-contrast")
    bad_link = finding("p", "javascript:alert(1)")
    write_report(PageCapture("https://example.test/", EVIL_TITLE), [good, bad_link], tmp_path)
    md = (tmp_path / "summary.md").read_text(encoding="utf-8")
    lines = md.splitlines()
    assert lines[0].startswith("# Accessibility audit: Shop")
    assert "<img" not in md
    assert "</h1>" not in md
    assert not any(line.startswith("# injected") for line in lines)
    assert "](javascript:" not in md
    rows = [line for line in lines if line.startswith("| serious")]
    assert len(rows) == 2
    assert all(unescaped_pipes(r) == 6 for r in rows), "every row keeps exactly five cells"
    assert "(<https://dequeuniversity.com/rules/axe/4.13/color-contrast>)" in rows[0]
    assert "](" not in rows[1], "a non-https help link is shown as plain text"


def test_code_spans_use_a_fence_longer_than_any_backtick_run() -> None:
    assert md_code("button") == "` button `"
    assert md_code("a`b") == "`` a`b ``"
    assert md_code("x``y\nz") == "``` x``y z ```"
