# Gmail Implementation

> Production Python scripts for every inbox-zero capability, using the Gmail API directly via OAuth2.

## What's in here

```
implementations/gmail/
├── requirements.txt
├── scripts/                 ← Gmail-specific: auth, API client, state, orchestrator
└── skills/
    ├── inbox-triage/scripts/       ← triage_inbox.py, label_sweep.py
    ├── escalation-handler/scripts/ ← scan_escalations.py
    ├── follow-up-tracker/scripts/  ← check_followups.py
    ├── exec-voice-builder/scripts/ ← extract_voice.py
    ├── health-check/scripts/       ← run_health_check.py
    └── inbox-onboarding/scripts/   ← setup_credentials.py, create_labels.py, create_filters.py, ...

shared/scripts/              ← platform-agnostic utilities (safety.py, atlas_labels.py, etc.)
                               lives at plugins/inbox-zero/shared/scripts/
```

## Setup

```bash
pip install -r requirements.txt
```

Then run the onboarding skill:
```
Run inbox onboarding.
```

The onboarding wizard handles everything: Google Cloud project setup, OAuth2 consent, label creation, filter setup.

## Script path setup

Scripts reference shared utilities via the `ATLAS_SHARED_SCRIPTS` environment variable. The orchestrator sets this automatically. When running scripts manually:

```bash
export ATLAS_SHARED_SCRIPTS=/path/to/plugins/inbox-zero/shared/scripts
python implementations/gmail/skills/inbox-triage/scripts/triage_inbox.py fetch
```

## Key scripts

| Script | Location | What it does |
|---|---|---|
| `gmail_client.py` | `scripts/` | All Gmail API operations — labels, filters, messages, drafts. Never sends. |
| `gmail_auth.py` | `scripts/` | OAuth2 token management, auto-refresh |
| `safety.py` | `../../shared/scripts/` | Blocks the send API at library level — `PluginSafetyError` on any send attempt |
| `orchestrator.py` | `scripts/` | Chains skills in the correct order with subprocess management |
| `state_store.py` | `scripts/` | Persists cadence state in `.plugin-state.json` |
| `triage_inbox.py` | `skills/inbox-triage/scripts/` | `fetch` — returns messages JSON; `apply-batch` — applies label decisions |
| `scan_escalations.py` | `skills/escalation-handler/scripts/` | Scans for red flags, applies `1-Action Required` |
| `check_followups.py` | `skills/follow-up-tracker/scripts/` | `scan`, `clear-waiting`, `escalate` subcommands |
| `extract_voice.py` | `skills/exec-voice-builder/scripts/` | Fetches and strips sent messages for voice extraction |

## Safety

- **No send.** `safety.py` monkey-patches the Gmail API's send method. Any send call raises `PluginSafetyError` regardless of which script calls it.
- **Approval gates.** Destructive operations (mass archive, filter removal, label migration) use a `--dry-run` → `--execute --approval-id <id>` pattern. Nothing destructive runs without an explicit approval ID.
- **Credentials stay local.** `credentials.json` and `token.json` never leave the machine. OAuth2 talks directly to Google.
- **Quota tracking.** `quota_tracker.py` monitors API calls in a rolling 24h window; warns at 80% of the 30k/day budget.

## Other providers

To implement inbox-zero for a different email provider, create `implementations/{provider}/` following this same structure:
- `scripts/` with equivalent auth, client, and orchestrator modules
- `skills/{skill}/scripts/` with equivalent fetch, apply, and scan scripts
- Same JSON contract as the Gmail scripts (skills read these contracts, not the scripts themselves)

Platform-agnostic utilities (safety, label definitions, rate limiting, etc.) are in `plugins/inbox-zero/shared/scripts/` and should be reused across all implementations.

The skill SKILL.md files define the JSON contract each script must return. Match that contract and the skills work without modification.
