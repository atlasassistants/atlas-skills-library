---
name: build-deck
description: Build a complete, polished HTML slide deck from a topic, audience, time budget, and content. Selects the right slide types for each section, applies the user's brand, and outputs a single self-contained HTML file that works in any browser with arrow key navigation.
when_to_use: Use when the user asks to create a new presentation, slide deck, or pitch deck from scratch. Trigger phrases: "create a presentation", "build a deck", "make slides", "put together a presentation", "slide deck for", "presentation for my meeting", "build slides for". Do NOT use for editing an existing deck — use `update-deck` instead.
atlas_methodology: opinionated
---

# build-deck

Build a complete slide deck from content — the right structure, the right slide types, brand-consistent, single HTML file.

## Purpose

Building a deck from scratch involves three bottlenecks: figuring out the right structure, picking the right slide types for each section, and making it look polished. This skill handles all three. The user provides content and context; the skill handles structure, pacing, and presentation.

## Inputs

- **Topic and purpose** (required) — what the deck is about and what it needs to accomplish
- **Audience** (required) — who will see this deck. Shapes vocabulary, depth, and how much context to include.
- **Time budget** (required) — how many minutes the presentation will run. Determines slide count and pacing.
- **Content** (required) — data, talking points, context, or any raw material. Can be notes, bullet points, a document, or a conversation.
- **Brand** (optional) — if `references/branding-guide.md` doesn't exist, uses clean defaults.

## Required capabilities

- **File read** — read `assets/base-template.html` and `references/branding-guide.md` from the plugin directory
- **File write** — write the finished HTML file to the specified output location

## Steps

1. **Load methodology references.** `references/atlas-presentation-methodology.md` (content rules, pacing, slide selection) and `skills/build-deck/references/atlas-slide-types.md` (type definitions and CSS patterns).
2. **Read the brand.** Load `references/branding-guide.md`. If it doesn't exist, note that defaults will be used.
3. **Assess the deck scope.** Based on time budget and pacing rules from the methodology: calculate target slide count. For a 20-minute deck: ~18–20 slides using 1 min/slide as baseline.
4. **Plan the deck structure.** Map the content to a logical arc: Title → (Agenda) → Content Sections → (Discussion) → Close. Identify which slide type fits each section.
5. **Draft the slide plan.** A brief outline of each slide: type, headline, content. Confirm with the user if scope is large or uncertain.
6. **Load the base template.** Read `assets/base-template.html`. Apply the brand's CSS variables, font import, and logo from the branding guide.
7. **Build each slide.** For each slide in the plan, generate the correct HTML structure using the slide type's CSS class and layout from `atlas-slide-types.md`. Apply content rules: bottom line up front, one idea per slide, real data only.
8. **Assemble the full deck.** Insert all slides into the template's slide container. Confirm navigation, slide counter, and transitions are intact.
9. **Write the file.** Output as a single self-contained HTML file. Filename: `{topic-slug}-deck.html` unless the user specifies a name.
10. **Confirm delivery.** Report: file name, slide count, and estimated run time.

## Output

```
Deck built: q2-roadmap-deck.html
- 22 slides
- Estimated run time: ~20 minutes
- Brand: Atlas (from branding-guide.md)
- Slide types used: title, agenda, metric-cards (×2), data-table, grid-cards, discussion, close
```

## Customization

Common things clients adjust:

- **Pacing defaults.** 1 slide per minute is the baseline. Override for faster-paced audiences or denser content.
- **Slide type library.** Add custom types in `skills/build-deck/references/atlas-slide-types.md` — define the CSS class and usage guidance.
- **Output location.** Default is current working directory. Specify a path when invoking.
- **Deck structure defaults.** Always starts with a title slide and ends with a close slide by default. Adjust if your format differs.
- **Skip agenda slide.** Agenda slides are included for decks over 15 minutes. Disable for shorter decks or specific formats.

## Why opinionated

Structure and pacing are where decks fail silently. A deck with the right content but the wrong structure leaves the audience confused. A deck with the right structure but wrong pacing leaves the presenter rushing or with dead air. The methodology encodes the defaults that work — bottom line up front, one idea per slide, pacing calibrated to the time budget. Clients customize these defaults; they don't start from scratch.
