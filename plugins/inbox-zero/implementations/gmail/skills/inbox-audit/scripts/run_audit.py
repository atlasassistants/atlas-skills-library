"""
Run Inbox Audit
===============
Entry point for inbox-audit. Checks for credentials, runs setup if
missing, then runs all four scans and saves results to client-profile/.

The agent reads the JSON output to produce the audit report and
label plan before onboarding begins.

Output files:
    client-profile/inbox-audit.json   — raw scan data for scripts to read
    (agent writes client-profile/inbox-audit.md from this data)

Usage:
    python run_audit.py
    python run_audit.py --days 180 --max-inbox 500
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_IMPL_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
_SHARED_SCRIPTS = Path(__file__).resolve().parents[5] / "shared" / "scripts"
for _p in (_IMPL_SCRIPTS, _SHARED_SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from profile_paths import CLIENT_PROFILE_DIR

CREDENTIALS_PATH = CLIENT_PROFILE_DIR / "credentials" / "credentials.json"
TOKEN_PATH = CLIENT_PROFILE_DIR / "credentials" / "token.json"
AUDIT_OUTPUT = CLIENT_PROFILE_DIR / "inbox-audit.json"

SCRIPTS_DIR = Path(__file__).resolve().parent
SETUP_CREDENTIALS = _IMPL_SCRIPTS / "setup_credentials.py"


def credentials_ready() -> bool:
    return CREDENTIALS_PATH.exists() and TOKEN_PATH.exists()


def run_setup() -> int:
    print("No credentials found. Running Gmail setup first...\n")
    result = subprocess.run(
        [sys.executable, str(SETUP_CREDENTIALS)],
        check=False,
    )
    return result.returncode


def run_scan(script: str, extra_args: list[str] | None = None) -> dict | None:
    cmd = [sys.executable, str(SCRIPTS_DIR / script)] + (extra_args or [])
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"  [WARN] {script} failed: {result.stderr.strip()}", file=sys.stderr)
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  [WARN] {script} returned invalid JSON", file=sys.stderr)
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run inbox audit — credentials check + all scans.")
    parser.add_argument("--days", type=int, default=90, help="Lookback window for sent analysis.")
    parser.add_argument("--max-inbox", type=int, default=400, help="Max inbox messages to scan.")
    args = parser.parse_args(argv)

    # Step 1 — ensure credentials
    if not credentials_ready():
        rc = run_setup()
        if rc != 0:
            print("ERROR: Credential setup failed. Cannot run audit.", file=sys.stderr)
            return 1
    else:
        print("Credentials found. Skipping setup.\n")

    # Step 2 — run all scans
    print("Running inbox audit...\n")

    results = {}

    print("  Scanning labels...")
    results["labels"] = run_scan("scan_labels.py", ["--days", str(args.days)])

    print("  Scanning filters...")
    results["filters"] = run_scan("scan_filters.py")

    print("  Scanning sent folder...")
    results["sent"] = run_scan("scan_sent.py", ["--days", str(args.days)])

    print("  Scanning inbox...")
    results["inbox"] = run_scan("scan_inbox.py", ["--max", str(args.max_inbox)])

    failed = [k for k, v in results.items() if v is None]
    if failed:
        print(f"\n[WARN] Some scans failed: {failed}. Partial audit saved.", file=sys.stderr)

    # Step 3 — save raw output
    AUDIT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_OUTPUT.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"\nAudit data saved to: {AUDIT_OUTPUT}")
    print("Ready for agent to produce audit report and label plan.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
