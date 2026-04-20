---
name: health-check
description: Audits the client profile for drift — stale voice guide, template placeholders left unfilled, empty VIP list, missing required sections. Runs as a pre-flight inside every inbox-zero orchestrator session. Also invoked standalone to check for drift between sessions.
when_to_use: Called automatically by inbox-zero as a pre-flight before every session. Also invoked directly: "run health check", "check atlas health", "scan for drift", "is the setup current", "health check".
atlas_methodology: neutral
---

# health-check

Audit the client profile for drift before it causes problems in a live session.

## Purpose

A stale voice guide produces drafts that sound wrong. Template placeholders left in the VIP list cause missed escalations. Missing team delegation map entries cause misclassified follow-ups. These problems are silent — triage runs, drafts are created, and nothing errors. The health check catches them before they silently degrade output quality.

## Inputs

- **Client profile directory** — default: `client-profile/`. Configurable per deployment.

## Required capabilities

- **File read** — read client profile files (no email access required)

## Steps

1. **Check voice guide age.** Read the timestamp from the first line of `client-profile/exec-voice-guide.md`. If ≥30 days old → warning. If missing entirely → error.
2. **Check VIP list.** Confirm `client-profile/vip-contacts.md` exists. An empty file is OK (exec may have no VIPs); a missing file is an error.
3. **Check for template placeholders.** Scan `client-profile/` files for literal placeholder strings: `[Name]`, `TODO`, `[email@example.com]`, `example.com`, `company.com`. Any found → warning.
4. **Check required sections.** Confirm `client-profile/team-delegation-map.md` and `client-profile/label-sweep-rules.md` exist and are non-empty.
5. **Return findings JSON** — list of findings with severity (warning / error), affected file, and recommended action.

**Gmail implementation:** `implementations/gmail/skills/health-check/run_health_check.py`

## Output

```json
{
  "skill": "health-check",
  "status": "warnings",
  "findings": [
    {"severity": "warning", "check": "voice_guide_age", "detail": "Voice guide is 34 days old. Re-run exec-voice-builder.", "file": "client-profile/exec-voice-guide.md"},
    {"severity": "warning", "check": "config_template", "detail": "Placeholder [email@example.com] found.", "file": "client-profile/vip-contacts.md"}
  ],
  "errored_checks": []
}
```

In the inbox-reporter SOD/EOD report, findings surface in the `📋 Health` section. Omitted if no findings.

## Customization

- **Voice guide staleness threshold.** Default 30 days → warning. Adjust if the exec's voice is stable.
- **Additional checks.** Add checks for any client-profile file that skills depend on.
- **Profile path.** Default is `client-profile/`. Override with `--profile /path/to/profile` when running the Gmail implementation script.

## Why neutral

The health check is mechanical — read files, check conditions, report findings. No judgment is involved. The thresholds (30 days for voice guide, placeholder strings to scan for) are configurable.
