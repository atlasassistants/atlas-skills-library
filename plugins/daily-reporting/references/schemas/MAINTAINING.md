# Maintaining the Schema Pair

Each of the four plugin schemas exists in TWO formats:

- **Markdown** (`*-schema.md`) — source-of-truth for human readers. Carries prose rationale, examples, and narrative context.
- **JSON Schema** (`*.schema.json`) — machine-readable mirror. Enables runtime validation by any tool that parses JSON Schema draft 2020-12.

Both files MUST change together in the same commit. There is no generator (the plugin is declarative-only; no scripts). Hand-maintenance discipline prevents drift.

## When you edit a markdown schema

Before committing, verify:

1. **The corresponding `.schema.json` file reflects the same change.** If you added a field, declared a new enum value, or changed a required/optional flag in the markdown, the JSON Schema file must mirror it.
2. **All example JSONs in `../examples/` still validate against the updated schema.** Mentally trace each example field against the schema (or use an offline JSON Schema validator). Both representations must agree.
3. **`schema_version` does NOT change for additive, backward-compatible changes.** Adding an optional field, declaring a new enum value that is not yet emitted anywhere, or clarifying prose — all keep `schema_version: "1.0"`. Incrementing the version is reserved for breaking changes (a future v1.2 migration story, deferred per the v1.1 design spec).

## When you review a schema change

Verify both files changed together. Flag a PR that modified only one. The same commit should touch:

- `*-schema.md` AND `*.schema.json` (always together)
- At least one example JSON in `../examples/` if the change affects examples (e.g., a renamed field, a new required field)

## Version policy

Current: `schema_version: "1.0"` for all four schemas.

Bumping: a future v1.2 (or later) will introduce a migration story. For v1.1, the version marker is present but no migration rules are declared. Deployments pinned to v1.0 continue to work.

## `$id` and validator compatibility

The four JSON Schemas use a path-based `$id` (e.g., `daily-reporting/schemas/deployment-config`) rather than a URL. This is a deliberate design choice — the plugin is portable and does not assume a hosted URL namespace — but some JSON Schema validators expect `$id` to be URL-shaped for resolving internal `$ref`s (like `#/$defs/participant`).

If your validator fails on `$ref` resolution:

- **Python (`jsonschema` >= 4.18):** use the modern `referencing.Registry` resolver, which handles path-based `$id` correctly. Alternatively, strip `$id` before validating: `schema.pop("$id")` then pass to `Draft202012Validator`.
- **JavaScript (AJV 8+):** AJV handles path-based `$id` out of the box. For older AJV versions, either strip `$id` before compiling or switch to a URL placeholder (e.g., `tag:daily-reporting,2024:schemas/deployment-config`).
- **Other languages:** if your library is strict about URL-shaped `$id`, stripping `$id` before validation is always safe — internal `$ref`s with `#/$defs/...` resolve from the root schema regardless.

The current example JSONs in `../examples/` all validate cleanly against the schemas using `Draft202012Validator` with `$id` stripped (verified during v1.1 cluster 6).
