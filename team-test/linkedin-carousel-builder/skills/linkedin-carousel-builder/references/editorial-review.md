# Editorial Review

This doc covers step 6 of the pipeline (editorial review). It is the most rules-heavy step in the whole pipeline — ten of the 16 craft rules (1, 2, 3, 4, 7, 8, 9, 12, 15, 16) are directly enforced here. The step turns `brief.md` plus a chosen cover hook into a finalized `slide-plan.md`.

## Inputs

- **Cover slide entry from the cover-angle lab.** The chosen hook, formula tag, runner-up hooks, alt-text intent, and (optionally) the source-language quote that motivated the hook — written into `slide-plan.md` by step 5. See `cover-angle-lab.md`'s "What goes in slide-plan.md after this step" section for the exact entry shape.
- **`brief.md` from the source-intake step.** Title, full body text, key quotes pulled, detected language, and (optional) author. See `source-intake.md`'s "Brief.md structure" section for the field list.

The editorial step has **read access** to the brand profile (audience, voice, accent color, fonts) so it can keep slide language consistent with the executive's voice. It does **not** alter the brand profile — brand capture is a separate step (step 3) and is out of scope here.

## Step A: outline core ideas from source content

The LLM is given the full body of `brief.md` and asked to enumerate the distinct ideas the source actually carries. Three guards apply:

- **Deduplicate paraphrases.** If the source restates the same idea in three different paragraphs, collapse those into one idea. The output is distinct ideas, not paragraph counts.
- **Count expectations.** Aim for 6–9 distinct ideas. The slide skeleton is elastic at 7–10 slides total (cover + stake + 3–6 core ideas + recap + CTA per rule 2), and the pattern-interrupt slot in Step C folds into a core-idea slot rather than adding a slide. Six to nine distinct ideas gives Step B and Step D enough material to survive cuts without padding.
- **No ideas about ideas.** Reject meta-takes like "we should think more about X" or "the field needs to reconsider Y." Every enumerated idea has to be a concrete claim, observation, or instruction from the source — not a frame around the source.

The output of Step A is a numbered list of distinct ideas, each one short enough to fit on a slide.

## Step B: assign one idea per slide, write headline + supporting line

One idea per slide (rule 1). Each body slide gets a headline plus one supporting line. The cover already exists from step 5; Step B writes body slides starting at slide 2 (the stake / proof slide) and continuing through the core-idea slides.

Constraints applied per slide:

- **Rule 3 length caps.** Body slide headline ≤8 words. Supporting line ≤15 words. Anything longer is rewritten or trimmed before it goes into `slide-plan.md`.
- **Rule 4 case rules.** Headlines use Title Case (each significant word capitalized). Supporting lines use sentence case (first word and proper nouns only).
- **Rule 7 "you" voice.** Direct address only. "You," "your." Strip "the executive," "the user," "leaders," "people," and similar third-person framings.
- **Rule 8 concrete > abstract.** Each slide names a number, a named entity, or a concrete outcome. Generic verbs ("grow," "improve," "leverage") without a specific object trigger a rewrite in Step D.
- **Rule 9 question→answer tension.** Each core-idea slide leaves a question the next slide answers — that's what carries the scroll. After drafting body slides, read them in order and check that each pair has the setup→payoff shape. If two adjacent slides both make a closed statement with no thread to the next, rewrite the earlier one to open a question, or reorder the sequence so the tension chains. Stake/proof, recap, and CTA slides are exempt (per the methodology doc) — they do other jobs.

One idea per slide also means **no compounding** — if a draft headline says "Cut meetings and protect deep work," Step B splits it into two slides or cuts the weaker half. Compound headlines are the most common rule 1 violation.

Step B also tags each slide with the rules that apply to it (so the slide-plan validation step in step 7 has a checklist). Tags use the rule numbers from `atlas-carousel-methodology.md` — e.g., a core-idea slide carries tags `1, 3, 4, 7, 8, 9, 16`.

## Step C: place the mid-carousel pattern-interrupt slot (rule 15)

At least one mid-carousel slide is a deliberate pattern-interrupt — typically slide 4–6 in a 7–10 slide carousel, where drop-off starts to compound. This slot is **required** in every carousel of 7+ slides (rule 15). It is folded into a core-idea slot, not added on top, so the slide count stays elastic at 7–10.

The content of the pattern-interrupt slide is the **strongest single signal** from the source: the biggest stat, the sharpest before/after contrast, or the boldest single-line claim. Pulled from `brief.md`'s key quotes or body text, never invented.

Format may break the headline + supporting-line template:

- A single dominant number ("47 → 18 days").
- A split before/after layout with two short lines instead of one headline.
- A one-line bold claim with no supporting text, sized large.

Step C picks which core-idea slot becomes the pattern-interrupt and rewrites that slide's entry in `slide-plan.md` to match the chosen format. The rule 15 tag is added to the slide's rule-tag list.

## Step D: specificity check on body slides (rule 16)

The rule 16 check applies to **body slides only** — the stake / proof slide and the core-idea slides. The cover is evaluated against rule 13 (its own picker criteria) and the CTA against rule 12 (its own structure). Recap is exempt because it just restates already-checked core-idea headlines; the recap's illustration is a checklist or summary visual derived from those same headlines, so it inherits their specificity.

The check, per body slide:

1. Does the slide name a number, a named entity, or a concrete outcome? If yes, the slide passes — move on.
2. If no, attempt **one rewrite** using language pulled directly from `brief.md`'s body or key quotes. Borrow the source author's own words and specifics. If a number, named company, or concrete outcome exists in `brief.md` adjacent to this idea, swap it in.
3. If the rewrite still fails the rule 16 check (no number, named entity, or concrete outcome), **cut the slide entirely.** Slide count is elastic. Padding is forbidden (rule 2). A cut slide is the right answer when the source can't support it.

Cuts are the upstream cause of thin-source halts in Step E — a source with too many cuts can no longer carry 7 strong slides.

## Step E: count post-cut body slides; thin-source halt

After Step D, the editorial step counts how many body slides survived. The slide skeleton (per `atlas-carousel-methodology.md`) requires cover (1) + stake (1) + 3–6 core ideas + recap (1) + CTA (1), with the pattern-interrupt slot folded into one of the core-idea positions. The halt threshold:

- **If body-slide count (post-cut) is 5 or more,** the carousel hits the 7-slide minimum and the run continues to Step F.
- **If body-slide count (post-cut) is fewer than 5,** the total carousel would be under 7 slides. The run halts.

On halt, the user is shown the thin-source failure message. The canonical text of that message lives in `references/atlas-carousel-methodology.md` (see the "Thin-source handling" section there). Do not duplicate the message in this doc — the methodology doc is the single source of truth so future edits stay consistent across both files.

There is no fallback shorter carousel. Padding is forbidden, and shipping below the 7-slide LinkedIn sweet spot is also forbidden.

## Step F: write recap and CTA

Two final slides get written into `slide-plan.md` after the body slides survive Step E. **Both are illustrated by default** (per the visual rule in `atlas-carousel-methodology.md`); typography-only is the fallback, not the default.

**Recap slide.** The chrome content is short — a one-line headline plus the supporting line that lists the core-idea slide headlines as a compressed sentence (e.g., "Workspace. Second Brain. Memory. Integrations."). The illustration is a focused summary visual that reinforces the recap job — typically a hand-drawn checklist with the core component labels, or a stacked-layer diagram showing the architecture in one frame. The visual_intent should describe one focal element (the checklist, the diagram) with ≤5 distinct sub-elements; the embedded_message names the recap concept (e.g., "The Harness").

**CTA slide** — follows rule 12 exactly. Three asks, all explicit:

1. **Save the carousel.** Direct instruction ("Save this for later," "Save this carousel so you can come back to it").
2. **Follow the account.** Direct instruction ("Follow [handle] for more like this").
3. **A specific comment-trigger.** A concrete question or trigger word tied to a payoff. "What's the first one you'll try?" or "Comment PLAYBOOK and I'll send the full template." Generic asks like "Let me know what you think" or "Thoughts?" are rejected.

The CTA's illustration is a single action-cue icon — a hand-drawn bookmark, a curved arrow, or similar — with the comment-trigger word as the embedded message (e.g., embedded_message = "Save" or "PLAYBOOK"). The CTA slide carries the rule 12 tag in its rule-tag list.

**Cover slide illustration** (added during Step 5 cover-angle lab if not already present). The cover gets a single focused iconic illustration of the pivot/idea — for example, if the cover hook is "Stop Chasing AI Tools. Start Building Infrastructure," the cover illustration is a small stack of labeled building blocks (the alternative) beside a discarded tool icon (the rejected option). Same ≤5-element discipline; embedded_message can be blank ONLY for the cover (the headline carries the words), but most covers benefit from a one-word embedded label.

**When typography-only is the right call.** Three exceptions where leaving `visual_intent` blank IS correct:
1. The source genuinely lacks a visual hook that fits the cover headline (rare).
2. The brand's hard_bans rule out any illustration aesthetic that would work.
3. The user explicitly requests typography-only via override.
In any of these cases, the template's `.typography-only` class renders the slide at 88pt centered (cover gets 80pt via `.cover` class). The slide still reads as intentional, not bare.

## Output: slide-plan.md finalized

After Step F, `slide-plan.md` is complete and ready for step 7 (slide-plan validation). The finalized shape:

- **Slide list, in order:** cover (slide 1) + stake / proof (slide 2) + core-idea slides (slides 3 through N, with one of them serving as the pattern-interrupt) + recap (slide N+1) + CTA (slide N+2). Total slides: 7–10.
- **Per-slide entry fields:** slide number; rule-tag list (the rule numbers from `atlas-carousel-methodology.md` that apply to that slide); chosen headline; supporting line (if the slide format has one); visual intent (a one-sentence description of what the illustration should make obvious — should describe **one focal element with ≤5 distinct sub-elements**; only blank in the three typography-only exceptions named in Step F); embedded message (the 1–5 short labels, numbers, or callouts the illustration should render inside the artwork, per the methodology's "AI illustration is the hero" architecture — **REQUIRED whenever visual intent is non-empty; never pass an empty string to `generate_illustration.py` when the visual intent is non-empty**, because the model substitutes literal visual_intent text as the annotation and the result is metadata-as-art); alt-text intent (a one-line accessibility description of what the slide's illustration will show — blank only for typography-only slides).
- **Cover slide entry retained as written by step 5** — Step F does not rewrite the cover, only appends body / recap / CTA entries.

Step 7 (slide-plan validation) runs structured checks against this artifact — length caps (rule 3), case rules (rule 4), no-emoji check (rule 6), embedded-message presence and length (≤30 chars, ≤5 short labels for illustrated slides; blank for typography-only), and the rule-tag completeness check. After step 7 passes, step 8 (illustration generation) reads each slide's visual intent AND embedded message to draft the per-slide image prompts — the art-style template renders the embedded message as a label baked into the artwork.
