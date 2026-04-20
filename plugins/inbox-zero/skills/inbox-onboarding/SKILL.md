---
name: inbox-onboarding
description: Two-phase setup wizard. Phase A configures the email system — credentials, the 9 Atlas labels, filters, UI settings, and initial inbox cleanup. Phase B builds the production profile — VIP contacts, team routing map, sweep rules. Resumable between sessions.
when_to_use: Run once before any other inbox-zero skill. Trigger phrases: "set up inbox zero", "inbox zero onboarding", "configure inbox zero", "start inbox setup", "run inbox onboarding". Also triggered automatically when any skill detects that setup is incomplete.
atlas_methodology: neutral
---

# inbox-onboarding

Configure everything needed to run inbox-zero end to end — two phases, resumable.

## Purpose

Inbox-zero requires setup that can't be skipped: the 9 Atlas labels must exist with exact names and colors, filters must be in place, and the client profile must have VIPs and team routing for classification to work. This skill handles the full setup flow in two phases, detects what's already done, and picks up mid-flow without redoing completed steps.

## Inputs

- **Existing configuration state** — detected automatically from the presence of credentials, labels, filter counts, and marker files

## Required capabilities

- **Label create** — create the 9 Atlas labels in the email system (once only; idempotent)
- **Filter create** — create core routing filters at message arrival
- **Email read** — scan existing labels and filters to detect conflicts; count inbox messages for cleanup
- **Label apply** — apply filters retroactively to existing inbox messages (Phase A cleanup)
- **State storage** — write phase completion marker files; read for resume detection

## Steps

### Phase detection (always first)

Before running any phase steps, check which are complete:
1. Credentials exist and valid?
2. 9 Atlas labels exist with correct names?
3. Core filters created (≥4)?
4. `.cleanup-done` marker exists?
5. `.onboarding-complete` marker exists?

Skip any completed step. If all markers exist, report onboarding complete.

### Phase A — Email system configuration

1. **Environment audit.** Scan for existing labels and filters that could conflict with Atlas names. Present findings. Offer three migration modes:
   - `keep_both` — leave existing labels, add Atlas ones alongside
   - `migrate_labels` — rename existing to Atlas names where possible
   - `clean_slate` — remove conflicting labels and filters (preview + approval required)

2. **Credentials and auth.** Run the configured implementation's credential setup (e.g., `implementations/gmail/scripts/setup_credentials.py`). Walk the user through creating API access, downloading credentials, and completing OAuth consent. Do not proceed until credentials are valid.

3. **Create 9 Atlas labels.** Create all labels with exact names and the correct colors. Idempotent — safe to re-run if partial.

4. **Configure email client settings.** Walk the user through any required manual settings in their email client (e.g., Gmail Multiple Inboxes, inbox type, reading pane). These cannot be automated — provide step-by-step instructions.

5. **Create core filters.** Create the four core auto-routing filters: subscriptions, receipts, calendar, meeting recordings.

6. **Apply filters to existing messages.** Dry-run first — show how many existing messages match. Apply with approval. Typically clears 40–70% of the inbox immediately.

7. **Initial inbox cleanup** (optional but recommended):
   - Archive messages older than 90 days (preview + approval)
   - Scan for bulk senders, offer to create per-sender filters

Touch `.cleanup-done` marker after Phase A completes.

### Phase B — Production profile

Ask only the minimum required for skills to work correctly:

1. **VIP contacts** → write to `client-profile/vip-contacts.md`
2. **Team routing map** (who handles what) → write to `client-profile/team-delegation-map.md`
3. **Label sweep rules** — present defaults, offer adjustments → `client-profile/label-sweep-rules.md`
4. **Processing schedule** (only if scheduled operation is configured)

Do not ask optional calibration questions during onboarding. Save those for later: reply voice convention, autonomy boundaries, custom escalation triggers, priority tiers, feedback loop.

Touch `.onboarding-complete` marker after Phase B completes.

**Gmail implementation:** `implementations/gmail/skills/inbox-onboarding/scripts/`

## Output

Progress reported step-by-step during the wizard. Final confirmation:

```
Onboarding complete ✅

Phase A: Labels created, filters applied, inbox cleaned
Phase B: VIP list (12 contacts), team map (4 members), sweep rules confirmed

Next steps:
1. Run exec-voice-builder to build the voice guide
2. Run inbox-zero to start your first managed session
```

## Customization

- **Migration mode default.** The default for conflicting labels is `keep_both` (safest). Change per deployment.
- **Cleanup aggressiveness.** The 90-day archive threshold is adjustable. Some execs prefer 180 days.
- **Phase B questions.** The required first-run questions are minimal by design. Add to the list only if a field is truly required for any skill to function correctly.

## Why neutral

The setup flow is mechanical — detect state, run steps, confirm completion. Atlas has no opinionated method for "the right way to set up API credentials." The opinionated work is in the skills that run after setup.
