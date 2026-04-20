---
name: pre-trip-briefing
description: When a flight or trip is detected on the calendar, generate a comprehensive pre-trip briefing — itinerary (from calendar + email confirmations), weather, packing notes, check-in reminder, seat upgrade opportunity, lounge access by card, ground transport, and event context from email. Delivers 72 hours before departure.
when_to_use: Runs automatically when a flight appears on the calendar and the 72-hour window before departure arrives. Also triggered manually: "pre-trip briefing", "prep my trip", "briefing for my trip to [destination]", "trip briefing for [date]", "what do I need for my trip next week". For the proactive trigger: fires when calendar scan detects a flight event and the departure date is within 72 hours.
atlas_methodology: opinionated
---

# pre-trip-briefing

Generate a full pre-trip briefing by connecting calendar, email, weather, and the traveler's profile — without being asked.

## Purpose

A travel briefing that just restates the calendar isn't useful. The value is in the connections: the hotel confirmation number from email, the lounge the traveler can access with their specific card, the event agenda attached to the conference registration, the dress code mentioned in the organizer's email. This skill makes those connections and surfaces them in a single scannable briefing.

## Inputs

- **Upcoming trip** (required) — inferred from calendar, or passed explicitly as a destination and date range
- **Travel Profile** (required for personalization) — read from `brain/knowledge/travel/travel-playbook.md`. If missing, run `travel-onboarding` first.
- **Calendar access** (required) — flights, hotels, meetings, and events during trip dates
- **Email access** (required for full briefing) — confirmation emails, event registrations, organizer correspondence

## Required capabilities

- **Calendar read** — all calendar accounts, full trip date range
- **Email search / read** — inbox search by date range, keywords (confirmation, booking, reservation, itinerary, flight, hotel)
- **Weather lookup** — multi-day forecast for destination
- **Knowledge base read + write** — read Travel Profile; append airport notes
- **Web search** (optional) — lounge research for airports not yet in Airport Notes

## Steps

1. **Load methodology references.** `references/atlas-travel-prep-methodology.md` (data sources, delivery timeline, proactive principles) and `skills/pre-trip-briefing/references/atlas-briefing-framework.md` (full briefing template and section definitions).
2. **Read the Travel Profile** from `brain/knowledge/travel/travel-playbook.md`. Note lounge-eligible cards, seat preferences, security enrollment, and packing style.
3. **Identify the trip.** From the calendar: flight events, hotel check-in/out, conference registrations, meetings, and dinners in the trip window. If multiple trips are detected, confirm which one to brief.
4. **Pull email confirmations.** Search email for: airline itinerary, hotel booking confirmation, rental car reservation, Airbnb confirmation, conference registration, event invites, restaurant reservations, and any organizer correspondence for events during the trip.
5. **Get weather.** Look up a multi-day forecast for the destination covering the trip dates.
6. **Research lounge access.** Check Airport Notes in the playbook for the departure airport (and layover airports). If notes don't exist, research lounges available with the traveler's cards and append to Airport Notes.
7. **Identify action items.** Based on trip timing: check-in window (typically 24 hours before), seat upgrade opportunity (check if upgrade is available), bag payment reminder (if checking bags), anything else the traveler needs to do before departure.
8. **Build the briefing** using the template in `atlas-briefing-framework.md`. Connect calendar and email data — don't just list calendar events, annotate them with confirmation details from email.
9. **Deliver the briefing** to the traveler's configured channel.
10. **Update Airport Notes** if new lounge or airport information was researched during this briefing.

## Output

See `skills/pre-trip-briefing/references/atlas-briefing-framework.md` for the full briefing format. A well-built briefing is scannable in under 3 minutes and contains no "check your email for details" — those details are already in the briefing.

```
Pre-Trip Briefing — Chicago | Apr 28–30

⚠️ Action items (before you leave):
- Check in opens: Apr 27 at 9:15am (United flight 423)
- Seat upgrade available: Seat 4C (Economy Plus) — upgrade for $89

ITINERARY
...

LOUNGE ACCESS
O'Hare Terminal 1: United Club (available — United Gold status)
Midway: No lounge access with your cards

WEATHER
Chicago Apr 28–30: 58°F / 42°F, partly cloudy, 20% chance rain Friday

[... full briefing continues per framework ...]
```

## Customization

Common things clients adjust:

- **Delivery timing.** Default is 72 hours before departure. Override in this SKILL.md.
- **Briefing depth.** Edit `skills/pre-trip-briefing/references/atlas-briefing-framework.md` to add, remove, or reorder sections.
- **Airport notes accumulation.** On by default — appends lounge research to the playbook. Disable if you don't want this.
- **Email search scope.** Default searches the primary inbox. Expand to include specific labels or folders if travel confirmations are filtered.

## Why opinionated

The briefing's value comes from the discipline of always connecting data sources — never just restating the calendar, never telling the traveler to "check your email for the confirmation." The methodology encodes that discipline: specific data sources for each section, always personalized to the Travel Profile, always proactive. That's what makes it feel like a well-briefed EA and not a calendar summary.
