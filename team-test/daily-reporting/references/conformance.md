# Conformance Checklist

## Purpose

This document names what a runtime MUST demonstrate to prove it implements each capability in `policies/runtime-capabilities.md`. One proof-of-implementation item per capability. Prose only — no tests, no code, no framework-specific assertions.

Runtimes hosting `daily-reporting` should be able to point to each proof item in their own operational documentation or a live demonstration. There is exactly one conformance item per capability; there are no orphans in either direction.

## Conformance items

### Capability 1 — Persistence

**Proof:** the deployment can write a `structured_state` record from a locked run, retrieve the same record on the following day's SOD run, and reject a malformed record (e.g., one missing the required `locked_at` field or carrying an out-of-enum `mode` value) per the corrupted-prior-state rule and validation checklist in `policies/continuity-model.md`.

### Capability 2 — Scheduling

**Proof:** the deployment has run at its scheduled time for at least one cycle without manual intervention. The deployment can also be invoked on-demand outside the schedule (e.g., to regenerate a report after fixing a source issue). `report_date` is correctly computed in the deployment's saved timezone, and a runtime-supplied timezone override is honored per the timezone-edge-case rules in `schemas/runtime-input-schema.md`.

### Capability 3 — Connector invocation

**Proof:** for a run where source data exceeds the budget for any source family, the deployment demonstrates that it (a) applied the `policies/source-filtering.md` noise-exclusion rules before counting against the budget, (b) applied signal prioritization to select the highest-signal items up to the budget, and (c) emitted a `validation_meta.warnings` entry naming the source and the budget that was hit.

### Capability 4 — Review surface

**Proof:** the deployment presents a drafted report to the named reviewer and records the reviewer's response (confirm / decline / edit). For an edit, the deployment applies the material-edit tie-breaker procedure in `policies/review-and-locking.md` and records the classification. The deployment handles a reviewer-declined and a reviewer-timeout case per the non-confirm exits in the same policy.

### Capability 5 — Delivery

**Proof:** the deployment sends a final locked report to the configured destination, records `delivery_meta` on the output record, and retries the delivery if the destination is transiently unavailable.

### Capability 6 — Warning surface

**Proof:** operators can point to the mechanism by which they receive `validation_meta.warnings` entries (email inbox, operations dashboard, log file, notification channel — any mechanism suffices). They can show a specific recent warning that reached them through that mechanism.

### Capability 7 — Run-history tracking

**Proof:** the deployment can answer, for a given deployment instance, (a) how many successful `reviewed_locked` runs have completed, (b) whether any corrupted-prior-state incident occurred in the last 7 days, and (c) what the current cooldown status is. For a deployment in the 7-day cooldown window, the deployment can show the upfront transparency message that was presented to the reviewer on the first post-incident run.

### Capability 8 — Safe-posture surfacing

**Proof:** the deployment correctly honors a customer's `finalization_mode: "auto_locked"` configuration when the run-history gate permits and emits the `day_zero_auto_lock` warning when it does not. During a 7-day corrupted-state cooldown, the deployment degrades to `reviewed_locked` and surfaces an explicit explanation to the reviewer (not a silent override).

## Scope

This conformance checklist covers the runtime contract only. It does NOT cover:
- Whether the runtime is built in Python, TypeScript, or anything else (the plugin is platform-agnostic).
- Authentication, authorization, data residency, or multi-tenancy — out of scope for this plugin release (the runtime-capabilities contract in `policies/runtime-capabilities.md` is deliberately narrower than a full operational contract).
- Performance, caching, or optimization beyond the retrieval-budget policy.
