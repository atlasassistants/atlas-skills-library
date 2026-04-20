# Atlas presentation methodology

> Loaded by `build-deck` and `update-deck` before building or editing any slide deck.

## The principle

A presentation that makes the audience work to find the point has already failed. The Atlas method: **bottom line up front, one idea per slide, real data only**. Every slide should be readable in 10 seconds. Every deck should be navigable in any browser with no setup.

## Content rules

- **Bottom line up front.** The headline states the insight. Detail goes below. Never bury the point in the body.
- **One idea per slide.** If you're trying to fit two ideas, split the slide.
- **Real data only.** Never invent numbers, percentages, or statistics. If data isn't available, use "TBD" — never a plausible-sounding fabrication.
- **Full names.** Always use first and last names for people referenced in slides.
- **Discussion slides are sparse.** They're prompts for the room, not presentations. One question, lots of white space.

## Pacing

| Slide type | Time budget |
|---|---|
| Standard content slides | 1 minute |
| Data / table slides | 2–3 minutes |
| Discussion / question slides | 3–5 minutes |
| Title / section break slides | 30 seconds |

For a 20-minute presentation: ~18–20 slides, assuming 1–2 discussion slides. Adjust down if the audience is expected to ask a lot of questions.

## Deck structure

Every deck follows this arc:

1. **Title slide** — topic, presenter, date or version
2. **Agenda or framing** (optional for short decks) — what the audience will get
3. **Content slides** — ordered by story logic, not chronology
4. **Discussion or decision slide** (if applicable) — what input is needed from the room
5. **Close slide** — the one thing to remember, next step, or CTA

## Slide type selection

Choose the slide type that matches the content — don't force content into the wrong shape.

| Content | Slide type |
|---|---|
| Opening, section break | Title |
| Meeting structure, agenda | Agenda |
| KPIs, key numbers | Metric Cards |
| Comparisons, pipeline, financials | Data Table |
| Showing transformation | Before / After |
| Features, values, capabilities | Grid Cards |
| Key principle or memorable quote | Quote / Statement |
| Team input, open question | Discussion |
| Side-by-side detail | Two Column |
| Memorable single takeaway | The Line |
| Reframing language | Conversation Table |
| Final CTA | Close |

Full definitions and CSS patterns for each type are in `skills/build-deck/references/atlas-slide-types.md`.

## Branding

Before building any deck:

1. Read `references/branding-guide.md` (in this plugin's directory)
2. Apply the brand's colors to the CSS custom properties in the template
3. Apply the brand's font via the Google Fonts import
4. Set the logo text or mark

If `references/branding-guide.md` doesn't exist, use clean neutral defaults:
- Colors: white background, near-black text, a mid-blue accent
- Font: Inter or system-ui
- No logo

## Technical requirements

Every deck output must be:

- **Single HTML file** — inline all CSS and JS. No external dependencies except Google Fonts.
- **Self-contained** — must open and work correctly with no internet connection, except for font loading.
- **Browser-navigable** — arrow keys (left/right), spacebar (advance), and swipe gestures on mobile.
- **Slide counter** — current / total in the bottom-right corner.
- **Smooth transitions** — translateX with cubic-bezier easing.
- **Responsive** — readable and navigable on mobile at 768px breakpoint.

## Iteration

When updating an existing deck:

- Edit specific slides using targeted edits — never regenerate the whole file for a small change.
- Return a changelog summary: which slides changed and how.
- Track version in the filename if the user requests multiple rounds (e.g., `deck-v2.html`).

## What good output looks like

- Every slide readable in under 10 seconds
- No slide that requires explanation from the presenter to make sense
- Data slides with clearly labeled axes, rows, or metrics — no mystery numbers
- Discussion slides with a single clear question and room to breathe
- File opens in any browser, navigates with arrow keys, looks right on mobile
- Brand colors and fonts match the branding guide

## What bad output looks like (avoid)

- Slides packed with text that should be speaker notes
- Numbers that aren't sourced or real
- Multiple competing ideas on a single slide
- A close slide that just says "Thank you" with no CTA or takeaway
- External CSS or JS dependencies that break offline
- Invented statistics or placeholders disguised as data
