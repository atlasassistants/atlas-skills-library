---
name: inbox-onboarding
description: Two-phase setup wizard. Phase A configures the email system — credentials, the 9 Atlas labels, filters, UI settings, and initial inbox cleanup. Phase B builds the production profile — VIP contacts, team routing map, sweep rules. Resumable between sessions.
when_to_use: Run after inbox-audit, before any other inbox-zero skill. Trigger phrases: "set up inbox zero", "inbox zero onboarding", "configure inbox zero", "start inbox setup", "run inbox onboarding". Also triggered automatically when any skill detects that setup is incomplete. If no audit report exists at client-profile/inbox-audit.md, run inbox-audit first.
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

1. **Load audit findings.** Check for `client-profile/inbox-audit.json` and `client-profile/label-plan.json`.
   - **If audit exists:** read findings. Pre-fill VIP candidates, voice draft, and label plan from audit data. Skip re-scanning — the audit already did this.
   - **If no audit:** surface this to the user and offer two options:
     - **Option A — Run audit first (recommended).** Runs `inbox-audit`, which scans existing labels, filters, and sent folder to build an adapted setup. Takes a few minutes. Results in a label structure that fits the exec's actual inbox.
     - **Option B — Skip audit, use standard labels.** Proceeds immediately with the default 9 Atlas labels and no pre-filled VIPs or voice guide. Faster, but the exec starts from scratch with no adaptation.
     
     Default to Option A unless the user explicitly chooses to skip.

2. **Credentials and auth.** Credentials should already exist if `inbox-audit` ran. Verify they are valid. If missing, run `implementations/gmail/scripts/setup_credentials.py`.

3. **Create labels (adapted from audit).** Run `create_labels.py`. If `client-profile/label-plan.json` exists, it uses the adapted label structure from the audit automatically. If not, falls back to standard 9 Atlas labels. Idempotent — safe to re-run.

4. **Configure email client settings.** Walk the user through any required manual settings in their email client (e.g., Gmail Multiple Inboxes, inbox type, reading pane). These cannot be automated — provide step-by-step instructions.

5. **Create core filters.** Create the four core auto-routing filters: subscriptions, receipts, calendar, meeting recordings.

6. **Apply filters to existing messages.** Dry-run first — show how many existing messages match. Apply with approval. Typically clears 40–70% of the inbox immediately.

7. **Initial inbox cleanup** (optional but recommended):
   - Archive messages older than 90 days (preview + approval)
   - Scan for bulk senders, offer to create per-sender filters

Touch `.cleanup-done` marker after Phase A completes.

### Phase B — Production profile

Ask only the minimum required for skills to work correctly. Pre-fill from audit findings where available — only ask the exec to confirm or adjust, not to answer from scratch.

1. **VIP contacts** — pre-fill from audit's top reply-to contacts. Confirm with exec, add any missing. → write to `client-profile/vip-contacts.md`
2. **Team routing map** (who handles what) → write to `client-profile/team-delegation-map.md`
3. **Label sweep rules** — present defaults adapted to the label plan, offer adjustments → `client-profile/label-sweep-rules.md`

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
