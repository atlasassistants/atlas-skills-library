---
name: linkedin-carousel-builder
description: Generate save-worthy LinkedIn carousel posts from articles, newsletters, or transcripts. Produces a brand-themed PDF carousel plus a companion LinkedIn post, both rooted in the source's actual voice. Trigger phrases include "build a LinkedIn carousel," "make a carousel from this article," "turn this newsletter into a LinkedIn carousel," "draft a LinkedIn carousel for [executive]," or the slash command /linkedin-carousel-builder.
when_to_use: |
  - User says "build a LinkedIn carousel" / "build LinkedIn" / "make a LinkedIn carousel" / "create a LinkedIn carousel" / "carousel builder."
  - User shares a URL, newsletter, blog post, or article file and asks for LinkedIn-ready slides.
  - User says "turn this into a LinkedIn carousel" / "make slides from this for LinkedIn."
  - User explicitly says "draft a LinkedIn carousel for [executive / brand]."
  - User invokes /linkedin-carousel-builder (Claude Code slash command).
atlas_methodology: opinionated
---

# LinkedIn Carousel Builder

The user invokes you with one of the trigger phrases listed in `when_to_use` (or the `/linkedin-carousel-builder` slash command). They may pass a URL, a file path, pasted text, or extra guidance.

You orchestrate a 12-step pipeline. Each step references a deterministic Python script and a methodology reference doc. **Do not skip steps. Do not reorder steps. Do not fabricate output that the scripts should produce.** If any step fails, surface the failure plainly to the user and halt.

**Conventions used below:**
- "Run the script" means invoke the Python script via the available shell-execution tool, with the user's CWD as the workspace root.
- "Read the reference doc" means open the relevant file in `${CLAUDE_PLUGIN_ROOT}/skills/linkedin-carousel-builder/references/` and follow its content as the methodology for that step.
- "Ask the user" means use the available structured-question capability (e.g., AskUserQuestion).
- "Workspace root" is the user's current working directory at invocation time. Resolve all user-data paths against it. Never use the plugin install dir for user-data paths.

---

## Step 1 — Startup gate

Confirm Python, the isolated venv, dependencies, workspace scaffolding, `.env`, API key, and brand availability. This step runs at the start of every carousel run. When everything is set up, it completes in ~1 second.

**Notation in this step:** `<skill_dir>` means the directory containing this `SKILL.md` (resolves to `${CLAUDE_PLUGIN_ROOT}/skills/linkedin-carousel-builder/`). `<venv-python>` means the venv's Python interpreter — `<skill_dir>/.venv/bin/python` on Mac/Linux, `<skill_dir>/.venv/Scripts/python.exe` on Windows.

1. **System Python check.** Run `python3 --version` (or `python --version` on Windows). If unavailable or version <3.10, halt and tell the user: "Couldn't find Python 3.10+. Install from python.org/downloads, then run me again. You only need to do this once — after Python is installed, I'll handle the rest automatically (no global package installs, no version conflicts)."

2. **Skill-local venv bootstrap** (uses the standard Atlas skill-local venv pattern):

   2a. Check whether `<venv-python>` exists.
      - **If yes** → jump to 2c (sanity check).
      - **If no** → run `<system-python> -m venv "<skill_dir>/.venv"`. Expected: exits 0, no output, `<skill_dir>/.venv/` now exists.

   2b. (Skipped if venv was just created.)

   2c. **Sanity-check the venv** runs:
      ```
      "<venv-python>" --version
      ```
      If it errors (broken symlink from a system-Python upgrade, corrupted venv, anti-virus quarantine), delete `<skill_dir>/.venv/` and rebuild via 2a once. If the rebuilt venv ALSO fails the sanity check, do NOT loop — surface the error verbatim and halt with: "The venv won't run even after a fresh rebuild — the error was: `<paste error>`. This usually means the system Python install is broken, the skill folder isn't writable, or anti-virus is quarantining the venv binary. Fix the underlying issue and re-trigger."

   2d. **Check + install dependencies** in the venv. Two probes — Python packages first, then the Chromium browser bundle that Playwright needs.

      **Probe 1 — Python packages:**
      ```
      "<venv-python>" -c "import importlib.util, sys; needed = ['openai','jinja2','playwright','PIL','docx','pypdf','langdetect','bs4','requests']; missing = [m for m in needed if not importlib.util.find_spec(m)]; sys.exit(0 if not missing else 1)"
      ```
      If exit code 0 → all Python packages installed, move to Probe 2. If non-zero, tell the user: "Installing the Python dependencies into the skill's isolated environment — one-time setup, takes about 30 seconds. No global packages affected." Then run:
      ```
      "<venv-python>" -m pip install -r "<skill_dir>/requirements.txt"
      ```
      Surface failures verbatim if pip errors (no network, proxy block, etc.).

      **Probe 2 — Chromium browser bundle for Playwright:**
      ```
      "<venv-python>" -c "import sys; from playwright.sync_api import sync_playwright; p = sync_playwright().start(); ok = bool(p.chromium.executable_path) and __import__('pathlib').Path(p.chromium.executable_path).exists(); p.stop(); sys.exit(0 if ok else 1)"
      ```
      If exit code 0 → Chromium is installed, move on. If non-zero, tell the user: "First-time setup: downloading the Chromium browser used to render carousel slides. About 150 MB — depending on your connection this can take 1–15 minutes. One-time per skill install. No system-wide changes — it lives inside the skill's isolated environment." Then run:
      ```
      "<venv-python>" -m playwright install chromium
      ```
      Surface failures verbatim. On Linux, if the install reports missing system libraries, point the user at the troubleshooting row "Linux: Chromium needs system libraries" in the README.

3. **Lock in `<venv-python>` for the rest of this run.** Every Python invocation in Steps 2–12 below (and in every reference doc) uses `<venv-python>`, never bare `python3`. Quote the path if `<skill_dir>` contains spaces.

4. **Workspace scaffolding.** Check whether `<user CWD>/linkedin-carousel-builder/` exists with `brands/` and `runs/` subfolders and whether `<user CWD>/linkedin-carousel-builder.config.json` exists. If anything is missing, run `"<venv-python>" "<skill_dir>/scripts/prepare_workspace.py" "<user CWD>"` after confirming the workspace location with the user.

5. **`.env` setup.** Check whether `<user CWD>/.env` exists. If not, run `"<venv-python>" "<skill_dir>/scripts/prepare_local_env.py" "<user CWD>"`. After scaffolding, read `.env` and check the `OPENAI_API_KEY` value.

6. **API key validation.** If `OPENAI_API_KEY` is empty, tell the user: "Action needed: open `.env` and paste your key after `OPENAI_API_KEY=`. Get one at https://platform.openai.com/api-keys — you'll need a billing-enabled account with gpt-image-2 access. Tell me when ready." Wait for confirmation, then run `"<venv-python>" "<skill_dir>/scripts/validate_openai_key.py" "<user CWD>/.env"`. If the validator reports failure, surface the error verbatim and ask the user to fix.

7. **Brand profile availability.** List `<user CWD>/linkedin-carousel-builder/brands/`. If empty, offer the user a choice: pick one of the built-in starter presets (list `<skill_dir>/assets/brand-profiles/`) or create a new brand (triggers Step 3's brand-creation flow). If the user picks a built-in starter, copy that JSON into `<user CWD>/linkedin-carousel-builder/brands/` before using it — built-in starters are never read from the plugin install dir at runtime.

All seven checks must pass before Step 2. On subsequent runs (after first successful setup), checks 1–2 complete in ~1 second and 4–7 are typically no-ops.

---

## Step 2 — Companion post opt-in

Read the workspace config at `<user CWD>/linkedin-carousel-builder.config.json` for `companion_post_default` (default `"yes"`). Ask the user:

> "Should I also draft a companion LinkedIn post to go with the carousel? Default is yes — the post is short (150–300 chars), in your source article's voice, and pulls a hook from the article to make people swipe."
>
> Options: **Yes** (recommended) / **No, just the carousel** / **Yes, and update my default to always yes / always no**

Save the choice into the run config (in-memory for this run). If the user picks an "update my default" option, write the new value back to `linkedin-carousel-builder.config.json`.

## Step 3 — Theme / brand selection

Read the reference doc `references/brand-theme-setup.md` and follow it for the brand-creation paths. **Brand identity and art-style are independent decisions in this skill** — every run picks an art-style explicitly, even when reusing an existing brand. The high-level flow:

1. List existing brand profiles in `<user CWD>/linkedin-carousel-builder/brands/`. Each file is a JSON profile; the `display_name` field is the human-friendly name. **Detect light/dark variant pairs** — when two profiles share the same root slug differing only by a `-dark` or `-light` suffix (e.g., `atlas-assistants.json` + `atlas-assistants-dark.json`), present them as a single grouped entry: "**Atlas Assistants** (light + dark variants available)" so the user understands they're paired. Selecting the group resolves to the matching variant later in step 7b based on the art-style choice.
2. Ask the user: pick an existing brand, create a new brand, or refresh an existing brand (re-trigger the theme-preview gate). If they pass `--refresh-brand <slug>`, skip selection and go directly into the refresh flow for that brand.
3. **For "create new brand":** ask which of the **six** creation paths the user wants — built-in preset / website URL / description / screenshots / **design system file or folder or PDF** / **folder/repo/file the orchestrator reads directly**. Follow the matching subflow in `brand-theme-setup.md`.
   - For the design-system path: run `parse_design_system.py <user-provided-path>`. If `ok: true`, use the returned colors + fonts + raw_notes + hard_bans to seed the brand profile. If `ok: false`, surface the error and fall back to the screenshots path with the same low-confidence message used for URL failures.
   - For the folder/repo/file path: do not run any script. Read the files at the user-supplied path per the "From a folder, repo, or file" section of `brand-theme-setup.md`, propose a brand profile with citations, accept user adjustments, write the JSON to `<user CWD>/linkedin-carousel-builder/brands/<slug>.json`, and run `brand_profile_schema.py` against the file as the save-time gate.
4. **URL path low-confidence handling:** if `scrape_brand_site.py` reports `confidence: low` or `fetch_failed`, do NOT silently fall through to wrong colors. Tell the user: "I couldn't reliably extract a brand from that URL. Please share 1–3 screenshots of the website (or your existing brand assets) and I'll build the brand from those. If you'd prefer to walk through questions instead, say 'use questions instead.'" Default to the screenshots subflow; switch to questions only if they explicitly ask.
5. **Footer questions:** once colors/fonts are decided, ask for the footer LinkedIn handle and brand mark per `brand-theme-setup.md`.
6. **Initial art-style pick (for new brands):** Open `${CLAUDE_PLUGIN_ROOT}/skills/linkedin-carousel-builder/assets/art-styles/contact-sheet.jpg` in the user's image viewer. Ask the user to pick one of the 7 presets OR "Create a custom style." **When presenting the options, include the brand-background compatibility label for each preset** (see the table in `references/brand-theme-setup.md` § Art-style picker — most presets are light-bg-tuned, `midnight-editorial` and `documentary-noir` are dark-bg-designed, `bold-flat-corporate` works for either). If the user's brand background is dark, surface `midnight-editorial` (recommended), `documentary-noir`, and `bold-flat-corporate` first to avoid a frame mismatch in illustrations. Whichever they pick is saved as the brand's `default art_style`. (For new brands only — existing brands go through the override flow in step 7 instead.)
7. **Per-run art-style override (for ALL runs that use an existing brand).** After the brand is selected, ALWAYS ask:
   > "This brand's saved default style is `<art_style>`. Use it for this carousel, or pick a different style?"
   > Options:
   > - **Use saved (`<art_style>`)**
   > - **Pick different for this run only**
   > - **Pick different and update the brand's saved default**

   If the user picks "Pick different for this run only," present the same picker as step 6 (7 presets + custom + any custom styles already saved with this brand). The choice is held in the in-memory run config and does NOT modify the saved brand JSON.

   If the user picks "Pick different and update the brand's saved default," present the same picker, then rewrite the brand profile JSON on disk with the new `art_style` value before continuing.

   If the brand was just created in steps 3–6, skip this step — they already picked an art-style during creation.
7b. **Variant auto-pair check.** After both brand and art-style are locked for this run, check whether the brand has a `-light` / `-dark` sibling on disk AND whether the chosen art-style mismatches the current variant. Use the art-style compatibility table in `references/brand-theme-setup.md` § Art-style picker:
   - If the user picked `midnight-editorial` or `documentary-noir` while the current variant is light AND a `<slug>-dark.json` exists → offer:
     > "`<chosen_art_style>` is designed for dark backgrounds, and you have a dark variant of this brand saved (`<slug>-dark`). Switch to the dark variant for this run? **Switch** / **Stay on light**"
   - If the user picked a light-bg-tuned preset (`clean-saas`, `editorial-magazine`, `pastel-diagram-marker`, `hand-drawn-marker`) while the current variant is dark AND a light sibling exists → offer the symmetric swap.
   - If the user picked `bold-flat-corporate` (bg-agnostic) → no prompt; both variants render fine.
   - If no sibling exists → no prompt; user proceeds with the brand they picked.

   **Default response is Switch** when the prompt fires (most users have already implicitly chosen by picking the art-style; the swap honors their intent). The chosen variant is held in the in-memory run config and does NOT modify any saved JSON. The non-chosen variant stays on disk untouched.
8. **Theme-preview gate:** render one sample slide using the locked brand profile + the locked art-style for this run. Call `render_slide.py` with a fixed sample slide payload — headline "Make the idea easy to see," supporting line "A quick check for fonts, colors, and illustration style". Generate one illustration for the sample slide using `generate_illustration.py` with a generic visual intent ("Three connected boxes labeled Problem, Signal, Action representing a framework"). Open the rendered sample slide in the user's default image viewer. Ask the user: **Approve / Adjust colors / Adjust art style / Adjust typography / Other.** Loop until approved.
9. **Populate `accent_name` from the accent hex.** Before saving the new or updated brand profile, infer a one-word common color name from `colors.accent` (e.g. `#BA9CFF` → `"lavender"`, `#B5471F` → `"rust"`, `#0A2540` → `"navy"`). Set `brand.accent_name` to that value. This field is used by the illustration prompt templates to name the brand color in addition to its hex — image models follow named colors more reliably. The brand profile JSON is human-editable, so a user who disagrees with the inferred name can correct it later.

10. Once approved, validate the profile against the schema (`brand_profile_schema.py`) and save it to `<user CWD>/linkedin-carousel-builder/brands/linkedin-carousel-builder-brand-<slug>.json` (only if it's a new brand or the user picked the "update default" option in step 7).

The selected/created brand profile + the locked art-style for this run are the locked brand context. Store both for downstream steps. **Downstream illustration generation uses the per-run art-style override, not necessarily the brand's saved default.**

## Step 4 — Source intake

Read the reference doc `references/source-intake.md`. Then:

1. **Determine input type.** If the user passed a URL at invocation, use it. If they passed a file path, use that. If neither, ask: "What's the source for this carousel? You can paste a URL, paste the article text directly, or give me a file path (.md, .txt, .docx, or .pdf)."
2. **URL path:** run `fetch_source_url.py <url>`. If it fails (any non-ok result), tell the user the exact error message and ask them to paste the article text directly or provide a file path. Do not silently retry or skip.
3. **File path:** run `parse_source_file.py <path>`. Surface failures plainly.
4. **Pasted text:** treat the pasted text as the body. Title = first non-empty line, author = (blank).
5. **Language detection.** Run `detect_language.py` with the body text on stdin. If status is `block`, surface the error verbatim and halt the run. If status is `proceed_with_warning`, surface the warning verbatim to the user before continuing.
6. **Determine a topic slug** for the run folder: lowercase the title, replace non-alphanumerics with hyphens, collapse consecutive hyphens, and strip leading/trailing hyphens. Then trim at the LAST hyphen that keeps the slug ≤ 50 chars — this avoids mid-word cuts (e.g., `stop-chasing-ai-tools-start-building-infrastructure` becomes `stop-chasing-ai-tools-start-building` at 35 chars, not `stop-chasing-ai-tools-start-building-infrastructur` mid-word at 50). If no hyphen exists within the first 50 chars, fall back to a hard 50-char cut. If a folder by that slug already exists for today's date, append `-2`, `-3`, etc.
7. **Create the run folder** at `<user CWD>/linkedin-carousel-builder/runs/linkedin-carousel-builder-<topic-slug>-<YYYY-MM-DD>/`.
8. **Write `brief.md`** in the run folder with this structure:
   ```
   # <title>

   - **Source:** <url or file path>
   - **Author:** <author or "unknown">
   - **Detected language:** <code>
   - **Run date:** <YYYY-MM-DD>

   ## Body
   <full body text>

   ## Key quotes (top 5 by specificity)
   <pull 3–5 sentences from the body that contain numbers, named entities, or specific outcomes>
   ```

Hand off to Step 5 with the run folder path and brief.md path.

## Step 5 — Strategy + cover-angle lab

Read the reference doc `references/cover-angle-lab.md` and `references/atlas-carousel-methodology.md`.

1. **Decide slide count (7–10).** Based on the brief's body length and the number of distinct ideas you can identify, pick a target. Default to 8–9. Use 10 only if the source genuinely has 6 distinct, specific core ideas. Use 7 only if the source is tight and high-density. Never below 7 (handled by thin-source path in Step 6).
2. **Generate 3–5 candidate cover hooks** across the four formulas:
   - Numbered value ("7 X mistakes killing your Y")
   - Bold specific claim ("I did X in Y. Here's how.")
   - Direct question ("Are you doing X wrong?")
   - Contrarian take ("X is overrated.")

   Each candidate is 6–10 words, mobile-readable in 140 chars, no jargon, no emojis. Specificity from the source where possible.
3. **Pick the strongest** based on the criteria in `cover-angle-lab.md` (specificity, formula diversity in case the user re-runs).
4. **Initialize `slide-plan.md`** in the run folder with just the cover slide entry:
   ```
   # Slide plan — <topic>

   ## Slide 1 — Cover
   - **Headline:** <picked hook>
   - **Supporting line:** (none on cover)
   - **Visual intent:** <one focused iconic illustration of the cover hook's pivot/idea per editorial-review.md § "Cover slide illustration" — e.g., for hook "Stop Chasing AI Tools. Build the Harness." this might be a stylized harness/scaffold beside a discarded gear icon>
   - **Embedded message:** <one-word kicker drawn from the hook (e.g., "HARNESS", "$140 → $10") — MAY be blank for cover only, since headline carries the words; most covers benefit from a one-word label>
   - **Alt-text:** (populated in Step 7)

   **Cover is illustrated by default per atlas-carousel-methodology.md.** Leave `Visual intent` blank ONLY if one of the 3 typography-only exceptions in editorial-review.md § "When typography-only is the right call" applies; in that case, replace the visual intent line with `- **Visual intent:** (typography-only — justification: <which of the 3 exceptions and why>)`.
   ```

Hand off to Step 6 with `slide-plan.md` (draft) and the rejected hook candidates (Step 11 may use one).

## Step 6 — Editorial review

Read the reference doc `references/editorial-review.md` and `references/atlas-carousel-methodology.md`.

Follow the editorial flow:

1. **Outline core ideas** from `brief.md` — enumerate distinct, specific ideas (each backed by a number, named entity, or specific outcome from the body).
2. **Draft a stake/proof slide** (slide 2) — the strongest single fact from the source that earns the next slides (a stat, a number, a named outcome).
3. **Assign one core idea per slide** (slides 3 through N+1, where N+1 is the second-to-last slide). Each slide:
   - Headline ≤ 8 words.
   - Supporting line ≤ 15 words.
   - Visual intent = one sentence describing what the illustration should make obvious ("show the 25× gap as a bold contrast," "show the three-step Problem → Signal → Action flow as a sequence").
   - Embedded message = the literal short text the illustration should render INSIDE the artwork as a label, callout, or annotation (e.g., `25×`, `Problem / Signal / Action`, `AEO`, `88%`). 1–5 short labels, numbers, or callouts — ≤30 chars total, no emojis. Pulled from the source's numbers, named entities, or framework labels. Required for every slide with a non-empty visual intent (see `references/atlas-carousel-methodology.md` § "Slide architecture: AI illustration is the hero"). Pattern-interrupt and stake/proof slides especially benefit.
   - Question-tension: each *core-idea* slide leaves a question the next slide answers. (Rule 9 exempts cover/stake/recap/CTA.)
4. **Place the mid-carousel pattern-interrupt slot.** Typically slide 4–6. The strongest stat slide, a comparison, or a visual surprise. Mark it explicitly in the slide plan.
5. **Specificity check on body slides** (cover and CTA are exempt — rule 16). For each body slide: does it have a number, named entity, or specific outcome? If not, attempt to rewrite using language pulled directly from `brief.md`'s "Key quotes" or body. If rewrite fails (no usable source language for that idea), **cut the slide entirely**.
6. **Count post-cut body slides.** If the resulting carousel total (cover + stake + body + recap + CTA) would be **fewer than 7 slides**, HALT with the thin-source message from `atlas-carousel-methodology.md`:
   > "This source has too few distinct, specific ideas for a strong carousel. A LinkedIn carousel works best with a longer or more specific source. You can: (a) provide a longer or more specific source; (b) paste additional context into the conversation; or (c) cancel this run. I won't ship a carousel with padding or generic-advice slides."
   Wait for user direction. Do not fall back to a shorter carousel.
7. **Write recap slide** (second-to-last) per editorial-review.md § "Recap slide" — **illustrated by default** with a focused summary visual (typically a hand-drawn checklist with the core component labels OR a stacked-layer architecture diagram; ≤5 distinct sub-elements). Supporting line lists the core-idea slide headlines as a compressed sentence (e.g., "Workspace. Second Brain. Memory. Integrations."). Embedded message names the recap concept (e.g., "The Harness"). Leave `Visual intent` blank ONLY if one of the 3 typography-only exceptions in editorial-review.md § "When typography-only is the right call" applies; in that case cite the exception explicitly in the slide entry as `(typography-only — justification: <which exception>)`.
8. **Write CTA slide** (last) per rule 12 — explicit save ask + follow ask + specific comment-trigger word (e.g., "Comment AEO for the framework"). Never "comment below." **Illustrated by default** per editorial-review.md § "CTA slide" — a single action-cue icon (hand-drawn bookmark, curved arrow, or similar) with the comment-trigger word as embedded message. Leave `Visual intent` blank ONLY if one of the 3 typography-only exceptions in editorial-review.md § "When typography-only is the right call" applies; in that case cite the exception explicitly in the slide entry.
9. **Finalize `slide-plan.md`** with all slides in order. Every slide entry has headline, supporting line, visual intent, embedded message, and (deferred to Step 7) alt-text.

Hand off to Step 7 with the finalized slide plan.

## Step 7 — Slide plan + alt-text + validation

For every slide in `slide-plan.md`:

1. **Add alt-text** — a 1-sentence accessibility description of what the illustration will show (used in the rendered HTML's `alt=` attribute and consumed by the visual review loop's LLM check). Typography-only slides (which should be rare — only when an editorial-review.md § "When typography-only is the right call" exception applies) have blank alt-text.
2. **Run validation checks inline.** Inspect each slide's JSON entry against the rules below. `render_slide.py` runs the word-count subset of these checks (`_validate_slide`) automatically during the actual render in Step 9 and surfaces violations in its result `warnings` field — Step 9 is the safety net, but Step 7 catches all rules earlier so you don't pay illustration-generation cost on a slide that will fail render. Check each slide for:
   - Cover headline: 6–10 words.
   - Body headline: ≤8 words.
   - Supporting line: ≤15 words.
   - Embedded message (illustrated slides only): non-empty, ≤30 chars total, ≤5 short labels/numbers, no emojis. Typography-only slides (rare; only when an editorial-review.md exception applies) must have embedded message blank AND must cite the exception in the slide entry.
   - No emojis (check for any character in Unicode ranges U+1F300–U+1FAFF, U+2600–U+27BF, U+2300–U+23FF, or U+1F000–U+1F9FF) — applies to headline, supporting line, AND embedded message.
   - Title case for headlines (first letter of each non-trivial word capitalized).
   - Sentence case for body (only first word and proper nouns capitalized).
3. **Typography-only justification check (REQUIRED).** For any slide where `Visual intent` is blank, the slide entry MUST contain a brief comment naming which of the 3 typography-only exceptions from editorial-review.md § "When typography-only is the right call" applies (e.g., `(typography-only — justification: brand hard_bans rule out illustration aesthetic)`). If no justification is cited, REJECT the slide and return to Step 6 to either populate `visual_intent` per the methodology OR cite the exception explicitly. The methodology defaults to illustrated; typography-only is never an implicit default — every blank `visual_intent` is an explicit, justified choice. Cover, recap, and CTA slides are illustrated by default and require justification to opt out.
4. If any validation fails, return to Step 6 and rewrite the failing slide (or cut it and re-check the total slide count from Step 6 thin-source rule).
5. Re-save `slide-plan.md` with all alt-text fields populated and validations passed.

Hand off to Step 8 with the validated slide plan.

## Step 8 — Generate illustrations

Read `references/visual-rule.md` for the visual rule.

For each slide in `slide-plan.md` that has a non-empty `visual intent`:

1. Run `generate_illustration.py` with these positional args, in order:
   1. `<api_key>` — value of `OPENAI_API_KEY` from `<user CWD>/.env`
   2. `<brand_json_path>` — path to the locked brand profile from Step 3
   3. `<visual_intent>` — the slide's visual intent text
   4. `<embedded_message>` — the slide's embedded message text (the literal short label, number, or callout the art-style prompt template renders inside the artwork — see Step 6 item 3). Per Step 7 validation, every slide reaching this step has a non-empty embedded message.
   5. `<out_png_path>` — `<run folder>/illustrations/slide-NN.png`
2. Slides without a visual intent (only those explicitly marked typography-only with a cited exception per Step 7 — should be rare) are skipped here — `render_slide.py` will render them without an illustration in Step 9. (Embedded message stays blank for these slides per Step 6 / Step 7.)
3. If an illustration generation fails (API error, rate limit, etc.), retry once. If it fails twice, flag the slide for the visual review loop in Step 10 to surface to the user.

Hand off to Step 9 with the illustrations directory.

## Step 9 — Render slides

For each slide in `slide-plan.md`:

1. Run `render_slide.py` with these positional args, in order:
   1. `<brand.json>` — brand profile path from Step 3
   2. `<slide.json>` — a JSON file (write a temp one per slide) containing the slide's `slide_number`, `total_slides`, `headline`, `supporting_line`, `alt_text`
   3. `<out.png>` — `<run folder>/slides/slide-NN.png`
   4. `<illustration.png>` — (optional, 4th arg) path to `<run folder>/illustrations/slide-NN.png` if it exists, otherwise the literal string `-` (hyphen) to indicate no illustration
2. Collect any warnings the renderer returns (e.g., word-count overflow). Append to a `render-warnings.json` log in the run folder.

Hand off to Step 10 with the slides directory.

## Step 10 — Visual review loop

Read `references/visual-review-loop.md`.

1. Run `create_contact_sheet.py` to build `<run folder>/contact-sheet.jpg`.
2. Open the contact sheet in the user's default image viewer (so they can also eyeball it).
3. Read the contact sheet image using the available image-vision capability. For each slide, judge:
   - **Color fidelity:** does the brand accent color appear where expected?
   - **Visual intent match:** does the illustration on each illustrated slide match its alt-text intent?
   - **Text overflow:** is any text visibly clipped or running off the slide?
   - **Missing illustration:** is an illustration slot empty when the slide plan said one was expected?
4. For each slide with a flagged issue:
   - If text overflow or missing illustration: re-run `render_slide.py` (illustration is unchanged) or `generate_illustration.py` then `render_slide.py` (illustration was bad) — depending on issue type. Cap at 2 regeneration attempts per slide.
   - If color or visual-intent issue: regenerate the illustration once. If still wrong, mark the slide to surface in the final user message.
5. Persistent failures (slides that failed both regeneration attempts) go into a `unresolved-issues.json` log alongside `render-warnings.json`.

Hand off to Step 11 with the final slides directory + any persistent issues.

## Step 11 — Companion post copy

Only run this step if the user opted into companion post copy in Step 2. Read `references/post-copy-extraction.md`.

1. Pull 8–12 candidate sentences from `brief.md`'s body — prefer sentences that contain numbers, named entities, or specific outcomes. These are extracted verbatim, not paraphrased.
2. Pick the strongest hook from the rejected cover-angle candidates from Step 5 (variety — don't re-use the cover slide's hook verbatim in the post).
3. Compose a 150–300 char post:
   - Line 1: the hook, lands inside the first 140 chars (mobile "see more" cutoff).
   - Lines 2–4: 2–3 supporting lines compressed from candidate sentences (delete words to fit; do not rewrite).
   - Final line: a one-sentence pointer to the carousel (e.g., "Walk-through in the carousel.")
4. **Never summarize the carousel.** The post sets up the swipe; it doesn't give away the answer.
5. No emojis (rule 6 applies to the post too).
6. Validate: total chars between 150 and 300; hook within first 140 chars; word count of any single sentence ≤25.
7. Write `post-copy.md` in the run folder.

Hand off to Step 12 with the post copy path.

## Step 12 — Package PDF + final user message

1. Run `build_pdf.py` with the slides directory → `<run folder>/carousel.pdf`.
2. Compose the final user message in plain language. Include:
   - The full path to `carousel.pdf`
   - The full path to `post-copy.md` (if generated)
   - One-sentence summary: "<slide count>-slide carousel on <topic> for the <brand display name> brand."
   - Any warnings collected in `render-warnings.json` (e.g., "Slide 6 headline was 9 words — eyeball it")
   - Any persistent issues from `unresolved-issues.json` (e.g., "Slide 4 illustration regenerated twice and the color match is still slightly off — review before posting.")
3. Do NOT auto-upload to LinkedIn — v1 is manual. User pastes the PDF and the post copy themselves.

## Partial re-runs

If the user invokes the skill with `--rerun-step <step-name> <run-folder-name>`, do NOT run the full 12-step pipeline. Instead:

1. Validate `<step-name>` is one of: `illustrations`, `slides`, `contact-sheet`, `post-copy`, `pdf`. If not, surface the list of valid names and halt.
2. Validate `<run-folder-name>` exists in `<user CWD>/linkedin-carousel-builder/runs/`. If not, halt.
3. Run only the matching step:
   - `illustrations` → re-runs Step 8 against the existing slide plan
   - `slides` → re-runs Step 9 against existing illustrations and slide plan
   - `contact-sheet` → re-runs the contact-sheet portion of Step 10 only
   - `post-copy` → re-runs Step 11 against the existing brief
   - `pdf` → re-runs Step 12 against the existing slides directory
4. Surface the same final user message as a full run, but indicate that this was a re-run of a specific step.

Steps 1–7 cannot be re-run individually — those are upstream and would invalidate downstream artifacts. To redo them, the user runs the full pipeline fresh.

## Refresh-brand handling

If the user invokes the skill with `--refresh-brand <slug>`, do NOT run the carousel pipeline. Instead, re-run the theme-preview gate for the named brand (see Step 3, item 6) and save the updated profile. Surface a confirmation message when done.

## --setup handling

If the user invokes with `--setup`, run only Step 1 (startup gate) end-to-end and report status — useful for re-validating wiring after a key rotation or workspace move.
