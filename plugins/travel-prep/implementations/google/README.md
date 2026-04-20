# Google Implementation

> Use Google Calendar and Gmail for trip detection and confirmation scanning.

## What this implements

| Capability | How it's fulfilled |
|---|---|
| Calendar read | Google Calendar MCP |
| Email search / read | Gmail MCP |

## Setup

### Google Calendar MCP

1. Install the Google Calendar MCP in your agent environment
2. Authenticate with the traveler's Google account (work + personal if flights may appear in either)
3. Confirm the MCP can list events across all relevant calendars
4. Test: ask the agent to list events for the next 7 days — flights should appear

### Gmail MCP

1. Install the Gmail MCP in your agent environment
2. Authenticate with the inbox where travel confirmations land
3. Confirm the MCP can search by date range and keywords
4. Test: search for "confirmation" in the last 30 days — booking emails should appear

## Multi-account note

Flights booked personally often appear in a personal Google Calendar, while work meetings are in a work calendar. If the traveler uses both:
- Authenticate both accounts with Google Calendar MCP
- Use `--all` flag or equivalent to search across all calendars
- Same applies to Gmail if personal and work inboxes are separate

## What the skills search for

**Calendar:** events with "flight", airline names (United, Delta, etc.), or `FLT` in the title. Also hotel check-in/out events and conference registrations.

**Gmail:** searches for — `confirmation`, `itinerary`, `booking`, `reservation`, `check-in`, airline names, hotel brand names, `Airbnb`, `rental car`. Date-scoped to the trip window.
