# inbox-zero — Setup Instructions

> Follow these steps before running any skill. This plugin requires real email access — setup cannot be skipped.

## What requires setup

This plugin reads, labels, and drafts against a live inbox. Two things must be configured:

1. **An email implementation** — the tool or scripts that give the agent access to your inbox
2. **A client profile** — the exec's VIPs, team routing map, and voice guide

---

## Option A: Gmail (recommended)

The Gmail implementation ships ready-to-use in `implementations/gmail/`. It uses the Gmail API directly via OAuth2 — no third-party services, credentials stay on your machine.

### Step 1: Install Python dependencies

```bash
cd implementations/gmail
pip install -r requirements.txt
```

### Step 2: Run the onboarding wizard

The `inbox-onboarding` skill handles the full Gmail setup in two phases. Start it with:

```
Run inbox onboarding.
```

**Phase A** (Gmail configuration — ~20 minutes first time):
- Creates a Google Cloud project and enables the Gmail API
- Downloads `credentials.json` to your machine
- Runs OAuth2 consent flow → writes `token.json` (auto-refreshes, never expires)
- Creates the 9 Atlas labels with exact names and colors
- Configures Gmail UI: Multiple Inboxes, reading pane, inbox sections
- Creates core filters (subscriptions, receipts, calendar, recordings)
- Retroactively applies filters to existing inbox messages (~40–70% inbox reduction)
- Runs optional initial cleanup: archives mail >90 days old, creates bulk-sender filters

**Phase B** (production profile — ~10 minutes):
- Collects VIP contacts → `client-profile/vip-contacts.md`
- Collects team routing map → `client-profile/team-delegation-map.md`
- Confirms label sweep rules
- Optionally configures a processing schedule

Phase A and Phase B can be done in separate sessions. Onboarding is fully resumable.

### Step 3: Build the exec voice guide

After onboarding completes, run:

```
Build the exec voice profile.
```

This extracts writing patterns from the exec's last 30 sent emails. Required before any triage or follow-up skill drafts replies.

### Step 4: Verify

Run a health check to confirm everything is configured:

```
Run health check.
```

Then run the full inbox-zero for the first time:

```
Do the inbox.
```

---

## Option B: Other email providers

The skills are provider-agnostic. To use a different provider:

1. Wire up the required capabilities to your email tool (see README for the full list)
2. Each skill's "Required capabilities" section lists what it needs at each step
3. Skip the Gmail-specific setup in `implementations/gmail/` — configure your tool instead
4. The `client-profile/` templates still apply — fill them in manually or adapt the onboarding questions

See `implementations/` for available implementations. To contribute a new one, follow the pattern in `implementations/gmail/README.md`.

---

## Notes

- **Scripts stay on your machine.** The Gmail implementation runs locally — no cloud service, no third-party API. Your email never leaves your machine except to talk to Gmail's own API.
- **The plugin never sends email.** Send is blocked at the library level. Only drafts are created. You always hit send.
- **Onboarding detects existing labels.** If your inbox already has labels, the wizard offers three migration modes (keep both, migrate, clean slate) before touching anything.
