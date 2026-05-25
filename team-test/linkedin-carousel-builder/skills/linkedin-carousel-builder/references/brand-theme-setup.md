# Brand-Theme Setup

This reference governs Step 3 of the carousel pipeline — how a brand profile is created, previewed, locked, and reused across runs. It is the contract that `scrape_brand_site.py` and `parse_design_system.py` produce against, and the contract the renderer reads from at slide time.

## Brand and art-style are independent decisions

Brand identity and art-style are two separate concepts in this skill — do not conflate them.

- **Brand identity** = colors + fonts + footer (handle, brand mark) + audience + voice. Captured once per executive or company. Reused across all their carousels.
- **Art-style** = the visual treatment of illustrations (`clean-saas` flat-vector, `hand-drawn-marker`, `documentary-noir`, and so on). Chosen for each carousel run. The same brand can use different art-styles on different days.

Examples of valid mix-and-match for a single Atlas brand:

- Atlas brand + `clean-saas` art-style → flat-vector geometric illustrations in Atlas colors
- Atlas brand + `hand-drawn-marker` art-style → marker-sketch illustrations in Atlas colors
- Atlas brand + `documentary-noir` art-style → dark grainy illustrations using Atlas's darker palette
- Atlas brand + custom art-style → bespoke style scoped to Atlas brand only

The brand profile JSON stores a default `art_style` used unless the user overrides, but every carousel run prompts for an art-style switch before generation starts. Art-style is picked separately from brand identity and can be overridden per run without touching the saved brand.

## The six creation paths

There are six paths to create a brand profile. Each captures **brand identity only** — colors, fonts, footer, audience, voice. The art-style is picked in a separate downstream step (see "Art-style picker" below) and is independent of how brand identity was created.

1. **Built-in starter preset.** Pick the built-in starter preset (`default-cream`) shipped with the plugin. Fastest path to a first carousel. The starter bundles a suggested art-style that populates the brand's saved default, but the art-style picker still runs as a separate downstream step — the user can switch the default or pick a different style for this run. Captures brand identity only; art-style is still a separate downstream decision.
2. **From a website URL.** `scrape_brand_site.py` extracts dominant colors, fonts, and visual signals from the live site. The skill proposes a profile and the user confirms. Captures brand identity only; art-style is picked separately.
3. **From description.** The skill asks for audience (2–4 words), brand feel (2–4 words), and hard bans, then generates a profile from the answers. Captures brand identity only; art-style is picked separately.
4. **From screenshots or reference assets.** The user shares 1–3 reference images. The skill extracts signals and proposes a profile. Captures brand identity only; art-style is picked separately.
5. **From a structured design system file** — W3C tokens JSON, a folder containing `colors.json` + `typography.json` + optional `style-guide.md`, or a brand-guidelines PDF. `parse_design_system.py` extracts colors and fonts; the skill proposes a profile and the user confirms. Best when you have one of those three formats; for CSS + markdown design systems, use path 6 instead.
6. **Point me at a folder, repo, or file (host-LLM extraction).** When the user has brand source files in less-structured formats (CSS custom properties, markdown design docs, Tailwind config, Figma exports), the skill reads the files directly and proposes a brand profile. No script — extraction is done by the orchestrator and validated by the user before save. Best when the brand publishes its design system as CSS + markdown (the common case for modern design systems). See "From a folder, repo, or file" below for the subflow.

## URL scrape low-confidence fallback

The URL path must never silently produce a wrong-colored brand. If `scrape_brand_site.py` returns low-confidence results — too few colors detected, no usable fonts found, dominant-color match is grey/white/black only, or stylesheet parsing fails — the skill does not save the half-extracted profile. It surfaces both fallback paths and asks the user to pick:

> I couldn't reliably extract a brand from that URL. You can: (a) share 1–3 screenshots of the website (or your existing brand assets) and I'll build the brand from those, or (b) walk through 3 quick questions — audience (2–4 words), brand feel (2–4 words), and any hard bans — and I'll build it from your answers. Which would you like?

Screenshots is listed first because visual evidence is more reliable than user descriptions; the walkthrough is offered as a peer option (not buried) for users without easy screenshot access. Both paths land at the same downstream artifact: a brand profile JSON the user can review and refine.

## Design system path parsing

`parse_design_system.py` accepts three input shapes:

- A **W3C Design Tokens JSON file** (`design-tokens.json`) — parsed directly for color and typography tokens.
- A **folder** containing some combination of `colors.json`, `typography.json`, `logo.svg`, and `style-guide.md` — parsed by reading each file and merging the signals.
- A **brand guidelines PDF** — text and embedded image swatches are extracted and mapped to color and font fields.

If the file or folder cannot be parsed (unrecognized format, no colors found, no fonts found), the skill surfaces both fallback paths and asks the user to pick — same shape as the URL fallback, with the noun adjusted to fit the input the user gave:

> I couldn't reliably extract a brand from those files. You can: (a) share 1–3 screenshots of your brand assets and I'll build the brand from those, or (b) walk through 3 quick questions — audience (2–4 words), brand feel (2–4 words), and any hard bans — and I'll build it from your answers. Which would you like?

## From a folder, repo, or file (host-LLM extraction)

Path 6 is the catch-all for brand identity that doesn't fit the three structured shapes path 5 supports. The orchestrator reads the user's files directly and proposes a brand profile JSON. No parsing script runs. The schema validator (`brand_profile_schema.py`) is the deterministic save-time gate; the user-confirmation step over a citations-annotated proposal is the human gate.

### Read step

When the user supplies a path:

- Walk the path. Read files matching: `*.css`, `*.scss`, `*.md`, `*.json`, `*.pdf`. Treat any depth.
- Skip noise folders: `node_modules/`, `dist/`, `build/`, `.git/`, `vendor/`.
- Soft cap at 20 files read total. If the folder genuinely contains more candidate files, pick the most-likely-relevant by filename heuristic (filenames containing `color`, `token`, `theme`, `style`, `design`, `brand`) and tell the user which files were sampled in the proposal.
- If the path is a single file, just read that file.

### Extract step

From the files read, identify:

- Four colors with hex/rgba values: `background`, `headline`, `body`, `accent`.
- Four optional human-readable color names: `background_name`, `headline_name`, `body_name`, `accent_name`. Populated where the source has an explicit name (e.g. `--lavender` variable name, "Lavender accent" in markdown prose); left empty otherwise.
- Two fonts: `headline` and `body`. If the source uses one typeface throughout, set both to the same value.
- A `raw_notes` string holding any prose-level brand guidance (voice, tone, hard-bans) from the markdown files. Matches the field name used by the existing folder-path parser; downstream consumers read it the same way.

### Propose step

Show the user a structured proposal with **one citation line per extracted field**. The citation names the source file and the literal substring the value came from. Example:

~~~
Proposed brand profile for "Atlas Assistants":

  background  Cosmic Black  #050314      from colors_and_type.css:36 — "--bg: #050314"
  headline    White         #ffffff      from colors_and_type.css:42 — "--fg-1: #ffffff"
  body        White 72%     rgba(...)    from colors_and_type.css:43 — "--fg-2: rgba(255,255,255,0.72)"
  accent      Lavender      #ba9cff      from colors_and_type.css:49 — "--lavender: #ba9cff"
                                          + design.md:14 — "Lavender — primary accent"

  headline font  Inter      from colors_and_type.css:8 — @font-face "Inter"
  body font      Inter      (same as headline — one typeface used throughout)

  raw_notes excerpt: "Cosmic dark theme. Inter type. Lavender accent + signature blue→magenta brand gradient."

  Save this as brands/atlas-assistants.json? (yes / adjust / cancel)
~~~

Citations are the guardrail against silent hallucination. Any field without a citation must be flagged in the proposal so the user can challenge it before save.

### Adjust loop

If the user replies `adjust`, ask for the correction in natural language ("accent should be magenta, not lavender — `#b675f5`"). Update the proposal in place; the corrected field's citation becomes `"user override"` rather than a source-file reference. Re-show the proposal. Re-ask. Repeat until the user replies `yes` or `cancel`.

### Save step

On `yes`:

1. **Check whether the source defined both a light and a dark theme.** Design systems commonly ship both — e.g., a `:root` color set plus a `[data-theme="light"]` (or `[data-theme="dark"]`) opt-in block in CSS, or two themed JSON files, or both palettes labeled in a markdown doc. If both variants are present in the files you read, ask the user:

   > Your source defines both a `<primary>` theme and a `<variant>` theme. Save **both** as separate brand profiles (so you can pick the right one for each carousel based on the art style), or just the `<primary>` you adjusted above?
   >
   > Options: **Save both** / **Save only `<primary>`**

   If the user picks **Save both**, save the adjusted proposal as `<slug>.json` and the counterpart variant as `<slug>-<variant>.json` (e.g., `atlas-assistants.json` + `atlas-assistants-dark.json`). The counterpart inherits all non-color fields from the primary (voice, audience, hard_bans, fonts, art_style, footer_handle, brand_mark) — only the color set differs. Surface a one-line note in chat: "Saved both — pick `atlas-assistants` for light-bg art styles (pastel-marker, editorial, clean-saas, hand-drawn-marker) and `atlas-assistants-dark` for `midnight-editorial` (recommended), `documentary-noir`, or `bold-flat-corporate`."

2. Write the JSON(s) to `<user CWD>/linkedin-carousel-builder/brands/`.
3. Run `python scripts/brand_profile_schema.py` against each saved file.
4. If any validator exits non-zero, treat the error message as an `adjust` step — show the validation errors, ask the user how to correct, re-propose.
5. On validator success, post the plain-language summary (next section). If both variants saved, summarize both back-to-back.

### Chat summary

After save + validation, post a plain-language summary in chat. The user reads chat, never the JSON file. Format:

> Saved brand profile **Atlas Assistants** →
> • Lavender accent (#ba9cff) on Cosmic Black background
> • White headline, white-72% body
> • Inter for headlines, Inter for body
>
> Ready to move to source selection, or want to adjust anything?

Use the `*_name` fields where they were populated. Fall back to the hex code alone when no name was extracted (e.g. user-supplied tokens JSON with no naming context). The summary is the source of truth for what the user agreed to; the JSON on disk is just storage.

## The accent_name field

The brand profile carries an optional `accent_name` field that names the accent color in one common word (`"lavender"`, `"rust"`, `"navy"`, `"forest"`, `"teal"`). It is consumed by the art-style illustration prompts alongside the hex code: `"Use lavender (#BA9CFF) as the dominant chromatic ..."`. Image models follow named colors more reliably than raw hex values, so the field meaningfully strengthens brand-color adherence in generated illustrations.

**Population.** During brand creation (any of the six paths above), the skill infers `accent_name` from the accent hex using common color-naming judgment. The orchestrator sets the field on the brand profile before saving. A user who prefers a different name can edit the JSON on disk after the fact — the field is plain text.

**Backward compatibility.** Existing brand profiles without `accent_name` continue to work. When the field is absent, the prompt template falls back to naming only the hex: `"Use the accent color (#BA9CFF) as the dominant chromatic ..."` — still meaningfully stronger than no instruction, but less reliable than the named version. Updating older brands to add `accent_name` is recommended but not required.

**Sibling fields.** The brand profile also carries three additional optional name fields with the same backward-compat semantics: `background_name`, `headline_name`, `body_name`. They are informational rather than prompt-substituted — the chat summary uses them so users read "Cosmic Black" instead of `#050314`. Path 6 (host-LLM extraction) populates all four `*_name` fields from the source files when names are available. Other paths populate only `accent_name` (existing behavior). Brand JSONs created before this release continue to validate green — all four fields are optional.

## The footer questions

After colors, fonts, and art-style are decided but before the theme-preview gate, the skill asks two short questions:

1. **LinkedIn handle for the slide footer** — empty by default. The user can paste a full LinkedIn URL and the skill extracts the slug. Leave-blank-to-skip is allowed.
2. **Brand mark or wordmark for the footer** — defaults to the executive display name. The user can override (for example, `ACME`) or leave blank.

If both are left blank, the footer shows the slide number only.

## Art-style picker

After brand identity is captured, the skill opens `assets/art-styles/contact-sheet.jpg` — a single grid showing all seven presets side-by-side for visual picking. The seven preset slugs and their brand-background compatibility are:

| Preset | Best for brand background | Why |
|---|---|---|
| `clean-saas` | Light bg | References Stripe / Linear / Notion / Vercel landing pages — all light-bg-leaning. Template assumes white or off-white surfaces. |
| `editorial-magazine` | Light bg | References HBR / Bloomberg Businessweek / Monocle print spreads — magazine paper aesthetic. |
| `pastel-diagram-marker` | Light bg | Hand-drawn pastel marker on heavy paper. Pastel + dark creates a frame mismatch on the model's output. |
| `hand-drawn-marker` | Light bg | Marker on white paper aesthetic (Wait But Why / sketchnoting). |
| `midnight-editorial` | **Dark bg** *(recommended)* | Polished dark editorial vector — single focal subject, solid brand-background, accent as UI highlight. The default dark choice for executive carousels. |
| `documentary-noir` | **Dark bg** | Moody photographic alternative — film-noir aesthetic, deep shadow + monochrome with one accent. Use when editorial mood matches the topic. |
| `bold-flat-corporate` | **Works for either** | Flat-vector consulting-deck — no paper-feel hardcoded, bg-agnostic. |

The picker should surface these compatibility hints next to each preset name when offering the choice, e.g.:

> Pick an art style:
> 1. **clean-saas** — Stripe/Linear-style product surfaces (best for light bg)
> 2. **editorial-magazine** — HBR/Bloomberg magazine spreads (best for light bg)
> 3. **pastel-diagram-marker** — pastel marker data viz (best for light bg)
> 4. **hand-drawn-marker** — Wait But Why marker sketches (best for light bg)
> 5. **midnight-editorial** — polished dark editorial vector (designed for dark bg, recommended)
> 6. **documentary-noir** — film-noir photographic (designed for dark bg)
> 7. **bold-flat-corporate** — McKinsey/BCG diagrams (works for either)
> 8. **Create a custom style** — for brands with their own visual identity

Users with a dark brand who pick a light-bg-tuned preset will see a frame mismatch in their illustrations (the model's rendered paper texture won't match the slide background). When the brand background is dark, gently recommend `midnight-editorial` (or `documentary-noir` for editorial-mood topics) first.

This is a separate decision from brand identity. The brand profile is not finalized to a specific art-style until the user picks here, and even after picking, the art-style can be overridden on any future run.

## Per-run art-style override

After a brand is selected on a future run (whether the brand is new or existing), the skill always asks the per-run art-style question:

> This brand's saved default style is `<saved-style>`. Use it for this carousel, or pick a different style? Options: Use saved / Pick different for this run only / Pick different and update the brand's default.

The three branches behave as follows. **Use saved** carries the brand's stored `art_style` straight into the run config. **Pick different for this run only** presents the picker (six presets + "create a custom style" + any custom styles already saved with this brand); the chosen style is written into the in-memory run config for this single run and the brand JSON on disk is untouched. **Pick different and update the brand's default** presents the same picker, writes the choice into the run config, and also rewrites the `art_style` field in the brand JSON so subsequent runs use the new default.

## Custom art-style handling

When the user picks "Create a custom style", the flow asks for reference images and/or a short description, generates a style-prompt template, renders a preview slide for confirmation, and saves the custom style scoped to the brand profile (not shared across brands).

When `art_style` is a preset slug (one of the six), the rest of the style data lives in `assets/art-styles/<slug>/`. When `art_style` is a custom slug (e.g., `acme-ceo-custom`), the brand profile JSON gains two additional fields:

- `art_style_prompt` — the custom style-prompt template string.
- `art_style_references` — a list of relative paths to reference images stored alongside the brand profile in `linkedin-carousel-builder/brands/<brand-slug>-art-style-references/`.

This keeps custom styles self-contained with the brand they belong to and survives the user copying a brand profile across workspaces.

## Theme-preview gate

After the profile is built, before locking it to disk:

1. Render one sample slide using the new profile (theme + chosen art-style).
2. Open the rendered slide in the user's default image viewer.
3. Ask the user to choose: **Approve / Adjust colors / Adjust art style / Adjust typography / Other**.
4. Loop on the chosen adjustment until the user approves.
5. Lock the profile to disk.

The locked profile is reused on every subsequent run for that brand. The user can re-trigger the gate any time via `/linkedin-carousel-builder --refresh-brand <slug>`.

## Brand profile JSON schema

The profile is plain JSON — a non-developer can open it in any text editor and edit colors, fonts, or art-style. No proprietary format. Fields are flat strings, simple objects, and short string arrays.

```json
{
  "brand_slug": "acme-ceo",
  "display_name": "Acme CEO",
  "audience": "B2B founders and sales leaders",
  "voice": "direct, contrarian, anti-jargon",
  "colors": {
    "background": "#FFFFFF",
    "headline": "#0A1A2F",
    "body": "#2A3B4F",
    "accent": "#3B82F6"
  },
  "fonts": {
    "headline": "Inter",
    "body": "Inter"
  },
  "art_style": "clean-saas",
  "footer_handle": "@acme-ceo",
  "brand_mark": "ACME",
  "hard_bans": ["stock photos", "generic icons"],
  "created_at": "2026-05-16",
  "last_used": "2026-05-16"
}
```

Custom art-styles add the `art_style_prompt` and `art_style_references` fields described above. All other fields are required.

## Where files save

Locked brand profiles save to the user's workspace under:

`linkedin-carousel-builder/brands/linkedin-carousel-builder-brand-<slug>.json`

The plugin-namespaced filename prefix (`linkedin-carousel-builder-brand-`) guarantees zero collision with any other Atlas plugin's profile files that share the same `brands/` territory. The `<slug>` segment is the executive or company slug — lowercased, alphanumeric, hyphens only. Custom art-style references for a given brand live in `linkedin-carousel-builder/brands/<brand-slug>-art-style-references/` next to the JSON.

## Built-in starter handling

Starter presets ship inside the plugin install directory at `assets/brand-profiles/default-cream.json` (and any other starters added later). They are never read directly from the plugin install directory at run time. On first use of a starter, the skill **copies** the starter file into the user's workspace `brands/` folder, renaming it to follow the plugin-namespaced convention (`linkedin-carousel-builder-brand-default-cream.json`), and reads only from the workspace copy thereafter. This follows the Atlas workspace-path rule: user-editable state lives in the user's workspace, never in the plugin install dir, so the user can edit colors / fonts / footer without their changes being overwritten on plugin updates and without needing write access to the install location.

## Notes on font rendering

The `fonts.headline` and `fonts.body` fields in your brand profile apply to the slide's HTML chrome layer (the summarizing headline, supporting line, slide number, brand mark, and handle). They do **not** control typography inside the AI-generated illustration — that typography is driven by the art-style preset.

**Behavior on the HTML chrome layer:**
- If the named font is installed on the rendering machine (or available as a web font Chromium can resolve), it is used.
- If not, Chromium falls back to the closest system match: usually Arial on Windows, Helvetica on macOS, the OS default sans-serif on Linux.
- We do not bundle fonts with the plugin in v1. Proprietary fonts (Brandon Grotesque, Sharp Sans, foundry-licensed fonts) cannot be redistributed safely. Free fonts (Inter, Lora, etc.) could be bundled but would add weight; we prefer to leave font selection to the user's environment.

**If exact brand typography matters to you:**
- Install the font system-wide on machines that render carousels.
- Or accept the closest fallback — in practice, a generic sans-serif at the chrome layer is rarely the part of the slide a reader fixates on, because the AI illustration carries the visual identity.

**v2 backlog:** per-brand-profile font upload (drop a `.ttf` into the brand-profile folder; the plugin injects an `@font-face` declaration into the slide template). Build when proprietary-font users ask for it.
