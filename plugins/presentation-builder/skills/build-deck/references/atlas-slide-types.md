# Atlas slide types

> Loaded by `build-deck` when selecting and building slide types. Loaded by `update-deck` when changing a slide's type.

## How to use this reference

Each slide type below defines: what it's for, the key elements it must contain, and the CSS class to apply to the slide container. When building a slide, apply the class to the slide's outer `<div>` and follow the element structure.

---

## Title

**Use for:** Opening slide, section breaks.

**Key elements:** Large heading (h1), subtitle or date, horizontal divider.

**CSS class:** `slide-title`

**Structure:**
```html
<div class="slide slide-title">
  <div class="logo">Brand Name</div>
  <h1>Slide Heading</h1>
  <p class="subtitle">Subtitle or context line</p>
  <div class="divider"></div>
  <p class="meta">Date · Version</p>
</div>
```

---

## Agenda

**Use for:** Meeting structure, what the audience will cover.

**Key elements:** Numbered or bulleted list of sections with estimated times.

**CSS class:** `slide-agenda`

**Note:** Only include for decks over 15 minutes. Skip for short presentations.

---

## Metric Cards

**Use for:** KPIs, key numbers, performance summaries.

**Key elements:** 3–4 cards in a grid, each with a label, a large number/value, and a one-line context note (vs. prior period, target, etc.).

**CSS class:** `slide-metric-cards`

**Content rule:** Never fabricate metrics. Use "TBD" if real data isn't available.

---

## Data Table

**Use for:** Comparisons, pipeline data, financials, any structured data with rows and columns.

**Key elements:** Header row, data rows, optional highlight on key cells (accent color background).

**CSS class:** `slide-data-table`

**Content rule:** Label all columns clearly. Don't omit units (%, $, hrs). Highlight the most important cell or row, not multiple.

---

## Before / After

**Use for:** Showing transformation, process improvements, reframing.

**Key elements:** Two columns — "Before" and "After" — each with a labeled list.

**CSS class:** `slide-before-after`

---

## Grid Cards

**Use for:** Features, values, team capabilities, product benefits — any content that's 3–6 parallel items.

**Key elements:** 3–6 cards in a grid, each with an icon or emoji, a short title, and 1–2 sentence description.

**CSS class:** `slide-grid-cards`

**Note:** Don't use for more than 6 items — split into two slides instead.

---

## Quote / Statement

**Use for:** A key principle, a memorable line from a customer, a mission statement, a bold claim.

**Key elements:** Large centered text (the quote), attribution line below.

**CSS class:** `slide-quote`

**Content rule:** One quote per slide. No supporting bullets — if the quote needs explanation, it's not ready to be on this slide type.

---

## Discussion

**Use for:** Open questions, team input moments, decision points that need the room.

**Key elements:** One clear question, minimal supporting context, lots of white space.

**CSS class:** `slide-discussion`

**Pacing:** Budget 3–5 minutes per discussion slide. Don't stack two discussion slides back-to-back.

**Content rule:** Sparse is better. This slide is a prompt, not a presentation.

---

## Two Column

**Use for:** Side-by-side detail, parallel options, split comparisons where both sides need more depth than Before/After allows.

**Key elements:** Left column heading + content, right column heading + content.

**CSS class:** `slide-two-column`

---

## The Line

**Use for:** A single memorable takeaway — the one thing the audience should walk away with.

**Key elements:** One sentence in large italic text, left border accent, attribution or context below (optional).

**CSS class:** `slide-the-line`

**Content rule:** One sentence only. If it needs two sentences, distill it further.

---

## Conversation Table

**Use for:** Reframing language, "say this not that" communication training, changing how a team talks about something.

**Key elements:** Two columns — old phrasing (with strikethrough) and new phrasing. Optional tag per row (e.g., "more confident", "client-facing").

**CSS class:** `slide-conversation-table`

---

## Close

**Use for:** Final slide — the CTA, the next step, or the mission reminder.

**Key elements:** Centered heading (the key message), optional supporting line, divider, CTA or next step.

**CSS class:** `slide-close`

**Content rule:** Never just "Thank you." Always end with the one thing you want the audience to do or remember.

---

## Adding new slide types

To add a custom slide type:

1. Add a new section to this file following the same format: name, use, key elements, CSS class, structure notes.
2. Add the corresponding CSS class to `assets/base-template.html`.
3. The new type will be available to `build-deck` and `update-deck` immediately.
