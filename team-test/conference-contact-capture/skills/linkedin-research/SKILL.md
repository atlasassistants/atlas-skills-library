---
name: linkedin-research
description: Research a person's LinkedIn profile end-to-end. Triggers on phrases like "research [name] on LinkedIn", "look up [name]", "scrape [name]", "linkedin research [name]". Handles first-time onboarding (auto-detects Chrome, walks user through LinkedIn login, saves config). Auto-launches a dedicated scraper Chrome on every run, paces requests safely (45s avg between scrapes, 25/day cap), persists multi-name batches across sessions, and produces TWO files per scrape: a raw dossier (`<slug>-<timestamp>-raw.md`, the script's first-pass output) and a clean structured dossier (`<slug>-<timestamp>.md`, written by the skill itself by extracting real profile data from the raw). Posts a 3-5 sentence summary plus both file paths in chat.
when_to_use: |
  - User asks to research a specific person on LinkedIn by name (e.g. "research Jane Doe on LinkedIn", "look up John Smith", "scrape [name]", "linkedin research [name]") and expects a structured dossier file plus an in-chat summary.
  - Capturing a batch of contacts from a conference or event where each person needs a LinkedIn dossier before follow-up emails or briefs are drafted (multi-name queue across sessions).
  - Building a pre-meeting briefing that requires LinkedIn-sourced background on an external attendee — role, company, recent posts, shared connections — saved to disk for reuse.
atlas_methodology: opinionated
---

# LinkedIn Research Skill

Follow this flow exactly. Do not paraphrase, summarize, or skip steps.

## Path resolution

The Python script and supporting modules live in this skill folder. Always run the script from the skill folder, or with the full path. The skill assumes:

- `linkedin_scraper.py` (entry point) lives next to this `SKILL.md`
- `lib/` contains the supporting modules
- `requirements.txt` lists Python dependencies (auto-installed into `<skill_dir>/.venv/` on first trigger — see Step 0)

User config lives at `~/.linkedin-scraper-config.json` (cross-machine). Output dossiers go to whatever folder the user chose during onboarding (default `~/Documents/linkedin-research/`).

## Step 0: Ensure prerequisites (one-time check)

Before running anything, set up an isolated Python environment for the skill. The skill always runs from a virtual environment at `<skill_dir>/.venv/` — this avoids PEP 668 errors on modern macOS Homebrew Python and keeps the skill's dependencies isolated from the user's system Python.

`<skill_dir>` means the directory containing this `SKILL.md`. Quote the path in shell commands if it contains spaces.

### 0a. Find or create the venv

Check whether the venv Python exists:
- Mac/Linux: `<skill_dir>/.venv/bin/python`
- Windows: `<skill_dir>/.venv/Scripts/python.exe`

**If it exists** → that's the Python command for the rest of this run. Skip to Step 0a.5.

**If it does not exist** → bootstrap it:

1. Find a working system Python. Try:
   ```bash
   python --version 2>&1
   ```
   If that errors, try:
   ```bash
   python3 --version 2>&1
   ```
   Use whichever works. If both error, **Python is not installed.** Walk the user through installation directly in chat — don't just point them at docs.

   Ask the user which OS they're on (Windows or Mac), then guide them through the steps for that platform. **Wait for them to say "done" after each step you can verify, then run the next check.**

   **On Windows, walk them through this exactly (one step at a time, wait for confirmation between each):**

   > 1. Open this link in your browser: https://www.python.org/downloads/
   > 2. Click the big yellow "Download Python 3.X.X" button at the top
   > 3. Run the downloaded `.exe` installer
   > 4. **CRITICAL** — On the first installer screen, check the box at the bottom that says **"Add python.exe to PATH"**. This is the most-skipped step and the most common cause of problems later.
   > 5. Click "Install Now" and wait for it to finish
   > 6. Tell me "done" when the installer says "Setup was successful"

   After they say done, verify:
   ```bash
   python --version
   ```

   If it works (shows Python 3.10+), continue.
   If it still fails, ask if they checked the "Add to PATH" box. If not, tell them to re-run the installer or use the "Modify" option to fix it.

   **On macOS, walk them through this exactly:**

   > 1. Open the Terminal app (Cmd+Space, type "Terminal", press Enter)
   > 2. Tell me whether you have Homebrew installed — type `brew --version` and tell me what it says.

   If they have Homebrew (`brew --version` shows a version):
   > 3. Run: `brew install python@3.13`
   > 4. Wait for it to finish (~1 minute)
   > 5. Tell me "done"

   If they don't have Homebrew (or don't know what it is):
   > 3. Open this link: https://www.python.org/downloads/
   > 4. Click "Download Python 3.X.X" — get the macOS 64-bit universal2 installer
   > 5. Run the downloaded `.pkg` installer — click through the prompts (no special settings needed on Mac)
   > 6. Tell me "done"

   After they say done, verify:
   ```bash
   python3 --version
   ```

   If it works (shows Python 3.10+), use `python3` as the system Python below.
   If not, ask them to copy/paste the error and help debug.

   **If the user gets stuck or the install isn't working after a few attempts**, suggest they try the [python.org troubleshooting docs](https://docs.python.org/3/using/index.html) or ask in their team's tech-help channel. Don't keep them trapped in a loop — gracefully let them know you can resume the skill setup once Python is working.

2. Verify the system Python is 3.10 or newer:
   ```bash
   <system-python> -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
   ```
   If exit code is non-zero, **Python is too old**. Walk them through upgrading directly in chat, the same way as the install branch above. The download steps are identical — installing a newer version replaces the old one (on Mac via Homebrew, this is `brew upgrade python@3.13` instead of `install`).

3. Create the venv:
   ```bash
   <system-python> -m venv "<skill_dir>/.venv"
   ```
   Expected: command exits 0, no output. The directory `<skill_dir>/.venv/` now exists.

4. Use the venv Python from here on (Mac: `<skill_dir>/.venv/bin/python`, Windows: `<skill_dir>/.venv/Scripts/python.exe`). Continue to Step 0a.5.

### 0a.5. Sanity-check the venv

Verify the venv Python actually runs:

```bash
"<venv-python>" --version
```

If it succeeds (prints a Python version), continue to Step 0b.

If it errors (broken symlink from a system-Python upgrade, corrupted venv, moved skill folder, anti-virus quarantine), the venv is unusable. Delete `.venv/` using whichever command matches the user's OS:

- Mac/Linux:
  ```bash
  rm -rf "<skill_dir>/.venv"
  ```
- Windows (PowerShell):
  ```powershell
  Remove-Item -Recurse -Force "<skill_dir>/.venv"
  ```

Then fall back to Step 0a's create path (steps 1–4 above) to bootstrap a fresh venv. After the rebuild, run the sanity check **once more**.

**If the sanity check fails on a freshly-created venv**, do not loop. The problem is fundamental (broken system Python, filesystem error, anti-virus actively interfering). Surface the `--version` error to the user verbatim and stop. Suggest:
> The venv won't run even after a fresh rebuild — the error was: `<paste error>`. This usually means the system Python install is broken, the skill folder isn't writable, or anti-virus is quarantining the venv binary. I can't fix this from chat; once the underlying issue is resolved, re-trigger the skill.

### 0b. Install dependencies

Test whether playwright is installed in the venv (exit code 0 = installed, 1 = missing):

```bash
"<venv-python>" -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('playwright') else 1)"
```

If exit code is non-zero, tell the user:

> Installing the Python dependency (playwright) — one-time setup, takes ~30 seconds.

Then run:

```bash
"<venv-python>" -m pip install -r "<skill_dir>/requirements.txt"
```

This succeeds on PEP-668 systems (modern macOS Homebrew Python) because pip is operating inside the venv.

If install fails, surface the actual pip error and stop:

> Couldn't install the Python dependency. The error was: `<paste error>`. Common causes: no network connection, corporate proxy/firewall blocking pip, or the skill folder isn't writable. Fix the underlying issue and re-trigger the skill.

If install succeeds (or playwright was already present), continue to Step 0c.

### 0c. Lock in the Python command for the rest of this skill

**From here on, every command in this skill that says `python` means the venv's Python:**
- **Mac/Linux:** `<skill_dir>/.venv/bin/python`
- **Windows:** `<skill_dir>/.venv/Scripts/python.exe`

Use this venv Python — quoted if `<skill_dir>` contains spaces — for every Python invocation in Steps 1–5 below, including the `python -c "..."` calls inside batch handling.

On subsequent triggers (after the first successful setup), Steps 0a, 0a.5, and 0b all return success instantly — Step 0 is effectively a no-op.

## Step 1: Detect state

Run from the skill folder:
```bash
python linkedin_scraper.py verify
```

Read the JSON output. Branch on the exit code:
- **Exit 0** → ready to scrape, go to **Step 4 (Scrape)**
- **Exit 10** → no config, go to **Step 2 (Onboarding)**
- **Exit 11** → no Chrome path saved, go to **Step 2 (Onboarding)**
- **Exit 12/13** → Chrome runtime problem, go to **Step 5 (Chrome troubleshooting)**
- **Exit 20** → LinkedIn signed out, go to **Step 3 (Re-auth)**

## Step 2: Onboarding

Tell the user:
> I'll set up the LinkedIn research skill. This takes about 2 minutes.

### 2a. Detect Chrome
Run:
```bash
python linkedin_scraper.py setup --stage detect
```

If exit 0: extract `chrome_path` from JSON output. Continue to 2b.
If exit 11: tell the user:
> I couldn't find Chrome at the standard install locations. Please paste the full path to chrome.exe (Windows) or "Google Chrome" (Mac binary inside the .app bundle). On Windows, right-click your Chrome shortcut → Properties → Target. On Mac, in Finder → Applications → right-click Google Chrome → Show Package Contents → Contents → MacOS → drag the file into chat.

Wait for user response. Use their answer as `chrome_path`.

### 2b. Confirm output folder
Read the `output_dir_default` from the detect output. Tell the user:
> I'll save dossier files to `<default>`. Press enter to keep this, or paste a different folder path.

If they pick a different folder, use it. Otherwise use the default.

### 2c. Save paths
Run:
```bash
python linkedin_scraper.py setup --stage save-paths --chrome-path "<chrome_path>" --output-dir "<output_dir>"
```

Confirm exit 0.

### 2d. Launch Chrome for LinkedIn login
Run:
```bash
python linkedin_scraper.py setup --stage launch-for-login
```

Tell the user:
> A Chrome window just opened — it's a dedicated browser for the scraper, separate from your everyday Chrome. The LinkedIn login page is loaded. **Sign in with your real LinkedIn account (the one you use professionally).** Established accounts are safer than throwaways. Tell me 'done' when you're signed in.

Wait for user to say 'done'.

### 2e. Verify session
Run:
```bash
python linkedin_scraper.py setup --stage verify-login
```

If exit 0: tell user:
> ✓ LinkedIn session verified. You're all set up. Try `research Reid Hoffman` to test it.

If exit 20: tell user:
> I don't see you logged in yet. Did you sign in fully? Make sure you see your LinkedIn feed in the Chrome window. Then say 'done' again.

Re-run verify-login.

## Step 3: Re-auth

Tell the user:
> LinkedIn signed you out. I'm opening Chrome to the login page now — please sign in, then say 'done'.

Run:
```bash
python linkedin_scraper.py setup --reauth-only
```

Wait for user to say 'done'.
Run:
```bash
python linkedin_scraper.py setup --stage verify-login
```

On success, automatically continue with whatever the user originally asked for.

## Step 4: Scrape

### 4a. Parse user input
Extract the person's name and (optional) company from the user message. If multiple names are mentioned (comma-separated, "and"-joined, or a list), it's a batch — see "Batch handling" below.

### 4b. Check for pending queue
Read `~/.linkedin-scraper-queue.json`. If a queue exists with pending items, ask the user:
> You have N lookups remaining from a batch started at <time>. Resume that batch, or start a new one?

### 4c. Run scrape (single-name)
For one name:
```bash
python linkedin_scraper.py scrape "<name>" [--company "<company>"]
```

Branch on exit code:
- **Exit 0** → success. Read JSON output for `raw_dossier_path` and `char_count` (this is the RAW scrape — script's first-pass cleaning only). Then do the following, in order:

  **1. Read the raw dossier file** at `raw_dossier_path`.

  **2. Produce a CLEAN structured dossier** by extracting only the profile owner's real data. Use the rules below.

  **KEEP** (these are the profile owner's data):
  - Name, headline, pronouns (if present), location
  - Profile owner's "X followers" / "X connections" line (the FIRST one only — see DROP rules)
  - Full About section text
  - Current company (from headline or top experience entry)
  - Each Experience entry: title, company, dates, location (if present), full description
  - Each Education entry: degree, institution, dates, description (if present)
  - Recent posts: post date, body text, engagement counts (likes/comments/reposts), and the post author IF different from the profile owner (e.g. the owner reposted someone else).

    **Reconciling Featured and Recent activity:** the same post often appears in BOTH the Profile main's "Featured" subsection (which usually has engagement counts but no date) AND the Recent activity feed (which usually has dates but no engagement counts). When this happens, treat them as the same post — match by the first ~80 characters of the post body, normalized for whitespace and emoji. List the post ONCE under "Recent posts" with merged metadata: date from Recent activity + engagement counts from Featured. Featured posts that don't appear in Recent activity should still be included (use a "Featured" sub-section if helpful, or inline with a "(pinned)" tag).
  - The "Search candidates considered" list (so the user can verify the right person was picked) — copy from the raw

  **DROP** (these are page chrome, sidebar leaks, or noise):
  - "Pages you may like" / "People you may know" / "People also viewed" / "More profiles for you" sidebar entries — any name, company, or industry label that isn't the profile owner's
  - Any "X followers" line that belongs to a SIDEBAR page or person (not the profile owner). Sparse profiles often have multiple follower-count lines from suggestion cards — keep only the profile owner's.
  - Language picker entries — any line ending with a parenthetical English language label like `(Norwegian)`, `(Punjabi)`, `(Chinese (Simplified))`, plus the surrounding "Select language" / "Visit our Help Center" chrome
  - Footer chrome — "Accessibility", "Talent Solutions", "Privacy & Terms", "© <year> LinkedIn Corporation", etc.
  - Repeated author headers within the activity feed — when LinkedIn renders the same author name 2-3 times in a row before each post (e.g. "Reid Hoffman / Reid Hoffman / Reid Hoffman"), keep just one occurrence per post
  - Video player UI — "Pause", "Play", "Loaded: 66%", "Mute", "Unmute", "1x", "0.5x", "Playback speed", "Turn closed captions on/off", "Turn fullscreen on/off", timestamps like "1:11"
  - "Activate to view larger image" alt text and similar accessibility-only strings
  - Empty-state messages like "Russel Mei has no recent posts" — don't echo them; use the structured "_(none on profile)_" placeholder instead
  - Standalone button labels: "Follow", "Message", "Connect", "Send", "Show all", "View my newsletter"
  - Connection-degree markers on their own line: "· 3rd+", "· 2nd", "· Premium", "· Influencer"

  **3. Write the cleaned dossier** to a file at the SAME directory as the raw, with the SAME filename but WITHOUT the `-raw` suffix. Example: if `raw_dossier_path` is `.../russel-mei-de-jesus-2026-04-28-2030-raw.md`, write the clean file to `.../russel-mei-de-jesus-2026-04-28-2030.md`.

  Use this exact structure for the cleaned file (omit pronouns line if not present; replace any empty section's body with `_(none on profile)_` rather than fabricating content):

  ```markdown
  # LinkedIn Research: <Name>

  **Profile:** <URL>
  **Captured:** <timestamp>
  **Pronouns:** <X>
  **Location:** <location>
  **Followers:** <count>

  ## Headline
  <headline>

  ## About
  <full About text, if present>

  ## Experience
  1. **<Title>** at **<Company>** (<dates>)
     <description if present>
  2. ...

  ## Education
  1. **<Degree>** — **<Institution>** (<dates>)
     <description if present>
  2. ...

  ## Recent posts
  1. <date> — by <author (only if different from profile owner)>
     <full post body>
     <engagement: X likes, Y comments, Z reposts>
  2. ...

  ## Search candidates considered
  1. [<name>](<url>) — <preview>
  2. ...

  ---
  *Source: raw scrape at <raw_dossier_path>*
  ```

  **4. Generate a 3-5 sentence summary** from the CLEANED file (not the raw) covering:
  - Who they are (current role + company)
  - Background highlights from experience/education
  - 1-2 themes from their recent posts (if any)
  - Anything notable for outreach context

  **5. Post in chat** (note both file paths and char counts):
  ```
  **Research: <Name>**
  <summary>

  Clean dossier: `<cleaned_path>` (<char_count> chars)
  Raw scrape: `<raw_dossier_path>` (<raw_char_count> chars)
  ```
- **Exit 10/20/30/31** → handle per error matrix below.

### 4d. Batch handling (multiple names)
If user provided multiple names:

1. Estimate time: `total_minutes = name_count * 0.75` (45s avg + scrape time + buffer).
2. Confirm: "I'll process N lookups, ~<estimate> minutes total, paced for account safety. Start the queue?"
3. On yes, write queue file by calling Python:
   ```bash
   python -c "from lib.queue import create_queue; create_queue([{'name':'A','company':None},{'name':'B','company':None}])"
   ```
4. Process items sequentially. After each scrape:
   - Update queue item status (mark done or failed) via `update_item_status`
   - Post the per-item summary
5. On full completion, archive the queue file via `archive_completed_queue` and post: "✓ Batch complete: N/N saved to <output_dir>."

## Step 5: Chrome troubleshooting

If verify returns exit 11 (no Chrome path), 12 (launch failed), or 13 (CDP unreachable), surface the JSON `reason` and `detail` to the user:
- **Exit 11**: trigger Onboarding (Step 2) — config exists but `chrome_path` is missing.
- **Exit 12**: tell the user "Chrome failed to launch. The launcher said: `<detail>`. Common cause: a previous scraper Chrome window is still running. Try closing all Chrome windows on your dedicated profile dir (`~/.linkedin-scraper-profile`) and re-trigger."
- **Exit 13**: tell the user "Chrome is unresponsive. Try closing the scraper Chrome window and re-running — I'll re-launch it."

## Error matrix (full)

| Exit | What user sees | What we do |
|---|---|---|
| 10 | (silent) | Run Onboarding |
| 11 | "I couldn't find Chrome at standard locations. Paste the full path." | Re-run with `--chrome-path` |
| 12 | "Chrome failed to launch. <detail>." | Surface error, suggest closing existing windows |
| 13 | "Chrome is unresponsive. Closing and re-launching." | Suggest user close and retry |
| 20 | "LinkedIn signed you out. Opening login..." | Re-auth flow |
| 30 | "LinkedIn flagged the account for unusual activity. Pausing for 1 hour." | Stop queue, set cooldown |
| 31 | "Daily cap of 25 reached. Resets at <time>." | Optional: queue for tomorrow |

## What this skill does NOT do

- Run while the user's device is off (the disclaimer)
- Use a throwaway LinkedIn account (real account is actually safer)
- Bypass LinkedIn ToS — this is best-effort defensive scraping with conservative pacing
- Post anything to LinkedIn (read-only)

## Installation note

Anyone reading this skill folder can use it. Install:
1. Copy/clone this folder to your Claude Code skills directory (e.g., `~/.claude/skills/linkedin-research/`)
2. Trigger the skill in chat (e.g., "research Reid Hoffman on LinkedIn") — on first trigger it auto-creates a Python venv inside the skill folder and installs dependencies, then walks you through onboarding.

See `README.md` for full installation walkthrough.
