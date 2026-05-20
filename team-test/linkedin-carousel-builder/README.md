# linkedin-carousel-builder

> Atlas plugin — generate save-worthy LinkedIn carousels from articles, newsletters, or transcripts.

## 1. What it does

Turns an article, newsletter, or transcript into a save-worthy LinkedIn carousel — a brand-themed PDF (7–10 slides) plus an optional companion LinkedIn post — both rooted in the source's actual voice, not generic AI paraphrasing.

You hand the skill a URL, a file, or pasted text. It picks the strongest cover hook across four formulas (numbered, bold-claim, question, contrarian), drafts one tight idea per slide, runs an editorial specificity check that rewrites or cuts any slide leaning on generic advice, generates per-slide AI illustrations in the chosen brand art style, renders each slide as a 1080×1350 PNG with your colors, fonts, handle, and slide-number footer, packages the deck as a PDF ready to upload, and (if you opted in) drafts a 150–300 character companion post in the source's voice.

Brand identity is captured once per executive and reused across every future carousel for that person. Art style is a per-run choice — the same brand can wear different visual treatments on different days.

**Cost per carousel:** roughly **$0.50–$0.70 per run** at current gpt-image-2 pricing (9 illustrated slides at ~$0.06 each, plus a theme-preview sample on first run, plus an occasional retry on a transient API failure). The cost is per carousel run — not per slide and not per brand. Built-in starter preset users incur the same cost as users with custom brands.

## 2. Who it's for

Built for Atlas's audience: businesses, executives, and public figures publishing on LinkedIn.

- **Executives and founders** who post regularly and want each carousel to feel on-brand without spending an afternoon in Canva.
- **Marketing teams and EAs** producing carousels on an executive's behalf, who need consistency across a backlog of source articles.
- **Public figures and operators** who already write the long-form content (newsletters, blog posts, transcripts) and need a repeatable way to repurpose it into LinkedIn-native carousels.

Not aimed at creator-economy aesthetics — the built-in art styles are tuned for business and editorial feel (clean SaaS, magazine editorial, bold corporate) rather than creator-template look.

## 3. Required capabilities

These are abstract — the skill works with any host that can satisfy them.

| Capability | What the skill needs to do |
|---|---|
| Read files | Open source files (`.md`, `.txt`, `.docx`, `.pdf`), brand profile JSONs, workspace config, methodology references. |
| List files | Discover saved brand profiles, prior runs, the `.env` file, and the workspace config. |
| Write files | Save brief, slide plan, illustrations, rendered slides, contact sheet, PDF, post copy, and warnings logs into the per-run folder. |
| Fetch URL content | Pull source articles and (during brand creation) brand-site colors/fonts. Needs raw HTML, not a summary. |
| Run a shell command | Execute the skill's bundled Python helper scripts (source fetch, brand scrape, illustration generation, slide rendering, PDF packaging). |
| Open a file in the user's default viewer | Show the theme preview, art-style picker contact sheet, and the final contact sheet during visual review. |
| Ask the user a structured question | Brand creation, art-style picker, theme approval, source clarifications, companion-post opt-in. |

## 4. Suggested Claude Code tool wiring

This is a validated default for Claude Code, not a coupling. Any host that exposes the abstract capabilities above can run the skill.

| Capability | Claude Code tool |
|---|---|
| Read files | `Read` |
| List files | `Glob` or `Bash ls` |
| Write files | `Write` / `Edit` |
| Fetch URL content | `Bash` (the skill calls its own `fetch_source_url.py` using `requests` — raw HTML is needed for downstream parsing, so the skill does not delegate fetching to a URL-summarizing tool) |
| Run a shell command | `Bash` |
| Open a file in the user's default viewer | `Bash` (`open` on macOS, `start` on Windows, `xdg-open` on Linux — wrapped by the skill in a cross-platform helper) |
| Ask the user a structured question | `AskUserQuestion` |

Image generation (`gpt-image-2`) runs from inside the skill's own Python script using your `OPENAI_API_KEY`. The host agent never makes the OpenAI call directly, which keeps the skill portable across hosts that don't have a native OpenAI integration.

## 5. Installation

Install via the Atlas marketplace:

```
/plugin marketplace add colin-atlas/atlas-skills-library
/plugin install linkedin-carousel-builder@atlas
```

After install, trigger the skill with `/linkedin-carousel-builder` or a natural-language phrase like "build a LinkedIn carousel from this article."

## 6. First-run setup

The first time you run the skill, it walks through six checks. Everything except installing Python is automatic — and on subsequent runs, the gate is silent when everything's healthy.

1. **Python 3.10+** — the skill needs Python 3.10 or newer installed on your machine. If it's missing, you'll be pointed to python.org/downloads to install it once. The skill does not auto-install Python (admin rights and OS variance make that unsafe).
2. **Skill-local virtual environment** — the skill creates its own isolated `.venv/` inside the skill folder and installs the Python packages it needs there (requests, beautifulsoup4, openai, jinja2, playwright, pillow, python-docx, pypdf, langdetect). One-time, about 30 seconds. Nothing is installed globally — your other Python projects are untouched.
3. **Chromium browser bundle** — the slide renderer uses Playwright + Chromium to convert HTML slides to PNGs. On first run, Chromium is downloaded into the skill's `.venv/` (about 150 MB, one-time). No system-wide changes.
4. **Workspace scaffolding** — the skill creates a `linkedin-carousel-builder/` folder inside your current working directory, with `brands/` (saved brand profiles), `runs/` (per-carousel output folders), and a `linkedin-carousel-builder.config.json` for workspace-level preferences. All paths resolve against your CWD, so each project workspace gets its own carousel history.
5. **OpenAI API key** — a `.env` file is created at the workspace root with an `OPENAI_API_KEY=` line. You paste your key (get one from platform.openai.com/api-keys). The account needs billing enabled and access to the `gpt-image-2` model — that's what generates the per-slide illustrations. The key is validated against OpenAI before the run continues.
6. **Brand profile** — if your workspace has no saved brands yet, the skill offers six creation paths (including the built-in starter preset `default-cream` as a zero-effort option): a website URL scrape, a short description, brand screenshots, a structured design-system file or folder (via `parse_design_system.py` — works for W3C tokens JSON, folder with literal `colors.json` + `typography.json`, or a brand PDF), or a folder/repo/file the orchestrator reads directly via host-LLM extraction (works for CSS variables, markdown design docs, Tailwind configs, Figma exports — the common case for modern design systems). The structured `parse_design_system.py` path and the host-LLM extraction path are independent — use whichever fits your source: structured if you already have W3C tokens or a brand PDF, host-LLM if you have CSS + markdown. The new brand is previewed on a sample slide before being locked to disk. (The seven art-style folders — clean-saas, editorial-magazine, hand-drawn-marker, bold-flat-corporate, midnight-editorial, documentary-noir, pastel-diagram-marker — control the visual look of illustrations and are separate from brand profiles; you choose one per run. For dark brand backgrounds, `midnight-editorial` is the recommended polished-executive choice; `documentary-noir` is kept for editorial-mood carousels.)

After setup, you'll see `<workspace>/linkedin-carousel-builder/` with your brands and runs, and `<workspace>/.env` holding your API key (auto-added to `.gitignore`).

## 7. Skills included

One skill: **`linkedin-carousel-builder`**.

Trigger it in Claude Code with the slash command:

```
/linkedin-carousel-builder [optional source URL or guidance]
```

In any host (Claude Code, Codex, Cursor, ChatGPT desktop, or anywhere else that loads SKILL.md files), the skill also triggers on natural-language phrases such as:

- "build a LinkedIn carousel" / "make a LinkedIn carousel" / "create a LinkedIn carousel"
- "turn this newsletter into a LinkedIn carousel"
- "make slides from this for LinkedIn"
- "draft a LinkedIn carousel for [executive name]"

Partial re-runs are available via the slash command:

```
/linkedin-carousel-builder --rerun-step <illustrations|slides|contact-sheet|post-copy|pdf> <run-folder-name>
```

A `--refresh-brand <slug>` flag re-opens the theme preview for an existing brand, and `--setup` re-runs the startup gate without producing a carousel.

## 8. Customization notes

The plugin is `atlas_methodology: opinionated` — the craft rules and visual rule are intentional defaults. Clients customize by **forking the plugin and editing the references and assets**, not by editing the SKILL body. The SKILL body stays stable across forks so future plugin updates don't conflict with your changes.

Common things to customize:

- **The 16 craft rules + visual rule** — `skills/linkedin-carousel-builder/references/atlas-carousel-methodology.md` and `skills/linkedin-carousel-builder/references/visual-rule.md`. Tighten or loosen the specificity check, change the slide-count band, swap the four cover-hook formulas, etc.
- **Visual feel of illustrations** — the prompt templates under `skills/linkedin-carousel-builder/assets/art-styles/<style>/prompt-template.txt`. Edit a preset's wording, or drop in a new preset folder of your own.
- **Brand profiles shipped as starters** — JSON files under `skills/linkedin-carousel-builder/assets/brand-profiles/`. Add your own starter presets here so they show up in the first-run picker.
- **Slide layout** — `skills/linkedin-carousel-builder/templates/slide.html.j2` controls HTML structure (where the headline / supporting line / illustration / footer sit). Edit CSS or markup to change layout.
- **Step-specific methodology** — the six reference docs (`cover-angle-lab.md`, `source-intake.md`, `editorial-review.md`, `brand-theme-setup.md`, `visual-review-loop.md`, `post-copy-extraction.md`) each capture a phase of the run. Editing the relevant reference is the right way to change behavior for that phase.

Brand profile JSONs (your saved brands in `<workspace>/linkedin-carousel-builder/brands/`) are also plain JSON — non-developers can open them in any text editor and adjust colors, fonts, footer, or default art style.

## 9. Atlas methodology

Atlas has an opinion about what makes a LinkedIn carousel save-worthy in 2026. The opinion is sixteen craft rules — one idea per slide, an elastic 7–10 slide count with padding forbidden, a cover headline of 6–10 words, title-case headlines with sentence-case body, one brand accent color and two fonts maximum, no emojis anywhere, "you" voice over third person, concrete numbers and named entities over abstract advice, each core-idea slide leaving a question the next slide answers, a slide-number-in-corner roadmap, brand-mark footer on every slide, an explicit save + follow CTA with a specific comment-trigger word, a cover-angle lab that generates 3–5 candidate hooks across four formulas, a companion post pulled from the source's voice rather than summarizing the carousel, a mid-carousel pattern-interrupt slide, and an editorial specificity check that rewrites or cuts any body slide leaning on generic advice. The accompanying visual rule says every illustrated slide's image represents the underlying concept and uses the brand art style's creative vocabulary — never decoration, never stock.

The full rules and rationale live in `skills/linkedin-carousel-builder/references/atlas-carousel-methodology.md` and `skills/linkedin-carousel-builder/references/visual-rule.md`. The 2026 LinkedIn carousel research brief that the rules are derived from is available on request.

Clients who disagree with any rule fork the plugin and edit the reference. The SKILL body stays stable; the methodology is the override point.

## 10. Troubleshooting

**Python 3.10+ isn't on the system.**
- Symptom: the startup gate halts with "Couldn't find Python 3.10+."
- Fix: install Python from python.org/downloads (3.10 or newer). On macOS, `brew install python@3.11` also works. Re-run the skill — it will create its venv automatically.

**OpenAI API key is rejected.**
- Symptom: the startup gate surfaces an `Incorrect API key provided` or `You exceeded your current quota` error from OpenAI.
- Fix: open `<workspace>/.env` and confirm the key after `OPENAI_API_KEY=` is correct (no quotes, no trailing spaces). Confirm at platform.openai.com that billing is enabled and the key has access to `gpt-image-2`. New OpenAI accounts sometimes need an explicit top-up before image models unlock.

**Image generation fails with `OpenAI image API error: Connection error.` after ~185 seconds.**
- Symptom: one or more illustration-generation calls hang for ~3 minutes then fail with `Connection error`. Retries hit the same wall. Some calls succeed in <125 seconds; others always fail at ~185s. Account quota is fine, key is valid.
- Diagnosis: a network path between your machine and OpenAI's image API is dropping long-running TCP streams. Most commonly this is a commercial VPN (NordVPN, ExpressVPN, etc.) closing connections after a short idle/streaming window. Corporate proxies and some restrictive firewalls can do the same. gpt-image-2 responses can take 60–180 seconds to deliver; when the connection drops mid-stream, the model still finishes server-side (and your account is billed) but the bytes never reach you.
- Fix: **disable your VPN before runs.** Re-run the failed step (`/linkedin-carousel-builder --rerun-step illustrations <run-folder>`). If you can't disable the VPN (corporate requirement), try a mobile hotspot to confirm the wall is path-specific, then work with your network admin on the idle-stream timeout for `api.openai.com`. If you regularly run this skill from networks with this issue, the deferred Finding 8 client-timeout patch (`timeout=60.0` on the OpenAI client) would make failures fail fast rather than slow — saves real money — but does NOT make the underlying calls succeed.

**Source URL won't fetch (paywall, 403, JS-heavy site).**
- Symptom: the source-intake step fails with a 403, a 404, or returns near-empty text.
- Fix: the skill doesn't try to defeat paywalls or render JavaScript in v1. Either paste the article body directly into the conversation, or save the article as a `.md`, `.txt`, `.docx`, or `.pdf` file and pass that path instead of the URL. Both fallbacks are first-class inputs.

**Only paste URLs you trust into the source-intake and brand-creation steps.**
- Why it matters: the plugin runs as you on your own machine. When you give it a URL, it fetches that URL with your network access — there is no built-in block against URLs that point at your own computer (`http://localhost/...`), your home or office network (`http://10.x.x.x/...`, `http://192.168.x.x/...`), or cloud-provider metadata endpoints (`http://169.254.169.254/...`). If you paste a URL someone else sent you that targets one of those addresses, the skill can pull data from places you probably didn't mean to — an internal admin panel, a router config page, an AWS instance-metadata endpoint.
- Fix: only paste URLs from public websites you trust. If you're forwarding a URL someone else sent, sanity-check the address — it should start with `https://` and look like a public site, not a local IP, `localhost`, or `169.254.x.x`. If you need to feed in a private document, save it as a `.md`, `.txt`, `.docx`, or `.pdf` and pass the file path instead — both are first-class inputs.

**Illustration regenerated twice and still looks wrong.**
- Symptom: the visual review loop auto-regenerates a slide twice and the third attempt still doesn't match the visual intent.
- Fix: the slide is surfaced in the final user message rather than blocking the run. Two options: (a) run `/linkedin-carousel-builder --rerun-step illustrations <run-folder>` to regenerate all illustrations (sometimes a fresh seed for the whole batch reads better), or (b) hand-edit the slide's entry in `slide-plan.md` to sharpen the visual intent and then re-run the `slides` step.

**Brand-site scrape returned no usable colors.**
- Symptom: during brand creation from a URL, the skill reports it couldn't reliably extract a brand and asks you to choose a fallback.
- Fix: the skill offers two fallback paths — share 1–3 screenshots of the website or existing brand assets (the most reliable path), or walk through three quick questions (audience, brand feel, hard bans). Pick whichever is faster. The scrape failure usually means the site uses CSS variables, web fonts loaded via JavaScript, or a dominant palette of grey/white/black only.

**Slide rendering fails with `playwright._impl._errors.Error: Executable doesn't exist`.**
- Symptom: the renderer can't find Chromium.
- Diagnosis: the Chromium browser bundle wasn't downloaded into the skill's virtual environment.
- Fix: run `"<venv-python>" -m playwright install chromium` from the skill directory (the skill's startup gate normally does this on first run; this command re-runs it manually). About 150 MB, one-time. Chromium lives inside the skill's `.venv/`, not system-wide.

**(Linux) Chromium launch fails with `error while loading shared libraries: libnss3.so`** (or a similar shared-library error).
- Symptom: Chromium is installed but can't start on a Linux machine.
- Diagnosis: the Linux distro is missing the system libraries Chromium needs to launch (commonly nss, atk, gtk, libxkbcommon, libdrm, libxcomposite, libxdamage, libxrandr, libasound, etc.).
- Fix: run `sudo "<venv-python>" -m playwright install-deps chromium`. Requires admin rights. This installs the underlying APT/RPM packages via your distro's package manager. Mac and Windows users don't hit this.

**Slide headline doesn't render in our brand font — looks like Arial / Helvetica.**
- Symptom: the rendered slide PNGs use a generic fallback font instead of the brand-profile font.
- Diagnosis: the brand font isn't installed on the rendering machine. The plugin does not bundle fonts in v1 — Chromium can only use fonts the operating system already exposes.
- Fix: install the font system-wide on the machine that runs the skill (download the `.ttf` / `.otf` from Google Fonts or the foundry, then double-click to install on macOS / Windows, or place in `~/.local/share/fonts/` on Linux). Re-run the `slides` step. The AI illustrations are unaffected — they use the art-style's own typography, not the brand font. See `skills/linkedin-carousel-builder/references/brand-theme-setup.md` § Notes on font rendering for details.
