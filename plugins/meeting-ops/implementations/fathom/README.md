# Fathom Implementation

> Use the Fathom API to fetch transcripts and detect unprocessed meetings for `meeting-debrief` and `meeting-scan`.

## What this implements

| Capability | How it's fulfilled |
|---|---|
| Transcript fetch | `fathom-api.sh transcript <recording_id>` |
| Meeting list | `fathom-api.sh meetings [limit]` |
| Auto-generated summary | `fathom-api.sh summary <recording_id>` |
| Unprocessed meeting detection | `fathom-api.sh new-since [limit]` |

## Setup

### 1. Get a Fathom API key

1. Go to your Fathom settings → Integrations → API
2. Generate an API key
3. Save it to your secrets directory:

```bash
mkdir -p ~/.atlas/secrets
echo "your-api-key-here" > ~/.atlas/secrets/fathom-api-key
chmod 600 ~/.atlas/secrets/fathom-api-key
```

The script reads from `~/.atlas/secrets/fathom-api-key` by default. Override by setting `ATLAS_SECRETS_DIR`.

### 2. Make the script available

```bash
chmod +x implementations/fathom/scripts/fathom-api.sh
```

Point the agent at this script during first-run setup as the "transcript fetch" capability.

### 3. Set WORKSPACE (for new-since)

`new-since` compares Fathom's meeting list against your local debrief files. It reads from `$WORKSPACE/brain/meetings/debriefs/`. Set `WORKSPACE` to your vault root:

```bash
export WORKSPACE=/path/to/your/vault
```

Add to your shell profile so it persists.

## Wiring to meeting-ops skills

**`meeting-debrief`** — transcript fetch:
```
Run: fathom-api.sh transcript <recording_id>
Returns JSON with transcript segments. Pass the full transcript text to the debrief skill.
```

**`meeting-scan`** — detect un-debriefed meetings:
```
Run: fathom-api.sh new-since 20
Returns: { "items": [...], "total_new": N }
Each item in "items" is a Fathom meeting not yet present in brain/meetings/debriefs/.
```

**Auto-debrief trigger.** A useful pattern: run `new-since` as part of a post-meeting check (e.g., via `/loop` or a cron) and feed any new items directly into `meeting-debrief`. The `new-since` command uses the `fathom_id` frontmatter field to track what's already been processed — so every meeting gets debriefed exactly once.

## Frontmatter contract

For `new-since` to correctly skip already-processed meetings, each debrief file must include `fathom_id` in its frontmatter:

```yaml
---
title: "Product Huddle"
date: 2026-04-21
attendees: [Alice, Bob]
fathom_id: 123456789
---
```

The debrief framework in `skills/meeting-debrief/references/atlas-debrief-framework.md` already includes `fathom_id` as an optional frontmatter field. Make sure it's populated whenever a Fathom transcript is used as the source.

## API response shapes

`meetings` and `new-since` return items in this shape:
```json
{
  "recording_id": 123456789,
  "title": "Product Huddle",
  "started_at": "2026-04-21T14:00:00Z",
  "duration_seconds": 3240
}
```

`transcript` returns segments:
```json
{
  "segments": [
    { "speaker": "Alice", "text": "...", "start_time": 0.0 }
  ]
}
```

`summary` returns Fathom's auto-generated summary — useful as a fallback when the transcript is long or not yet available.
