# Examples

These examples make the package easier to review and test.

Use them as sample payloads, not as hidden requirements.

Included:
- `./deployment-config.connected.json` — example saved setup output for a connected deployment
- `./runtime-input.sod-minimal.json` — smallest valid runtime input
- `./runtime-input.eod-override.json` — example one-run override payload
- `./normalized-context.sod.json` — representative normalized SOD context before drafting
- `./normalized-context.eod.json` — representative normalized EOD context before drafting
- `./output.sod-reviewed-locked.json` — representative reviewed/locked SOD output artifact
- `./output.eod-reviewed-locked.json` — representative reviewed/locked EOD output artifact

Rules:
- examples should use source keys, not replace them with connector names
- examples should avoid client-specific routing details
- examples should illustrate the schema, not become hidden implementation requirements
