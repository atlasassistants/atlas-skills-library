# Source Windows

These are the default retrieval windows for a normal run. The canonical enum of retrieval-window string values — the exact values that appear in `deployment_config.defaults.retrieval_windows.<mode>.<source>` and in `runtime_input.source_overrides.<family>.retrieval_window` — is declared in `../schemas/deployment-config-schema.md` under "Retrieval windows". The prose below describes the intent; the schema declares the canonical strings.

## Default SOD Windows

- `prior_state` → most recent locked EOD
- `calendar` → today only
- `email` → since last locked EOD
- `tasks` → active executive items only
- `meetings` → last 3 business days, unresolved/action-relevant only

## Default EOD Windows

- `prior_state` → current day locked SOD
- `calendar` → today plus optional tomorrow preview
- `email` → today unresolved only
- `tasks` → today plus executive carryforward candidates
- `meetings` → today only

## Rule

Pull older context only when an unresolved current-cycle item clearly depends on it.
