# Atlas pre-trip briefing framework

> Loaded by `pre-trip-briefing` before generating any travel briefing.

## The principle

A pre-trip briefing is not a calendar summary. It connects calendar events with email confirmation details, Travel Profile preferences, weather, and lounge research into a single scannable document. The traveler should be able to read it in under 3 minutes and have everything they need — no "check your email for details."

## Briefing sections

Every pre-trip briefing follows this structure. All sections are required unless explicitly marked optional.

---

### ⚠️ Action items

**What it is:** Things the traveler needs to do before departure. Shown first, above everything else.

**What to include:**
- Check-in window: exact open date/time for each flight
- Seat upgrade opportunity (if available)
- Bag payment reminder (if checking bags per Travel Profile)
- Anything else time-sensitive before departure

**Format:**
```
⚠️ Action items (before you leave):
- Check in opens: [date] at [time] ([airline] flight [number])
- [Any other action item]
```

If there are no action items, omit this section.

---

### Trip overview

**What it is:** One-line summary of the trip — where, when, why.

**Format:**
```
Pre-Trip Briefing — [Destination] | [Dates]
[One sentence: trip purpose — conference, client visit, personal, etc.]
```

---

### Itinerary

**What it is:** All confirmed travel elements, in chronological order, annotated with confirmation details from email.

**What to include:**
- Each flight: airline, flight number, departure time, arrival time, confirmation number
- Hotel: name, check-in date, check-out date, confirmation number
- Rental car (if applicable): company, pickup location, confirmation number
- Any other confirmed bookings

**Format:**
```
ITINERARY

[Day, Date]
[Time] [Airline] [Flight #] — [Origin] → [Destination]
  Confirmation: [number]
  Duration: [Xh Ym]

[Date] — Hotel: [Hotel Name]
  Check-in: [date] | Check-out: [date]
  Confirmation: [number]
```

**Content rule:** Never say "check your email for confirmation" — extract the confirmation number from email and include it.

---

### Lounge access

**What it is:** Which lounges the traveler can access at the departure airport (and any layover airports), based on their card benefits.

**What to include:**
- Airport and terminal
- Lounge name
- Which card provides access
- Any access restrictions (e.g., guest policy, visit limits)

**Source:** Airport Notes in travel playbook + Travel Profile card benefits.

**Format:**
```
LOUNGE ACCESS

[Airport Name] — Terminal [X]:
- [Lounge Name]: [card that provides access]
  [Any notes: guest policy, hours, etc.]

[Layover Airport] — Terminal [X]:
- No lounge access with your current cards.
```

---

### Weather

**What it is:** Multi-day forecast for the destination, covering the full trip dates.

**Format:**
```
WEATHER — [Destination]
[Day, Date]: [High]°F / [Low]°F — [condition]
[Day, Date]: [High]°F / [Low]°F — [condition]
[Day, Date]: [High]°F / [Low]°F — [condition]
```

---

### Packing notes

**What it is:** Tailored packing guidance based on weather, trip type, and Travel Profile.

**What to include:**
- Weather-appropriate clothing guidance
- Any specific items relevant to the trip type (business attire for a conference, etc.)
- Notes based on bag preference (carry-on only: no liquids over 3oz, etc.)
- Anything the traveler has noted they always forget

**Keep it brief — 3–5 bullets max.**

---

### Ground transport

**What it is:** How the traveler is getting to/from the airport and around the destination.

**What to include:**
- Departure: transport to the origin airport (based on Travel Profile preference)
- Arrival: transport from destination airport to hotel
- Local: any rental car, rideshare notes, or ground transport relevant to the trip
- Return: transport from destination airport home

**Format:**
```
GROUND TRANSPORT

To airport: [Rideshare / Car service arranged / Own car — note any logistics]
Airport → Hotel: [Option based on Travel Profile]
Return: [Status]
```

---

### Event context

**What it is:** What's actually happening during the trip, pulled from calendar events and email correspondence.

**What to include:**
- Meetings with attendees
- Conference sessions or agenda highlights (if available from email or web)
- Dinners or social events — restaurant name, who's attending, any notes from email
- Dress code or logistics from organizer emails
- Any other relevant context from email correspondence during the trip window

**Format:**
```
EVENT CONTEXT

[Date]
[Time] — [Event name]
  Attendees: [Names]
  [Any relevant notes from email: location, agenda, dress code, etc.]
```

**Content rule:** Connect calendar events to email context. Don't just list the calendar event title — annotate it with what you know from email.

---

## What a complete briefing looks like

- Action items at the top, flagged clearly
- Confirmation numbers included for every booking (not "check email")
- Lounge access specific to the traveler's actual cards
- Weather for the actual destination and actual dates
- Packing notes calibrated to weather + trip type + bag preference
- Event context that connects calendar events to email details

## What an incomplete briefing looks like (avoid)

- Sections left empty with "no information available" — research harder or omit the section
- "Check your email for the hotel confirmation" — extract it
- Generic packing advice not tailored to weather or the traveler
- Lounge recommendations not matched to the traveler's actual card benefits
- Event context that just restates calendar event titles with no additional detail
- Missing action items when check-in windows are within 24 hours
