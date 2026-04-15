# Validation Tiers

Every plugin and skill in the Atlas Skills Library ships at one of two tiers. The tier is a trust signal — it tells a client (human or agent) how much scrutiny this piece of work has received before being published. The tier is stored in `plugin.json` under the `tier` field.

## 1. Two tiers

- **`lightweight`** — reviewed and smoke-tested on a real input. This is the default for newly contributed plugins.
- **`validated`** — everything in `lightweight` plus eval-based review with variance analysis and a quality threshold.

Both tiers are legitimate. Clients can and should use `lightweight` plugins freely — the tag doesn't mean "beta" or "untrusted", it means "we've run it for real but haven't yet built a formal eval suite for it".

## 2. Lightweight gate

The lightweight gate is the minimum bar for merge into the library. Every new plugin and every new skill must pass it:

- **`skill-creator` review passes.** Each skill's description is trigger-rich, the `when_to_use` is specific, the body follows progressive-disclosure conventions, and the frontmatter is complete.
- **Real smoke test.** The author runs the skill on a real input — an actual meeting, an actual inbox item, an actual client task. Not a toy, not a hypothetical.
- **Results documented in the PR description.** The PR description names the input, shows the output, and honestly assesses whether the output was good. If the smoke test revealed problems, the PR either fixes them or explains why they're acceptable for v1.

No automation enforces this gate today. It's a discipline the reviewer checks by reading the PR. A PR that skips the smoke test — or stages a synthetic one — should be sent back.

Lightweight is the default `tier` value for any new plugin. If you're adding a new plugin to the library, your `plugin.json` should include `"tier": "lightweight"` unless you're doing a promotion PR.

## 3. Validated gate

The `validated` tier is a higher bar that adds formal eval review on top of the lightweight gate. To earn it, a plugin must satisfy all the lightweight requirements **plus**:

- **3 to 5 representative eval cases per skill.** Each case is a realistic input and a description of what a good output looks like. The cases should cover the range of scenarios the skill is meant to handle — not just the happiest path.
- **Eval run with variance analysis.** The eval is executed using `skill-creator`'s eval tooling (or its successor). Variance analysis matters: a skill that produces a great answer once but a bad answer three times out of ten is not validated.
- **Quality threshold met.** A threshold is defined at promotion time for the plugin in question. It should be specific and defensible: "at least 4/5 cases produce outputs rated 'acceptable or better' by the reviewer, with no case rated 'harmful'."

Thresholds aren't globally fixed — they're set per plugin based on what "good" means for that skill's work. A debrief skill and a calendar-scan skill shouldn't share the same pass bar.

## 4. How promotion works

Promotion from `lightweight` to `validated` is a **separate PR**, not something bundled into the original plugin PR. The promotion PR:

1. Adds the eval cases under an agreed location (in the plugin folder, likely `plugins/<name>/evals/`).
2. Runs the eval suite and attaches the output — full results and variance analysis — to the PR description.
3. Flips `"tier": "lightweight"` to `"tier": "validated"` in `plugin.json`.
4. Gets reviewed by one Atlas reviewer, same as any other PR.

> **v1 note:** The eval infrastructure described here is **not built yet**. Atlas is shipping v1 with the `lightweight` gate only. This document exists so that when we're ready to build the eval tooling and start promoting plugins, the path is already defined and the `tier` field already has the right shape. No plugin in v1 is expected to be `validated`.

## 5. How clients use the signal

Clients consuming the library can use the tier field as a trust signal however they like. Two common patterns:

- **Filter to validated.** A client agent configured for very high-stakes work may prefer (or require) `validated` plugins only. They can read the marketplace metadata and filter accordingly.
- **Prefer validated, fall back to lightweight.** Most clients will happily use lightweight plugins — they just want to know which ones have extra evidence behind them. The tier field lets them show or emphasize validated plugins without excluding the rest.

Importantly, the badge is a **trust signal, not a gate**. Lightweight plugins are not second-class citizens — they're the default, and the vast majority of useful work in this library will live there. `validated` exists for the cases where a client needs (or wants) extra proof.
