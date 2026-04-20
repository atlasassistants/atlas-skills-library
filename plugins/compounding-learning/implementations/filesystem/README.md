# Filesystem Implementation

> Default implementation. Uses local file paths for all knowledge base and memory writes.

## What this implements

All three skills write to local markdown files. No external services, no APIs.

| Capability | Path |
|---|---|
| Knowledge base write (skills) | `brain/knowledge/skills/{name}.md` |
| Knowledge base write (insights) | `brain/knowledge/lessons-learned.md` |
| Memory write (patterns) | `memory/patterns.md` |
| Memory write (decisions) | `memory/decisions.md` |
| Memory write (corrections) | `memory/corrections.md` |
| Memory write (people) | `memory/people/{name}.md` |
| Rules file write | `AGENTS.md` |

## Setup

1. Confirm the `brain/` and `memory/` directories exist in your agent's working context
2. Confirm `AGENTS.md` exists and is writable
3. No credentials, no API keys, no dependencies

That's it. The filesystem implementation is the default — no configuration required if your agent has access to these paths.

## Changing default paths

If your knowledge base uses a different structure, edit the file paths in each skill's `SKILL.md` under the Steps section. The paths are the only thing to change — the skill logic is identical regardless of where the files live.
