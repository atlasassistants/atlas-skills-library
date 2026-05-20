#!/usr/bin/env python3
"""Validate the OpenAI API key from a .env file by probing the API.

The probe is a lightweight `models.list()` call — much cheaper than an image generation,
just confirms the key is accepted by OpenAI's auth layer.
"""
import json
import os
import sys
from pathlib import Path
from typing import Optional, Tuple


def _read_api_key(env_path: Path) -> Optional[str]:
    if not env_path.exists():
        return None
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("OPENAI_API_KEY="):
            return line.split("=", 1)[1].strip()
    return None


def _probe_openai(api_key: str) -> Tuple[bool, Optional[str]]:
    try:
        from openai import OpenAI, AuthenticationError, APIError
    except ImportError as exc:
        return False, f"openai SDK not installed: {exc}"
    client = OpenAI(api_key=api_key)
    try:
        client.models.list()
        return True, None
    except AuthenticationError as exc:
        return False, f"OpenAI rejected the key: {exc}"
    except APIError as exc:
        return False, f"OpenAI API error: {exc}"
    except Exception as exc:
        return False, f"Unexpected error during probe: {exc}"


def validate(api_key: Optional[str]) -> Tuple[bool, Optional[str]]:
    if not api_key:
        return False, "OPENAI_API_KEY is empty in the .env file."
    return _probe_openai(api_key)


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "Usage: validate_openai_key.py <path-to-.env>"}))
        sys.exit(2)
    env_path = Path(sys.argv[1])
    if not env_path.exists():
        print(json.dumps({"ok": False, "error": f".env file not found: {env_path}"}))
        sys.exit(1)
    api_key = _read_api_key(env_path)
    ok, err = validate(api_key)
    payload = {"ok": ok}
    if err:
        payload["error"] = err
    print(json.dumps(payload, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
