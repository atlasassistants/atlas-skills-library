# Voice Guide Output Format

> The exact structure of `client-profile/exec-voice-guide.md` when the `exec-voice-builder` skill writes it. Extracted from Section 10 of `atlas-inbox-rules-reference.md`. Every section below must be present in the output file — no omissions, no reordering.

---

## Why the format matters

Downstream skills (`inbox-triage`, `follow-up-tracker`, and anything else that drafts outgoing text) read this file at every session start. They rely on consistent section headers to find the right guidance. If the headers drift, the drafts drift. Keep the format exact.

---

## The Template

When writing the voice guide, produce a file that uses the **exact labels from Section 10 of the Atlas reference**. The downstream skills (`inbox-triage`, `follow-up-tracker`) parse by these labels — if they drift, drafts break. The template below adds enrichment lines (secondary forms, message length, calibration) beyond Section 10's minimum, but the core labels are mandatory and must appear literally.

```markdown
EXECUTIVE VOICE PROFILE

_Extracted on {YYYY-MM-DD} from the last {N} sent messages in the exec's Gmail._

Name: {Exec first name}
Tone: {1–2 word descriptor, e.g., "Direct and warm", "Crisp and professional"}

Opens with: {typical greeting — quote the exact form, e.g., `Hey {first name},`}
_Also seen:_ {secondary form if there's a clear split, e.g., `Hi {name},` for external}

Closes with: {typical sign-off — e.g., `Best,\n{First name}`}
_Also seen:_ {secondary closer if any — or "none" if they only use one}

Typical message length: {short 2–3 sentences / medium 4–6 sentences / long 1–2 paragraphs}
Contractions: {heavy use / moderate / rare}
Exclamation points and emoji: {frequent / occasional / never}

Signature phrases:
1. "{distinctive phrase 1}"
2. "{distinctive phrase 2}"
3. "{distinctive phrase 3}"
4. "{distinctive phrase 4}"
5. "{distinctive phrase 5}"

When saying yes: {pattern}
> "{example phrasing 1}"
> "{example phrasing 2}"

When saying no: {pattern}
> "{example phrasing 1}"
> "{example phrasing 2}"

When urgent: {pattern}
> "{example phrasing or structural pattern — e.g., 'no greeting, single-sentence ask, no sign-off'}"

When delegating: {pattern}
> "{example phrasing — e.g., 'Looping in {Name} who owns this.'}"

When showing enthusiasm: {pattern}
> "{example phrasing — e.g., 'This is great — let's make it happen.'}"

Anti-patterns (never use):
- "{anti-pattern phrase 1, e.g., 'Per my last email'}"
- "{anti-pattern phrase 2, e.g., 'I hope this email finds you well'}"
- "{anti-pattern phrase 3, e.g., 'Circling back to touch base'}"
- "{anti-pattern phrase 4, e.g., 'At your earliest convenience'}"
- "{anti-pattern 5 — tone rule, e.g., 'No exclamation points — keeps tone flat and professional'}"

Calibration notes:
- Internal vs external recipients: {note any tone/greeting split}
- Urgent messages: {if <3 examples found, say "not enough signal — defaults to direct short sentences"}
- Formal escalations: {if exec has a distinct voice for board/investor comms, note it here}

_This guide is used by `inbox-triage`, `follow-up-tracker`, and any other skill that drafts outgoing messages. Re-run `exec-voice-builder` quarterly or whenever drafts start to feel off._
```

---

## Filling-in Rules

### Every field is mandatory

If a field truly has no signal in the 30 sent messages, don't delete it — fill it with an explicit note: `not enough examples in the last 30 — defaults to {fallback}`. This tells downstream skills "no guidance here, use defaults" rather than leaving a mysterious gap.

### Signature phrases must be real quotes

Quote the exact phrase the exec used, character for character. `"let's make it happen"` not `"let's get this done"`. Downstream drafters will insert these phrases verbatim into drafts, so precision matters.

### Situational patterns should show actual examples

Pull 1–2 quoted examples per pattern directly from the sent messages. If the exec said "no" three times in different ways, list two of them and describe the range. Don't paraphrase.

### Anti-patterns are the most important section

The single biggest way an AI draft gives itself away is using generic business-speak ("per my last email", "circling back", "I hope this finds you well", "at your earliest convenience", "please don't hesitate"). Every voice guide MUST include at least 3 anti-patterns — more if the exec has a strong opinion against specific phrasings.

Also include tone-level anti-patterns when applicable:
- `No exclamation points` (if the exec writes flat and professional)
- `No softening hedges like "just wanted to"` (if the exec is direct)
- `No "gentle reminder" framing` (if the exec is direct in follow-ups)
- `No emoji` (if the exec is formal)
- `No "touching base"` (if the exec hates vague check-in framing)

### Calibration notes cover the edges

The Calibration Notes section is where nuance lives. Examples of good notes:

- _Internal writing is noticeably warmer than external — internal emails lead with "Hey", external with "Hi"._
- _Not enough urgent examples in the last 30; defaults to short sentences with no pleasantries._
- _Formal escalations (board, investors) use full name in sign-off and avoid contractions._
- _Uses British English — "organised", "realised", "favourite" — preserve this in drafts._

---

## Example — Fully Filled Guide

This is what the agent's output should look like when it's actually good. (The placeholders below are concrete, not template text.)

```markdown
EXECUTIVE VOICE PROFILE

_Extracted on 2026-04-11 from the last 30 sent messages in the exec's Gmail._

Name: Alex
Tone: Direct and warm

Opens with: `Hey {first name},`
_Also seen:_ `Hi {first name},` — used for external contacts and first-time outreach.

Closes with: `Best,\nAlex`
_Also seen:_ Just `Alex` for internal team members on short replies.

Typical message length: Short — 2 to 4 sentences for most replies; longer only for strategic updates.
Contractions: Heavy — uses "I'll", "won't", "let's", "we're" throughout.
Exclamation points and emoji: Occasional exclamation points for genuine enthusiasm. No emoji.

Signature phrases:
1. "let's make it happen"
2. "100%"
3. "appreciate you flagging this"
4. "over to you"
5. "tracking"

When saying yes: Enthusiastic and short
> "Love it — let's go."
> "Sounds great, I'm in."

When saying no: Direct but appreciative
> "Not the right fit for us right now — appreciate you thinking of us."
> "Going to pass on this one, but let me know how it goes."

When urgent: No greeting, single-sentence ask, no sign-off
> "Need this by 3pm today — who's driving it?"

When delegating: Loops in by name, one sentence
> "Looping in Marcus who owns this."
> "Nina can you take point on this?"

When showing enthusiasm: Strong positive adjective + action
> "This is fantastic — really great work."
> "Amazing. Let's build on this."

Anti-patterns (never use):
- "Per my last email"
- "I hope this email finds you well"
- "Circling back to touch base"
- "At your earliest convenience"
- "Please don't hesitate to reach out"
- No softening hedges like "just wanted to" — Alex is direct, never apologetic about asks
- No "gentle reminder" framing — follow-ups are plain and specific, not soft

Calibration notes:
- Internal writing is noticeably warmer than external — internal emails lead with "Hey", external with "Hi".
- Urgent messages drop the greeting and sign-off entirely — pure ask, single sentence.
- Formal escalations to board members use full "Alexandra" sign-off instead of "Alex".
- Not enough examples of declining large opportunities in the last 30; defaults to direct "passing on this".

_This guide is used by `inbox-triage`, `follow-up-tracker`, and any other skill that drafts outgoing messages. Re-run `exec-voice-builder` quarterly or whenever drafts start to feel off._
```

---

## Do Not

- Do not paraphrase the exec's phrases — quote them exactly.
- Do not fill fields with generic placeholder text like "direct and professional" without an observed example.
- Do not skip the Anti-Patterns section. Minimum 3 entries.
- Do not include fields not in the template (no `Favorite words:`, no `Tone by day of week:`). The format is fixed.
- Do not remove the `_Extracted on {date}_` line — it's how downstream skills detect a stale guide.
- Do not change the title from `EXECUTIVE VOICE PROFILE` — this literal string is used by downstream consumers and eval assertions.
