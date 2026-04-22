# Skill Lifecycle

Every plugin and skill in this library moves through a defined set of phases from first idea to public release. This document describes those phases, the gates between them, where each phase physically lives, and who drives each transition.

The goal is simple: at any moment you should be able to tell what phase a plugin is in by looking at the folder it lives in — or by checking the product-management board in Notion, which tracks phases 1–2 before any code exists.

## 1. Why this exists

The library is a shared product. Plugins that reach `plugins/` are installed by Atlas clients and EAs and are expected to work on real client work. That requires two things: a deliberate path from "someone had an idea" to "this is publicly installable", and discipline about not publishing work that hasn't been validated by someone other than the author.

A clean lifecycle makes that discipline legible. A reviewer knows what a plugin has already been through. A builder knows what's expected of them before merge. A client knows that anything in `plugins/` has passed the team-test bar.

## 2. The seven phases

| # | Phase | Where it lives | Who drives it |
|---|-------|----------------|---------------|
| 1 | Candidate | R&D backlog (Notion + weekly skill R&D notes) | Product team |
| 2 | Scoped | Scope brief written; tracked on the Notion board | Product team |
| 3 | In Build | Author's working branch in this repo | Author |
| 4 | Self-Test | Same branch; PR opened against `main` | Author |
| 5 | Team Test | Merged to `main`, lives in `team-test/<plugin>` | Atlas teammates |
| 6 | Live | Promoted into `plugins/<plugin>`, listed in `marketplace.json` | Product team |
| 7 | Deprecated | Moved to `deprecated/<plugin>` (or removed) | Product team |

A plugin can exit to Deprecated from any earlier phase if the work no longer makes sense. The seven phases are the progression of a successful plugin, not a guaranteed path.

## 3. Phases in detail

### 3.1 Candidate

The plugin is an idea, scored and triaged but not committed to build. Candidates live in the weekly skill R&D notes and on the Notion board. No repo presence yet.

**Exit gate:** Product team picks the candidate for build and a one-paragraph scope brief is written.

### 3.2 Scoped

The scope brief defines the plugin's job, trigger, write contract, and what's explicitly out of scope. An owner is assigned. The Notion card moves to "Scoped".

**Exit gate:** Owner has capacity and starts authoring.

### 3.3 In Build

The author creates a working branch in this repo and authors the plugin following the standard layout in `contributing.md`. Nothing is merged yet.

**Exit gate:** Plugin is functionally complete — all skills, references, and README sections are drafted.

### 3.4 Self-Test

The author runs the plugin on real input (not a toy example) and documents the smoke test in the PR description: real input, real output, honest assessment. The author fixes anything the smoke test surfaces before requesting review.

**Exit gate:** Product team reviews the PR and merges the plugin into `team-test/` on `main` (not `plugins/`).

### 3.5 Team Test

The plugin now lives at `team-test/<plugin-name>` on `main`. Because it's not listed in `marketplace.json`, clients and EAs using `/plugin marketplace add` cannot see it. Atlas teammates install it directly (by local path or git subpath) to try it on their own real work.

The goal of this phase is to get the plugin run by at least one non-author Atlas teammate on real work. Feedback goes back to the author; fixes ship as additional commits to the `team-test/` folder.

**Exit gate:** At least one non-author teammate has used the plugin on real work and confirmed it works. Promotion PR opened.

### 3.6 Live

The product team opens a promotion PR that:

1. Moves the plugin folder: `git mv team-test/<plugin> plugins/<plugin>`.
2. Adds a plugin entry to `.claude-plugin/marketplace.json`.
3. Documents the teammate validation in the PR description — who ran it, on what work, whether the outcome was good.

Once merged, the plugin is publicly installable via `/plugin install <name>@atlas`.

### 3.7 Deprecated

A plugin retires when it's no longer useful, has been superseded, or failed in a way that can't be patched. The product team moves the folder to `deprecated/<plugin>` (or removes it entirely) and removes the entry from `marketplace.json`.

Clients who had it installed continue running their local copy; updates stop.

## 4. Folder structure

| Folder | Meaning | Listed in marketplace? |
|--------|---------|------------------------|
| `plugins/` | Live, publicly installable | Yes |
| `team-test/` | In team testing, not public | No |
| `deprecated/` | Retired | No |

`plugins/` is the single public surface. The marketplace manifest at `.claude-plugin/marketplace.json` only lists plugins in `plugins/`. This is the enforcement mechanism — a plugin that is not listed is invisible to `/plugin install`. No special ignore rule is required.

## 5. Installing a team-test plugin

Atlas teammates install a team-test plugin directly (by local path or git subpath) rather than through the marketplace, because the marketplace does not expose it. Exact commands depend on your Claude Code version — check `/plugin help`. The point is that team-test is opt-in; only teammates who deliberately install from the `team-test/` path see the plugin.

## 6. Promotion ritual (Team Test → Live)

Promotion is a separate PR, not bundled with any other change. The PR:

- Moves the plugin folder from `team-test/` to `plugins/`.
- Adds the plugin entry to `marketplace.json`.
- Documents the teammate validation — who ran it, on what work, whether the outcome was good.
- Gets product-team review like any other PR.

There is no automated eval suite gating promotion in v1. The trust signal is "at least one non-author teammate used this on real work and it worked." A future version of this lifecycle may add eval-based promotion on top of team validation; when it does, it will be documented here.

## 7. Updating a live plugin

Once a plugin is in `plugins/`, changes to it — bug fixes, new skills, behavior changes, breaking changes — follow the same lifecycle as a brand-new plugin. There is no fast-path for small updates. Everything in `plugins/` must have been validated by a non-author Atlas teammate, and that bar holds for updates too.

The flow:

1. Author creates a working branch and authors the new version under `team-test/<plugin>/`. While this work is in flight, the plugin exists in the repo twice — the current live version in `plugins/<plugin>/` and the candidate version in `team-test/<plugin>/`. This is expected, not a duplication bug.
2. Author self-tests, opens a PR, product team merges into `team-test/`.
3. An Atlas teammate other than the author uses the candidate on real work.
4. Product team opens a promotion PR that:
   - Replaces the current live version: `rm -rf plugins/<plugin>/ && git mv team-test/<plugin> plugins/<plugin>`.
   - Bumps the `version` field in `plugin.json` following semver (patch for bug fixes, minor for additive changes, major for breaking changes).
   - Documents the teammate validation in the PR description.

Once the promotion PR merges, clients who update the plugin receive the new version. Clients who haven't updated keep running the previous version locally until they manually update.

Previous versions are not preserved on `main` — `plugins/<plugin>/` always holds the current live version only. Git history is the record of past versions.

The Notion board tracks each version as its own lifecycle card. The new version moves from Candidate through Live independently; the previous version's card is closed when the new version promotes.

## 8. Ownership summary

| Phase | Owner |
|-------|-------|
| Candidate, Scoped | Product team |
| In Build, Self-Test | Author |
| Team Test | Atlas teammates (anyone on the team other than the author) |
| Live, Deprecated | Product team |

"Product team" means whoever on Atlas is responsible for the library's direction at a given time.

## 9. Tracking

The Notion product-management board is the source of truth for what plugins are in what phase from Candidate through Deprecated. The repo folder structure is the physical reflection of phases 5–7; Notion tracks the full lifecycle including phases 1–4 that don't yet exist in the repo.

When a plugin moves between phases, update the Notion card. The folder move in the repo is the commit that records the transition on the code side.
