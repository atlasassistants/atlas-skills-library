# Atlas Conference Followup Methodology

> The opinionated methodology behind the briefs and emails the `capture-contacts` skill produces. Atlas developed this from running real exec post-event followups; the structure is tested, not theoretical. Fork the plugin and edit this file to override.

## Why this methodology exists

Generic "post-event followup email" templates fail two ways:
1. **Too cold** — they read like CRM autoresponders, not like a real person who actually met you
2. **Too vague** — they reference the event but not the specific conversation, making them indistinguishable from spam

This methodology forces specificity at three points: the conversation reference (what you actually talked about), the common ground (where the exec's themes intersect this person's work), and the soft CTA (a concrete next step, not "let's keep in touch").

## Brief structure

Each contact's brief MUST contain these six sections in this exact order:

### 1. Person summary

2–3 sentences pulled from the LinkedIn dossier. Cover:
- Current role and seniority signal
- Career arc (founder, operator, IC-track, etc. — what kind of person are they?)
- Notable specialization or domain expertise

Don't pad. If LinkedIn surfaces only the basics, write only the basics.

### 2. Company snapshot

Four labeled sub-fields, populated from Tavily content:

- **What they do** — 2–3 sentences on their product or service. Plain language; avoid quoting marketing copy verbatim.
- **Target customer** — who they sell to (segment, use case, sometimes named customers from case studies)
- **Differentiation / value prop** — what makes them stand out, in their own positioning
- **Recent activity** — funding rounds, product launches, leadership changes, notable blog posts. Date-stamped where possible.

If Tavily wasn't connected or returned thin content, write `Company research unavailable for [Name] — using LinkedIn-only context.` Do NOT fabricate.

### 3. Conversation context

Paraphrase the executive's notes from the brain dump cleanly. Preserve specific details — venue, topic, opinions exchanged, any concrete artifacts mentioned (slides, demos, links, names of mutual contacts).

If the brain dump had no context for this contact, write `No conversation notes captured.` and proceed.

### 4. Common ground

The most valuable section. Cross-reference the executive's themes (`client-profile/exec-themes.md`) with the person's work (LinkedIn + company snapshot).

Look for:
- Direct overlap (you both work on X)
- Adjacent overlap (you do X, they do something X depends on)
- Substantive challenge overlap (you're both wrestling with the same problem from different angles)

Write 1–2 specific sentences. Vague ("we're both interested in operations") = useless. Specific ("you're building usage-based pricing into your onboarding flow; that maps directly to my pricing-model thinking from the dinner") = the seed of the email.

If there's no real common ground, say so honestly: `No clear thematic overlap — fallback angle: [generic but truthful angle, e.g., "shared interest in B2B GTM"]`.

### 5. Suggested follow-up angle

One concrete next step the email could lead with:
- "Intro to [mutual contact]"
- "Share the [resource] mentioned"
- "15-min call to compare notes on [specific topic]"
- "Invite to [event the exec is attending]"

Pick ONE. The email drafter uses this as the soft CTA.

### 6. Source

Event name + date the executive met this person. Used for grouping briefs by event.

## Email structure

Drafted in the executive's voice (read from `client-profile/conference-email-voice.md`) with these four sections, in this order. Total length: 80–150 words. Anything longer reads like a pitch deck.

### 1. Personal opener

References where you met + something specific. Required signals:
- Where you met (the event, by name)
- Some specific anchor from the conversation (a topic, a venue, a person you both know)

Bad: *"Great to meet you at SaaStr."*
Good: *"Great to meet you at the Tuesday-night dinner — your point about onboarding metrics shifting from activation to time-to-value stuck with me."*

### 2. Substance

The common-ground angle from the brief, written in the executive's voice. ONE thing, specific and concrete.

Bad: *"I'd love to keep in touch and learn more about your work."*
Good: *"We're seeing the same shift on the EA-product side — the executives who track activation lift on their own ops are getting 3x the AI leverage."*

### 3. Soft CTA

The suggested follow-up from the brief, framed as an invitation, not a demand.

Bad: *"Let's set up a meeting."*
Good: *"If a 15-min compare-notes makes sense in the next two weeks, here's my Calendly: [link]. Otherwise, no rush at all — just wanted to put this on your radar."*

### 4. Signoff

The executive's standard signoff (from profile). Don't improvise.

## Anti-patterns (do not write)

- *"Hope this email finds you well."* — never. Even in formal voices.
- *"Just circling back…"* — they didn't reach out first; circling back implies they owe you a reply.
- *"As we discussed…"* — paraphrase or reference specifically; "as we discussed" is filler.
- Asking 3+ questions in a follow-up. Ask one or zero.
- Mentioning the executive's company more than twice. The email is about the recipient, not a pitch.
- Generic compliments (*"You're doing great work"*). Specific or omit.

## What gets logged where

- **Brief** → `<output_folder>/<event-slug>/<person-slug>.md` (full structure above)
- **Email draft** → user's email Drafts folder (via Composio)
- **CRM record** → 4 mapped fields (Name / Company / full Brief content / full Email draft content)
- **Per-contact failures** → flagged in the Phase 7 chat summary with plain-language explanation
