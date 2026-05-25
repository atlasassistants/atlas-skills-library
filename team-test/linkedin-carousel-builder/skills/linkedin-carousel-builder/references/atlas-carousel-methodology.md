# Atlas Carousel Methodology

This document captures the opinionated Atlas methodology for building LinkedIn carousels. It is loaded on demand by the editorial-review step and the slide-plan-validation step in the linkedin-carousel-builder pipeline. Each rule is derived from the 2026 LinkedIn carousel research brief; supporting evidence lives in that brief. Clients fork the plugin and edit this file to customize the methodology — the skill body itself stays stable.

## The 16 craft rules

### 1. One idea per slide

Each slide carries exactly one idea. If a slide tries to make two points, split it or cut the weaker one. Multi-idea slides force the reader to slow down and parse, which is exactly what kills swipe-through.

### 2. Adaptive slide count 7–10, content-driven, default 8–9, padding forbidden

The carousel length is elastic within the 7–10 band and is dictated by the strength of the source, not by a target number. A weak slide gets cut, not filled with filler. The default sweet spot is 8–9 slides. Padding to hit a quota is forbidden; if the source can't carry 7 strong slides, the run halts (see "Thin-source handling" below).

### 3. Cover headline 6–10 words; body slide headline ≤8 words; supporting line ≤15 words

Length caps are non-negotiable. The cover headline is 6–10 words — short enough to read at a glance, long enough to set up a stake. Body slide headlines are at most 8 words. Supporting lines are at most 15 words. Anything longer gets rewritten or cut.

### 4. Title case headlines, sentence case body

Headlines use Title Case (each significant word capitalized). Body / supporting lines use sentence case (only the first word and proper nouns capitalized). This contrast helps the reader's eye separate the punch from the elaboration.

### 5. One brand accent color used consistently; two fonts maximum

A single brand accent color carries through every slide. The carousel uses at most two fonts (typically one display for headlines, one for body). More than two fonts or shifting accent colors reads as template-soup and undermines trust.

### 6. No emojis anywhere

No emojis on carousel slides, in the post copy, in the cover — nowhere. This is house style. It keeps the carousel safe across industries and seniority levels, and it forces the writing to carry the tone.

### 7. "You" voice — direct address to the reader, not third person

Speak to the reader directly: "you," "your." Avoid "the executive," "the user," "people," "leaders," etc. Direct address pulls the reader through; third person creates distance.

### 8. Concrete > abstract — specific numbers, named entities, named outcomes

Generic claims get rewritten as concrete ones. Use specific numbers, named companies / products / people, and named outcomes. "Increase productivity" becomes "saves 4 hours a week" or "what Stripe did to cut onboarding from 6 weeks to 9 days." Abstract advice slides are the leading cause of weak carousels.

### 9. Each core-idea slide leaves a question the next slide answers

Tension carries the scroll. Every core-idea slide should set up a question the next slide pays off. This is the rule that distinguishes a sequence from a list. The cover, stake/proof, recap, and CTA slides are exempt — they do other jobs.

### 10. Slide number in a corner so the reader sees the roadmap

A small slide number ("2/9," "3/9," etc.) lives in a corner of every slide. The reader sees the roadmap at a glance and is more likely to swipe through to the end.

### 11. Brand mark / handle in the footer of every slide

The brand handle and a small brand mark sit in the footer of every slide. This trains recognition over time and protects the carousel from being decontextualized when screenshotted and reshared.

### 12. Final slide: explicit save + follow ask + specific comment-trigger word

The CTA slide makes three specific asks: save the carousel, follow the account, and comment with a specific trigger word ("comment STRATEGY for the playbook," not "comment below"). The trigger word is concrete and tied to a payoff. Generic "let me know what you think" CTAs are forbidden.

### 13. Cover-angle step generates 3–5 candidate hooks across four formulas

The cover slide is decided by a dedicated cover-angle step. That step generates 3–5 candidate hooks spanning four formulas — numbered list, bold claim, question, contrarian. The editorial step picks the strongest candidate. Single-shot covers are forbidden; the candidate set is the quality bar.

### 14. Companion post copy is 150–300 characters, hook in the first ~140 chars

The companion LinkedIn post is 150–300 characters total. The strongest hook lives in the first ~140 characters because that's the mobile "see more" cutoff. Post copy is pulled from the source's own language — it never summarizes the carousel (which kills the swipe-through incentive).

### 15. At least one mid-carousel pattern-interrupt slide

Drop-off compounds across the carousel. To defend against it, at least one mid-carousel slide is a deliberate pattern-interrupt — a big stat, a comparison layout, a visual surprise — that breaks the rhythm and re-engages the reader. It's folded into a core-idea slot, not added on top.

### 16. Editorial specificity check — body slides only

Every body slide (the core-idea slides and the stake/proof slide) is run through a specificity check. Body slides using generic advice without a number, named entity, or specific outcome are rewritten using source-article language or cut entirely. Slide count is elastic; padding is forbidden — cutting is the right answer when a slide can't be made specific. The cover and CTA slides are evaluated against their own rules (rules 13 and 12 respectively), not against rule 16.

## Slide architecture: AI illustration is the hero, HTML is chrome

Every slide is two visual layers, and the split is deliberate.

**Layer 1 — the AI illustration (the hero).** gpt-image-2 generates one image per slide that needs one. The image carries the slide's actual visual punch: the chart, the diagram, the metaphor, the stylized callout. Crucially, **the data and labels that matter live inside this image, rendered in the art-style's own typography**. Numbers like "88%", labels like "Problem / Signal / Action", row headers like "WHAT HURTS / WHAT PROVES IT / WHAT TO DO" — these are baked into the artwork, not laid over it. The art style (hand-drawn marker, documentary noir, pastel diagram, etc.) determines how those baked-in words look. This is why the slide feels designed rather than templated.

**Layer 2 — HTML chrome (the frame).** Rendered locally by Playwright/Chromium from a Jinja template. Carries the things that must be precise and consistent across every slide: a short summarizing headline (~44px, not the visual hero), the supporting line, the slide number ("3/8"), the brand mark, and the LinkedIn handle. Brand colors flow into this layer via CSS. Brand fonts apply here on a best-effort basis (system fonts only, no bundling in v1).

**Why this split.** Letting the AI generate the entire slide (typography included) is tempting — it would make every slide aesthetically coherent. But it costs ~8× the API spend per carousel, takes ~8× the wall-clock time, and surrenders precise control over things that absolutely cannot drift: the user's exact handle, slide numbering, brand-color hex codes, the exact wording the editorial pass settled on. Letting the AI handle the creative middle while HTML guarantees the chrome gives us both: art-style coherence where the eye lands, and predictable precision where the brand depends on it.

**What this implies for editorial work.** When planning a slide, the slide-plan output must include both a chrome `headline` (the summarizing line shown in HTML) AND an `embedded_message` field — the 1–5 short labels, numbers, or callouts the illustration should render inside the artwork. The illustration prompt template consumes `embedded_message` and instructs gpt-image-2 to incorporate it into the composition.

## The visual rule

> Every illustrated slide's image represents the underlying concept (data, contrast, idea) — not decoration — AND uses the chosen brand art style's creative vocabulary (arrows, callouts, hand-drawn marks, characters, scribbles, layered elements) to feel hand-crafted, not template.

**All 9 slides default to illustrated.** The cover, recap, and CTA slides each get a focused, simple illustration that reinforces their job — a single iconic visual for the cover (e.g., the brand's "pivot" metaphor), a checklist or summary diagram for the recap, an action-cue icon (bookmark, arrow) for the CTA. **Typography-only is the fallback**, not the default: use it only when the visual would dilute the message (rare — empirically, a well-chosen illustration always strengthens cover/recap/CTA presence on LinkedIn's feed).

This rule sits alongside the 16 craft rules and is enforced by the visual-review step.

## Slide skeleton (elastic 7–10)

```
1.    Cover                              — hook (6–10 words) + focused iconic illustration of the pivot/idea
2.    Stake / proof slide                — number, stat, or visual that earns the next slides
3–N.  Core ideas                         — one idea per slide, ≤8-word headline + ≤15-word supporting line +
                                           meaningful illustration in brand art style
M.    Mid-carousel pattern-interrupt     — big-stat / comparison / visual surprise (folded into a core-idea slot)
N+1.  Recap                              — all core ideas in one glance + checklist/summary illustration
N+2.  CTA                                — save + follow + specific comment-trigger + action-cue icon (bookmark, arrow)
```

**Cost note.** Default-illustrated means 9 OpenAI image-gen calls per run instead of 6 — roughly $0.54/run vs $0.36/run at current gpt-image-2 pricing. The visual lift is worth the 50% cost increase for most production carousels. Users who explicitly want typography-only cover/recap/CTA can override by leaving `visual_intent` empty for those slides in `slide-plan.md` before Step 8 runs — `render_slide.py` handles the no-illustration case.

- Minimum 7 = cover + stake + 3 core ideas + recap + CTA.
- Maximum 10 = cover + stake + 6 core ideas + recap + CTA.

The pattern-interrupt slide (rule 15) is folded into one of the core-idea slots — it does not add a slide to the count.

## Thin-source handling

If the source content is too thin for 7 strong slides (e.g., a 200-word LinkedIn post with a single idea, or a 2000-word article of generic advice where the specificity check kills 6+ slides), the skill **fails loudly with a plain-language message and does not produce a weak carousel**. The message shown to the user is verbatim:

> "This source has too few distinct, specific ideas for a strong carousel. A LinkedIn carousel works best with a longer or more specific source (e.g., a detailed article, a structured newsletter, or a transcript). You can: (a) provide a longer or more specific source; (b) paste additional context into the conversation to flesh out the ideas; or (c) cancel this run. I won't ship a carousel with padding or generic-advice slides."

**Halt threshold:** the editorial-review step counts body slides surviving the specificity check (rule 16). If that count falls below 5 — which would give fewer than 7 total slides once cover + stake + recap + CTA are added — the run halts and the message above is shown. There is no fallback shorter carousel. Padding is forbidden, and shipping below the LinkedIn 7-slide sweet spot is also forbidden.

## How this is enforced

Each rule is enforced by one or more steps in the 12-step pipeline. The table below points each rule at the step responsible for catching violations.

| Rule | Enforced by |
|---|---|
| 1 — One idea per slide | Step 6 editorial review |
| 2 — Adaptive slide count 7–10, padding forbidden | Step 5 strategy + cover-angle lab; Step 6 editorial review |
| 3 — Headline / supporting-line length caps | Step 7 slide-plan validation |
| 4 — Title case headlines, sentence case body | Step 7 slide-plan validation |
| 5 — One brand accent color; two fonts maximum | Step 3 theme / brand selection; Step 9 render HTML carousel |
| 6 — No emojis anywhere | Step 7 slide-plan validation; Step 11 companion post copy |
| 7 — "You" voice | Step 6 editorial review |
| 8 — Concrete > abstract | Step 6 editorial review |
| 9 — Each core-idea slide leaves a question the next answers | Step 5 strategy + cover-angle lab; Step 6 editorial review |
| 10 — Slide number in a corner | Step 9 render HTML carousel |
| 11 — Brand mark / handle in footer | Step 9 render HTML carousel |
| 12 — Final-slide CTA structure | Step 6 editorial review |
| 13 — Cover-angle candidate set (3–5 hooks, four formulas) | Step 5 strategy + cover-angle lab |
| 14 — Companion post copy 150–300 chars, hook in first ~140 | Step 11 companion post copy |
| 15 — Mid-carousel pattern-interrupt slide | Step 5 strategy + cover-angle lab; Step 6 editorial review |
| 16 — Specificity check (body slides) | Step 6 editorial review |
| Visual rule — concept-representing illustration in brand art style | Step 8 generate illustrations; Step 10 visual review loop |
