"""Bootstrap the Python runtime for Atlas Inbox Zero.

This script exists because many agent-hosted Linux environments do not ship
with a ready-to-use Python packaging toolchain. It checks whether the Gmail
dependencies are importable and can install them into a plugin-local
``.python-packages/`` directory.

Typical usage:

    python shared/scripts/bootstrap_runtime.py
    python shared/scripts/bootstrap_runtime.py --install
    python shared/scripts/bootstrap_runtime.py --install --bootstrap-pip
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from runtime_paths import LOCAL_PACKAGES_DIR, PLUGIN_ROOT, ensure_runtime_paths


REQUIRED_MODULES: dict[str, str] = {
    "google.auth": "google-auth",
    "google_auth_oauthlib": "google-auth-oauthlib",
    "googleapiclient": "google-api-python-client",
    "requests": "requests",
}


def _module_missing(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return False
    except Exception:
        return True


def get_missing_modules() -> dict[str, str]:
    ensure_runtime_paths()
    missing: dict[str, str] = {}
    for module_name, package_name in REQUIRED_MODULES.items():
        if _module_missing(module_name):
            missing[module_name] = package_name
    return missing


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(PLUGIN_ROOT))


def pip_available() -> bool:
    result = _run([sys.executable, "-m", "pip", "--version"])
    return result.returncode == 0


def ensure_pip(bootstrap_pip: bool = False) -> tuple[bool, list[str]]:
    notes: list[str] = []
    if pip_available():
        return True, notes

    ensurepip_result = _run([sys.executable, "-m", "ensurepip", "--upgrade"])
    if ensurepip_result.returncode == 0 and pip_available():
        notes.append("Bootstrapped pip with ensurepip.")
        return True, notes

    notes.append("ensurepip was unavailable on this host.")
    if not bootstrap_pip:
        return False, notes

    with tempfile.TemporaryDirectory() as tmpdir:
        bootstrap_path = Path(tmpdir) / "get-pip.py"
        urllib.request.urlretrieve("https://bootstrap.pypa.io/get-pip.py", bootstrap_path)
        get_pip_result = _run([
            sys.executable,
            str(bootstrap_path),
            "--user",
            "--break-system-packages",
        ])
        if get_pip_result.returncode == 0 and pip_available():
            notes.append("Bootstrapped pip with get-pip.py.")
            return True, notes
        stderr = (get_pip_result.stderr or get_pip_result.stdout or "").strip()
        notes.append(f"get-pip bootstrap failed: {stderr[:300]}")
        return False, notes


def install_requirements() -> subprocess.CompletedProcess:
    LOCAL_PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
    requirements_path = PLUGIN_ROOT / "requirements.txt"
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--target",
        str(LOCAL_PACKAGES_DIR),
        "-r",
        str(requirements_path),
    ]
    return _run(cmd)


def build_status(install: bool = False, bootstrap_pip: bool = False) -> dict:
    ensure_runtime_paths()
    initial_missing = get_missing_modules()
    notes: list[str] = []
    pip_ready = pip_available()
    install_result: dict[str, str | int] | None = None

    if install and initial_missing:
        pip_ready, pip_notes = ensure_pip(bootstrap_pip=bootstrap_pip)
        notes.extend(pip_notes)
        if pip_ready:
            result = install_requirements()
            install_result = {
                "returncode": result.returncode,
                "stdout": (result.stdout or "")[-1200:],
                "stderr": (result.stderr or "")[-1200:],
            }
            if result.returncode == 0:
                notes.append("Installed Python dependencies into .python-packages/.")
            else:
                notes.append("Dependency installation failed.")

    ensure_runtime_paths()
    final_missing = get_missing_modules()
    ready = not final_missing

    return {
        "ready": ready,
        "python": sys.executable,
        "local_packages_dir": str(LOCAL_PACKAGES_DIR),
        "pip_available": pip_ready,
        "missing_modules": final_missing,
        "notes": notes,
        "install_result": install_result,
        "recommended_command": (
            "python shared/scripts/bootstrap_runtime.py --install --bootstrap-pip"
            if final_missing
            else "Runtime ready"
        ),
    }


def render_text(status: dict) -> str:
    lines = []
    lines.append("Atlas Inbox Zero runtime check")
    lines.append(f"Python: {status['python']}")
    lines.append(f"Local packages dir: {status['local_packages_dir']}")
    lines.append(f"pip available: {'yes' if status['pip_available'] else 'no'}")
    if status["ready"]:
        lines.append("Status: ready")
    else:
        lines.append("Status: missing dependencies")
        for module_name, package_name in status["missing_modules"].items():
            lines.append(f"  - {module_name} (install package: {package_name})")
        lines.append(f"Recommended command: {status['recommended_command']}")
    for note in status["notes"]:
        lines.append(f"Note: {note}")
    install_result = status.get("install_result")
    if install_result and install_result.get("returncode"):
        stderr = (install_result.get("stderr") or install_result.get("stdout") or "").strip()
        if stderr:
            lines.append(f"Last installer output: {stderr[:500]}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap Atlas Inbox Zero Python runtime")
    parser.add_argument("--install", action="store_true", help="Install missing dependencies into .python-packages")
    parser.add_argument(
        "--bootstrap-pip",
        action="store_true",
        help="Attempt to bootstrap pip first if the host Python does not provide it",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    status = build_status(install=args.install, bootstrap_pip=args.bootstrap_pip)
    if args.json:
        print(json.dumps(status, indent=2))
    else:
        print(render_text(status))
    return 0 if status["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
