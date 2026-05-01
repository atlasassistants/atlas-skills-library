# LinkedIn Research Skill

A self-contained Claude Code skill that researches a person on LinkedIn and produces a structured markdown dossier you can use for meeting prep, outreach drafting, or feeding into a downstream contact-capture workflow.

## Quickstart

1. **Drop this folder** into your Claude Code skills directory (typically `~/.claude/skills/linkedin-research-skill/`).
2. **Trigger the skill** in Claude Code chat:
   > research Reid Hoffman on LinkedIn

That's it. The skill handles everything else automatically:

- **First trigger:** auto-creates a Python virtual environment inside the skill folder and installs the one Python dependency (`playwright`) into it (~30 seconds). Then walks you through a ~2-minute onboarding (auto-detects Chrome, opens a dedicated scraper window, asks you to sign into LinkedIn once).
- **Every trigger after:** just works — searches LinkedIn, scrapes the profile, saves a clean dossier, and posts a 3-5 sentence summary in chat.

**Prerequisites you must already have installed:**
- Python 3.10+ (verify with `python --version`)
- Google Chrome
- A LinkedIn account (use your real one — established accounts are safer than throwaways)

The skill will surface a clear error if either Python or Chrome is missing.

Per scrape you'll get a clean structured dossier saved to `~/Documents/linkedin-research/<name>-<timestamp>.md` plus a 3-5 sentence summary in chat.

It works by attaching to a real Chrome browser (not headless — LinkedIn detects headless) that's logged into your LinkedIn account. The skill auto-launches that Chrome on demand, so day-to-day you just say "research [name] on LinkedIn" in chat and a dossier file appears.

## What you get per lookup

Two markdown files per scrape (see "Two-output model" below):
- A **clean structured dossier** with:
  - **Profile** — name, headline, pronouns, location, follower count, About
  - **Experience** — full work history with role descriptions
  - **Education** — degrees, institutions, dates
  - **Recent posts** — most recent posts with full text and engagement counts
  - **Search candidates considered** — the top 10 LinkedIn matches for the searched name, so you can verify the right person was picked
- A **raw dossier** (the unprocessed scrape) kept alongside as an audit trail.

Plus a 3-5 sentence summary that Claude posts in chat alongside both file paths.

Typical clean dossier size: ~5K–20K characters depending on how active the person is on LinkedIn. Raw can be 2–3× larger.

## Requirements

- **Python 3.10+** (uses modern type hints; tested on 3.13) — *if you don't have Python, see [Setup Help](#setup-help) below*
- **Google Chrome** installed (Windows or macOS) — *if you don't have Chrome, see [Setup Help](#setup-help) below*
- **A real LinkedIn account** (use your normal one — established accounts are safer than throwaways)
- **Claude Code** with skill loading enabled

## Setup Help

If you don't have Python or Chrome installed yet, here's how to set them up. **Skip this section if you already have both.**

### Installing Python (if needed)

**On Windows:**
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Click the big yellow "Download Python 3.X.X" button (any version 3.10 or newer is fine)
3. Run the downloaded installer
4. **IMPORTANT:** On the first installer screen, check the box **"Add python.exe to PATH"** at the bottom. This is the most-skipped step and the most common cause of "python: command not found" errors later.
5. Click "Install Now"
6. Verify by opening PowerShell or Command Prompt and typing: `python --version` — you should see something like `Python 3.13.x`

**On macOS:**
The system Python that ships with macOS is too old for this skill. You have two options:

*Option A — Homebrew (recommended if you already have it, or are comfortable with the terminal):*
1. Open Terminal
2. If you don't have Homebrew yet: install from [brew.sh](https://brew.sh) (one paste command)
3. Install Python: `brew install python@3.13`
4. Verify: `python3 --version`
5. Note: on Mac, the command is `python3` (not `python`). The skill auto-detects this.

*Option B — Official installer:*
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download the macOS installer for the latest Python 3.13.x
3. Run the installer (it walks you through everything — no special checkboxes needed on Mac)
4. Verify: open Terminal and run `python3 --version`

### Installing Google Chrome (if needed)

If you somehow don't have Chrome:
1. Go to [google.com/chrome](https://www.google.com/chrome/)
2. Download and run the installer for your OS
3. Open Chrome once after install (the skill needs it to be a working install, not just present on disk)

### Verifying you're ready

Open a terminal and run these two commands:

```bash
python --version    # Windows: should print Python 3.10+
# or
python3 --version   # macOS: should print Python 3.10+
```

```bash
# On Windows — find Chrome:
where chrome
# On macOS — find Chrome:
ls "/Applications/Google Chrome.app"
```

If both work, you're ready. Drop the skill folder in (next section) and trigger it — the skill takes over from there.

### A note on Python dependencies

The skill creates a Python virtual environment at `.venv/` inside the skill folder on first run (~50MB, gitignored). All Python dependencies install into this venv, so there's no risk of conflicting with your system Python and no PEP 668 errors on modern macOS. You don't need to do anything — the skill handles it.

If `pip install` fails inside the venv (rare — usually a network or proxy issue):

**"SSL: CERTIFICATE_VERIFY_FAILED"** — Your network may be behind a corporate proxy or firewall. Talk to your IT team, or try from a different network.

**"Could not connect" / network timeout** — Check your internet connection and re-trigger the skill.

**"pip: command not found"** — Should not happen inside a venv. If it does, your Python install is likely missing `ensurepip`; reinstall Python from python.org and re-trigger the skill.

## Installation

### 1. Get the folder

Copy or clone this whole folder to your Claude Code skills directory. Common locations:
- `~/.claude/skills/linkedin-research-skill/`
- Or wherever your Claude Code looks for skills

### 2. Trigger the skill

In Claude Code chat, say:

```
research Reid Hoffman on LinkedIn
```

The skill handles installation automatically:
- **Detects if Playwright is installed in the skill's venv** — on first trigger, creates a Python venv at `.venv/` inside the skill folder and runs `pip install -r requirements.txt` into it (one-time, ~30 seconds). Note: the skill does NOT run `playwright install` — it connects to your existing Chrome via CDP, no bundled browsers needed.
- **Walks you through a ~2-minute onboarding** the first time:
  - Auto-detecting your Chrome installation (or asking for the path)
  - Picking an output folder for saved dossiers
- Opening a dedicated scraper Chrome window (separate from your everyday browser)
- Signing into LinkedIn in that window — one time
- Verifying the session

Total onboarding time: ~2 minutes.

## Daily use

Once onboarded, just trigger the skill in chat with phrases like:
- `research [name] on LinkedIn`
- `look up [name]`
- `linkedin scrape [name]`
- `research [name] from [company]` (company narrows the search)

For multiple people:
- `research these contacts I met at the conference: Jane Smith, John Doe, Alice Chen`

The skill paces multi-name batches automatically (~45s between scrapes, with random jitter) to keep your account safe. Batches survive Claude/laptop restarts via a queue file.

## How it works (short version)

1. The skill calls `python linkedin_scraper.py verify` to check state
2. If not onboarded → walks you through the onboarding wizard
3. If LinkedIn signed you out → walks you through re-authentication
4. Otherwise → calls `python linkedin_scraper.py scrape "[name]"`, which:
   - Auto-launches a dedicated scraper Chrome (off-screen so it doesn't disrupt you) if not already running
   - Searches LinkedIn for the name
   - Picks the top result (and lists the other 9 candidates in the dossier so you can spot mistakes)
   - Visits the profile, experience subpage, education subpage, and recent activity subpage
   - Captures the rendered text (robust to LinkedIn's frequent CSS class changes)
   - Runs a regex-based strip pass to drop the obvious noise (sidebars, footer chrome, video UI, language picker, button labels)
   - Saves the **raw dossier** as `<output_dir>/<name-slug>-<timestamp>-raw.md`
5. Claude (in the chat session that triggered the skill) reads the raw dossier, extracts the profile owner's real data into a structured format, and writes the **clean dossier** to `<output_dir>/<name-slug>-<timestamp>.md` (same name, no `-raw` suffix). Then it posts a 3-5 sentence summary in chat alongside both file paths.

### Two-output model

Each scrape produces two files:

- `<name-slug>-<timestamp>-raw.md` — the raw scrape with the script's first-pass strip applied. Audit trail and fallback if the clean pass missed something.
- `<name-slug>-<timestamp>.md` — the clean structured dossier written by Claude. This is the source of truth.

Why two files? The scraper is a regex-based stripper — it's robust at removing the obvious chrome but can't reliably distinguish, say, a sidebar suggestion card's name + headline + follower count from the profile owner's. Claude is already in the loop (the skill is triggered from a Claude Code conversation), so the skill instructs Claude to do the structured extraction directly — no extra API call, more robust than regex, and the raw file stays around so you can spot-check.

## Pacing and account safety

This skill is conservative by default to protect your LinkedIn account:

- **45s average between scrapes** (with ±15s random jitter so it doesn't look mechanical)
- **25 scrapes per 24 hours** maximum
- **Slow-mode** triggers if you do 8 scrapes in 30 minutes (90s between scrapes for 30 min)
- **Auto-stop** if LinkedIn shows any "unusual activity" warning text — pause for 1 hour before resuming

These defaults are tuned for real, established LinkedIn accounts. If you want to tune them, edit `~/.linkedin-scraper-config.json` directly (the skill won't expose pacing knobs in chat to keep casual users safe).

## Limitations

- **Requires a device with Chrome running** when scraping. If you trigger the skill from your phone but your laptop is closed, nothing happens until your laptop is on. The skill is designed for "research happens on your device" not "research in the cloud."
- **Chrome only** in v1 (Edge / Brave support is feasible but not yet implemented).
- **Windows + macOS** in v1. Linux is untested but the script is platform-agnostic; it likely works with a small `detect_chrome_path` patch.
- **Best-effort scraping** — if LinkedIn fundamentally restructures their site, this skill will need updates. Their CSS classes change every few weeks but we don't depend on those; URL patterns and HTML structure changes are the real risk. Expect occasional small fixes over time.
- **Single user, single LinkedIn account per machine.**

## Folder layout

```
linkedin-research/
├── SKILL.md                 ← Claude reads this when the skill is triggered
├── README.md                ← this file
├── linkedin_scraper.py      ← Python CLI: setup / scrape / verify subcommands
├── cmd_setup.py, cmd_scrape.py, cmd_verify.py  ← subcommand implementations
├── lib/                     ← supporting modules
│   ├── strip.py             ← dossier text cleaning
│   ├── config.py            ← user config + Chrome detection
│   ├── pacing.py            ← daily caps + burst cooldowns
│   ├── queue.py             ← multi-name batch persistence
│   ├── browser.py           ← Chrome launch + CDP connection
│   └── scrape.py            ← LinkedIn search + crawl + dossier build
└── requirements.txt
```

Created on first run (gitignored, inside the skill folder):
- `.venv/` — Python virtual environment (~50MB, auto-managed by the skill)

State files (created at runtime, in your home directory):
- `~/.linkedin-scraper-config.json` — your config (Chrome path, output dir, pacing, history)
- `~/.linkedin-scraper-queue.json` — pending batch (only if you have one in flight)
- `~/.linkedin-scraper-profile/` — Chrome's user-data dir for the scraper profile (where your LinkedIn cookie lives)

## Troubleshooting

**"I couldn't find Chrome at the standard install locations"**
The skill auto-detects Chrome at common paths. If you've installed it somewhere unusual, paste the full path when prompted. On Windows: right-click your Chrome shortcut → Properties → Target. On macOS: Finder → Applications → right-click Google Chrome → Show Package Contents → Contents → MacOS → drag the file into chat for the path.

**"Chrome failed to launch"**
Most common cause: a previous scraper Chrome window is already running with the same profile dir. Close any windows that have the URL `localhost:9222/json/version` working, or just close all Chrome instances using the dedicated profile, then retry.

**"LinkedIn signed you out"**
Normal — LinkedIn occasionally invalidates sessions for security reasons. The skill walks you through re-authentication. Once you sign in again in the scraper Chrome window, it'll resume.

**"LinkedIn flagged the account for unusual activity"**
The skill detected a warning page during a scrape and paused. Wait an hour. If this happens repeatedly, lower your pacing limits in `~/.linkedin-scraper-config.json` (e.g., `daily_cap: 15` or `min_interval_seconds: 90`).

## License and ethics

This skill scrapes data that LinkedIn shows to logged-in users. It uses the user's own LinkedIn session — not an automated farm of accounts. Pacing defaults stay well below LinkedIn's documented rate limits.

That said:
- This may violate LinkedIn's Terms of Service. Use at your own risk.
- Saved dossiers contain personal information about people who haven't explicitly consented. Treat them like any other research notes you'd take during a meeting prep — don't share, post, or aggregate them carelessly. Comply with your local privacy laws (GDPR for EU contacts, etc.).

## Roadmap (potential future work)

- Edge / Brave browser support
- Linux support
- A "company" research counterpart (scrape `linkedin.com/company/...` pages)
- An orchestrator skill that triggers this one as part of a contact-capture workflow (brain dump → research → outreach draft → CRM entry)
- Optional integration with paid LinkedIn APIs (Apify, etc.) for higher-volume use cases without account risk

---

This skill is part of a larger contact-capture system.
