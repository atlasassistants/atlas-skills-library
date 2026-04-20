---
name: exec-voice-builder
description: Extracts the exec's writing voice from their last 30 sent emails. Analyzes openings, closings, tone, signature phrases, situational patterns (yes/no/urgent/delegating), and anti-patterns. Writes a voice guide used by triage and follow-up-tracker for all drafting. Required before any drafting skill runs.
when_to_use: Run during onboarding Phase B before the first triage session. Re-run quarterly or when drafts feel off. Trigger phrases: "build voice profile", "extract exec voice", "update voice guide", "drafts don't sound right", "refresh voice", "voice guide is stale".
atlas_methodology: opinionated
---

# exec-voice-builder

Extract writing patterns from the exec's sent mail. Build the voice guide every drafting skill depends on.

## Purpose

Generic AI drafting sounds like AI. The only way to draft in the exec's voice is to study what the exec actually writes. This skill reads the exec's last 30 sent emails, extracts the real patterns — not approximations — and writes them to a voice guide that every drafting skill loads before producing a single word.

## Inputs

- **Sent messages** (required) — the exec's last 30 sent emails, fetched from the Sent folder
- **Exec name** (required) — first name used in the voice guide header

## Required capabilities

- **Email read** — fetch the exec's sent messages (Sent folder, last N messages, strip quoted content)

## Steps

1. **Confirm with the user** before running — this reads sent mail and will overwrite any existing voice guide.
2. **Fetch the last 30 sent messages.** Strip quoted blocks, forwarded content, and signatures before analysis — analyze only the exec's original writing.
3. **Require at minimum 10 messages.** Fewer than 10 messages = not enough signal. Stop and report.
4. **Analyze each message for the fields defined in `references/voice-guide-template.md`:**
   - Opening style (greeting form, internal vs. external variation)
   - Closing style (sign-off, secondary options)
   - Tone (formal/direct/warm/casual/crisp/blunt)
   - Signature phrases — 3–5 expressions that appear repeatedly, character-for-character
   - Patterns for: saying yes, saying no, when urgent, when delegating, when enthusiastic
   - Anti-patterns — phrases and tone rules that are never present (minimum 3)
   - Calibration notes — internal vs. external variation, edge cases
5. **Every observation must be grounded in actual messages.** No fabrication. If a field doesn't have enough examples, mark it "not enough signal" rather than guessing.
6. **Build the voice guide text** using the exact format from `references/voice-guide-template.md`. Write the ISO8601 UTC timestamp as the first line.
7. **Show the user a summary** of what was extracted. Give them a chance to correct anything before saving.
8. **Write to `client-profile/exec-voice-guide.md`.** Overwrite — do not append.

**Gmail implementation:** `implementations/gmail/skills/exec-voice-builder/extract_voice.py`

## Output

A summary shown to the user before saving:

```
Voice guide ready for review:

Tone: Direct and warm
Opens with: "Hey {first name}," (internal) / "Hi {name}," (external)
Closes with: "Best, Alex"
Message length: Short (2–3 sentences typical)
Signature phrases: "Let's do it", "Make sense?", "Happy to jump on a call"

Anti-patterns identified:
- "Per my last email" — never used
- "Hope this finds you well" — never used
- "At your earliest convenience" — never used
- No exclamation points on professional emails

Confirm save to client-profile/exec-voice-guide.md? [yes to save]
```

## Customization

- **Message count.** Default 30. Increase for execs with varied tone across contexts; 30 is the minimum for reliable signal.
- **Refresh cadence.** Voice drift happens over ~90 days. `health-check` flags guides older than 30 days. Re-run to refresh.
- **Manual overrides.** The voice guide is a markdown file — the exec can edit it directly after extraction if any patterns were missed or wrong.

## Why opinionated

The voice guide's value comes from real signal, not templates. The extraction methodology — stripping quoted content, requiring 10+ messages, grounding every observation in actual examples, mandating anti-patterns — is what makes the guide usable. A voice guide built from fewer examples or with fabricated patterns produces drafts that feel wrong and erode trust in the system.
