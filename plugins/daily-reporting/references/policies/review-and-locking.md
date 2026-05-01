# Review and Locking

## Purpose

This document defines how `daily-reporting` moves from draft to reviewed report to saved continuity.

## Core Definitions

- `verified` — checked against a real source or explicitly supplied by a human
- `reviewed` — examined by a human reviewer
- `confirmed` — approved by an authorized human
- `locked` — confirmed and saved as continuity

## Reviewer authority resolution

`review_policy.can_review` and `review_policy.can_confirm` declare who is authorized to review and confirm reports. This subsection is the canonical definition of how their entries resolve to participants; other files (deployment-config schema, setup skill) must defer to it.

### Resolution contract

Each `can_review` and `can_confirm` entry is a closed enum value drawn from the `owner_type` vocabulary declared in `../schemas/deployment-config-schema.md` ("Participants (canonical shape)"). Allowed values: `exec`, `ea`, `assistant`. Do not use `"executive"`, a participant `name`, or a free-text `role` label as an authority entry.

### Referential-integrity rule

Every value that appears in `can_review` or `can_confirm` must correspond to the `owner_type` of at least one entry in `defaults.participants`. A saved config fails validation if any authority entry does not resolve to a participant — for example, `can_confirm: ["exec"]` is invalid when no participant has `owner_type: "exec"`.

At runtime, a reviewer or confirmer is authorized when their `owner_type` appears in the relevant list. Names in `structured_state.confirmed_by` resolve to participants via `participants[].name`; the participant's `owner_type` is then checked against `can_review` / `can_confirm`.

The authority vocabulary, the `owner_type` enum, and `structured_state.confirmed_role` share one closed set of values (`exec` | `ea` | `assistant`) so the resolution rule is unambiguous and can be checked statically at setup time rather than only at runtime.

## Executive Scope Rule

Review and locking validate only executive-relevant content:
- executive priorities
- executive blockers
- executive dependencies
- executive carryovers
- executive unresolved items
- support work only when it materially affects executive execution

If the draft drifts beyond that, narrow it before finalization.

## Finalization Modes

### `reviewed_locked`
- draft generated
- review may happen
- confirmation required
- final report sent
- final report/state become continuity

### `auto_locked`
- report generated
- no per-run confirmation required
- **auto-lock validation gate runs before the lock** (see "Auto-lock validation gate" below)
- sent automatically if the gate passes
- report/state become continuity automatically if the gate passes

### `send_only`
- report generated
- report sent
- no lock by default
- does not create continuity by default

### Auto-lock validation gate

Because `auto_locked` commits the report to continuity with no human in the loop, it must not commit a poisoned report. Before the lock, the runtime must evaluate the following gate. If any condition below is true, **do not auto-lock** — downgrade `status` to `blocked` (or route the run to manual review per the saved review policy) and surface the failing condition in `validation_meta.warnings`.

Block the auto-lock if any of the following are true:

1. `merged_context.priorities` is empty. An auto-locked report with no priorities has no executive content to carry forward and almost always reflects upstream source failure rather than a genuinely empty day.
2. `validation_meta.warnings` contains at least one blocking-class entry. Blocking-class warnings include (but are not limited to) any warning emitted by the "If data is missing" case (b) path in `../../skills/daily-reporting/SKILL.md` (connector error/timeout/auth failure/invalid payload), any `validation_meta.missing_sources[]` entry with `reason: required_but_absent` or `reason: invalid_payload`, and any explicit "prior locked state failed schema validation" warning from the corrupted-prior-state rule in `continuity-model.md`.
3. `continuity_status` is `unavailable` when continuity was expected for this run. "Expected" means the `prior_state` source is enabled in `deployment_config.defaults.source_map` and the run is not a known `first_run`. A silent `unavailable` on an established deployment almost always indicates connector failure or a corrupted prior-state record — not a genuinely empty cycle — and must not be auto-locked.

Deployments running EOD in `auto_locked` mode should consider stricter defaults, since EOD's structured state seeds the next SOD (see `continuity-model.md`, "Default Continuity Flow"): a poisoned EOD auto-lock silently corrupts the next day's starting point.

The gate is additive to — not a replacement for — upstream source validation; its purpose is to catch the residual cases where upstream validation passed individual records but the composed report is still not safe to lock.

## Draft state

"Draft state" is a **persisted continuity class**, distinct from the `draft` lifecycle stage inside `reviewed_locked` (where "draft" just names the not-yet-confirmed report produced by the current run). This subsection is the canonical definition; other files (the `prior-state` connector, the deployment-config schema's `continuity_store.allow_draft_continuity` flag, the setup skill) must defer to it.

### Definition

A **draft state** is a `structured_state` record written to the continuity store *before* confirmation and locking — that is, a `structured_state` record whose corresponding report never reached `report_stage: final` and for which no `locked_at` was recorded. A **locked state** is the opposite: a `structured_state` record written only after the report reached final, confirmed, and locked status (see "Core Definitions" and "Finalization Modes" above).

Both are `structured_state` records persisted to the same continuity store; they differ only in whether the locking handshake completed before the write.

### When a host runtime writes draft state vs. locked state

A host runtime writes **locked state** whenever a run finishes the locking handshake:
- `reviewed_locked` after confirmation (the default path), or the correct-then-reconfirm path under "Correction Handling"
- `auto_locked` after the auto-lock validation gate passes

A host runtime writes **draft state** only when **both** of the following hold:

1. `continuity_store.allow_draft_continuity = true` in the deployment's saved configuration (see `../schemas/deployment-config-schema.md`, the `continuity_store` sub-shape). When this flag is `false` (the default in the starter template and example config), the runtime must not persist draft state at all — an un-locked run ends without writing `structured_state` to continuity, and the next cycle resolves prior state per the fallback chains in `continuity-model.md`.
2. The run ended without reaching `locked` — for example, a `reviewed_locked` run whose reviewer never confirmed within the review window (see "Non-confirm exits from `reviewed_locked`"), a `send_only` run under a deployment that has opted into `send_only_reports_create_continuity = true` but has not yet locked, or an `auto_locked` run whose validation gate blocked the lock and left the draft in `report_stage: generated`.

When both conditions hold, the runtime **may** persist the run's `structured_state` as draft state. When `allow_draft_continuity = false`, neither condition is sufficient on its own — the runtime must not write draft state even if the rest of the report pipeline completed.

### How draft state interacts with the `prior-state` connector

The `prior-state` connector's rule "do not use draft state unless the deployment explicitly allows draft continuity" (see `../../skills/prior-state/SKILL.md`) is the read-side mirror of the write-side rule above. When `connector_settings.prior-state.allow_draft_continuity = false` (the default), the connector must refuse to seed `prior_locked_state` from any `structured_state` record that is not a locked state — even if one is present on disk — and must resolve prior state as if no eligible record existed, following the fallback chains in `continuity-model.md`. When the flag is `true`, the connector may seed from draft state, and the resulting run must surface the weaker provenance via `validation_meta.warnings` so reviewers know continuity came from an un-locked record.

This keeps `allow_draft_continuity` load-bearing on both sides of the continuity store: the write side decides whether draft state is ever persisted, and the read side decides whether a persisted draft is eligible to seed the next cycle.

## Critical Rule

`send_only` must not create continuity unless `send_only_reports_create_continuity = true`.

## Correction Handling

"Correction Handling" scopes only to **pre-lock** reports — a report whose `report_stage` is not yet `final` and for which no `locked_at` has been recorded (see "Core Definitions" and "Draft state"). A correction arriving against a pre-lock draft is the normal path:

1. apply the correction
2. generate a revised draft
3. follow the saved review policy

A correction is not confirmation unless `correction_from_authorized_confirmer_implies_confirmation = true`.

### Post-lock corrections

A correction arriving after a report has reached `locked` status (its `structured_state` is already saved as continuity — see "Core Definitions") does not follow the pre-lock path above. Locked continuity is immutable by default; the correction-apply-and-revise handshake above would silently mutate a continuity record that the next cycle may already have read.

Post-lock corrections are handled by an explicit **unlock + relock** cycle:

1. an authorized confirmer (per `review_policy.can_confirm`) must explicitly unlock the report — this clears `locked_at`, moves `report_stage` back to `generated` (so the original draft is re-available for editing), and emits a `validation_meta.warnings` entry naming the unlock (for example, "post-lock correction: unlocked 2025-01-14 SOD for re-review")
2. the correction is then applied via the pre-lock "Correction Handling" path above
3. the revised draft follows the deployment's saved review policy and, on reconfirmation, relocks — overwriting the prior continuity record for the same `(mode, report_date, deployment)` tuple

A post-lock correction that does not go through the unlock step must be refused. Silent in-place mutation of a locked `structured_state` is forbidden — it would break the "locked is immutable" invariant the `prior-state` connector and the continuity fallback chains in `continuity-model.md` rely on. Deployments that prefer not to support post-lock corrections at all may refuse the unlock request outright; the default for deployments that accept them is the explicit unlock + relock cycle above.

## Non-confirm exits from `reviewed_locked`

The `reviewed_locked` flow documented above covers the confirm path (draft → review → confirm → lock) and, via "Correction Handling", the correct-then-reconfirm path. It must also cover the non-confirm exits below; a `reviewed_locked` run must never remain in `report_stage: generated` indefinitely because of a missing reviewer response.

### Reviewer declines without correcting

If an authorized reviewer explicitly declines to confirm the draft and does not supply a correction:

- do not lock
- set `status: blocked` and add a `validation_meta.warnings` entry naming the decline (for example, "reviewer declined draft for 2025-01-14 SOD without correction")
- leave `report_stage` at `generated` (the draft never advanced past review) and omit `confirmed_by` / `confirmed_role` / `confirmed_at` / `locked_at`
- do not write `structured_state` to continuity for this run

The decline is an explicit outcome, not a timeout — the reviewer saw the draft and refused it.

### Review does not complete within the deployment's window

If no confirmation (and no decline) arrives within a deployment-configured review window, the run has timed out. Each deployment must pick exactly one of the following three resolutions in its saved review policy; the chosen resolution is the authoritative exit:

1. **retry** — re-send the draft to the `review_destination` (or to a deployment-defined escalation surface) and reset the window. Continue to hold the run in `report_stage: generated` with a `validation_meta.warnings` entry recording the retry.
2. **escalate** — route the draft to a deployment-defined escalation reviewer (typically a second authorized confirmer). Set `status: partial` until escalation resolves, and add a `validation_meta.warnings` entry naming the escalation.
3. **expire** — abandon the draft. Set `status: blocked`, leave `report_stage` at `generated`, add a `validation_meta.warnings` entry naming the expiry, and do not write `structured_state` to continuity.

All three exits tie the outcome to `report_stage` and `validation_meta.warnings` so the output captures the result deterministically rather than leaving the run silently unfinished. Deployments that have not chosen a resolution should default to `expire` — the conservative choice, since it never locks un-reviewed content.

## Material vs. non-material edits

The `material_edits_require_reconfirmation` and `non_material_edits_require_reconfirmation` fields in `review_policy` gate whether an authorized reviewer must re-confirm a report after an edit. This subsection is the canonical definition of which edits fall into each class. Other files (deployment-config schema, setup skill) must defer to this definition.

### Material edits

An edit is **material** when it changes any content that feeds continuity or changes the executive decisions the report asserts. Any change to the following counts as material:

- any field of `structured_state` (the machine-readable continuity block)
- priorities — adding, removing, reordering, or changing the wording of a priority's intent (e.g., swapping priority 1 and priority 2; replacing "ship pricing page" with "ship pricing page v2"; adding a fourth priority)
- carryovers — adding, removing, or changing the subject of a carryover (e.g., marking a carryover as resolved, adding a new carryover pulled from a meeting)
- unresolved items / blockers / dependencies — adding, removing, or changing the subject (e.g., adding "waiting on legal review" as a new blocker)
- scope or day boundaries — changing the reporting date, timezone, or the set of participants the report is about
- source attribution or authority — changing which source a claim is tied to, or flipping a claim between `verified` and unverified

### Non-material edits

An edit is **non-material** when it only polishes the human-readable report without changing continuity or executive decisions. Examples:

- typo or grammar fix in the prose narrative
- rewording a sentence for tone or clarity where the underlying claim is unchanged
- reformatting a bullet list, reflowing paragraphs, fixing markdown rendering
- adjusting greeting, sign-off, or framing sentences
- tightening verbose phrasing without changing the asserted fact

### Tie-breaker

If an edit is ambiguous (e.g., a reworded narrative sentence that arguably shifts emphasis), treat it as material. The cost of an unnecessary re-confirmation is lower than the cost of silently locking a changed claim.

### Tie-breaker procedure

When the tie-breaker above is invoked, apply these three tests in order. Each test is a concrete check a reviewer (or an automated diff tool) can run against the before-and-after artifacts of the edit.

1. **Structural test first.** If the edit changes any value in `structured_state` — the arrays (`priorities`, `carryovers`, `dependencies`, `risks`, `unresolved_items`, `completed_items`, `notes_for_next_cycle`), the scalars (`report_date`, `mode`, `timezone`, `status`), or adds/removes entries in any of those arrays — the edit is material. This holds regardless of how similar the surrounding wording looks, because `structured_state` is what seeds the next cycle via continuity (see `../schemas/output-schema.md` "Structured state" and `continuity-model.md` "EOD → next-SOD handoff payload").
2. **Human-readable-report test.** If the edit changes ONLY `human_readable_report` text AND the underlying `merged_context` fields the slot draws from are unchanged, the edit is non-material polish. This is the ordinary typo-fix / rewording case and does not need re-confirmation under `non_material_edits_require_reconfirmation = false`.
3. **Slot-change test.** If the edit changes which source field a polish slot draws from (for example, rewriting `{{priority_context_summary}}` so that it now draws from `merged_context.blockers` instead of `merged_context.priorities`), or changes the polish slot's substance such that a re-derivation from `merged_context` would not produce the same output, the edit is material — even if no `structured_state` field changed. The "Polish-slot verification" rule in `../schemas/output-schema.md` treats re-derivation equivalence as the polish-legitimacy test, and an edit that breaks that equivalence has moved the report off its declared sources.
4. **Default to material.** When the three tests above are inconclusive — the reviewer cannot decide whether the reworded sentence re-derives from the same sources, or a structural diff is ambiguous because of field reordering — treat the edit as material. This is the conservative default: it costs at most one extra re-confirmation, while misclassifying a material edit as non-material erodes the audit trail and, under `auto_locked`, would silently commit the changed claim to continuity.

Worked examples:

- **Example A (non-material).** A reviewer reworded `{{priority_context_summary}}` from "Renewal decision is the priority" to "The renewal decision is this cycle's priority." The underlying `merged_context.priorities[0]` is unchanged and a re-derivation from the same source would produce an equivalent synthesis. Structural test: no `structured_state` change. Human-readable-report test: prose-only. Slot-change test: same source, equivalent output. **Non-material.**
- **Example B (material).** A reviewer changed the first priority from "Finalize operator training outline" to "Finalize operator training deck." `structured_state.priorities[0]` changed — the underlying executive commitment the report asserts is now different. Structural test: `structured_state.priorities` changed. **Material**, regardless of how small the wording delta looks.

## Deployment posture

**Guiding principle.** The plugin respects deployment choice — if a customer configures `auto_locked`, that is the customer's call, not something the plugin second-guesses. Operational guardrails here are limited to: (a) starting customers on a safe default, (b) warning transparently on clearly risky configurations, and (c) a narrow corrupted-state cooldown that forces review only while data integrity is in question.

### Rules (runtime enforces)

1. **Run-history gate on `auto_locked`.** A deployment must have at least N successful `reviewed_locked` runs (recommended default: N = 10) before the runtime permits `auto_locked`. The runtime tracks this via its own run-history mechanism (see `runtime-capabilities.md`, "Run-history tracking"). This is not a persisted continuity field — tracking is runtime-local.

2. **Day-0 `auto_locked` warning.** A deployment configured with `auto_locked` from day 0 causes the runtime to emit a `day_zero_auto_lock` warning entry in `validation_meta.warnings` on every run until the run-history gate in rule 1 is satisfied. This is a warning, not a block — the customer's configuration is honored.

3. **Corrupted-state cooldown on `auto_locked`.** After a corrupted-prior-state incident (see `continuity-model.md`, "Corrupted prior state rule"), the runtime SHOULD NOT honor an `auto_locked` configuration for the affected deployment for 7 days (one week from the incident). During that window, the runtime SHOULD degrade to `reviewed_locked`. On the FIRST run after the incident, the runtime SHOULD present an upfront, human-readable explanation to the reviewer: (a) what happened (a corrupted prior state was detected on run X at time Y), (b) what the runtime is doing about it (forcing `reviewed_locked` for 7 days), (c) when the cooldown ends (date/time), (d) a pointer to where operators can investigate the root cause. The goal is transparency, not paternalism.

4. **Safe-posture defaults (starter).** The starter config template (`../../skills/daily-reporting-setup/assets/config-template.json`) begins customers on the safe posture. Customers can change any default; the starter just begins them safely.
