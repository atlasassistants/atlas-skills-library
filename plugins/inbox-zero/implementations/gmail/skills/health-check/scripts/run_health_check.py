"""
Run Atlas Health Check
======================
Standalone entry point for ``health_check.run_checks()``. Prints a
human-readable drift report to stdout (or JSON with ``--json``). Exits:

    0 — no error-severity findings (warnings ok)
    1 — at least one error-severity finding
    2 — the --profile directory does not exist

Usage:
    python run_health_check.py [--profile PATH] [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parents[2]
_SHARED_SCRIPTS = _PLUGIN_ROOT / "shared" / "scripts"
_DEFAULT_PROFILE = _PLUGIN_ROOT / "client-profile"

if str(_SHARED_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SHARED_SCRIPTS))

from health_check import HealthReport, run_checks  # noqa: E402


def render_text(report: HealthReport) -> str:
    n_find = len(report.findings)
    n_err = sum(1 for f in report.findings if f.severity == "error")
    header = f"Health check: {n_find} findings, {n_err} errors"
    if report.errored_checks:
        header += f", {len(report.errored_checks)} checks errored"
    lines = [header]
    for f in report.findings:
        lines.append(f"  {f.severity.upper()} {f.check} - {f.detail}")
        if f.file:
            lines.append(f"    file: {f.file}")
    for name in report.errored_checks:
        lines.append(f"  CHECK-ERRORED {name}")
    return "\n".join(lines)


def render_json(report: HealthReport) -> str:
    return json.dumps(
        {
            "findings": [asdict(f) for f in report.findings],
            "errored_checks": list(report.errored_checks),
        },
        indent=2,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Atlas client-profile health check")
    parser.add_argument(
        "--profile",
        type=Path,
        default=_DEFAULT_PROFILE,
        help="Path to client-profile directory (default: %(default)s).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable text.",
    )
    args = parser.parse_args()

    if not args.profile.exists() or not args.profile.is_dir():
        print(f"client-profile directory not found: {args.profile}", file=sys.stderr)
        return 2

    report = run_checks(args.profile)

    print(render_json(report) if args.json else render_text(report))

    return 1 if any(f.severity == "error" for f in report.findings) else 0


if __name__ == "__main__":
    sys.exit(main())
