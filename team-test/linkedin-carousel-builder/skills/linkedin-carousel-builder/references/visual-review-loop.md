# Visual Review Loop

This document covers step 10 of the linkedin-carousel-builder pipeline. The visual review loop is the **last quality gate** before packaging the PDF: broken slides discovered here either get regenerated (up to 2 attempts each) or are surfaced to the user in the final run message. The loop runs after step 9 (HTML→PNG render) and before step 11 (companion post copy) and step 12 (PDF packaging).

## Inputs

- `slides/slide-NN.png` — rendered slide PNGs from step 9 (one per slide, 1080×1350 portrait).
- `illustrations/slide-NN.png` — raw illustration PNGs from step 8 (only present for illustrated slides; recap and CTA are typography-only).
- `contact-sheet.jpg` — a single grid image assembled fresh at the start of step 10 by tiling every `slides/slide-NN.png` in slide order. This is the artifact the LLM reads in the LLM-driven checks.
- The locked brand profile from step 3 — accent color hex(es), font families, and the chosen art-style preset.
- The finalized slide plan from step 7 — per-slide headline, supporting line, visual intent, and alt-text.

## Programmatic checks

Programmatic checks are deterministic Python validations that run against the rendered HTML and PNG artifacts. They flag mechanical failures the LLM should not be asked to judge.

- **Text-overflow detection.** The HTML render captures the bounding box of every text element (headline, supporting line, footer, slide number). Python compares each box against its slot dimensions in the template. Any element whose rendered box exceeds its slot is flagged as text-overflow on that slide.
- **Missing-file check.** For every slide N in the plan, verify `slides/slide-NN.png` exists and is non-zero-byte. For every illustrated slide, verify `illustrations/slide-NN.png` exists, is non-zero-byte, and opens as a valid PNG (catches truncated downloads from the gpt-image-2 call). Either failure flags the slide as missing-file.
- **Word-count re-validation.** Re-counts each slide's headline (≤8 words) and supporting line (≤15 words). This is a backstop for atlas-carousel-methodology rules 3 and 4 — the first enforcement happens in step 7, and this check catches any drift introduced between step 7 and the rendered output. An over-cap headline or supporting line flags the slide as word-count-fail.

All three checks return a structured per-slide verdict (`pass` or `fail` + failure type) that feeds into the regenerate logic.

## LLM-driven checks

LLM-driven checks are model calls that judge things deterministic code cannot — color fidelity, illustration intent, art-style consistency. The split between programmatic and LLM-driven checks is deliberate: programmatic checks stay cheap and deterministic; LLM checks handle the visual-judgment work.

**Inputs to the LLM call:**

- `contact-sheet.jpg` (the LLM reads the image directly).
- The locked brand profile (accent color hex, font families, art-style preset).
- The per-slide alt-text and visual intent from the slide plan.

**Per-slide questions the LLM is prompted with:**

- "Is the brand accent color visible on slide 3?" (color fidelity — confirms the chosen accent actually appears on each slide, not just in the footer).
- "Does the illustration on slide 4 match its visual intent of 'show the 25× gap'?" (concept fidelity — confirms the gpt-image-2 output drew the right idea, not a generic decoration).
- "Is the art-style consistent across slides — for example, no `clean-saas` illustration mixed into a `hand-drawn-marker` carousel?" (style fidelity — catches a single off-style image that breaks the set).
- "Are the colors on each slide consistent with the brand palette, or has the palette drifted on any slide?" (palette drift — catches off-brand color casts introduced during illustration generation).

The LLM returns a structured per-slide verdict (`pass` or `fail` + failure type + one-line reason). Failure types map to the regenerate logic below: `bad-illustration`, `wrong-colors`, or `style-mismatch`.

## Regenerate logic

Each failure type maps to a specific fix action. The action picks the cheapest artifact to re-do — for example, a color problem usually means re-rendering the slide, not regenerating the illustration.

| Failure type | Source of failure | Fix action |
|---|---|---|
| `text-overflow` | Programmatic | Re-render the slide. Layout/typography is what failed; the illustration is fine. |
| `missing-file` (slide PNG) | Programmatic | Re-render the slide. |
| `missing-file` (illustration PNG) | Programmatic | Re-call `gpt-image-2` with the same prompt to regenerate the illustration, then re-render the slide. |
| `word-count-fail` | Programmatic | Skip retries (0 attempts, not 2) and surface in the final user message immediately. A re-render won't fix a slide-plan word-count drift, so retrying is wasted cost — the user needs to edit the slide plan and re-run the affected step. The run still packages the PDF and continues, same as any other capped slide. (Rule 3 / rule 4 enforcement.) |
| `bad-illustration` | LLM | Regenerate the illustration via `gpt-image-2` with the same alt-text prompt plus the brand art-style fragment, then re-render the slide. |
| `wrong-colors` | LLM | Re-render the slide with a fresh read of the brand profile. Cheaper than regenerating the illustration; the illustration is rarely the source of color drift. |
| `style-mismatch` | LLM | Regenerate the illustration via `gpt-image-2` with the brand art-style fragment re-applied, then re-render the slide. |

After any fix action, the affected slide is re-checked through both programmatic and LLM-driven passes. The contact sheet is rebuilt for the LLM pass so the model sees the updated slide in context.

## Two-attempt cap

Each broken slide gets **at most 2 regeneration attempts**. After the second failure, the slide ships as-is and is surfaced to the user in the final run message with the specific failure type and reason.

The cap exists to prevent infinite loops on prompts the model cannot satisfy (e.g., an alt-text intent that gpt-image-2 reliably misreads, or a brand palette the chosen template fights). Burning more attempts costs OpenAI dollars without improving the outcome — better to ship the run, surface the problem, and let the user decide whether to redo with a different angle.

The cap is per-slide, not per-run. A run with three different broken slides can use up to 6 total regeneration attempts (2 per slide).

## How issues are surfaced in final user message

Per spec §6 "Final user message," the run ends with a plain-language summary. Capped-out slides land in the warnings section. The run does NOT halt for capped slides — the PDF still packages, the user sees the warnings, and the user decides whether to redo the run or accept the result.

Final message structure:

- Full path to `carousel.pdf` and `post-copy.md`.
- One-sentence description of what was made.
- Any warnings flagged during the run that weren't blockers.

Each warning names the slide number, the failure type, and a one-line user-facing reason in plain language. Example:

> Heads up: slide 4 hit the regeneration cap. The illustration didn't clearly show the 25× gap after two attempts — you may want to redo this run with a different visual angle, or accept the slide as shipped.

Warnings are listed inline in the final message, not buried in a log file. The user sees them in the same place they see the PDF path, so they can act on them immediately.
