# Retrieval Budgets

## Purpose

This policy declares per-source retrieval budgets for `daily-reporting`. Budgets keep reports focused on executive-actionable signal, keep customer API cost predictable, avoid rate-limit-induced flakiness, and bound run latency.

## Governing principle — Signal over volume

The plugin biases toward insight and actionability, not comprehensive coverage. Budgets are intentionally tight: a focused 5-item list of decisions and action items is more valuable than a 40-item dump. Connectors apply source filtering (see `source-filtering.md`) *before* retrieval budgets, so budget slots go to high-signal items — not to items that would have been filtered out downstream anyway.

## Default budgets

| Source | SOD budget | EOD budget | Rationale |
|---|---|---|---|
| `calendar` | ≤ 10 events | ≤ 15 events | SOD's window is today only; EOD covers today + tomorrow preview (per `source-windows.md`). A packed executive has 8–10 meetings per day. |
| `email` | ≤ 10 threads | ≤ 10 threads | Signal-prioritized (not FIFO) — see `source-filtering.md` for selection. |
| `tasks` | ≤ 10 items | ≤ 10 items | Executive-owned, priority-flagged, due this cycle. |
| `meetings` | ≤ 5 notes | ≤ 5 notes | Last 7 days at most; decisions-rich or action-item-rich only. |
| `prior_state` | 1 record | 1 record | Single locked state. |
| `manual` | unbounded | unbounded | Operator-authoritative. |

## Backpressure semantics

When a budget is hit, the connector truncates by keeping the highest-signal items first (per the per-source selection rules in `source-filtering.md`), NOT by keeping the newest / most recent. The connector then emits a `validation_meta.warnings` entry naming the source and the budget that was hit.

Budgets never fail a run; they degrade gracefully to partial coverage. A truncated run still produces an insight-rich report, not a garbage-in-garbage-out summary.

## Override mechanism

A deployment may override default budgets per source via `connector_settings.<connector>.budget` — a new optional integer sub-field declared in `../schemas/deployment-config-schema.md` (`connector_settings` sub-shape).

## Validation note

The defaults above are Atlas recommendations calibrated to the signal-over-volume principle. Deployments with unusually low-volume or high-volume executives can tune them, but looser budgets should be paired with tighter filtering (see `source-filtering.md`) — otherwise the report becomes noisy. Deployments with unusually low executive engagement can tighten budgets below the defaults; this does not require loosening filtering.
