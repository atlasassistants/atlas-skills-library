---
name: travel-onboarding
description: Collect the traveler's preferences in a conversational flow — airlines, loyalty status, credit card travel benefits, seat preferences, hotel loyalty, ground transport style, and packing habits. Write the Travel Profile to the travel playbook. Run once; update as preferences change.
when_to_use: Use when travel preferences haven't been captured yet, or when the user asks to update them. Trigger phrases: "travel onboarding", "set up travel preferences", "update my travel profile", "I changed my seat preference", "I got Global Entry", "add my new credit card", "set up travel prep for me". Also triggered when `pre-trip-briefing` detects that the Travel Profile section in the playbook is missing or incomplete.
atlas_methodology: neutral
---

# travel-onboarding

Collect travel preferences once, conversationally. Write them to the travel playbook so every future briefing is personalized.

## Purpose

Pre-trip briefings are only as good as the preferences behind them. Without a Travel Profile, the skill can tell the traveler their flight is at 9am — but it can't tell them which lounge they can access with their Amex Platinum, whether they should request a window seat on the overnight leg, or that they always carry on only. Onboarding fills in that profile so it never needs to be asked again.

## Inputs

- **Existing travel playbook** (optional) — if a playbook exists at `brain/knowledge/travel/travel-playbook.md`, read it first to avoid re-asking for information already captured.

## Required capabilities

- **Knowledge base write** — read and update `brain/knowledge/travel/travel-playbook.md`

## Steps

1. **Load the methodology reference.** `references/atlas-travel-prep-methodology.md` — the Travel Profile structure and onboarding question flow.
2. **Check existing playbook.** If `brain/knowledge/travel/travel-playbook.md` exists and has a Travel Profile section, read it. Only ask about sections that are missing or need updating.
3. **Run onboarding conversationally** — not as a form dump. Use the question flow from the methodology reference: Round 1 (flying basics), Round 2 (preferences), Round 3 (nice-to-haves). Wait for answers before moving to the next round.
4. **Clarify if needed.** For credit card benefits, ask specifically which cards have lounge access — this is what determines Priority Pass vs. Centurion vs. Chase Sapphire Reserve access in future briefings.
5. **Write the Travel Profile** to `brain/knowledge/travel/travel-playbook.md` under the `## Travel Profile` section. Preserve any existing Airport Notes or Trip History sections.
6. **Confirm back.** Summarize what was captured: airlines and status, cards with lounge access, security enrollment, preferences. Give the user a chance to correct anything.

## Output

```
Travel Profile saved to brain/knowledge/travel/travel-playbook.md

Captured:
- Airlines: United (Gold), Delta (no status)
- Lounge access: Amex Platinum (Centurion + Priority Pass), Chase Sapphire Reserve (Priority Pass)
- Security: TSA PreCheck ✓, Global Entry ✓, CLEAR ✗
- Seat: Aisle (short flights), Window (overnight)
- Bags: Carry-on only
- Hotel: Marriott Bonvoy (Gold)
- Ground transport: Car service preferred for airports; rideshare OK locally
- Home airport: SFO

Pre-trip briefings are now personalized. Run `pre-trip-briefing` for any upcoming trip.
```

## Customization

Common things clients adjust:

- **Playbook location.** Default is `brain/knowledge/travel/travel-playbook.md`. Override if your knowledge base uses a different path.
- **Profile fields.** Add or remove fields in the Travel Profile structure (defined in the methodology reference) if your traveler has preferences the default doesn't cover (e.g., preferred meal type on long-haul flights).
- **Update flow.** When re-running to update, the skill only asks about changed or missing sections by default. Override to always run the full flow if you prefer.

## Why neutral

The onboarding flow is mechanical — ask questions, capture answers, write to a file. Atlas has no opinionated method for "the right way to ask someone about their travel preferences." The opinionated work happens in `pre-trip-briefing`, which uses the profile to generate a personalized briefing.
