#!/usr/bin/env python3
"""Create .env (from template) and update .gitignore at the workspace root."""
import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = PLUGIN_ROOT / "templates" / "env.template"


def prepare(workspace: Path) -> dict:
    workspace.mkdir(parents=True, exist_ok=True)
    env_path = workspace / ".env"
    gitignore_path = workspace / ".gitignore"

    created_env = False
    if not env_path.exists():
        env_path.write_text(TEMPLATE.read_text())
        created_env = True

    if gitignore_path.exists():
        existing = gitignore_path.read_text()
        if ".env" not in existing.splitlines():
            updated = existing.rstrip("\n") + "\n.env\n"
            gitignore_path.write_text(updated)
    else:
        gitignore_path.write_text(".env\n")

    return {
        "ok": True,
        "env_path": str(env_path),
        "gitignore_path": str(gitignore_path),
        "env_created": created_env,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "Usage: prepare_local_env.py <workspace-path>"}))
        sys.exit(2)
    workspace = Path(sys.argv[1]).resolve()
    try:
        result = prepare(workspace)
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
