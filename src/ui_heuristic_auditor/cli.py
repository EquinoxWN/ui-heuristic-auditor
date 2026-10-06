"""ui-audit URL --out DIR: capture, audit and report; exits 1 when findings reach --fail-on."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from ui_heuristic_auditor.capture import Auditor, CaptureError
from ui_heuristic_auditor.findings import IMPACT_ORDER, at_least, merge
from ui_heuristic_auditor.report import write_report
from ui_heuristic_auditor.viewports import VIEWPORTS


def main(argv: list[str] | None = None) -> int:
    """Run the command line; 0 clean, 1 findings at or above --fail-on, 2 errors."""
    parser = argparse.ArgumentParser(prog="ui-audit", description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--viewports", default="mobile,desktop", help="comma-separated: mobile, desktop"
    )
    parser.add_argument("--fail-on", choices=list(IMPACT_ORDER), default=None)
    parser.add_argument("--timeout", type=int, default=30, help="seconds per page load")
    parser.add_argument(
        "--cache", type=Path, default=Path(os.environ.get("UI_AUDIT_CACHE", ".tmp/cache"))
    )
    args = parser.parse_args(argv)
    try:
        viewports = [VIEWPORTS[name] for name in args.viewports.split(",")]
    except KeyError as e:
        print(f"error: unknown viewport {e}", file=sys.stderr)
        return 2
    try:
        with Auditor(args.cache, timeout_ms=args.timeout * 1000) as auditor:
            capture = auditor.capture(args.url, args.out, viewports)
    except CaptureError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    findings = merge(capture)
    report = write_report(capture, findings, args.out)
    print(f"{len(findings)} findings; report: {report}")
    for f in findings:
        print(f"  [{f.impact}] {f.rule} at {f.selector} ({', '.join(f.viewports)})")
    if args.fail_on and at_least(findings, args.fail_on):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
