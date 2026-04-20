from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from profile_paths import CLIENT_PROFILE_DIR, PLUGIN_ROOT


CLIENT_PROFILE = CLIENT_PROFILE_DIR
CONFIG_PATH = CLIENT_PROFILE / "sweep-schedule.json"
LOG_DIR = PLUGIN_ROOT / "logs" / "scheduled-runs"
RUN_MODES = ("morning", "midday", "eod")
MODE_LABELS = {
    "morning": "Morning",
    "midday": "Midday",
    "eod": "EOD",
}
DEFAULT_TIMES = {
    "morning": "08:00",
    "midday": "12:30",
    "eod": "16:00",
}

SCHEDULER_CMD = "claude"


def default_config() -> dict[str, Any]:
    return {
        "version": 1,
        "timezone": None,
        "days": "weekdays",
        "scheduler": {
            "backend": "none",
            "updatedAt": None,
            "managedJobs": {},
        },
        "runs": {
            mode: {
                "enabled": False,
                "time": DEFAULT_TIMES[mode],
            }
            for mode in RUN_MODES
        },
    }


def _merge_defaults(current: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(default_config())
    if not isinstance(current, dict):
        return merged

    for key in ("version", "timezone", "days"):
        if key in current:
            merged[key] = current[key]

    scheduler = current.get("scheduler")
    if isinstance(scheduler, dict):
        merged["scheduler"].update(scheduler)

    runs = current.get("runs")
    if isinstance(runs, dict):
        for mode in RUN_MODES:
            if isinstance(runs.get(mode), dict):
                merged["runs"][mode].update(runs[mode])
    return merged


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    if not path.exists():
        return default_config()
    data = json.loads(path.read_text(encoding="utf-8"))
    return _merge_defaults(data)


def save_config(config: dict[str, Any], path: Path = CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_time(value: str) -> str:
    raw = (value or "").strip()
    parts = raw.split(":")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ValueError(f"Invalid time '{value}'. Use HH:MM in 24-hour format.")
    hour = int(parts[0])
    minute = int(parts[1])
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError(f"Invalid time '{value}'. Use HH:MM in 24-hour format.")
    return f"{hour:02d}:{minute:02d}"


def parse_schedule_value(value: str | None) -> dict[str, Any] | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"off", "disable", "disabled", "none"}:
        return {"enabled": False}
    return {"enabled": True, "time": normalize_time(value)}


def cron_expr_for_time(time_value: str, days: str = "weekdays") -> str:
    normalized = normalize_time(time_value)
    hour, minute = normalized.split(":")
    if days != "weekdays":
        raise ValueError(f"Unsupported day set '{days}'. Only 'weekdays' is supported right now.")
    return f"{int(minute)} {int(hour)} * * 1-5"


def managed_job_name(mode: str, plugin_root: Path = PLUGIN_ROOT) -> str:
    if mode not in RUN_MODES:
        raise ValueError(f"Unsupported mode '{mode}'.")
    digest = hashlib.sha1(str(plugin_root.resolve()).encode("utf-8")).hexdigest()[:8]
    return f"Atlas Inbox Zero [{digest}] {MODE_LABELS[mode]} Sweep"


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def _parse_jobs_payload(payload: str) -> list[dict[str, Any]]:
    data = json.loads(payload or "{}")
    jobs = data.get("jobs", [])
    return jobs if isinstance(jobs, list) else []


def list_scheduler_jobs() -> list[dict[str, Any]]:
    result = run_command([SCHEDULER_CMD, "cron", "list", "--all", "--json"])
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Unable to list scheduler cron jobs: {stderr}")
    return _parse_jobs_payload(result.stdout)


def _existing_jobs_by_name() -> dict[str, dict[str, Any]]:
    return {
        job.get("name"): job
        for job in list_scheduler_jobs()
        if isinstance(job, dict) and job.get("name")
    }


def build_scheduler_message(mode: str, plugin_root: Path = PLUGIN_ROOT) -> str:
    command = (
        f"cd {shlex.quote(str(plugin_root))} && "
        f"python3 shared/scripts/orchestrator.py --mode {mode}"
    )
    return (
        f"Run `{command}`. If it exits successfully and there is nothing user-facing to send, "
        f"reply NO_REPLY. If it fails, reply with a brief error summary."
    )


def scheduler_job_description(mode: str) -> str:
    return (
        f"Runs the Atlas Inbox Zero {mode} sweep using the plugin-local orchestrator. "
        f"Managed by shared/scripts/configure_schedule.py."
    )


def install_scheduler_jobs(config: dict[str, Any], *, dry_run: bool = False) -> list[str]:
    timezone_name = config.get("timezone")
    if not timezone_name:
        raise ValueError("Set a timezone before installing a scheduler backend.")
    if config.get("days") != "weekdays":
        raise ValueError("Only 'weekdays' schedules are supported right now.")

    existing = _existing_jobs_by_name()
    summaries: list[str] = []
    managed_jobs: dict[str, str] = {}

    for mode in RUN_MODES:
        run_cfg = config["runs"][mode]
        name = managed_job_name(mode)
        job = existing.get(name)
        enabled = bool(run_cfg.get("enabled"))
        if not enabled:
            if job:
                command = [SCHEDULER_CMD, "cron", "remove", job["id"]]
                summaries.append(_execute_or_describe(command, dry_run, f"remove {name}"))
            continue

        expr = cron_expr_for_time(run_cfg["time"], config.get("days", "weekdays"))
        base_command = [
            SCHEDULER_CMD, "cron",
            "edit" if job else "add",
        ]
        if job:
            base_command.append(job["id"])
        base_command.extend(
            [
                "--name", name,
                "--description", scheduler_job_description(mode),
                "--cron", expr,
                "--tz", timezone_name,
                "--session", "isolated",
                "--message", build_scheduler_message(mode),
                "--timeout-seconds", "900",
                "--tools", "exec",
            ]
        )
        summaries.append(_execute_or_describe(base_command, dry_run, f"upsert {name}"))
        if job:
            managed_jobs[mode] = job["id"]

    if not dry_run:
        refreshed = _existing_jobs_by_name()
        for mode in RUN_MODES:
            run_cfg = config["runs"][mode]
            if not run_cfg.get("enabled"):
                continue
            job = refreshed.get(managed_job_name(mode))
            if job:
                managed_jobs[mode] = job["id"]

    config["scheduler"] = {
        "backend": "claude-cron" if any(config["runs"][mode]["enabled"] for mode in RUN_MODES) else "none",
        "updatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "managedJobs": managed_jobs,
    }
    return summaries


def remove_scheduler_jobs(config: dict[str, Any], *, dry_run: bool = False) -> list[str]:
    existing = _existing_jobs_by_name()
    summaries: list[str] = []
    for mode in RUN_MODES:
        name = managed_job_name(mode)
        job = existing.get(name)
        if not job:
            continue
        command = [SCHEDULER_CMD, "cron", "remove", job["id"]]
        summaries.append(_execute_or_describe(command, dry_run, f"remove {name}"))

    config["scheduler"] = {
        "backend": "none",
        "updatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "managedJobs": {},
    }
    return summaries


def _execute_or_describe(command: list[str], dry_run: bool, label: str) -> str:
    rendered = " ".join(shlex.quote(part) for part in command)
    if dry_run:
        return f"[dry-run] {label}: {rendered}"
    result = run_command(command)
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"{label} failed: {stderr}")
    return f"[ok] {label}"


def render_crontab(config: dict[str, Any], *, python_bin: str = "python3") -> str:
    timezone_name = config.get("timezone")
    if not timezone_name:
        raise ValueError("Set a timezone before rendering crontab lines.")
    lines = [f"CRON_TZ={timezone_name}"]
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    for mode in RUN_MODES:
        run_cfg = config["runs"][mode]
        if not run_cfg.get("enabled"):
            continue
        expr = cron_expr_for_time(run_cfg["time"], config.get("days", "weekdays"))
        log_path = LOG_DIR / f"{mode}.log"
        command = (
            f"cd {shlex.quote(str(PLUGIN_ROOT))} && "
            f"{shlex.quote(python_bin)} shared/scripts/orchestrator.py --mode {mode} "
            f">> {shlex.quote(str(log_path))} 2>&1"
        )
        lines.append(f"{expr} {command}")
    if len(lines) == 1:
        lines.append("# No enabled runs. Use set --morning/--midday/--eod first.")
    return "\n".join(lines)


def apply_updates(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    updated = _merge_defaults(config)
    if getattr(args, "tz", None) is not None:
        updated["timezone"] = args.tz.strip() or None

    for mode in RUN_MODES:
        value = getattr(args, mode, None)
        parsed = parse_schedule_value(value)
        if parsed is None:
            continue
        updated["runs"][mode].update(parsed)
    return updated


def print_text_summary(config: dict[str, Any]) -> None:
    print(f"Config: {CONFIG_PATH}")
    print(f"Timezone: {config.get('timezone') or '(unset)'}")
    print(f"Days: {config.get('days')}")
    print(f"Scheduler backend: {config.get('scheduler', {}).get('backend', 'none')}")
    managed = config.get("scheduler", {}).get("managedJobs", {})
    for mode in RUN_MODES:
        run_cfg = config["runs"][mode]
        status = "enabled" if run_cfg.get("enabled") else "disabled"
        time_value = run_cfg.get("time")
        suffix = f" [{managed[mode]}]" if mode in managed else ""
        print(f"- {mode}: {status} @ {time_value}{suffix}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Configure Atlas Inbox Zero sweep scheduling.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    show_parser = subparsers.add_parser("show", help="Show the current schedule config.")
    show_parser.add_argument("--json", action="store_true", help="Print raw JSON.")

    set_parser = subparsers.add_parser("set", help="Update schedule config and optionally install it.")
    set_parser.add_argument("--tz", help="IANA timezone, for example America/New_York.")
    set_parser.add_argument("--morning", help="HH:MM to enable morning, or 'off'.")
    set_parser.add_argument("--midday", help="HH:MM to enable midday, or 'off'.")
    set_parser.add_argument("--eod", help="HH:MM to enable eod, or 'off'.")
    set_parser.add_argument("--install-scheduler", action="store_true", help="Install/update matching Claude cron jobs.")
    set_parser.add_argument("--dry-run", action="store_true", help="Preview scheduler changes without applying them.")

    install_parser = subparsers.add_parser("install-scheduler", help="Install/update Claude cron jobs from the current config.")
    install_parser.add_argument("--dry-run", action="store_true", help="Preview scheduler changes without applying them.")

    remove_parser = subparsers.add_parser("remove-scheduler", help="Remove managed Claude cron jobs.")
    remove_parser.add_argument("--dry-run", action="store_true", help="Preview scheduler changes without applying them.")

    crontab_parser = subparsers.add_parser("render-crontab", help="Render portable crontab lines for the current config.")
    crontab_parser.add_argument("--python-bin", default="python3", help="Python executable to use in rendered crontab lines.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config()

    try:
        if args.command == "show":
            if args.json:
                print(json.dumps(config, indent=2, sort_keys=True))
            else:
                print_text_summary(config)
            return 0

        if args.command == "set":
            updated = apply_updates(config, args)
            summaries: list[str] = []
            if args.install_scheduler:
                summaries = install_scheduler_jobs(updated, dry_run=args.dry_run)
            if not args.dry_run:
                save_config(updated)
            if summaries:
                for line in summaries:
                    print(line)
            print_text_summary(updated)
            return 0

        if args.command == "install-scheduler":
            summaries = install_scheduler_jobs(config, dry_run=args.dry_run)
            if not args.dry_run:
                save_config(config)
            for line in summaries:
                print(line)
            print_text_summary(config)
            return 0

        if args.command == "remove-scheduler":
            summaries = remove_scheduler_jobs(config, dry_run=args.dry_run)
            if not args.dry_run:
                save_config(config)
            for line in summaries:
                print(line)
            print_text_summary(config)
            return 0

        if args.command == "render-crontab":
            print(render_crontab(config, python_bin=args.python_bin))
            return 0
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
