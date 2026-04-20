from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

_IMPL_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
_SHARED_SCRIPTS = Path(__file__).resolve().parents[5] / "shared" / "scripts"
for _p in (_IMPL_SCRIPTS, _SHARED_SCRIPTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import configure_schedule


RUN_MODES = ("morning", "midday", "eod")
MODE_PROMPTS = {
    "morning": "Morning sweep time",
    "midday": "Midday check time",
    "eod": "End-of-day sweep time",
}


def _is_unconfigured_schedule(config: dict[str, Any]) -> bool:
    scheduler = config.get("scheduler", {})
    runs = config.get("runs", {})
    return (
        not config.get("timezone")
        and scheduler.get("backend", "none") == "none"
        and not scheduler.get("updatedAt")
        and not scheduler.get("managedJobs")
        and not any(bool(runs.get(mode, {}).get("enabled")) for mode in RUN_MODES)
    )


def prompt_defaults(config: dict[str, Any]) -> dict[str, str]:
    defaults: dict[str, str] = {
        "timezone": config.get("timezone") or "",
    }
    if _is_unconfigured_schedule(config):
        defaults["morning"] = configure_schedule.DEFAULT_TIMES["morning"]
        defaults["midday"] = "off"
        defaults["eod"] = configure_schedule.DEFAULT_TIMES["eod"]
        return defaults

    for mode in RUN_MODES:
        run_cfg = config["runs"][mode]
        defaults[mode] = run_cfg["time"] if run_cfg.get("enabled") else "off"
    return defaults


def apply_schedule_answers(
    config: dict[str, Any],
    *,
    timezone_name: str | None,
    morning: str | None,
    midday: str | None,
    eod: str | None,
) -> dict[str, Any]:
    args = SimpleNamespace(
        tz=timezone_name,
        morning=morning,
        midday=midday,
        eod=eod,
    )
    return configure_schedule.apply_updates(config, args)


def _prompt(text: str, *, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    try:
        value = input(f"{text}{suffix}: ").strip()
    except EOFError:
        value = ""
    return value or (default or "")


def _yes_no(text: str, *, default: bool = True) -> bool:
    default_token = "Y/n" if default else "y/N"
    try:
        value = input(f"{text} [{default_token}]: ").strip().lower()
    except EOFError:
        value = ""
    if not value:
        return default
    return value in {"y", "yes"}


def interactive_answers(config: dict[str, Any]) -> tuple[dict[str, str], bool]:
    defaults = prompt_defaults(config)

    print("Atlas Inbox Zero — Schedule Setup")
    print("=" * 40)
    print("Answer one thing at a time. Use HH:MM in 24-hour time, or type 'off'.")
    print()

    enabled_now = _yes_no("Do you want scheduled sweeps turned on now?", default=True)
    if not enabled_now:
        return {
            "timezone": defaults["timezone"] or None,
            "morning": "off",
            "midday": "off",
            "eod": "off",
        }, False

    timezone_name = _prompt("Timezone (IANA, for example America/New_York)", default=defaults["timezone"] or None)

    answers = {
        "timezone": timezone_name,
        "morning": _prompt(MODE_PROMPTS["morning"], default=defaults["morning"]),
        "midday": _prompt(MODE_PROMPTS["midday"], default=defaults["midday"]),
        "eod": _prompt(MODE_PROMPTS["eod"], default=defaults["eod"]),
    }

    install_scheduler = False
    if shutil.which(configure_schedule.SCHEDULER_CMD):
        install_scheduler = _yes_no("Install or update Claude cron jobs now?", default=True)

    return answers, install_scheduler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture Atlas Inbox Zero schedule choices during onboarding.")
    parser.add_argument("--tz", help="IANA timezone, for example America/New_York.")
    parser.add_argument("--morning", help="HH:MM to enable morning, or 'off'.")
    parser.add_argument("--midday", help="HH:MM to enable midday, or 'off'.")
    parser.add_argument("--eod", help="HH:MM to enable end-of-day, or 'off'.")
    parser.add_argument("--install-scheduler", action="store_true", help="Install or update Claude cron jobs after saving the schedule.")
    parser.add_argument("--dry-run", action="store_true", help="Preview the result without writing files or creating jobs.")
    parser.add_argument("--interactive", action="store_true", help="Ask the schedule questions interactively.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = configure_schedule.load_config()

    interactive = args.interactive or not any(
        getattr(args, name) is not None for name in ("tz", "morning", "midday", "eod")
    )

    if interactive:
        answers, install_scheduler = interactive_answers(config)
    else:
        answers = {
            "timezone": args.tz,
            "morning": args.morning,
            "midday": args.midday,
            "eod": args.eod,
        }
        install_scheduler = args.install_scheduler

    try:
        updated = apply_schedule_answers(
            config,
            timezone_name=answers["timezone"],
            morning=answers["morning"],
            midday=answers["midday"],
            eod=answers["eod"],
        )
        summaries: list[str] = []
        if install_scheduler:
            summaries = configure_schedule.install_scheduler_jobs(updated, dry_run=args.dry_run)
        if not args.dry_run:
            configure_schedule.save_config(updated)
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if summaries:
        for line in summaries:
            print(line)
    configure_schedule.print_text_summary(updated)
    if not any(updated["runs"][mode]["enabled"] for mode in RUN_MODES):
        print("Scheduled sweeps are currently off.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
