"""Merging viewport results: one finding per rule and element, worst first."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ui_heuristic_auditor.capture import PageCapture, ViewportCapture
from ui_heuristic_auditor.findings import merge
from ui_heuristic_auditor.viewports import VIEWPORTS


def violation(
    rule: str, impact: str, target: str, box: dict[str, float] | None = None
) -> dict[str, Any]:
    return {
        "rule": rule,
        "impact": impact,
        "help": f"{rule} help",
        "helpUrl": f"https://dequeuniversity.com/rules/axe/4.13/{rule}",
        "tags": ["wcag2a", "wcag111"],
        "nodes": [
            {
                "target": target,
                "html": f"<x id={target}>",
                "summary": "Fix any of the following: x",
                "box": box,
            }
        ],
    }


def capture(per_viewport: dict[str, list[dict[str, Any]]]) -> PageCapture:
    return PageCapture(
        "http://x",
        "t",
        [
            ViewportCapture(VIEWPORTS[n], Path("s.png"), Path("d.html"), 1000, v)
            for n, v in per_viewport.items()
        ],
    )


def test_the_same_problem_at_two_sizes_is_one_finding_with_both() -> None:
    box = {"x": 1.0, "y": 2.0, "width": 3.0, "height": 4.0}
    findings = merge(
        capture(
            {
                "mobile": [violation("label", "critical", "#a", box)],
                "desktop": [violation("label", "critical", "#a")],
            }
        )
    )
    assert len(findings) == 1
    assert findings[0].viewports == ["mobile", "desktop"]
    assert findings[0].boxes == {"mobile": box}


def test_findings_are_sorted_worst_first_then_by_rule() -> None:
    findings = merge(
        capture(
            {
                "desktop": [
                    violation("region", "moderate", "#r"),
                    violation("image-alt", "critical", "#i"),
                    violation("color-contrast", "serious", "#c"),
                    violation("button-name", "critical", "#b"),
                ]
            }
        )
    )
    assert [f.rule for f in findings] == ["button-name", "image-alt", "color-contrast", "region"]
