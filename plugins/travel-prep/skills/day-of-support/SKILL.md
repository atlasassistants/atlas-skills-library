---
name: day-of-support
description: On travel days, monitor flight status, surface gate changes, confirm ground transport logistics, and track return flights. Runs proactively on any day a flight appears on the calendar.
when_to_use: Fires automatically on any day where the calendar shows a flight event. Also triggered manually: "flight status", "what's my gate", "is my flight on time", "check my flight", "day of travel support", "travel day check". For the proactive trigger: scans calendar each morning and activates for any day with a flight.
atlas_methodology: neutral
---

# day-of-support

Monitor and surface what the traveler needs on travel days — without being asked.

## Purpose

On travel days, the traveler's attention is elsewhere. This skill runs in the background: checking whether the flight is on time, surfacing gate changes before the traveler discovers them at the airport, and confirming ground transport so nothing is left to chance.

## Inputs

- **Flight information** (required) — inferred from calendar or Travel Profile confirmation details
- **Travel Profile** (optional) — ground transport preferences from `brain/knowledge/travel/travel-playbook.md`

## Required capabilities

- **Calendar read** — identify flight events and confirm travel day details
- **Travel information source** — fetch live flight status, gate, and delay information
- **Messaging send** (optional) — proactively push flight status updates to the traveler

## Steps

1. **Load the methodology reference.** `references/atlas-travel-prep-methodology.md` — day-of monitoring context and timeline.
2. **Identify today's flight(s)** from the calendar. Note departure time, airline, flight number, and origin airport.
3. **Check initial flight status.** Look up current status: on time, delayed, or cancelled. Note gate if available.
4. **Surface any issues immediately.** If delayed or cancelled, surface the full impact — connection risk, arrival time change, options if applicable. Don't wait for the next scheduled check.
5. **Confirm departure-side ground transport.** Based on Travel Profile preferences — confirm the traveler has transport to the airport arranged.
6. **Monitor during the travel window.** Continue checking flight status and gate at reasonable intervals through departure. Surface any changes.
7. **Track return flight** (if applicable). Identify the return leg on the calendar. Monitor its status starting a few hours before the return departure.
8. **Confirm arrival-side ground transport** (if applicable). Based on the return itinerary — flag if anything needs to be arranged for the trip home.

## Output

A brief status update pushed to the traveler when there's something to know:

```
Flight check — United 423 to Chicago (today, 9:15am)
Status: On time ✅
Gate: B22 (Terminal 1)
Departs in: 3h 20min

Ground transport: Rideshare — no action needed if using app.
```

If there's an issue:

```
⚠️ Flight alert — United 423 to Chicago
Status: Delayed — new departure 11:45am (+2h 30min)
Gate: B22 (no gate change)

Impact: Hotel check-in pushed to ~4:30pm. Dinner at 7pm should still be fine.
No action needed unless you want to notify your contacts.
```

## Customization

Common things clients adjust:

- **Monitoring frequency.** Default checks a few times before departure. Adjust cadence if the traveler wants more or fewer updates.
- **Status push channel.** Confirm where updates should go — same channel as the pre-trip briefing, or a different one for day-of alerts.
- **Return flight monitoring.** On by default. Disable if the traveler doesn't want return flight tracking.
- **Ground transport prompts.** On by default, based on Travel Profile preferences. Disable if the traveler always handles this independently.

## Why neutral

The day-of workflow is mechanical — find the flight, check the status, surface changes. Atlas has no opinionated method for "the right way to check whether a flight is on time." The value is in proactive delivery — the traveler doesn't have to ask.
