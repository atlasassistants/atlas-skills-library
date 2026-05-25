# Post-Copy Extraction

This doc covers step 11 of the carousel pipeline — the optional companion LinkedIn post that ships alongside the carousel PDF. The post is opt-in at startup and defaults to yes (rule 14, spec §6 step 2). When generated, the post is **extracted** from the source article's voice — sentences are pulled from `brief.md` and edited only by deletion. The skill never composes prose from a summary of the carousel.

---

## The rule

Verbatim summary of rule 14 (spec §4) and research §8:

- **Length: 150–300 characters total.** Inclusive on both ends.
- **Source-voice extraction.** Every line except the closing tease comes from the source body. Edits are deletions only — no rephrasing, no synthesis, no LLM-generated bridging text. The author's phrasing carries through to the post intact.
- **Hook in the first ~140 characters.** LinkedIn's mobile "see more" cutoff sits at ~140 chars; the strongest specific claim (number, named entity, concrete outcome) must land before that fold or the swipe is lost.
- **The post does not summarize the carousel.** The post teases. The carousel is the payoff. Summary captions ("here's a thread on…", "key takeaways…", "5 lessons learned…") are the most common failure mode in research §8 — they give away the value and kill the swipe.

---

## Step A: pull 8–12 candidate sentences from source

Read `brief.md` body (the normalized source-article text written in step 4 of the pipeline). Score every sentence in the body against three criteria, then pull the top 8–12 candidates into a working list.

Scoring criteria:

- **Contiguous span.** The sentence reads end-to-end as a single thought, with no mid-sentence ellipses, no cross-paragraph references, and no "as shown above / below" deictic that breaks without the surrounding article.
- **Specific-claim density.** The sentence contains at least one number, named entity, or concrete outcome. Generic claims ("this is important," "many companies struggle") score zero on this axis and are skipped.
- **Standalone readability.** The sentence carries its own subject — no orphan pronouns ("it," "they," "this") whose antecedents live in a prior paragraph. A reader seeing only this one line should understand what it is about.

Pull 8–12 candidates (more than the post needs). Step C discards the weaker half — over-pulling at this stage gives the picker headroom to enforce variety and trim the longest candidates first.

---

## Step B: pick the strongest hook from cover-angle runner-ups

Step 5 of the pipeline (cover-angle lab) generated 3–5 candidate cover hooks across four formulas (`numbered_value`, `bold_specific_claim`, `direct_question`, `contrarian_take` — using the canonical tag names from cover-angle-lab) and chose the strongest for slide 1. The runners-up were preserved in `slide-plan.md` under the **Runner-up hooks** field.

The post hook is selected from those runner-ups — **not** from the chosen cover hook. Reasoning: the carousel image already shows the cover hook in large type. Repeating the same line verbatim in the post copy wastes the dual-channel exposure — the reader sees the same hook twice and the post stops earning its keep.

Picking rule: **prefer a runner-up whose formula tag differs from the cover's formula tag.** If the cover used `numbered_value`, prefer a `contrarian_take`, `bold_specific_claim`, or `direct_question` runner-up. Formula variety across the two surfaces (post + cover) keeps the dual-channel exposure compounding instead of stacking. If no off-formula runner-up is available, fall back to the highest-scoring runner-up regardless of formula and note the duplication in `post-copy.md`'s warnings block.

---

## Step C: compress 2–3 supporting lines from source sentences

From the 8–12 candidates pulled in Step A, pick 2–3 to follow the hook. These are the body of the post.

Compression is **deletion only**. Allowed edits:

- Drop filler adverbs: "really," "very," "actually," "basically," "in fact," "essentially."
- Drop modal hedges: "might," "could," "may," "would," "should" — when they soften a claim that the source elsewhere asserts firmly.
- Drop opinion hedges: "perhaps," "arguably," "in my view," "I think."
- Drop parenthetical asides and prepositional tail-clauses that don't carry the claim.

Disallowed edits:

- No rephrasing. If a sentence doesn't work compressed, drop it and pick a different candidate from the Step A list.
- No bridging conjunctions added between sentences. Each line stands on its own.
- No re-ordering of words inside a sentence.

Result: each of the 2–3 supporting lines reads in the source author's voice. The post sounds like the article, not like the skill.

---

## Step D: write the close

This is the **only** line in the post the skill writes itself. Everything in Steps A–C is extracted from the source.

The close is a single short line that gestures at the carousel without describing what's in it. It signals "there's more — swipe" without telegraphing the payoff.

Length: ≤8 words. Plain second-person voice.

Acceptable closes:

- `Walk-through in the carousel.`
- `Full breakdown in the slides above.`
- `Details in the carousel.`
- `The how-to is in the slides.`

Disallowed closes — any line that previews carousel content ("5 lessons inside," "here's the framework," "I broke it down into 7 steps") violates the no-summary rule.

---

## Step E: validate against 150–300 char range and mobile-cutoff hook

Programmatic validation runs after Steps A–D assemble a draft. Every check is a pass/fail; failures block the draft from being written until the picker reruns the failing step.

Checks:

- **Total length in [150, 300] characters, inclusive.** Whitespace and punctuation count. If under 150, the picker re-adds one of the unused Step A candidates. If over 300, the picker drops the weakest supporting line or recompresses a candidate further.
- **First 140 characters contain the strongest specific claim from the hook.** The hook's number, named entity, or concrete outcome must sit before the 140-char fold. If it doesn't, the hook is reordered (move the claim to the front) or replaced with a different runner-up from Step B.
- **No emojis.** Rule 6 backstop — the post copy, like the slides, contains zero emojis.
- **No carousel summary phrases.** A denylist of summary-caption openers blocks the draft if any line contains them: "here's a thread on," "key takeaways," "5 lessons learned," "here's what I learned," "in this carousel," "swipe to see X tips," "I broke it down into," "here are the [N] things." These are the anti-patterns from research §8 — caught here rather than relying on the user to spot them.

If any check fails, the validator returns a specific failure message naming the step to rerun (Step B for hook failures, Step C for length / summary-phrase failures in the body). The draft is not written to disk until all checks pass.

---

## Output: post-copy.md

A plain markdown file the user can copy-paste directly into LinkedIn's composer. No frontmatter, no rendering — the file's body is the post body, ready for the clipboard.

Structure:

```
<!-- hook formula: contrarian_take -->
<hook line — pulled from a Step B runner-up, edited by deletion only>

<supporting line 1 — from Step A candidates, compressed by deletion>
<supporting line 2 — from Step A candidates, compressed by deletion>
<supporting line 3, optional — from Step A candidates, compressed by deletion>

<close line — the only line the skill writes itself>
```

Formatting rules:

- The hook formula tag sits in an HTML comment on the line above the hook, using the canonical tag from cover-angle-lab (`numbered_value`, `bold_specific_claim`, `direct_question`, `contrarian_take`). The comment is invisible when the post is pasted into LinkedIn but visible to anyone reading the file. It exists as a human-readable record of which formula won — useful for the user auditing their own past runs and for a future cross-surface variety check if one is added. The cover-angle picker's existing cross-run variety rule (cover-angle-lab "How to pick the strongest" — formula-diversity bullet) reads cover-hook formulas from `slide-plan.md`, not from this comment.
- **One blank line between the hook and the supporting lines.** LinkedIn renders the blank line as a paragraph break, which gives the hook room to land before the reader hits the fold.
- No blank line between supporting lines — they read as a single block.
- One blank line before the close.

Warnings block (optional, appended after the post body, prefixed with `---`):

If the picker had to fall back to a same-formula runner-up in Step B because no off-formula runner-up was available, append a note: `Cover hook is a {cover_formula} formula; post hook is also {cover_formula} — no off-formula runner-up was available. Consider hand-swapping the post hook for a different line from the article body.` (Substitute the canonical formula tag from cover-angle-lab — e.g., `numbered_value`, `contrarian_take`.) Other notable conditions (e.g., the post landed at exactly 150 or 300 chars — at the edge of the band) are surfaced here too. The warnings block is read but never blocking; the run completes regardless.
