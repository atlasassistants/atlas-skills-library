# Methodology Patterns

This library exists because Atlas Assistants has developed opinionated ways of doing specific kinds of work — meeting prep, debriefs, inbox triage, client onboarding — that consistently outperform the naive default. When we publish a plugin that encodes one of those methods, the method **is** the product. The wrapper is easy; the method is why the wrapper is worth installing.

This doc explains how methodology is structured, how to decide whether your skill should encode a method or stay neutral, and how opinionated skills are expected to load their reference material.

## 1. Why methodology matters

A meeting-debrief skill that just says "summarize the meeting" is a thin wrapper any team could write in an afternoon. A meeting-debrief skill that loads Atlas's specific framework for capturing commitments, surfacing unspoken concerns, and triaging follow-ups is a different product entirely — it transfers real expertise into the agent runtime and gives every client the benefit of how Atlas actually runs the work.

Treat opinionated methodology as the differentiator. A skill that bakes in a battle-tested Atlas method is more valuable than a generic one, and it's the reason clients want to install our library rather than roll their own.

## 2. The two stances

Every skill in this library declares one of two methodology stances in its SKILL.md frontmatter:

### `opinionated`

The skill assumes Atlas's method. It loads one or more methodology reference docs by default (via progressive disclosure) and shapes its output around that framework. Clients who want to customize the method fork the plugin and edit the reference docs — the skill body stays stable, only the references change. This gives each client a clean override path without forking the whole skill.

### `neutral`

The skill is generic and methodology-free. It performs a mechanical task where there's no meaningful "Atlas way" — or where the right approach varies so much by client context that encoding one would hurt more than it helps. The `references/` folder is optional for neutral skills; if it exists at all, it holds configuration or examples rather than opinionated framework docs.

## 3. How to decide

Use this checklist when deciding whether your new skill should be opinionated or neutral:

- **Does Atlas have a battle-tested way of doing this?** If yes → lean `opinionated`.
- **Is the Atlas way meaningfully better than the naive default?** If you can't explain how it's better in one sentence, it's probably not worth encoding → lean `neutral`.
- **Does the right approach vary heavily by client context?** If the "right answer" flips depending on industry, team size, or project stage → lean `neutral`.
- **When in doubt, start `neutral` and promote later.** It's easier to add opinionation to a neutral skill once you've seen it run on real work than to rip out a half-baked method after clients have started forking it.

The worst outcome is a skill that's opinionated in name but has a weak method — clients get a thin framework with no real insight, and they end up forking it anyway. Don't ship `opinionated` until you have something worth opinion-ing.

## 4. How it's declared

The stance is declared in the skill's YAML frontmatter:

```yaml
---
name: meeting-debrief
description: [trigger-rich description]
when_to_use: [concrete situations]
atlas_methodology: opinionated
---
```

Or, for a neutral skill:

```yaml
---
name: meeting-scan
description: [trigger-rich description]
when_to_use: [concrete situations]
atlas_methodology: neutral
---
```

The field is required. Reviewers will block any skill that omits it.

## 5. Reference doc conventions for opinionated skills

Opinionated skills keep their method in separate markdown files under `skills/<skill-name>/references/`. This matters for two reasons: it keeps the skill body focused on "what to do" while the references hold "how Atlas thinks about it", and it gives clients a single place to override when they fork.

Naming convention:

- `atlas-<topic>-methodology.md` — the core method (principles, steps, decision rules).
- `atlas-<topic>-framework.md` — if you have a named framework with steps or a model.
- Additional reference docs as needed, always prefixed with `atlas-` so they're obviously part of the method.

Each reference doc should cover:

- **Principles** — the three to five beliefs the method is built on.
- **Framework or steps** — the concrete procedure, in an order the agent can follow.
- **Examples of good output** — one or two real (or realistic) examples that show what "done well" looks like.

The skill body loads these references via progressive disclosure — it tells the host agent to read the reference when the skill activates, rather than inlining the whole framework into the skill itself. This keeps the skill body short and makes the method swappable.

## 6. Examples from v1

The `meeting-ops` plugin ships four skills that illustrate both stances:

- **`meeting-scan`** — `neutral`. Scanning a calendar for upcoming meetings is a mechanical task; there's no meaningful Atlas opinion about how to list events, so the skill stays generic.
- **`internal-meeting-prep`** — `opinionated`. Atlas has a specific approach for preparing for internal syncs (what context to pull, what to surface, what to ignore), and it's loaded from a methodology reference.
- **`external-meeting-prep`** — `opinionated`. External meetings (clients, partners, prospects) get a different Atlas playbook that emphasizes stakeholder context, unspoken concerns, and explicit outcome targets.
- **`meeting-debrief`** — `opinionated`. The debrief skill is where the methodology pays off most — it uses an Atlas framework for capturing commitments, surfacing blockers, and triaging follow-ups into the right downstream systems.

Use these as references when you're structuring your own skill. If your skill is doing mechanical listing or filtering, it probably should be neutral. If it's shaping judgment or producing structured output that reflects how Atlas works, it probably should be opinionated.
