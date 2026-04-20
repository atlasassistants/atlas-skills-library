# travel-prep

> Proactive travel preparation for executive travelers — onboarding, pre-trip briefings, and day-of support.
> v0.1.0 — `medium` tier.

## What it does

Handles the full pre-trip workflow for a frequent traveler:

- **Captures travel preferences once** — airline status, loyalty programs, credit card benefits, seat preferences, hotel loyalty, ground transport style, packing habits — and stores them in a travel playbook so every future briefing is personalized.
- **Delivers pre-trip briefings automatically** — when a flight appears on the calendar, generates a comprehensive briefing covering itinerary, weather forecast, packing list, check-in reminders, seat upgrade opportunities, lounge access, ground transport, and event context pulled from email and calendar.
- **Supports day-of travel** — flight status, gate changes, ground transport confirmation, return flight monitoring.

The result: the traveler never has to ask "did you check my flight?" Everything that can be prepared is prepared before they ask.

## Who it's for

Executive assistants, personal agents, and operators supporting frequent travelers. Atlas built this for high-travel executives and founders who run back-to-back trips and need an agent that acts like an EA who already has all the context — connecting dots between calendar events, email confirmations, event agendas, and weather without being asked.

## Required capabilities

The plugin's skills depend on these capabilities. Each is named abstractly — wire it up to whatever tools the host agent has access to.

- **Calendar read** — list upcoming events, flights, meetings, and events in a time window across all relevant calendar accounts
- **Email search / read** — search inbox for travel confirmations, event registrations, hotel bookings, restaurant reservations, and related correspondence
- **Weather lookup** — fetch a multi-day forecast for a given destination
- **Knowledge base read + write** — read and update the travel playbook at `brain/knowledge/travel/travel-playbook.md`
- **Web search** (optional) — look up lounge access, airport information, and event details not available in email

## Suggested tool wiring

| Capability | Common options |
|---|---|
| Calendar read | Google Calendar MCP, Outlook MCP, any calendar API |
| Email search / read | Gmail MCP, Outlook MCP, any email search tool |
| Weather lookup | Any weather API MCP, wttr.in, OpenWeather |
| Knowledge base read + write | Filesystem MCP, Notion MCP, Obsidian vault |
| Web search | Any web search MCP, Perplexity, Brave Search |

These are examples, not requirements. Pick what the agent already has.

## Installation

```
/plugin install travel-prep@atlas
```

After installing, complete the first-run setup below — `travel-onboarding` must run before `pre-trip-briefing` will be fully personalized.

## First-run setup

> See [`instructions.md`](instructions.md) for the full setup walkthrough.

1. **Calendar wiring.** Confirm the calendar capability can read all accounts the traveler uses (work + personal if relevant). Flight events need to be visible.
2. **Email wiring.** Confirm the email capability can search and read the inbox where travel confirmations land. This is critical for pulling hotel, rental car, and event details.
3. **Travel playbook location.** Default: `brain/knowledge/travel/travel-playbook.md`. Create the file (empty is fine) and confirm it's readable and writable.
4. **Run `travel-onboarding`.** The onboarding skill collects the traveler's preferences in a conversational flow and writes the Travel Profile to the playbook. Pre-trip briefings will work without this, but they won't be personalized.
5. **Weather capability.** Wire up the weather lookup to any weather source. No specific tool required.

## Skills included

- **`travel-onboarding`** — *neutral.* Collects the traveler's preferences (airlines, status tiers, credit card benefits, seat preferences, hotel loyalty, ground transport style) in a conversational flow and writes the Travel Profile to the playbook. Run once; update as preferences change.
- **`pre-trip-briefing`** — *opinionated.* When a flight or trip is detected on the calendar, generates a comprehensive pre-trip briefing. Pulls itinerary from calendar, confirmations from email, weather for the destination, lounge access by card, and event context.
- **`day-of-support`** — *neutral.* On travel days, monitors flight status, surfaces gate changes, confirms ground transport, and tracks return flights.

## Customization notes

Common things clients change:

- **Travel playbook location.** Default is `brain/knowledge/travel/travel-playbook.md`. Override to match your knowledge base layout.
- **Briefing delivery timing.** Default: 72 hours before departure. Override in `skills/pre-trip-briefing/SKILL.md` to match the traveler's preference.
- **Briefing depth.** The briefing framework defines what sections are always included vs. optional. Edit `skills/pre-trip-briefing/references/atlas-briefing-framework.md` to adjust.
- **Airport notes accumulation.** The skill appends lounge and airport notes to the playbook over time, building institutional knowledge. Disable or redirect this if you don't want it.
- **Day-of monitoring cadence.** Default checks flight status a few hours before departure and monitors for changes. Adjust the cadence in `skills/day-of-support/SKILL.md`.

When customizing, edit the `SKILL.md` and reference files in your installed copy or fork.

## Atlas methodology

This plugin encodes Atlas's travel prep methodology — the discipline that means the traveler never has to brief themselves. Key principles:

- **Act like an EA who already has the context.** Don't just list calendar entries — connect dots. If there's a conference, pull the agenda. If there's a dinner, note the restaurant. If email mentions a dress code, surface it.
- **Proactive, not reactive.** Briefing arrives before the traveler asks. Day-of monitoring runs without prompting.
- **Build institutional knowledge.** Airport notes, lounge details, and preference updates accumulate in the travel playbook. Each trip makes future trips easier.

The full briefing framework lives at [`skills/pre-trip-briefing/references/atlas-briefing-framework.md`](skills/pre-trip-briefing/references/atlas-briefing-framework.md).

## Troubleshooting

**`pre-trip-briefing` isn't triggering on an upcoming flight.** Check that the calendar capability can see the event and that the event contains recognizable flight information (airline name, flight number, or "flight" in the title). For manually-added events, confirm the format.

**Briefing is missing hotel or event details.** The skill searches email for confirmations. If they landed in a different account or folder, check the email capability's scope. You can also provide confirmation details directly.

**Travel Profile sections are missing from the playbook.** Run `travel-onboarding` to fill in the profile. The onboarding skill will ask about any sections that are empty.

**Weather isn't showing in the briefing.** Check that the weather capability is wired up and that the destination city is parseable from the calendar event. For unusual event formats, pass the destination explicitly.

**Day-of flight status is stale.** The `day-of-support` skill relies on the configured travel information source. If flight data isn't updating, check the wired tool's coverage for that airline or route.
