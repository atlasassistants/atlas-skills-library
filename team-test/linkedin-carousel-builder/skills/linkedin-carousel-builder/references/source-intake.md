# Source Intake

This doc is the contract for steps 1 and 2 of the carousel pipeline — source ingestion and the language gate. It is read by the skill body when accepting input from the user and by the supporting scripts (`fetch_source_url.py`, `parse_source_file.py`, `detect_language.py`). The downstream artifact is a single `brief.md` file that the cover-angle lab reads next to draft cover hooks.

---

## Three input types

The skill accepts three input types. All three normalize to plain text plus extracted metadata before any downstream step runs.

- **URL.** The user passes a link. `fetch_source_url.py` performs an HTTP fetch and uses BeautifulSoup to convert HTML to text, extracting title and author where the page exposes them. No headless browser in v1 — paywalled or JavaScript-heavy pages fall through to the paste fallback.
- **Pasted text.** The user pastes the article body directly into the conversation. No fetch, no parsing — the skill takes the text as-is. Quality issues are caught later in editorial review.
- **File path.** The user passes a path to a local file. `parse_source_file.py` reads it and supports `.md`, `.txt`, `.docx`, and `.pdf`. Paths resolve against the user's current working directory (see "File path resolution" below).

The user may also pass guidance alongside the source at invocation — a topic emphasis, an audience override, or a desired angle. The skill carries this through to the cover-angle lab and editorial steps.

---

## URL fetch failure handling

The URL path fails in several common ways:

- HTTP error response (403 paywall, 404 missing, 5xx server error).
- Timeout or network error.
- Successful fetch that returns an empty or near-empty body (typically a JavaScript-rendered page that needs a headless browser to expose its content).
- Anti-bot block returning a challenge page instead of the article.

On any of these, the skill stops the URL attempt and asks the user to switch to the paste or file path.

**Behavioral contract (from spec §2):**

> Plain-language error if fetch fails (403, 404, paywall, JS-heavy). User is asked to paste text or provide a file. No silent degradation.

**Example concrete message** `fetch_source_url.py` may print:

> Couldn't fetch that URL (got a 403 — looks like a paywall or anti-bot block). Paste the article text into the chat, or save it locally and pass the file path instead.

The skill does not retry silently, does not partially proceed with whatever bytes came back, and does not attempt to scrape with a headless browser in v1. The right move when a URL fails is to paste the article body or save it locally and pass the file path.

---

## File path resolution

File paths the user provides always resolve against the **user's current working directory**, never against the plugin install directory. This is the Atlas workspace-path rule and applies to every plugin: user data and user-provided paths belong to the workspace the user is running the skill from.

The skill enforces this in two layers:

1. **Top-of-steps callout.** The skill body opens its steps list with a workspace-path reminder so every step that touches a path is on notice.
2. **Step 0 explicit clause.** The first step of the pipeline restates the rule for source-file paths specifically: relative paths are resolved against the user's CWD, and the resolved absolute path is what gets passed to `parse_source_file.py`.

If a path doesn't resolve to a readable file with a supported extension (`.md`, `.txt`, `.docx`, `.pdf`), the skill stops and shows the path it tried plus the supported extension list. No auto-fallback, no guessing — the user fixes the path or switches input type.

The script enforces the rule mechanically; this doc states the rule so the skill body knows what contract the script is honoring.

---

## Language detection step

Once source text is normalized, `detect_language.py` runs a small offline detection library (e.g., `langdetect` or `langid`) on the body and returns a language code. v1 is "Latin-script best effort" — the gate has three outcomes:

- **English (`en`).** The skill proceeds normally. Methodology rules apply as written (cover headline 6–10 words, 100–150 characters per slide, etc.).
- **Other Latin-script languages** (Spanish `es`, French `fr`, German `de`, Portuguese `pt`, Italian `it`, Dutch `nl`). The skill proceeds with a one-line warning, then continues. The exact warning message:

> Source detected as [language]. The methodology rules (e.g., 6–10 word cover headline, 100–150 char per slide) are tuned for English. They generally transfer to other Latin-script languages but may need light manual editing in compound-heavy languages like German. Proceeding.

- **Non-Latin scripts** (CJK, Arabic, Hebrew, Hindi, Thai, etc.) and anything else. The skill halts. The exact failure message:

> v1 supports English plus other Latin-script languages (Spanish, French, German, Portuguese, Italian, Dutch). Non-Latin scripts need typography and layout work scheduled for v2. Cancel this run or provide a Latin-script source.

The slide text generated downstream always matches the detected source language. Image-generation prompts stay in English regardless — that's an implementation detail of the illustration step, not something the source-intake step decides.

---

## Brief.md structure

`brief.md` is plain markdown so a human can scan it in any editor. It collects everything the rest of the pipeline needs to know about the source in one place. Fields:

- **Original URL or file path.** The raw input the user provided — link, absolute path, or the marker `pasted-text` if the user pasted the body directly.
- **Detected language.** The language code returned by `detect_language.py` (e.g., `en`, `es`, `de`). Used by editorial to keep slide text in the source's language.
- **Extracted title.** The article title, lifted from the URL's HTML metadata, the file's first heading, or inferred from the first line of pasted text.
- **Extracted author.** The author name if the source exposes one. This field is optional — if no author can be extracted, the field is omitted from `brief.md` rather than left blank or filled with a placeholder.
- **Full body text.** The normalized plain-text body of the source. This is what editorial will draw from when writing slide headlines and supporting lines.
- **Key quotes pulled.** A short list of high-signal sentences extracted from the body — typically the lines with the sharpest specificity, numbers, or contrast. The cover-angle lab uses these as raw material for hook drafting.

---

## How the next step reads brief.md

Step 5 of the pipeline — the cover-angle lab — reads `brief.md` to draft 3–5 candidate cover hooks. It depends on three fields: **extracted title** (signals the source's framing), **full body text** (the substrate for hook generation), and **key quotes pulled** (the highest-signal source material).

If any of those three fields is missing or empty in `brief.md`, the skill flags the gap to the user and stops rather than silently substituting a generic placeholder. A missing title is recoverable — the user can supply one. A missing body is not — the run cancels and the user re-runs with a usable source.
