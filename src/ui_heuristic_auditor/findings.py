"""Turn raw axe-core results from several viewports into one list of findings."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ui_heuristic_auditor.capture import PageCapture

IMPACT_ORDER = {"critical": 0, "serious": 1, "moderate": 2, "minor": 3}


@dataclass
class Finding:
    """One problem on one element, with the viewports where it occurs and where it is drawn."""

    rule: str
    impact: str
    summary: str
    help_url: str
    wcag: list[str]
    selector: str
    html: str
    fix: str
    viewports: list[str] = field(default_factory=list)
    boxes: dict[str, dict[str, float]] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        """Plain dict for the JSON report."""
        return {
            "rule": self.rule,
            "impact": self.impact,
            "summary": self.summary,
            "help_url": self.help_url,
            "wcag": self.wcag,
            "selector": self.selector,
            "html": self.html,
            "fix": self.fix,
            "viewports": self.viewports,
            "boxes": self.boxes,
        }


def merge(capture: PageCapture) -> list[Finding]:
    """One finding per (rule, element), listing every viewport it appears at; worst first."""
    found: dict[tuple[str, str], Finding] = {}
    for vc in capture.viewports:
        for v in vc.violations:
            for node in v["nodes"]:
                key = (v["rule"], node["target"])
                f = found.get(key)
                if f is None:
                    f = Finding(
                        rule=v["rule"],
                        impact=v["impact"] or "minor",
                        summary=v["help"],
                        help_url=v["helpUrl"],
                        wcag=sorted(set(v["tags"])),
                        selector=node["target"],
                        html=node["html"],
                        fix=node["summary"].strip(),
                    )
                    found[key] = f
                f.viewports.append(vc.viewport.name)
                if node["box"]:
                    f.boxes[vc.viewport.name] = node["box"]
    return sorted(found.values(), key=lambda f: (IMPACT_ORDER.get(f.impact, 9), f.rule, f.selector))


def at_least(findings: list[Finding], impact: str) -> list[Finding]:
    """Findings whose impact is the given level or worse."""
    limit = IMPACT_ORDER[impact]
    return [f for f in findings if IMPACT_ORDER.get(f.impact, 9) <= limit]
