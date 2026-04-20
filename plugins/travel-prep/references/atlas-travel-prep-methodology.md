# Atlas travel prep methodology

> Loaded by `travel-onboarding`, `pre-trip-briefing`, and `day-of-support` before any travel workflow runs.

## The principle

A great travel briefing feels like an EA who already has all the context prepared it. It doesn't just list calendar events — it connects dots. If there's a conference, the agenda is pulled. If there's a dinner, the restaurant is noted and who's attending is surfaced. If an email mentions a dress code, it's in the briefing. The traveler should never have to ask "did you check my flight?" — it's already been checked.

**Proactive, not reactive.** The briefing arrives before the traveler asks. Day-of monitoring runs without prompting. Lounge access is researched. Check-in windows are tracked. The traveler's job is to show up; the agent's job is to make sure everything is ready.

## The travel playbook

The travel playbook at `brain/knowledge/travel/travel-playbook.md` is the persistent record of everything the agent needs to do travel prep well. It has three sections:

### 1. Travel Profile

Captured once via `travel-onboarding`, updated as preferences change:

- **Airlines:** Preferred carriers, frequent flyer programs, status tier on each
- **Credit cards:** Cards with travel benefits — lounge access (Priority Pass, Centurion, etc.), trip delay coverage, Global Entry credit
- **TSA/Security:** PreCheck, Global Entry, CLEAR enrollment status
- **Seat preferences:** Aisle vs. window preference; does it change for overnight vs. short flights?
- **Baggage:** Carry-on only or willing to check bags?
- **Hotel:** Loyalty programs, status tier, preferences (floor, quiet room, etc.)
- **Ground transport:** Preferred style — car service, rideshare, rental car? Home airport car service vendor?
- **Home airport:** Primary departure airport

### 2. Airport Notes

Accumulated over time from past trips and research — one section per airport:

- Lounge locations by terminal and who has access (Priority Pass, Chase Sapphire Reserve, Amex Platinum, etc.)
- Security checkpoint locations and PreCheck availability
- Ground transport pickup locations
- Any useful local knowledge (best terminal for connections, hidden fast lanes, etc.)

The skill appends to this section after researching a new airport. Never duplicates — if an airport's notes already exist, update them rather than adding a second entry.

### 3. Trip History

Brief notes from past trips that may be relevant to future prep (optional, populated if useful).

## Pre-trip briefing framework

The full briefing template is in `skills/pre-trip-briefing/references/atlas-briefing-framework.md`. High-level structure:

1. **Trip overview** — destination, dates, trip type (conference, client visit, personal, etc.)
2. **Itinerary** — flights, hotel check-in/out, car rental, with confirmation numbers from email
3. **Action items before departure** — check-in window, seat upgrade opportunity, bag payment, anything the traveler needs to do
4. **Weather** — forecast for trip dates and destination
5. **Packing notes** — based on weather, trip type, and traveler's stated packing style
6. **Lounge access** — which lounges are available at departure airport and any layover, and which cards provide access
7. **Ground transport** — airport arrival transport, ground transport at destination, return transport
8. **Event context** — what's happening during the trip (from calendar and email): conference sessions, meetings, dinners, any relevant correspondence

## Data sources

| What | Where to look |
|---|---|
| Flights, meetings, events | Calendar — all accounts |
| Hotel, rental car, airline confirmations | Email — search for confirmation numbers, booking references |
| Conference agenda, event details | Email — registrations, welcome emails; web search for public agendas |
| Dinner reservations | Email — reservation confirmations |
| Dress code, logistics | Email — event invites, organizer correspondence |
| Weather | Weather lookup tool |
| Lounge access | Travel Profile (card benefits) + Airport Notes |

## Briefing delivery timeline

| When | Action |
|---|---|
| Trip detected on calendar | Create trip tracking record, start gathering information |
| 72 hours before departure | Deliver full pre-trip briefing |
| 48 hours before | Weather update; flag any unbooked items |
| 24 hours before | Check-in reminder + seat upgrade check |
| Day of departure | Flight status, gate confirmation, ground transport confirmation |
| During trip | Monitor return flight, surface gate changes |

The 72-hour default is adjustable per traveler preference.

## Onboarding flow

`travel-onboarding` collects the Travel Profile conversationally — not as a form dump. Run in two or three natural rounds:

**Round 1 — Flying basics:**
- Preferred airlines and status/loyalty tiers?
- Credit cards with travel benefits?
- TSA PreCheck, Global Entry, or CLEAR?

**Round 2 — Preferences:**
- Seat preference (aisle/window) — does it change for overnight flights?
- Carry-on only or check bags?
- Hotel loyalty programs and status?
- Preferred ground transport style?

**Round 3 (if conversation flows there):**
- Dietary needs relevant to lounge/flight meals?
- Preferred home airport?
- Anything always forgotten or always worth reminding about?

After collecting, write the complete Travel Profile to the playbook and confirm what was captured.

## What good output looks like

- Briefing arrives 72 hours before departure without being asked
- Every section is populated — no empty headers
- Confirmation numbers are pulled from email, not left as "check your email"
- Lounge access is specific: which lounge, which terminal, which card gets you in
- Action items are clearly flagged — what the traveler needs to do vs. what's just FYI
- Weather is for the actual destination and the actual trip dates

## What bad output looks like (avoid)

- Listing calendar events without connecting them to email context
- Generic packing advice not tailored to weather, trip type, or traveler preferences
- "Check your email for hotel confirmation" instead of extracting the confirmation
- Lounge recommendations that don't match the traveler's actual card benefits
- Delivering a briefing after departure
- Treating a day trip the same as a week-long conference trip
