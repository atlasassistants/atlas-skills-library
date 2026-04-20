# Default Implementation

> A working base template and branding guide to get started immediately.

## What's in here

- `base-template.html` — a complete, working HTML presentation shell
- `branding-guide.md` — a minimal brand configuration you can customize

## Setup

1. Copy `base-template.html` to `assets/base-template.html` in the plugin directory
2. Copy `branding-guide.md` to `references/branding-guide.md` in the plugin directory
3. Edit `references/branding-guide.md` with your actual brand colors, font, and logo
4. Run `build-deck` — it will use your brand automatically

## Customizing the template

The template uses CSS custom properties for all brand values. Change these in `references/branding-guide.md` — the skill reads the guide and applies the values to the template at build time:

```css
--color-primary: #111111;    /* headings, strong text */
--color-accent: #0066FF;     /* dividers, highlights, buttons */
--color-bg: #FFFFFF;         /* slide background */
--color-text: #333333;       /* body text */
--color-muted: #6B7280;      /* secondary text, labels */
```

## Adding a logo

In `references/branding-guide.md`, set the logo field to either:
- A text string (company name rendered as styled text)
- An inline SVG string (logo mark rendered directly)

The template renders it in the top-left corner of every slide.
