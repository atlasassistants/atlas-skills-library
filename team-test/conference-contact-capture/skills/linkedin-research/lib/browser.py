"""Chrome launch and CDP connection."""

import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout


def is_debug_port_open(port: int = 9222, host: str = "localhost") -> bool:
    """Check if a Chrome instance is listening on the CDP debug port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1.0)
    try:
        return sock.connect_ex((host, port)) == 0
    finally:
        sock.close()


def launch_chrome(chrome_path: str, profile_dir: str, port: int = 9222,
                  visible: bool = False) -> subprocess.Popen:
    """Launch a Chrome instance with the debug port enabled.

    visible=False puts the window off-screen via --window-position.
    Use visible=True during onboarding so the user can sign into LinkedIn.
    """
    args = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    if not visible:
        args.append("--window-position=-2400,-2400")

    proc = subprocess.Popen(args)

    # Wait up to 10s for the debug port to come up
    for _ in range(40):
        if is_debug_port_open(port):
            return proc
        time.sleep(0.25)

    proc.terminate()
    raise RuntimeError(
        f"Chrome did not start listening on port {port} within 10 seconds"
    )


def ensure_chrome_running(chrome_path: str, profile_dir: str, port: int = 9222,
                          visible: bool = False) -> subprocess.Popen | None:
    """Check if Chrome is already on the debug port; if not, launch it.

    Returns the launched subprocess (or None if Chrome was already running).
    """
    if is_debug_port_open(port):
        return None
    return launch_chrome(chrome_path, profile_dir, port, visible=visible)


def dismiss_cookie_banner(page) -> bool:
    """Click 'Reject' on LinkedIn's cookie consent banner if present.

    Returns True if a button was clicked, False otherwise.
    """
    try:
        rejected = page.evaluate("""() => {
            const buttons = Array.from(document.querySelectorAll('button, a'));
            for (const b of buttons) {
                const t = (b.innerText || '').trim().toLowerCase();
                if (t === 'reject' || t === 'reject all' ||
                    t === 'decline' || t === 'decline all') {
                    if (b.offsetParent !== null) {
                        b.click();
                        return true;
                    }
                }
            }
            return false;
        }""")
        if rejected:
            page.wait_for_timeout(800)
        return bool(rejected)
    except Exception:
        return False
