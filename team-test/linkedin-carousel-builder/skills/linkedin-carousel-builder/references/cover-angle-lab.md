# Cover-Angle Lab

This doc covers step 5 of the pipeline (cover-angle generation). The cover slide is the only slide whose hook is engineered before editorial review — everything downstream (body slide framing, companion post copy, visual direction) cascades from the chosen cover hook, so it gets its own dedicated step.

## The four hook formulas

LinkedIn carousel research converges on four hook formulas that consistently outperform generic openers. Cover-angle generation must produce candidates across these four; editorial then picks the strongest (rule 13).

### 1. Numbered value

A specific, finite list the reader can mentally scope before opening. Works because the count sets expectation ("I'll learn N things in N slides") and because numbered headlines lift CTR roughly 36% over un-numbered equivalents in industry tests. Odd numbers (7, 9, 11) read as more credible than round numbers — they feel like the result of real counting rather than rounding to a marketing-friendly figure.

Example hooks:
- "7 LinkedIn carousel mistakes killing your reach"
- "9 onboarding emails every B2B SaaS founder gets wrong"
- "5 calendar habits that protect deep work"

### 2. Bold specific claim

A first-person outcome statement that names a number, a timeframe, or a named result. Works because specificity reads as evidence — vague claims trigger skepticism, specific claims trigger curiosity ("how did you actually do that?"). The mechanism reveal lives inside the carousel, so the cover only has to earn the open.

Example hooks:
- "I gained 10K followers in 90 days. Here's how"
- "We cut our hiring cycle from 47 days to 18"
- "$0 ad spend, 2M impressions in Q1 — the playbook"

### 3. Direct question

A second-person question that names a specific pain or mistake the reader recognizes in themselves. Works because the reader has to pause to answer it internally — that pause is the open. Generic questions ("Want to grow on LinkedIn?") fail because the answer is obvious; sharp, specific questions ("Are you making this profile mistake?") trigger the click.

Example hooks:
- "Are you making this profile mistake?"
- "Why does your team keep missing OKR targets?"
- "What if your morning routine is the problem?"

### 4. Contrarian take

A claim that contradicts conventional wisdom in the reader's field. Works because the reader's first reaction is disagreement, and disagreement drives the open ("prove it"). Has to be defensible inside the carousel — a contrarian cover with a soft middle reads as bait. Best used when the author has real evidence or an unusual angle the rest of the field hasn't caught up to.

Example hooks:
- "Hashtags on LinkedIn are a waste of time"
- "Stop doing 1:1s. Do this instead"
- "The four-day week is a productivity tax, not a perk"

## How to generate 3–5 candidates per run

The skill prompts the LLM with a template that takes the source title and a trimmed source body, then asks for 3–5 cover-hook candidates spanning the four formulas. Formula diversity is one of the picking criteria, so the prompt explicitly asks for coverage across at least three of the four formulas (single-formula slates get rejected and regenerated).

Prompt template (the skill substitutes the placeholders before the call):

```
You are drafting LinkedIn carousel cover hooks for the following source.

Source title: {{source_title}}
Source body (trimmed): {{source_body}}

Generate 3–5 candidate cover hooks for a LinkedIn carousel based on this source.

Constraints:
- Each hook is 6–10 words. Reject anything outside this range.
- Each hook must fit within 140 characters (LinkedIn mobile "see more" cutoff).
- No emojis. No insider jargon or acronyms the general LinkedIn reader wouldn't know.
- Plain language. Second-person ("you" / "your") is fine; third person ("the exec") is not.
- Specificity is non-negotiable — name a number, a named entity, or a concrete outcome.
- Cover at least three of these four formulas across your candidates:
    1. Numbered value
    2. Bold specific claim
    3. Direct question
    4. Contrarian take

Output format: numbered list. For each candidate, give the hook on one line and tag the formula in parentheses on the next line.
```

The skill then parses the LLM output into a candidate list with formula tags attached.

## How to pick the strongest

Editorial scores candidates against four criteria, plus a tie-breaker:

- **Specificity** — Does the hook name a number, a named entity, or a concrete outcome? Generic verbs ("grow," "improve," "learn") without an object fail this check. "How I grew my audience" loses to "200 → 12,000 followers in 90 days, no ads."
- **Mobile-readability under 140 chars** — The first ~140 characters of a LinkedIn post are visible before the "see more" cut; the same visual constraint applies to the cover slide's framing on a phone screen. Hooks at or under 140 chars survive the fold; longer ones get cut and the punchline is lost.
- **No jargon** — Plain language only. No insider acronyms, no industry shorthand the general LinkedIn reader wouldn't recognize. If a non-specialist reader has to pause to decode a word, the hook fails.
- **Formula diversity across runs** — If the most recent run for this user used a "numbered value" hook, the picker prefers a different formula this run to keep the user's feed varied. Formula tags are stored in `slide-plan.md` for each shipped carousel so the picker can check history.

Tie-breaker: if two candidates score equally across the four criteria, pick the one whose phrasing most closely echoes the source author's own language — it lands more authentic and is easier to defend inside the carousel.

## Headline word-count enforcement

Cover slide hooks must be **6–10 words**. Hard rule, no exceptions (rule 3).

If the LLM produces a candidate outside the 6–10 word range, the skill rejects it before it reaches the picker and asks for a regenerated candidate in the same formula. Out-of-range candidates are not surfaced to the user — they're filtered silently and replaced.

The slide-plan-validation step (step 7 of the pipeline) re-checks the chosen cover hook against the 6–10 word rule as a backstop, in case an edit or hand-tweak after the cover-angle step pushed the headline out of range.

## What goes in slide-plan.md after this step

This step writes only the cover-slide entry. The editorial review step (step 6 of the pipeline) appends body slides, recap, and CTA. The cover-slide entry has the following fields:

- **Slide number** — always 1.
- **Chosen hook** — the engineered headline, 6–10 words, plain text.
- **Formula tag** — one of: `numbered_value`, `bold_specific_claim`, `direct_question`, `contrarian_take`. Used by future runs to score formula diversity.
- **Runner-up hooks** — the other 2–4 candidates from this run with their formula tags, kept so the user (or a later edit pass) can swap in an alternate without a full regen.
- **Alt-text intent** — illustrated by default. A one-line accessibility description of what the cover illustration will show, drafted alongside the visual intent in the editorial review step. Only blank when one of the three documented typography-only exceptions in `editorial-review.md` § Step F applies (source genuinely lacks a visual hook, brand hard_bans rule out any aesthetic that would work, or user explicitly requests typography-only via override).
- **Visual intent** — illustrated by default. A one-sentence description of the focused iconic illustration that represents the pivot/idea in the cover hook (e.g., for "Stop Chasing AI Tools. Start Building Infrastructure," a small stack of labeled building blocks beside a discarded tool icon). One focal element with ≤5 distinct sub-elements. Only blank under the three exceptions above.
- **Embedded message** — by default, a one-word label baked into the cover artwork; can be left blank for the cover only (the headline already carries the words), but most covers benefit from one. Body slides 2 through N+1 get a non-empty embedded message during editorial review; see `editorial-review.md` § "Output: slide-plan.md finalized" and `atlas-carousel-methodology.md` § "Slide architecture: AI illustration is the hero".
- **Source-language quote (optional)** — if the chosen hook was motivated by a specific phrase or stat from the author's source material, the quote and a source pointer go here. This is the anchor editorial uses to defend the hook if the user questions it.

Everything else in `slide-plan.md` (body slides, recap, CTA, companion post copy) gets filled in by the editorial review step that runs next.
