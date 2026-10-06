"""The real command line, run as a subprocess: report files, summary and exit codes."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def ui_audit(*args: str) -> subprocess.CompletedProcess[str]:
    """Run `python -m ui_heuristic_auditor.cli` with the given arguments."""
    return subprocess.run(  # noqa: S603 (fixed interpreter, test-controlled arguments)
        [sys.executable, "-m", "ui_heuristic_auditor.cli", *args],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_report_and_summary_are_written(site: str, tmp_path: Path) -> None:
    r = ui_audit(f"{site}/responsive.html", "--out", str(tmp_path))
    assert r.returncode == 0, r.stderr
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["schema"] == 1
    assert [v["name"] for v in report["viewports"]] == ["mobile", "desktop"]
    assert len(report["findings"]) == 2
    assert sum(report["counts"].values()) == 2
    summary = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "| Impact | Rule | Element | Viewports | How to fix |" in summary
    assert "2 findings" in r.stdout


def test_fail_on_turns_findings_into_a_failing_exit_code(site: str, tmp_path: Path) -> None:
    assert (
        ui_audit(
            f"{site}/seeded.html", "--out", str(tmp_path / "a"), "--fail-on", "serious"
        ).returncode
        == 1
    )
    assert (
        ui_audit(
            f"{site}/clean.html", "--out", str(tmp_path / "b"), "--fail-on", "minor"
        ).returncode
        == 0
    )


def test_bad_input_exits_with_two(tmp_path: Path) -> None:
    r = ui_audit("file:///etc/passwd", "--out", str(tmp_path))
    assert r.returncode == 2
    assert "only http(s) URLs" in r.stderr
    assert (
        ui_audit("http://127.0.0.1:9/", "--out", str(tmp_path), "--viewports", "watch").returncode
        == 2
    )
