---
name: daily-reporting-setup
description: Configure a deployment of the daily-reporting skill. Use when a deployment is setting up daily-reporting for first use or updating its saved defaults (source map, continuity store, review/finalization rules, retrieval windows).
when_to_use: User says "set up daily reporting", "configure daily-reporting", "daily-reporting setup", "update daily-reporting defaults", "install daily-reporting". Also runs when first-time setup is incomplete or a deployment needs its saved config updated. Do NOT use for running the reporting cycle itself — invoke `daily-reporting` for that.
atlas_methodology: neutral
---

# Daily Reporting Setup

`daily-reporting-setup` saves the defaults the reporting skill should reuse each run.

Use this file when a deployment needs to set up `daily-reporting` for first use or update its saved defaults later.

## Write Contract

| Output | Target | When |
|--------|--------|------|
| Saved deployment config | deployment config store chosen by the client or tool using this package | after successful setup or update |
| Validation result | `validation_status` block in the saved config | whenever setup validates the deployment |

**Naming:** keep the saved object named `deployment_config`.
**Skip write when:** if required fields are missing or validation is blocked, do not mark setup complete. A partial config should be saved only if the client intentionally supports incomplete setup.

## Source keys

See `../../references/schemas/deployment-config-schema.md` §Source keys for the canonical list of the six source keys the setup config must use in `source_map` and retrieval windows. Connector names may differ from these keys (for example, `tasks` → `executive-workflow`, `meetings` → `meeting-notes`, `prior_state` → `prior-state`).

## What setup needs to save

A valid setup should save at least:
- default timezone
- default participants
- continuity store
- delivery policy
- review policy
- retrieval policy
- retrieval windows
- source map
- validation status

## Precondition — connections exist

Before starting setup, determine whether the deployment has at
least one active connection for each external source family the
operator intends to enable (`calendar`, `email`, `tasks`,
`meetings`). The two internal source keys (`prior_state`,
`manual`) need no connection.

If the operator has no connections yet, or is unsure, run
`../connect-sources/SKILL.md` first and return here once every
intended-enabled external source family has an active connection.

An AI tool running this skill MUST resolve this precondition
before proceeding to step 1 of Setup workflow. Do not begin the
setup workflow with unresolved connection state.

## Setup workflow

1. Confirm the executive's task and priority context shape and enabled modes (`sod`, `eod`, or both).
2. Save default participants and timezone.
3. Choose where reports and structured continuity state will be saved.
4. Map approved source families only.
5. Configure `prior_state` and `manual` support.
6. Confirm the priority-resolution rule. The plugin ships a single canonical priority ladder in `../../references/policies/retrieval-rules.md` ("Source Priority"); setup does not save a per-deployment priority policy. Setup's only obligation here is to confirm the deployment accepts the canonical ladder (a no-op for most deployments) and to ensure the source map in step 4 provides the sources the ladder references (at minimum `tasks` or `manual`; see `../../references/policies/retrieval-rules.md` "Required vs. optional sources").
7. Define review, finalization, and continuity behavior.
8. Define delivery behavior.
9. Define retrieval rules.
10. Validate the deployment.
11. Run a lightweight test cycle when possible — see "Example test cycle" below for the minimum `runtime_input`, expected output shape, and pass/fail rule.

Keep setup focused on reusable configuration.

What belongs in this setup file:
- reusable defaults
- source mapping
- review and finalization rules
- retrieval rules
- continuity rules

What stays outside this setup file:
- auth and secrets
- exact storage wiring
- delivery destinations
- scheduling
- transport or runtime wrappers

## Review, finalization, and continuity

Setup must save a `review_policy` block.

The deployment must choose one finalization mode. See `../../references/policies/review-and-locking.md` ("Finalization Modes") for the three modes (`reviewed_locked`, `auto_locked`, `send_only`) and their per-mode semantics.

Save the full `review_policy` shape defined in `../../references/schemas/deployment-config-schema.md` §Review policy.

Important rules:
- for the `send_only`-does-not-create-continuity rule, see `../../references/policies/review-and-locking.md` ("Critical Rule")
- a correction should not count as confirmation unless explicitly configured

## Validation rules

Do not mark setup complete unless every rule in the canonical "Minimum valid deployment" checklist is satisfied. The authoritative list lives in `../../references/schemas/deployment-config-schema.md` ("Minimum valid deployment"); consult it for the full set of rules (including "at least one mode is enabled," "every `review_policy.can_review` and `review_policy.can_confirm` entry corresponds to the `owner_type` of at least one participant" — see `../../references/policies/review-and-locking.md`, "Reviewer authority resolution," — "approved source mappings are connected or explicitly manual," and "validation has no unresolved blocking issue").

Before marking setup complete, confirm the runtime implements all capabilities in `../../references/policies/runtime-capabilities.md`. For a per-capability proof checklist, see `../../references/conformance.md` (written in cluster 5 of the v1.1 rollout).

## Example test cycle

Step 11 of the setup workflow is a one-run sanity check that the deployment's saved config produces a runnable `daily-reporting` cycle. It does not replace validation (step 10); it exercises the wiring end-to-end.

Minimum `runtime_input`:

```text
runtime_input
- mode: "sod"
```

This is the smallest runnable input per `../../references/schemas/runtime-input-schema.md` ("Minimum required runtime input"). `report_date` resolves from the saved default timezone; all other runtime overrides are omitted so the run exercises saved config rather than one-run changes.

Expected output shape: conformant to `../../references/schemas/output-schema.md` — a populated `structured_state` block and a human-readable report. `merged_context.priorities` should be non-empty (sourced from `tasks` or `manual` per `../../references/policies/retrieval-rules.md` "Required vs. optional sources").

Pass/fail rule:

- **Pass** when `status` is `final` or `partial`, `validation_meta.warnings` contains no blocking-class entries (see `../../references/policies/review-and-locking.md` "Auto-lock validation gate" for the blocking-class enumeration), and the output conforms to `../../references/schemas/output-schema.md`.
- **Fail** when `status` is `blocked`, or a blocking-class warning is present, or the output does not conform to the output schema. A failing test cycle indicates the deployment is not yet ready for regular runs — resolve the warnings and re-run before relying on the deployment.

A test cycle that ends in `status: partial` with only optional-source outages is a pass; the deployment is runnable but degraded. Use `finalization_mode: send_only` (see `../../references/policies/review-and-locking.md` "Finalization Modes") to exercise the end-to-end path without writing continuity during setup verification.

## References

- `./assets/config-template.json`
- `../../references/schemas/deployment-config-schema.md`
- `../../references/schemas/runtime-input-schema.md`
- `../../references/schemas/output-schema.md`
- `../../references/policies/retrieval-rules.md`
- `../../references/policies/review-and-locking.md`
- `../../references/policies/runtime-capabilities.md`
- `../../references/conformance.md`
