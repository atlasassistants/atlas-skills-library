# Slack Implementation

> Use Slack for internal follow-up messages and status reports.

## What this implements

| Capability | How it's fulfilled |
|---|---|
| Messaging send (chase messages) | Slack MCP — send DM or channel message to team member |
| Status report delivery | Slack MCP — send to user's DM or ops channel |

## Setup

1. Install the Slack MCP in your agent environment
2. Authenticate with your Slack workspace
3. Note the channel or DM IDs for:
   - Internal team members (for chase messages)
   - User's primary ops channel or DM (for status reports)
4. In `skills/run-proactive-actions/SKILL.md`, update the messaging step to use Slack MCP calls with these IDs

## Channel routing

The skill sends two types of messages:
- **Chase messages** → internal team member's DM (use their Slack user ID)
- **Status report** → user's configured ops channel or DM

Configure both in the skill's first-run setup. Never route chase messages to external-facing channels.

## Notes

- The Slack MCP's `chat.postMessage` covers all messaging needs
- Keep chase messages short — 2–3 sentences, conversational tone
- The status report can be sent as a formatted block message for better readability
