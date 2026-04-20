# presentation-builder — Setup Instructions

> Follow these steps before running `build-deck` for the first time.

## What requires setup

This plugin needs two files to exist before it can build branded decks:

1. **`assets/base-template.html`** — the HTML shell every deck is built from (navigation, CSS variables, slide container, transitions)
2. **`references/branding-guide.md`** — your brand's colors, fonts, logo, and style rules

If neither file exists, `build-deck` will fall back to clean defaults — it will still work, but decks won't match your brand.

---

## Setup step 1: Create the base template

Create `assets/base-template.html` in this plugin's directory. The template must include:

- CSS custom properties for brand colors (see branding guide below)
- A slide container element (`<div id="slides">`)
- Arrow key, spacebar, and swipe navigation (inline JS)
- A slide counter (bottom-right)
- CSS classes for each slide type (title, metric-cards, data-table, grid-cards, quote, two-column, close, etc.)
- Smooth slide transitions

**Minimum viable template structure:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{DECK_TITLE}}</title>
  <link href="https://fonts.googleapis.com/css2?family=YOUR_FONT" rel="stylesheet">
  <style>
    :root {
      --color-primary: #000000;
      --color-accent: #0066FF;
      --color-bg: #FFFFFF;
      --color-text: #111111;
      --font-body: 'Your Font', sans-serif;
    }
    /* slide layout, transitions, responsive styles */
  </style>
</head>
<body>
  <div class="logo">{{LOGO}}</div>
  <div id="slides">
    <!-- slides injected here -->
  </div>
  <div class="slide-counter"></div>
  <script>
    // arrow key / spacebar / swipe navigation
    // slide counter update
  </script>
</body>
</html>
```

**Recommended:** Use any existing HTML presentation template you have, or ask the agent to scaffold a default template for you with `build a default base template for the presentation-builder plugin`.

---

## Setup step 2: Create the branding guide

Create `references/branding-guide.md` in this plugin's directory with your brand details.

**Template:**

```markdown
# Branding Guide

## Colors
- Primary: #000000
- Accent: #0066FF
- Background: #FFFFFF
- Text: #111111
- Muted: #6B7280

## Typography
- Body font: Inter (Google Fonts)
- Heading weight: 700
- Body weight: 400

## Logo
- Text logo: Your Company Name
- (Optional) SVG or image path if using a logo mark

## Style rules
- Use sentence case for slide headings
- Tables: highlight key cells in accent color
- Cards: 4px border-radius, subtle shadow
- Dividers: 2px accent color
```

Fill in your actual values. The agent reads this guide before building every deck.

If you skip this file, the agent uses clean neutral defaults.

---

## Setup step 3: Verify

Once both files exist, test the setup:

```
Build a 3-slide test deck: title slide, one metric card slide, one close slide.
```

The agent should produce a single HTML file. Open it in a browser and confirm:
- Arrow key navigation works
- Fonts and colors match your brand guide
- Slide counter appears in the bottom-right

---

## Optional: Configure delivery location

By default, the agent writes the HTML file to the current working directory. To change this, note your preferred output path when invoking `build-deck`:

```
Build a deck for [topic] and save it to ~/Decks/
```

No further configuration required — the plugin has no external API dependencies.
