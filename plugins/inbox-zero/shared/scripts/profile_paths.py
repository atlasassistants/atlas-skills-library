"""Client-profile runtime/template path helpers for Atlas Inbox Zero."""

from __future__ import annotations

import shutil
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent
CLIENT_PROFILE_DIR = PLUGIN_ROOT / "client-profile"
CLIENT_PROFILE_TEMPLATES_DIR = CLIENT_PROFILE_DIR / "templates"

PROFILE_TEMPLATE_MAP = {
    "exec-preferences.md": "exec-preferences.template.md",
    "exec-voice-guide.md": "exec-voice-guide.template.md",
    "label-sweep-rules.md": "label-sweep-rules.template.md",
    "team-delegation-map.md": "team-delegation-map.template.md",
    "vip-contacts.md": "vip-contacts.template.md",
    "sweep-schedule.json": "sweep-schedule.template.json",
}


def runtime_profile_path(
    name: str,
    *,
    client_profile_dir: Path = CLIENT_PROFILE_DIR,
) -> Path:
    return Path(client_profile_dir) / name


def template_profile_path(
    name: str,
    *,
    client_profile_dir: Path = CLIENT_PROFILE_DIR,
    templates_dir: Path | None = None,
) -> Path:
    template_name = PROFILE_TEMPLATE_MAP.get(name)
    if not template_name:
        return runtime_profile_path(name, client_profile_dir=client_profile_dir)
    base = Path(templates_dir) if templates_dir else (Path(client_profile_dir) / "templates")
    return base / template_name


def profile_read_path(
    name: str,
    *,
    client_profile_dir: Path = CLIENT_PROFILE_DIR,
    templates_dir: Path | None = None,
) -> Path:
    runtime_path = runtime_profile_path(name, client_profile_dir=client_profile_dir)
    if runtime_path.exists():
        return runtime_path
    template_path = template_profile_path(
        name,
        client_profile_dir=client_profile_dir,
        templates_dir=templates_dir,
    )
    return template_path if template_path.exists() else runtime_path


def ensure_runtime_profile_path(
    name: str,
    *,
    client_profile_dir: Path = CLIENT_PROFILE_DIR,
    templates_dir: Path | None = None,
) -> Path:
    runtime_path = runtime_profile_path(name, client_profile_dir=client_profile_dir)
    if runtime_path.exists():
        return runtime_path

    template_path = template_profile_path(
        name,
        client_profile_dir=client_profile_dir,
        templates_dir=templates_dir,
    )
    if template_path.exists():
        runtime_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(template_path, runtime_path)
    return runtime_path


def bootstrap_runtime_profiles(
    *,
    client_profile_dir: Path = CLIENT_PROFILE_DIR,
    templates_dir: Path | None = None,
    force: bool = False,
    dry_run: bool = False,
    names: list[str] | None = None,
) -> dict[str, list[str]]:
    """Copy tracked templates into missing runtime files.

    By default, only missing runtime files are created. When ``force`` is
    true, existing runtime files are overwritten from templates.
    """
    selected_names = names or list(PROFILE_TEMPLATE_MAP.keys())
    result: dict[str, list[str]] = {
        "created": [],
        "overwritten": [],
        "skipped": [],
        "missing_templates": [],
    }

    for name in selected_names:
        runtime_path = runtime_profile_path(name, client_profile_dir=client_profile_dir)
        existed_before = runtime_path.exists()
        template_path = template_profile_path(
            name,
            client_profile_dir=client_profile_dir,
            templates_dir=templates_dir,
        )

        if not template_path.exists():
            result["missing_templates"].append(name)
            continue

        if runtime_path.exists() and not force:
            result["skipped"].append(name)
            continue

        if not dry_run:
            runtime_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(template_path, runtime_path)

        if existed_before and force:
            result["overwritten"].append(name)
        else:
            result["created"].append(name)

    return result
