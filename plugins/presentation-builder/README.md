# presentation-builder

> Build polished, self-contained HTML slide decks that work in any browser and navigate with arrow keys.
> v0.1.0

## What it does

Turns meeting context, data, and conversation into presentation-ready slide decks:

- **Builds decks from scratch** — takes a topic, audience, and time budget and produces a fully structured HTML slide deck with proper pacing, the right slide types for each section, and brand-consistent styling.
- **Updates existing decks surgically** — edits specific slides without regenerating the whole file. Version-tracked, changelog-summarized.
- **Adapts to any brand** — reads a branding guide and base template to match colors, fonts, and logo automatically. Without one, uses clean defaults.

Output is always a single self-contained HTML file that works in any browser, with no external dependencies except Google Fonts.

## Who it's for

Operators, EAs, and agents who build decks regularly — all-hands presentations, client pitch decks, training materials, meeting readouts. Atlas built this for situations where the content is ready but assembly takes too long. The skill handles structure, pacing, and polish so the user focuses on content.

## Required capabilities

The plugin's skills depend on these capabilities. Each is named abstractly — wire it up to whatever tools the host agent has access to.

- **File read** — read the base HTML template and branding guide from the plugin's `assets/` and `references/` directories
- **File write** — write the finished HTML file to a delivery location
- **Context / conversation read** — access the content, data, and context provided by the user in the session

## Suggested tool wiring

| Capability | Common options |
|---|---|
| File read | Filesystem MCP, any file-access tool |
| File write | Filesystem MCP, any file-write tool |
| Context read | Built into any conversational agent |

These are examples, not requirements. The plugin has no external API dependencies.

## Installation

```
/plugin install presentation-builder@atlas
```

After installing, complete the first-run setup below before running any skill.

## First-run setup

> See [`instructions.md`](instructions.md) for the full setup walkthrough.

Two files must exist before `build-deck` can run:

1. **`assets/base-template.html`** — the HTML shell all decks are built from. Contains the navigation, CSS variables, slide container, and transition logic. Create one using the template in `instructions.md`, or bring your own.
2. **`references/branding-guide.md`** — defines your brand's colors, fonts, logo, and any style rules the agent should apply. Create one using the guide in `instructions.md`, or omit to use clean defaults.

## Skills included

- **`build-deck`** — *opinionated.* Takes a topic, audience, time budget, and content; selects the right slide types; builds a complete, brand-consistent HTML deck. Outputs a single self-contained file.
- **`update-deck`** — *neutral.* Edits specific slides in an existing deck without touching the rest. Accepts a list of changes, applies them surgically, and returns a changelog.

## Customization notes

Common things clients change:

- **Base template.** The template in `assets/base-template.html` controls all layout, animation, and navigation behavior. Replace it with any HTML shell that supports the same CSS variable and slide structure.
- **Branding guide.** Edit `references/branding-guide.md` to match any brand — colors, fonts, logo SVG or text, style rules.
- **Slide type library.** The available slide types and their CSS patterns are defined in `skills/build-deck/references/atlas-slide-types.md`. Add new types or adjust layouts to match your presentation style.
- **Pacing defaults.** Default is 1 slide per minute for standard slides, 3–5 minutes for discussion slides, 2–3 for data slides. Override in `skills/build-deck/SKILL.md`.
- **Delivery location.** Default writes the HTML file to the current working directory. Configure an output path during first-run setup.

When customizing, edit the `SKILL.md` and reference files in your installed copy or fork.

## Atlas methodology

This plugin encodes Atlas's presentation methodology — the discipline that makes decks scannable, purposeful, and fast to build:

- **Bottom line up front.** Every slide headlines the insight, detail below. No slide that makes the reader work to find the point.
- **One idea per slide.** If you're cramming, split it. Density is not clarity.
- **Real data only.** Never invent numbers. If data isn't available, leave the cell as "TBD."
- **Discussion slides are sparse.** They're prompts, not presentations — minimal content, maximum space for the room.

The full slide type library and content rules live at [`skills/build-deck/references/atlas-slide-types.md`](skills/build-deck/references/atlas-slide-types.md).

## Troubleshooting

**`build-deck` says the base template isn't found.** Check that `assets/base-template.html` exists in the plugin's installed location. See `instructions.md` for the setup walkthrough.

**Deck doesn't match our brand.** Check `references/branding-guide.md` — if it's missing or empty, the skill falls back to clean defaults. Add your brand's colors, fonts, and logo to the guide.

**Slide count or pacing feels off.** The default is 1 slide per minute. For a 20-minute deck, that's roughly 20 slides. If your tempo differs, override the pacing defaults in `skills/build-deck/SKILL.md`.

**A slide type I need isn't available.** The available types are in `skills/build-deck/references/atlas-slide-types.md`. Add a new type definition there, following the same pattern as existing types.

**`update-deck` changed the wrong slide.** Confirm the slide reference in your request — either by slide number or by the heading text of the slide. If the heading isn't unique, use the slide number.
