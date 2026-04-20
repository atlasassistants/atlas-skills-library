# travel-prep — Setup Instructions

> Follow these steps before running `pre-trip-briefing` for the first time.

## What requires setup

This plugin reads live data — calendar events, emails, weather — to build personalized travel briefings. Three capabilities must be wired up, and one onboarding skill must run before briefings are fully personalized.

1. **Calendar access** — to detect upcoming trips and read event details
2. **Email access** — to find travel confirmations, hotel bookings, and event correspondence
3. **Travel playbook** — where travel preferences are stored
4. **`travel-onboarding`** — must run once to capture preferences before briefings are personalized

---

## Setup step 1: Wire calendar access

The skill scans for upcoming flights and trip-related events.

- **What it needs:** read access to all calendar accounts the traveler uses (work and personal if relevant)
- **What to check:** flight events, hotel check-ins, conference registrations, and meetings during travel dates must all be visible
- **Multi-account note:** if the traveler uses separate work and personal calendars, confirm both are accessible. Flights booked personally often appear in the personal calendar only.

Configure the calendar capability in your agent's tool settings to include all relevant accounts.

---

## Setup step 2: Wire email access

The skill searches email to pull travel confirmations, itinerary details, and event correspondence.

- **What it needs:** search and read access to the inbox where travel confirmations land
- **What it looks for:** airline confirmations, hotel reservations, rental car bookings, Airbnb confirmations, conference registration emails, dinner reservations, event invites
- **Multi-account note:** if travel confirmations go to a personal email but the agent primarily reads a work inbox, confirm access to both

This capability is what makes the briefing feel like a human EA prepared it — connecting flight itineraries with hotel check-ins and event agendas from email.

---

## Setup step 3: Create the travel playbook

Create the file where travel preferences are stored:

**Default path:** `brain/knowledge/travel/travel-playbook.md`

The file can start empty — `travel-onboarding` will populate it. If the path doesn't exist yet, create the directory and an empty markdown file:

```
brain/
  knowledge/
    travel/
      travel-playbook.md   ← create this (empty is fine)
```

Confirm the agent can read and write this file.

If you prefer a different path, note it and update `SKILL.md` in each travel skill to match.

---

## Setup step 4: Wire weather lookup

The skill fetches a multi-day forecast for the travel destination.

- **What it needs:** any weather tool that accepts a city name and returns a multi-day forecast
- **Common options:** any weather API MCP, wttr.in (no API key required), OpenWeather

No specific tool required — any weather source that the agent can call works.

---

## Setup step 5: Run travel-onboarding

Before the first pre-trip briefing, run:

```
Run travel onboarding for [traveler name].
```

The skill will ask about:
- Preferred airlines and loyalty status
- Credit cards with travel benefits (for lounge access and perks)
- TSA PreCheck / Global Entry / CLEAR status
- Seat preferences (aisle/window, short vs. overnight flights)
- Bag preferences (carry-on only vs. check bags)
- Hotel loyalty programs and status
- Ground transport preferences (car service, rideshare, rental)
- Home airport

This runs conversationally — not a form dump. Answers are written to the travel playbook automatically.

**Skip onboarding?** The skill will still produce a briefing — it just won't include personalized lounge recommendations, seat upgrade advice, or packing notes.

---

## Setup step 6: Verify

After onboarding, test with an upcoming trip:

```
Generate a pre-trip briefing for my trip to [destination] on [date].
```

Confirm:
- Itinerary pulled from calendar
- Hotel / event details pulled from email
- Weather included
- Travel Profile preferences reflected (lounge access, seat advice, packing)

---

## Notes

- **Briefings run proactively by default.** Once wired up, the skill delivers briefings 72 hours before departure without being asked. Adjust the timing in `skills/pre-trip-briefing/SKILL.md`.
- **Airport notes accumulate over time.** The skill appends lounge and airport details to the playbook after each trip. This builds up automatically.
- **Day-of support runs separately.** The `day-of-support` skill monitors flight status on travel days — no additional setup beyond calendar and travel information access.
