---
name: update-deck
description: Edit specific slides in an existing HTML deck without regenerating the whole file. Accepts a list of changes (slide number or heading, what to change), applies them surgically, and returns a changelog. Use for iteration rounds after build-deck.
when_to_use: Use when the user wants to change, fix, or update an existing deck. Trigger phrases: "update slide 3", "change the title on the metrics slide", "fix the data on slide 5", "add a slide after the agenda", "remove the discussion slide", "update this deck", "make these changes to the deck". Do NOT use to build a new deck from scratch — use `build-deck` instead.
atlas_methodology: neutral
---

# update-deck

Edit specific slides in an existing deck — surgical changes, not a full rebuild.

## Purpose

After a deck is built, iteration happens. The user reviews it, wants to change a headline, fix a number, swap a slide type, or add a section. Regenerating the whole deck for a small change is wasteful and risks losing customizations already applied to the file. This skill edits only what's specified, leaves everything else intact, and returns a clear changelog.

## Inputs

- **The existing deck file** (required) — the HTML file to edit
- **List of changes** (required) — each change specifies: which slide (by number or heading text), and what to change (headline, body content, slide type, data, add/remove slide)
- **Version note** (optional) — if the user wants the output saved as a new version (`deck-v2.html`) rather than overwriting the original

## Required capabilities

- **File read** — read the existing HTML deck file
- **File write** — write the updated file (overwrite or new version)

## Steps

1. **Read the existing deck.** Parse the HTML to identify slide structure, existing slide types, and current content.
2. **Map each requested change to a slide.** Match by slide number or heading text. If a heading isn't unique or the slide number is unclear, ask which slide before proceeding.
3. **Apply each change in order:**
   - **Headline change** — update the heading element within that slide's container
   - **Body content change** — update the relevant content element (bullets, table cells, metric values, etc.)
   - **Slide type change** — replace the slide's CSS class and restructure the content for the new type, using the layout from `atlas-presentation-methodology.md`
   - **Add slide** — insert a new slide in the correct position using the appropriate type's HTML structure
   - **Remove slide** — remove the slide's container element and update slide count
4. **Verify navigation and counter still work** after any add/remove changes.
5. **Write the updated file.** Overwrite the original unless a version note was given (then write as `{original-name}-v{N}.html`).
6. **Return a changelog.** List each slide that changed and what was changed.

## Output

```
Deck updated: q2-roadmap-deck.html

Changes applied:
- Slide 3 (Metric Cards): updated Q1 revenue figure from $1.2M to $1.4M
- Slide 7 (Discussion): updated question text
- Slide 11: removed (duplicate of slide 9)
- New slide added after slide 8: Two Column — "Build vs. Buy comparison"

Slide count: 21 → 21 (removed 1, added 1)
```

## Customization

Common things clients adjust:

- **Version behavior.** Default overwrites the original. Change to always version if you prefer to keep a history.
- **Slide type reference.** When changing a slide's type, the skill reads `skills/build-deck/references/atlas-slide-types.md` for the correct HTML structure. Add new types there to make them available here.

## Why neutral

The update logic is mechanical — find the slide, apply the change, verify structure, write the file. Atlas has no opinionated method for "the right way to edit a slide." The opinionated work happened in `build-deck`; this skill just applies the user's requested changes faithfully.
