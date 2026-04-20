# Microsoft Implementation

> Use Outlook Calendar and Outlook email for trip detection and confirmation scanning.

## What this implements

| Capability | How it's fulfilled |
|---|---|
| Calendar read | Outlook MCP / Microsoft Graph MCP |
| Email search / read | Outlook MCP / Microsoft Graph MCP |

## Setup

### Outlook Calendar MCP

1. Install the Outlook MCP or Microsoft Graph MCP in your agent environment
2. Authenticate with the traveler's Microsoft account
3. Confirm the MCP can list calendar events with attendees, start/end times, and event body
4. Test: list events for the next 7 days — flights should appear

### Outlook email MCP

1. Authenticate the same MCP for mailbox access (Microsoft Graph covers both)
2. Confirm the MCP can search mail by date range, sender, and keywords
3. Test: search for "confirmation" in the last 30 days

## Notes

- Microsoft Graph API covers both Calendar and Mail with a single authentication — one MCP setup for both capabilities
- Outlook calendar events from flight booking services (Expedia, direct airline booking) typically include the flight details in the event body
- Outlook mail search supports the same keyword patterns as Gmail — airline names, "confirmation", "itinerary", hotel brands
