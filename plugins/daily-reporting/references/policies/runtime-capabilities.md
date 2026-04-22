# Runtime Capabilities

## Purpose

This policy enumerates the capabilities a runtime must provide in order to host `daily-reporting`. It is a prose checklist, not an interface definition — no function signatures, no code, no language-specific types. Any runtime — an AI coding assistant, an AI agent platform, or a traditional engineering stack — can satisfy this list in its own way.

## Capability tiers

Not all 8 capabilities are equally critical. This section clarifies which MUST exist for the plugin to function at all and which are graceful-degradation.

**Hard-required.** A runtime missing any of these cannot host `daily-reporting`:

- **Capability 1 (Persistence)** — without saving `structured_state` between runs, continuity cannot work and the plugin's core promise fails.
- **Capability 3 (Connector invocation)** — without calling enabled connectors, there is no source data to report on.
- **Capability 5 (Delivery)** — without sending the report to a destination, running the plugin has no consumable output.

**Graceful-degradation.** A runtime missing any of these can still host the plugin, with the named tradeoff:

- **Capability 2 (Scheduling)** — without automated scheduling, operators must invoke runs manually; plugin still works on-demand.
- **Capability 4 (Review surface)** — only exercised in `reviewed_locked` finalization mode. Deployments running exclusively in `auto_locked` or `send_only` do not require a review surface.
- **Capability 6 (Warning surface)** — operators miss `validation_meta.warnings` signals but reports still produce. Strongly recommended for any non-trivial deployment but not a hard block.
- **Capability 7 (Run-history tracking)** — without run-history, the operational guardrails in `../policies/review-and-locking.md` ("Deployment posture") do not fire. Plugin runs freely; deployments lose the safety net. Recommended.
- **Capability 8 (Safe-posture surfacing)** — without this, the day-0 / corrupted-state cooldown / run-history-gate advisories do not reach operators. Runs proceed but surface-level transparency is lost.

Deployments SHOULD aim for all 8. Deployments with fewer than all 8 graceful-degradation capabilities should be aware of what they lose — the conformance checklist in `../conformance.md` names what each capability must demonstrate.

## Required capabilities

### 1. Persistence

The runtime MUST write and read `structured_state` records keyed by (deployment_id, mode, report_date). It MUST support listing and single-record lookup. Before treating a loaded record as valid, it MUST honor the corrupted-prior-state validation rule in `continuity-model.md` (and the detailed checklist in the v1.0 corrupted-state validation section).

### 2. Scheduling

The runtime MUST trigger runs at schedulable times (daily minimum). It MUST support on-demand invocation outside the schedule. It MUST support timezone-aware `report_date` computation per the timezone edge cases declared in `../schemas/runtime-input-schema.md` ("Timezone edge cases").

### 3. Connector invocation

The runtime MUST call each enabled connector with the appropriate retrieval window (per `source-windows.md`). It MUST apply the retrieval-budgets policy (`retrieval-budgets.md`) and the source-filtering policy (`source-filtering.md`) in order: filter first, then apply budget truncation to the highest-signal remaining items.

For runtimes that lack native connectors, or deployments whose operators do not want to manage OAuth or API keys per provider, see `../connector-onboarding.md` for a worked example of an aggregator-backed deployment. That document is operator guidance, not a conformance requirement — Capability 3 is satisfied by any path that meets the rules in this section.

### 4. Review surface

The runtime MUST present a drafted report to the named reviewer (the mechanism is the runtime's choice: inbox, web surface, chat, whatever). It MUST accept confirm / decline / edit responses. It MUST classify edits using the material-edit tie-breaker procedure declared in `review-and-locking.md` ("Material vs. non-material edits" → "Tie-breaker procedure"). It MUST honor the reviewer-declined and reviewer-timeout exit rules declared in `review-and-locking.md` ("Non-confirm exits from reviewed_locked").

### 5. Delivery

The runtime MUST send final reports to configured destinations (per `deployment_config.defaults.delivery_policy`). It MUST handle retries using a retry policy of its own choosing. It MUST record `delivery_meta` on completion.

### 6. Warning surface

The runtime MUST surface `validation_meta.warnings` to operators via some mechanism (inbox, dashboard, notification, log). Operators MUST have a way to see the warnings. The surfacing mechanism is the runtime's choice; existence is required.

### 7. Run-history tracking

The runtime MUST track successful `reviewed_locked` run counts per deployment and corrupted-prior-state incident timestamps (with a 7-day rolling window for cooldown enforcement) in service of the operational guardrails declared in `review-and-locking.md` ("Deployment posture"). The runtime enforces the run-history gate on `auto_locked` transitions (rule 1), emits the day-0 `auto_locked` warning (rule 2), and enforces the 7-day corrupted-state cooldown with upfront human-readable transparency on the first post-incident run (rule 3).

Run-history data is runtime-local; it is NOT persisted in `structured_state` or any plugin-owned schema.

### 8. Safe-posture surfacing

The runtime MUST honor customer configuration choices — if a customer sets `finalization_mode: "auto_locked"`, the runtime MUST comply when the guardrails permit. The runtime MUST surface warnings transparently when a configuration falls into a safe-posture advisory case declared in `review-and-locking.md` ("Deployment posture"). The runtime MUST NOT silently override customer configuration; degradations (e.g., the 7-day cooldown) are explicit, explained upfront to reviewers, and time-bounded.

## Conformance

For the checklist that names WHAT A RUNTIME MUST DEMONSTRATE to prove it implements each capability above, see `../conformance.md`.
