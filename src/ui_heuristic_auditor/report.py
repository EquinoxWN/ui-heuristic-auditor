"""Write the JSON report and a short Markdown summary."""

from __future__ import annotations

import html
import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from ui_heuristic_auditor.capture import PageCapture
from ui_heuristic_auditor.findings import IMPACT_ORDER, Finding

# Characters that start Markdown syntax; the audited page controls titles and selectors.
_MD_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+!|~>-])")


def md_text(value: str) -> str:
    """Page-controlled text as inert Markdown: one line, HTML escaped, syntax characters escaped."""
    one_line = " ".join(value.split())
    return _MD_SPECIAL.sub(r"\\\1", html.escape(one_line, quote=False))


def md_code(value: str) -> str:
    """Page-controlled text as an inline code span that no backtick or pipe inside can break."""
    one_line = " ".join(value.split()).replace("|", "\\|")
    fence = "`" * (max((len(run) for run in re.findall(r"`+", one_line)), default=0) + 1)
    return f"{fence} {one_line} {fence}"


def write_report(capture: PageCapture, findings: list[Finding], out_dir: Path) -> Path:
    """Write report.json and summary.md into out_dir; returns the JSON path."""
    counts = Counter(f.impact for f in findings)
    report = {
        "schema": 1,
        "url": capture.url,
        "title": capture.title,
        "captured_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "viewports": [
            {
                "name": vc.viewport.name,
                "width": vc.viewport.width,
                "height": vc.viewport.height,
                "page_height": vc.page_height,
                "screenshot": vc.screenshot.name,
                "dom": vc.dom.name,
            }
            for vc in capture.viewports
        ],
        "counts": {k: counts.get(k, 0) for k in IMPACT_ORDER},
        "findings": [f.to_json() for f in findings],
    }
    path = out_dir / "report.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        f"# Accessibility audit: {md_text(capture.title or capture.url)}",
        "",
        f"{len(findings)} findings ({', '.join(f'{counts.get(k, 0)} {k}' for k in IMPACT_ORDER)}).",
        "",
        "| Impact | Rule | Element | Viewports | How to fix |",
        "|---|---|---|---|---|",
    ]
    for f in findings:
        rule = md_text(f.rule)
        link = (
            f"[{rule}](<{f.help_url}>)" if re.fullmatch(r"https://[^\s<>]+", f.help_url) else rule
        )
        lines.append(
            f"| {md_text(f.impact)} | {link} | {md_code(f.selector)} | "
            f"{', '.join(md_text(v) for v in f.viewports)} | {md_text(f.fix)} |"
        )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
