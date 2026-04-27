#!/usr/bin/env python3
"""Register the recurring scan-ideal-week schedule with the local OS scheduler.

NOTE — this is the LOCAL FALLBACK option. Local OS scheduling only fires when
the device is on, so a closed laptop at 5pm means a missed evening scan.
For reliable unattended scheduling, prefer your runtime's native recurring-task
feature: Cowork Scheduled tasks, Claude Code `/schedule`, an SDK-driven
scheduled agent, GitHub Actions cron, etc. See the plugin's README §4 for the
recommended approach. Use this script only if no runtime-native option is
available on your setup.

Usage:
  setup_schedule.py --invoke-cmd "<full command to run scan-ideal-week>"
                    [--cron-spec "0 17 * * 1-5;0 7 * * 1-5"]
                    [--dry-run]

Multiple cron specs are separated by SEMICOLONS (not commas), because cron
specs themselves use commas inside fields (e.g. dow="0,6" for weekends).

By default, registers two weekday entries (Mon-Fri only):
  - 5:00 PM local time — scan tomorrow
  - 7:00 AM local time — scan today

Skips Saturday and Sunday by default. Override with --cron-spec for different cadences.

Detects the platform:
  - Linux / macOS — appends entries to the user's crontab
  - Windows       — creates Task Scheduler tasks via schtasks.exe
  - Other         — prints manual instructions

Idempotent: re-running with the same --invoke-cmd is a no-op.
"""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from typing import Iterable

# Force UTF-8 on stdout/stderr so em-dashes render on Windows (cp1252 default).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

DEFAULT_CRON_SPECS = ["0 17 * * 1-5", "0 7 * * 1-5"]
TASK_NAME_PREFIX = "ideal-week-scan"


def register_cron(invoke_cmd: str, specs: Iterable[str], dry_run: bool) -> int:
    """Append cron entries on Linux/macOS. Detects existing entries to stay idempotent."""
    marker = f"# ideal-week-ops: {invoke_cmd}"
    new_lines = [marker] + [f"{spec} {invoke_cmd}" for spec in specs]

    try:
        existing = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=10)
        current = existing.stdout if existing.returncode == 0 else ""
    except (subprocess.SubprocessError, FileNotFoundError):
        sys.stderr.write("crontab command not available\n")
        return 2

    if marker in current:
        print(f"Schedule already registered: {invoke_cmd}")
        return 0

    combined = current.rstrip("\n") + "\n" + "\n".join(new_lines) + "\n"
    if dry_run:
        print("--- DRY RUN — would write the following crontab ---")
        print(combined)
        return 0

    proc = subprocess.run(["crontab", "-"], input=combined, text=True, capture_output=True, timeout=10)
    if proc.returncode != 0:
        sys.stderr.write(f"crontab write failed: {proc.stderr}\n")
        return 3
    print(f"Registered {len(list(specs)) if not isinstance(specs, list) else len(specs)} cron entries.")
    return 0


def register_windows_tasks(invoke_cmd: str, specs: Iterable[str], dry_run: bool) -> int:
    """Register Task Scheduler tasks on Windows. One task per cron spec.

    Supports daily-at-fixed-time and weekday-at-fixed-time cron specs:
      '0 17 * * *'   → daily at 17:00
      '0 17 * * 1-5' → weekly Mon-Fri at 17:00
    More complex specs (specific dates, hour ranges) require manual setup.
    """
    specs_list = list(specs)
    registered = 0
    for i, spec in enumerate(specs_list):
        schedule_args = _cron_to_schtasks_args(spec)
        if schedule_args is None:
            sys.stderr.write(f"Cannot convert cron spec '{spec}' to a Windows scheduled task. Skipping.\n")
            continue
        task_name = f"{TASK_NAME_PREFIX}-{i + 1}"
        cmd = [
            "schtasks", "/Create",
            "/TN", task_name,
            "/TR", invoke_cmd,
            *schedule_args,
            "/F",   # force overwrite if task exists — keeps the call idempotent
        ]
        if dry_run:
            print("--- DRY RUN — would run ---")
            print(" ".join(cmd))
            continue
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            sys.stderr.write(f"schtasks failed for {task_name}: {result.stderr}\n")
            continue
        registered += 1
        print(f"Registered Windows task: {task_name} (cron: {spec})")

    if registered == 0 and not dry_run:
        return 4
    return 0


def _cron_to_schtasks_args(spec: str) -> list[str] | None:
    """Convert a cron spec into schtasks /SC ... /ST ... args. Returns None if unsupported.

    Supported shapes:
      '<m> <h> * * *'       → /SC DAILY /ST HH:MM
      '<m> <h> * * 1-5'     → /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST HH:MM
      '<m> <h> * * 0,6'     → /SC WEEKLY /D SUN,SAT /ST HH:MM
    """
    parts = spec.split()
    if len(parts) != 5:
        return None
    minute, hour, dom, mon, dow = parts
    if dom != "*" or mon != "*":
        return None
    try:
        h = int(hour)
        m = int(minute)
        if not (0 <= h <= 23 and 0 <= m <= 59):
            return None
    except ValueError:
        return None
    time = f"{h:02d}:{m:02d}"

    if dow == "*":
        return ["/SC", "DAILY", "/ST", time]

    days = _parse_dow(dow)
    if days is None:
        return None
    return ["/SC", "WEEKLY", "/D", ",".join(days), "/ST", time]


def _parse_dow(dow: str) -> list[str] | None:
    """Parse a cron day-of-week field into Windows day codes (SUN..SAT).

    Cron: 0 or 7 = Sunday, 1 = Monday, ..., 6 = Saturday.
    Supports comma-separated values and simple a-b ranges.
    """
    code = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
    out: list[str] = []
    for part in dow.split(","):
        part = part.strip()
        if "-" in part:
            try:
                start, end = (int(x) for x in part.split("-", 1))
            except ValueError:
                return None
            if not (0 <= start <= 7 and 0 <= end <= 7) or start > end:
                return None
            for i in range(start, end + 1):
                idx = i % 7
                if code[idx] not in out:
                    out.append(code[idx])
        else:
            try:
                i = int(part)
            except ValueError:
                return None
            if not (0 <= i <= 7):
                return None
            idx = i % 7
            if code[idx] not in out:
                out.append(code[idx])
    return out or None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--invoke-cmd", required=True,
                        help="full command to invoke scan-ideal-week (use absolute paths)")
    parser.add_argument("--cron-spec", default=";".join(DEFAULT_CRON_SPECS),
                        help="semicolon-separated cron specs; default: 5pm + 7am weekdays only")
    parser.add_argument("--dry-run", action="store_true",
                        help="print what would be registered without modifying the system")
    args = parser.parse_args()

    specs = [s.strip() for s in args.cron_spec.split(";") if s.strip()]

    system = platform.system()
    if system in ("Linux", "Darwin"):
        return register_cron(args.invoke_cmd, specs, args.dry_run)
    if system == "Windows":
        return register_windows_tasks(args.invoke_cmd, specs, args.dry_run)

    sys.stderr.write(f"Unsupported platform: {system}\n")
    sys.stderr.write("Manual setup: register a recurring task that runs the following command:\n")
    sys.stderr.write(f"  {args.invoke_cmd}\n")
    sys.stderr.write(f"At these times (cron syntax): {args.cron_spec}\n")
    return 5


if __name__ == "__main__":
    sys.exit(main())
