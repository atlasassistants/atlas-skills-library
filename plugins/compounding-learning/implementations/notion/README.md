# Notion Implementation

> Use Notion as the knowledge base and memory store instead of local files.

## What this implements

Replace local file writes with Notion MCP calls. Each destination maps to a Notion database or page.

| Capability | Notion equivalent |
|---|---|
| Skills (`brain/knowledge/skills/`) | A "Skills" database — one page per skill |
| Lessons learned | A "Lessons Learned" database or page with append blocks |
| Patterns (`memory/patterns.md`) | A "Patterns" database or running page |
| Decisions (`memory/decisions.md`) | A "Decisions" database |
| Corrections (`memory/corrections.md`) | A "Corrections" database |
| People notes (`memory/people/`) | A "People" database — one page per person |
| Rules file (`AGENTS.md`) | A "Rules" page in Notion (read back into context each session) |

## Setup

1. Install the Notion MCP in your agent environment
2. Create the databases/pages above in your Notion workspace
3. Copy the database IDs and note them somewhere accessible
4. In each skill's SKILL.md, replace the file path references with Notion MCP calls pointing to your database IDs

## Notes

- The Notion MCP provides `create_page`, `append_block_children`, and `update_page` — these cover all write operations the skills need
- For `AGENTS.md` equivalence, read the Notion rules page into context at session start
- The skill logic is identical — only the write destination changes
