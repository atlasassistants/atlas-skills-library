# Source-Quality Filtering

## Purpose

This policy declares per-source filtering rules for `daily-reporting`. Filtering has two phases: (a) **noise exclusion** — drop items that are definitely not executive-relevant; (b) **signal prioritization** — rank remaining items by executive-relevance so retrieval budgets (see `retrieval-budgets.md`) keep the highest-signal items.

## Validation note

The filtering rules below are Atlas defaults based on typical executive noise profiles. Sample your organization's real data during deployment setup and tune the rules via `connector_settings.<connector>.filtering_overrides` if the defaults misfire. Filtering is applied before retrieval budgets so budget slots reflect kept items, not raw source volume.

## Per-source rules

### calendar

**Noise exclusion:**
- Drop events with no attendees AND no title.
- Drop events the executive declined.
- Drop events marked private unless on the executive's own calendar.
- Drop all-day holiday events by default (deployments can override for holiday-heavy industries).

**Signal prioritization** (rank remaining events by):
1. Executive is a required attendee (highest signal)
2. Event falls in working hours
3. Event has a linked doc / agenda / prep material
4. Recency relative to now

### email

**Noise exclusion:**
- Drop threads with a `List-Unsubscribe` header (marketing / promotional).
- Drop automated notifications (common sender patterns: `noreply@`, `no-reply@`, `donotreply@`, `notifications@`).
- Drop threads where the executive is only BCC'd.
- Drop threads with no executive-directed content in the most recent 3 messages.

**Signal prioritization** (rank remaining threads by):
1. Thread carries a deployment-configured high-signal label (examples: `Needs Action`, `Urgent`, `Important`, `VIP`). Configurable via `connector_settings.gmail.high_signal_labels` (new optional string-array field).
2. Starred by the executive.
3. Sender is a VIP. Configurable via `connector_settings.gmail.vip_senders` (new optional string-array field).
4. Addressed directly to the executive (To:, not Cc:).
5. Most recent reply is from the executive.

### tasks

**Noise exclusion:**
- Drop archived tasks.
- Drop tasks completed before the retrieval window.
- Drop tasks owned by non-executives unless `connector_settings.executive-workflow.include_support_work_only_if_exec_relevant` is true.

**Signal prioritization** (rank remaining tasks by):
1. Priority flag (high first).
2. Due this cycle (today for SOD; today-or-tomorrow for EOD).
3. Blocked / blocking status.
4. Most recently updated.

### meetings

**Noise exclusion:**
- Drop notes with no action items AND no decisions.
- Drop notes from meetings the executive didn't attend unless decisions were cc'd to the executive.
- Drop speaker-notes-only transcripts lacking structured meeting output.

**Signal prioritization** (rank remaining notes by):
1. Contains a decision affecting the current cycle.
2. Contains an action item owned by or affecting the executive.
3. Recency (last 7 days).
4. Meeting had executive attendance.

### prior_state

No filtering. Already shape-validated by the `structured_state` schema and the v1.0 corrupted-prior-state rule in `continuity-model.md`.

### manual

No filtering. Operator input is authoritative.

## Interaction with `validation_meta`

Filtered items are **not** `missing_sources` and do **not** emit warnings. They are deliberate exclusions, invisible to the report.

## Override mechanism

Deployments extend `connector_settings.<connector>.filtering_overrides` (optional object sub-field declared in `../schemas/deployment-config-schema.md`) to relax or tighten noise rules. Whitelist-style signal-prioritization fields (like `gmail.high_signal_labels`, `gmail.vip_senders`) are also declared in that schema and overridable via the same path. Override shape is per-connector; documented in each connector's Rules section.
