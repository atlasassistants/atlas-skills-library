"""LinkedIn research skill — CLI entry point.

Subcommands:
  setup [--reauth-only] [--stage X] [--chrome-path X] [--output-dir X]
                            Run interactive onboarding wizard (multi-stage)
  scrape NAME [--company X] Scrape a person's LinkedIn profile
  verify                    Health check: config + Chrome + LinkedIn session

Exit codes:
  0   Success or no-match (clean termination)
  1   Generic error
  10  No config (needs setup)
  11  Chrome path not found / not provided
  12  Chrome failed to launch
  13  CDP attach failed
  20  LinkedIn signed out (needs reauth)
  30  LinkedIn rate-limited (auto-stop triggered)
  31  Daily cap exceeded
  4   Network timeout
"""

import argparse
import os
import sys

# Silence Node.js deprecation warnings (Playwright's driver subprocess emits them
# to stderr and they interleave with our JSON output). Set BEFORE importing
# playwright — the env var is read when the driver subprocess starts.
os.environ.setdefault("NODE_NO_WARNINGS", "1")

from cmd_setup import cmd_setup
from cmd_scrape import cmd_scrape
from cmd_verify import cmd_verify


def main():
    # Force UTF-8 stdout/stderr on Windows so emoji and non-Latin chars print correctly
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    parser = argparse.ArgumentParser(prog="linkedin_scraper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_setup = sub.add_parser("setup", help="Interactive onboarding wizard")
    p_setup.add_argument("--reauth-only", action="store_true",
                         help="Just re-verify LinkedIn login; don't reconfigure paths")
    p_setup.add_argument("--stage",
                         choices=["detect", "save-paths", "launch-for-login", "verify-login"],
                         default=None,
                         help="(used by skill) which stage of the onboarding to run")
    p_setup.add_argument("--chrome-path", default=None,
                         help="Override auto-detected Chrome path")
    p_setup.add_argument("--output-dir", default=None,
                         help="Override output directory")
    p_setup.add_argument("--non-interactive", action="store_true",
                         help="Don't prompt; use saved config or fail")

    p_scrape = sub.add_parser("scrape", help="Scrape a LinkedIn profile")
    p_scrape.add_argument("name", help="Person's name to search")
    p_scrape.add_argument("--company", default=None, help="Company hint for disambiguation")

    p_verify = sub.add_parser("verify", help="Health check (config + Chrome + LinkedIn)")

    args = parser.parse_args()
    if args.cmd == "setup":
        sys.exit(cmd_setup(args))
    elif args.cmd == "scrape":
        sys.exit(cmd_scrape(args))
    elif args.cmd == "verify":
        sys.exit(cmd_verify(args))


if __name__ == "__main__":
    main()
