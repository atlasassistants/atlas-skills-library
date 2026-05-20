# Visual Rule

This doc governs how illustrations are conceived, scoped, and prompted for every carousel the plugin produces. It is read by two consumers:

- The **skill body** when authoring per-slide visual intent during slide planning.
- The **image-generation script** (`generate_illustration.py`) when assembling the final prompt sent to `gpt-image-2`.

If the skill is unsure whether a slide earns an illustration, or how to phrase a visual intent, the answer lives here.

---

## The core rule

> Every illustrated slide's image represents the underlying concept (data, contrast, idea) — not decoration — AND uses the chosen brand art style's creative vocabulary (arrows, callouts, hand-drawn marks, characters, scribbles, layered elements) to feel hand-crafted, not template. Slides that don't earn a visual (recap, CTA) stay typography-only.

Two halves, both required. Either half alone fails the rule:

- A perfectly on-brand image that doesn't represent the slide's concept is decoration.
- A concept-faithful image rendered in a generic stock-asset style is templated and forgettable.

The job is **concept × craft**, every illustrated slide.

---

## What "represents the concept" means

The visual is the argument, not the wallpaper. Read the slide's headline and supporting line, identify the single most-load-bearing idea, and find the visual form that idea would naturally take if a designer were drawing it from scratch on a whiteboard. A few worked examples:

- **"The 25× gap"** — the slide claims one thing is 25 times bigger than another. Visual: a bar chart with two bars at wildly different heights and a curved-arrow callout labeling the gap. Not a generic chart icon — the actual proportions.
- **"Before vs after"** — the slide contrasts two states. Visual: a vertically- or horizontally-split frame with the "before" state on one side and the "after" state on the other, clearly differentiated by color or treatment.
- **"The framework"** — the slide names a 3-part or 4-part model. Visual: a labeled diagram (boxes, arrows, hub-and-spoke, layered pyramid — whichever fits the model's logic), with each part visually distinct.
- **"The trade-off"** — the slide names two competing forces. Visual: a see-saw, scales, or tug-of-war frame with the two forces on either side.
- **"The funnel"** — the slide names a narrowing process (leads to customers, applicants to hires). Visual: stacked narrowing rectangles or a literal funnel shape, each stage labeled with the drop-off.

Pattern: identify the geometric or relational core of the claim (gap, split, structure, balance, narrowing) and let the visual *be* that shape. Never default to a stock-icon metaphor (a lightbulb for "idea", a rocket for "growth") — those are decoration in costume.

---

## What "creative vocabulary" means per art style

Each of the seven built-in art-style presets has a distinct visual vocabulary — the specific marks, treatments, and layout moves that signal "this style, hand-crafted by someone with taste" rather than "generic AI render". When the script assembles a prompt, the brand art-style fragment loads this vocabulary in.

**`clean-saas`** — flat vector, generous whitespace, one bold accent color against a near-neutral background. Visual marks: geometric icons with sharp corners or perfect arcs, thin labeled arrows, simple grid alignment, no gradients. Think Stripe / Linear / Notion marketing pages. The hand-crafted feel comes from confident negative space, not flourish.

**`editorial-magazine`** — magazine layout sensibility, serif headline pairings, photographic crops or restrained illustration, muted prestige palette. Visual marks: photographic accents (sometimes desaturated or duotone), pull-quote treatments, generous margins, asymmetric balance. Think HBR / Economist long-form. The craft comes from typographic restraint and editorial pacing.

**`pastel-diagram-marker`** — structured diagrams rendered in soft pastel-marker treatment. Visual marks: hand-drawn-style frames around boxes, marker-textured fills in soft pinks/greens/blues, looping arrows with slight wobble, handwritten-style annotations on the side. Framework- and data-heavy content reads playful but still organized.

**`hand-drawn-marker`** — hand-drawn marker sketches, deliberately less polished. Visual marks: scribbled callouts and underlines, lo-fi character sketches or stick figures, marker bleed at edges, off-square frames, handwritten labels. The craft is in the imperfection — too clean breaks the style.

**`documentary-noir`** — dark, high-contrast, grainy, photojournalism feel. Visual marks: black-and-white or heavily desaturated photographic crops, harsh shadows, halftone or film-grain texture, white sans-serif labels overlaid on dark images, narrow accent color used sparingly for emphasis. Best on serious or contrarian topics.

**`midnight-editorial`** — polished dark editorial vector. Single clean focal subject on a solid dark background, no glow or atmospheric effects. Visual marks: flat vector composition with one product surface or abstract data shape, accent color used as a focal highlight (a UI element, an underline, a status pill) against neutral surfaces, generous negative space, soft shadow grounding under the focal subject. Think Stripe / Linear / Vercel landing-page aesthetic with the polarity flipped. Best for strategy frameworks, product launches, financial topics, and investor-facing content where a dark brand signals seriousness without sliding into moody photo aesthetics.

**`bold-flat-corporate`** — restrained geometric flat design, no flourish, no scribble. Visual marks: pure flat shapes, two- or three-color palette in conservative tones (navy, charcoal, single accent), thick clean lines, axis-aligned layouts, no texture. Reads as professional and trustworthy for finance / law / government.

---

## When to skip an illustration

Every slide is **illustrated by default** — cover, body, recap, and CTA. Typography-only is the fallback, not the default. There are three documented exceptions where leaving `visual_intent` blank is the right call (see `editorial-review.md` § Step F):

1. **The source genuinely lacks a visual hook** that fits the slide's headline or job. Rare.
2. **The brand's `hard_bans` rule out** any illustration aesthetic that would work for the slide.
3. **The user explicitly requests typography-only** via override for a specific slide.

In any of these cases, the template's `.typography-only` class renders the slide at 88pt centered (cover gets 80pt via `.cover` class). The slide still reads as intentional, not bare.

**For recap and CTA specifically**, the default illustrations are restrained on purpose: the recap's illustration is a focused summary visual (a hand-drawn checklist with the core component labels, or a stacked-layer diagram showing the architecture in one frame); the CTA's illustration is a single action-cue icon (a hand-drawn bookmark, a curved arrow) with the comment-trigger word as the embedded message. Both follow the same ≤5-element discipline as body slides — they amplify the recap-and-ask job, they don't compete with it.

---

## Prompt construction for `gpt-image-2`

The image-generation script (`scripts/generate_illustration.py`) loads one art-style template per call and substitutes five named placeholders into it. There is no separate aspect-ratio fragment and no no-text directive — the art-style template owns aspect, brand-color enforcement, and the in-artwork text policy. Output size is **1024×1024 square** for every illustration.

### The template

The script loads the prompt template from `assets/art-styles/<slug>/prompt-template.txt` for the chosen built-in art-style preset, or from the brand profile's `art_style_prompt` field if the brand uses a custom style. Each template encodes the visual vocabulary for its style (clean-saas, editorial-magazine, pastel-diagram-marker, hand-drawn-marker, documentary-noir, bold-flat-corporate, midnight-editorial), plus four standing clauses that every shipped template carries:

- **Brand-color enforcement** — the template asserts `{accent_name} ({accent_color})` as the dominant chromatic and restricts other colors to `{background_color}`, neutrals, and soft greys.
- **Brand marks and app icons** — when the visual intent names a real app or company, the template instructs the model to render an abstract neutral category icon (an envelope for email, a calendar grid for scheduling) rather than the company's actual logo. Same clause across all art styles, per the global BRAND MARKS policy.
- **Text in the image** — the model may render text *only* (a) inside the embedded annotation, or (b) as a concrete label explicitly named in the visual intent. Invented UI text, fabricated metrics, and made-up button labels are forbidden. This is why there is no no-text directive: the embedded_message is the *intended* text in the artwork.
- **Embedded annotation rules** — the template instructs the model to render `{embedded_message}` exactly once inside the artwork as a label native to one of the surfaces (a card title, a row label, a marker note), spelled exactly as provided, not duplicated elsewhere.

### The five substitution placeholders

| Placeholder | Source | Notes |
|---|---|---|
| `{accent_color}` | `brand.colors.accent` | Hex string. Required. |
| `{accent_name}` | `brand.accent_name` | Falls back to `"the brand accent"` when empty. |
| `{background_color}` | `brand.colors.background` | Hex string. Required. |
| `{visual_intent}` | per-slide, from `slide-plan.md` | The one-sentence description of what the illustration must show (one focal element, ≤5 sub-elements). |
| `{embedded_message}` | per-slide, from `slide-plan.md` | The 1–5 short labels (≤30 chars) the template renders inside the artwork as a native UI label or marker note. The script rejects an empty `embedded_message` when `visual_intent` is non-empty — otherwise the model substitutes literal `visual_intent` text as the in-artwork annotation, producing metadata-as-art. |

### Worked input examples

These are the per-slide inputs (`visual_intent` + `embedded_message`) the orchestrator writes into `slide-plan.md`. The art-style template wraps them with the brand-color, brand-mark, and text-policy clauses above before sending to `gpt-image-2`.

**A "25× gap" slide:**
- `visual_intent`: *"A horizontal bar chart with two bars: a short bar on the left, and a bar 25 times taller on the right. A curved arrow between the two bars indicates the gap. Single focal element."*
- `embedded_message`: *"25× gap"*

**A "before vs after" slide:**
- `visual_intent`: *"A vertically split frame: the left half shows a tangled, chaotic scribble; the right half shows a clean, organized arrangement of the same elements."*
- `embedded_message`: *"Before / After"*

The script does not log the fully-assembled prompt to disk. To inspect what was sent to the model, run the per-slide step manually or add a print of the `prompt` variable in `_build_prompt` during a debug run.
