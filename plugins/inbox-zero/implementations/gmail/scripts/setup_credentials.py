"""
Credential Setup Wizard (ADHD-friendly)
=========================================
Guides a user through creating a Google Cloud project and getting
credentials.json for the Atlas Inbox Zero plugin.

This is the ONE-TIME setup everyone has to do. After this, the plugin
runs automatically forever.

Design principles:
- ONE action per step
- Plain English — no jargon, no assumed knowledge
- Progress indicator ("Step 2 of 5")
- Auto-open browser tabs; fall back to printing clickable links
- If credentials.json already exists, skip straight to OAuth consent

Usage:
    python setup_credentials.py
"""

import sys
import time
import shutil
import webbrowser
from pathlib import Path


# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent
_CREDENTIALS_DIR = _PLUGIN_ROOT / "client-profile" / "credentials"
_CREDENTIALS_PATH = _CREDENTIALS_DIR / "credentials.json"
_TOKEN_PATH = _CREDENTIALS_DIR / "token.json"

# Each step is a dict with plain-English instructions and a URL
_SETUP_STEPS = [
    {
        "title": "Create a Google Cloud project",
        "url": "https://console.cloud.google.com/projectcreate",
        "what_to_do": [
            "A browser tab will open to Google Cloud Console.",
            "You may need to sign in with the Gmail account you want the plugin to manage.",
            "Click 'CREATE PROJECT' (or 'NEW PROJECT' if you already have one).",
            "Project name: anything you want — 'inbox-zero' works fine.",
            "Leave Location as 'No organization' if that's the only option.",
            "Click 'CREATE'.",
            "Wait about 10 seconds for the project to finish creating.",
        ],
        "confirmation": "Done — project created",
    },
    {
        "title": "Turn on the Gmail API for your project",
        "url": "https://console.cloud.google.com/apis/library/gmail.googleapis.com",
        "what_to_do": [
            "A browser tab will open to the Gmail API page.",
            "Make sure your new project is selected at the top of the page.",
            "Click the blue 'ENABLE' button.",
            "Wait for it to finish (a few seconds).",
        ],
        "confirmation": "Done — Gmail API enabled",
    },
    {
        "title": "Set up the OAuth consent screen",
        "url": "https://console.cloud.google.com/apis/credentials/consent",
        "what_to_do": [
            "A browser tab will open to the OAuth consent screen setup.",
            "Select 'External' and click 'CREATE'.",
            "App name: anything — 'Inbox Zero' is fine.",
            "User support email: pick your email from the dropdown.",
            "Skip everything else that's optional. Scroll down.",
            "Developer contact information: enter your email.",
            "Click 'SAVE AND CONTINUE' through the next screens (Scopes, Test users, Summary).",
            "On the Test users screen, click 'ADD USERS' and add your own Gmail address. This is important — only users in this list can use the app.",
            "Click 'SAVE AND CONTINUE', then 'BACK TO DASHBOARD'.",
        ],
        "confirmation": "Done — consent screen configured",
    },
    {
        "title": "Create OAuth credentials",
        "url": "https://console.cloud.google.com/apis/credentials",
        "what_to_do": [
            "A browser tab will open to the Credentials page.",
            "Click '+ CREATE CREDENTIALS' at the top.",
            "Select 'OAuth client ID'.",
            "Application type: choose 'Desktop app'.",
            "Name: anything — 'Inbox Zero Desktop' is fine.",
            "Click 'CREATE'.",
            "A popup will appear showing your Client ID and Client Secret.",
            "Click 'DOWNLOAD JSON' to download the credentials file.",
            "The file will be named something like 'client_secret_XXXXX.json'.",
        ],
        "confirmation": "Done — JSON file downloaded",
    },
    {
        "title": "Place the credentials file in the plugin folder",
        "url": None,
        "what_to_do": [
            "Find the file you just downloaded (check your Downloads folder).",
            f"Move or copy it into: {_CREDENTIALS_DIR}",
            "Rename it to exactly 'credentials.json'.",
            "You can also tell me the full path to the downloaded file and I'll move it for you.",
        ],
        "confirmation": "Done — credentials.json is in place",
    },
]


# ─────────────────────────────────────────────
# UI helpers
# ─────────────────────────────────────────────


def _print_banner() -> None:
    print()
    print("=" * 60)
    print("  Atlas Inbox Zero — Credential Setup")
    print("=" * 60)
    print()


def _print_step_header(step_num: int, total: int, title: str) -> None:
    print()
    print("-" * 60)
    print(f"  Step {step_num} of {total}: {title}")
    print("-" * 60)
    print()


def _open_url(url: str) -> bool:
    """
    Try to open a URL in the default browser.
    Returns True if it worked, False if we should fall back to printing the link.
    """
    if not url:
        return False
    try:
        # webbrowser.open returns True if it thinks it succeeded,
        # but on some systems it returns True even when no browser opens.
        # We trust it here since there's no reliable way to verify.
        opened = webbrowser.open(url, new=2)
        return bool(opened)
    except Exception:
        return False


def _print_instructions(instructions: list[str], url: str | None) -> None:
    if url:
        opened = _open_url(url)
        if opened:
            print(f"  (Opening browser tab: {url})")
        else:
            print(f"  Open this link in your browser:")
            print(f"    {url}")
        print()
        # Give the browser a moment to open
        time.sleep(1)

    print("  What to do:")
    for i, instruction in enumerate(instructions, 1):
        print(f"    {i}. {instruction}")
    print()


def _wait_for_confirmation(prompt: str) -> None:
    """Pause until the user confirms they're done with this step."""
    print(f"  When you're done, press ENTER to continue.")
    print(f"  (Or type 'quit' to stop the wizard and come back later.)")
    response = input("  > ").strip().lower()
    if response == "quit":
        print("\nNo problem — your progress is saved. Just run this wizard again when you're ready.")
        sys.exit(0)


# ─────────────────────────────────────────────
# Step 5 helper — move downloaded file into place
# ─────────────────────────────────────────────


def _handle_credentials_placement() -> None:
    """
    After the user downloads the JSON, help them place it in the right folder.
    Offer to move it for them if they provide the path.
    """
    _CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        if _CREDENTIALS_PATH.exists():
            print(f"  Found credentials.json at {_CREDENTIALS_PATH}")
            return

        print("  I don't see credentials.json yet.")
        print()
        print("  You can either:")
        print("    (a) Move the downloaded file into the credentials folder yourself,")
        print(f"        renaming it to 'credentials.json' in: {_CREDENTIALS_DIR}")
        print("    (b) Paste the full path to the downloaded file and I'll move it for you.")
        print()
        user_input = input("  Path to downloaded file (or press ENTER to check again): ").strip().strip('"').strip("'")

        if not user_input:
            continue

        source = Path(user_input).expanduser()
        if not source.exists():
            print(f"  Couldn't find a file at {source}. Try again.")
            continue

        try:
            shutil.copy2(source, _CREDENTIALS_PATH)
            print(f"  Moved credentials.json into place.")
            return
        except Exception as e:
            print(f"  Couldn't copy the file: {e}")
            continue


# ─────────────────────────────────────────────
# Main wizard flow
# ─────────────────────────────────────────────


def run_wizard() -> None:
    """
    Run the full credential setup wizard.
    Skips the 5-step setup if credentials.json already exists.
    """
    _print_banner()

    # Ensure the credentials directory exists
    _CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

    # If credentials already exist, skip straight to OAuth consent
    if _CREDENTIALS_PATH.exists():
        print("  Good news: credentials.json is already set up.")
        print("  Skipping straight to the login step.")
        print()
        _run_oauth_consent()
        return

    # Otherwise, walk through the 5-step setup
    print("  Welcome! This wizard will get your Gmail connected to the")
    print("  Atlas Inbox Zero plugin. It's a one-time setup — about 5 minutes")
    print("  of clicking. After this, everything runs automatically.")
    print()
    print("  You'll need:")
    print("    - A web browser")
    print("    - The Gmail account you want the plugin to manage")
    print()
    print("  Ready? Press ENTER to start.")
    input("  > ")

    total = len(_SETUP_STEPS)
    for i, step in enumerate(_SETUP_STEPS, 1):
        _print_step_header(i, total, step["title"])
        _print_instructions(step["what_to_do"], step.get("url"))

        if i == total:
            # Final step: verify or help place the credentials file
            _handle_credentials_placement()
        else:
            _wait_for_confirmation(step["confirmation"])

    # All 5 steps done — run OAuth consent
    print()
    print("-" * 60)
    print("  Setup complete! Now let's log in to Gmail.")
    print("-" * 60)
    print()
    _run_oauth_consent()


def _run_oauth_consent() -> None:
    """
    Run the OAuth consent flow. Opens a browser for the user to authorize,
    then saves token.json for future use.
    """
    print("  A browser will open so you can sign in to your Gmail account")
    print("  and click 'Allow' to give the plugin access.")
    print()
    print("  Important: you may see a warning screen saying 'Google hasn't")
    print("  verified this app.' That's expected — you're using your own")
    print("  personal Google Cloud project, which doesn't need verification.")
    print("  Click 'Advanced' → 'Go to [your app name] (unsafe)' to continue.")
    print()
    print("  Press ENTER when you're ready.")
    input("  > ")

    # Import here (after credentials.json exists) so the import doesn't fail
    try:
        _scripts_dir = Path(__file__).resolve().parent
        if str(_scripts_dir) not in sys.path:
            sys.path.insert(0, str(_scripts_dir))
        from runtime_paths import ensure_runtime_paths
        ensure_runtime_paths()
        from gmail_auth import get_credentials
    except ImportError as e:
        print(f"  Import error: {e}")
        print("  Gmail auth dependencies are not ready on this machine.")
        print("  Run this first, then re-run the wizard:")
        print("    python shared/scripts/bootstrap_runtime.py --install --bootstrap-pip")
        sys.exit(1)

    try:
        creds = get_credentials(_CREDENTIALS_PATH, _TOKEN_PATH)
    except Exception as e:
        print(f"  Something went wrong: {e}")
        print("  Try running this wizard again.")
        sys.exit(1)

    if creds and creds.valid:
        print()
        print("=" * 60)
        print("  All set! Your Gmail is connected.")
        print("=" * 60)
        print()
        print(f"  Your access token is saved at:")
        print(f"    {_TOKEN_PATH}")
        print()
        print("  From now on, the plugin will authenticate automatically.")
        print("  You don't need to do this again unless you revoke access.")
        print()
    else:
        print("  Authentication didn't complete. Try running the wizard again.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        run_wizard()
    except KeyboardInterrupt:
        print("\n\n  Wizard cancelled. Your progress is saved — run it again when you're ready.")
        sys.exit(0)
