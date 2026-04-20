# Linear Implementation

> Use Linear as the task board for action item tracking.

## What this implements

| Capability | How it's fulfilled |
|---|---|
| Task system write | Linear MCP — create and update issues |

## Setup

1. Install the Linear MCP in your agent environment
2. Authenticate with your Linear workspace
3. Identify or create a team/project for proactive-actions tasks
4. Set owner labels: one for the agent (e.g., "atlas"), one for the user
5. Confirm the `proactive`, `meeting-action`, and `follow-up` labels exist in Linear (or create them)

## Task creation pattern

When the skill creates a task, it maps to a Linear issue:

| Field | Value |
|---|---|
| Title | Action item description |
| Assignee | Agent label or user label |
| Status | In Progress / Done / In Review (maps to bucket) |
| Labels | `proactive`, `meeting-action`, source tag |
| Description | Full context including source meeting and date |

## Notes

- Linear MCP's `createIssue` and `updateIssue` cover all task operations
- Include the source meeting in the issue description: "From: [Meeting Title] [Date]"
- For NEEDS HUMAN items, set priority to Urgent or High based on meeting context
