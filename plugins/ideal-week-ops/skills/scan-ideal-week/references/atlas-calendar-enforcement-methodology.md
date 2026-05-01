# Atlas Calendar Enforcement Methodology

The methodology behind `scan-ideal-week`. Read this before customizing the rule engine, severity model, or suggestion logic.

## What the scan is *for*

The scan exists to surface every calendar event that violates the documented ideal week, with a concrete fix, on a cadence the user can act on. Three things follow:

1. **Surface everything; let the human filter.** Better to over-flag and have the user dismiss noise than to under-flag and miss a real conflict. Severity exists to communicate priority, not to suppress lower-priority items.
2. **Every flag needs a fix suggestion.** A flag without a suggestion is a complaint. The user needs an actionable next step. If the engine can't generate a sensible suggestion, the flag is noise — drop it or escalate to "needs human review" with the reason.
3. **The schedule is the discipline.** Real-time alerting interrupts the exec for events that haven't happened yet. Twice-daily batched scans give the user a window to fix or escalate before the conflict is live. The cadence (EOD for tomorrow + morning-of for today) is the methodology, not just a default.

## Rule taxonomy

Every check the scan runs falls into one of these seven categories:

### 1. Protected-block violations
- **Definition:** Event scheduled inside a time range marked `protected` in the ideal-week document.
- **Default severity:** `block`.
- **Examples:** Meeting at 7:30am when 7-8am is thinking time. Anything on a no-meeting Tuesday. Lunch slot used for a call.
- **Suggestion strategy:** Find the next available non-protected slot in the same day's allowed blocks. If no slot today, suggest tomorrow's first allowed slot.

### 2. NEVER-rule violations
- **Definition:** Event matches a pattern in the NEVER rule bucket.
- **Default severity:** `block`.
- **Examples:** Back-to-back without buffer. Meeting before workday start. Meeting on a no-meeting weekday.
- **Suggestion strategy:** If the rule is about timing (e.g., "no back-to-back"), suggest a specific buffer addition. If it's about category (e.g., "no status meetings"), suggest declining or converting to async.

### 3. Cap violations
- **Definition:** Sum of meeting hours in a day exceeds the configured cap.
- **Default severity:** `block` if the cap is hard ("absolute max 4 hours"), `warning` if it's a target ("3-hour target with 4-hour ceiling").
- **Examples:** Day has 4.5 hours of meetings against a 4-hour cap. Day has 3.5 hours against a 3-hour target.
- **Suggestion strategy:** Identify the lowest-priority meeting on the day (heuristics: smallest attendee count, "sync" or "check-in" in title, no agenda) and suggest moving it.

### 4. PREFER-rule violations
- **Definition:** Event violates a soft pattern in the PREFER bucket.
- **Default severity:** `warning` or `nudge` per rule (extract from the ideal-week document — don't default).
- **Examples:** 1on1 not on a Thursday for a Thursday-batched exec. Third external call in a day when preference is "no more than 2".
- **Suggestion strategy:** Suggest the preferred slot. If no preferred slot exists in the window, leave the suggestion as "consider moving to next week's <preferred-slot>".

### 5a. Overlap (double-booking) violations
- **Definition:** Two or more events whose time ranges overlap (the gap between them is less than zero).
- **Default severity:** `block`. The exec literally cannot attend both — this is never acceptable, regardless of who scheduled it. Distinct from a buffer violation, which is about tightness; this is about a true double-booking.
- **Examples:** Leadership sync 10:00-11:20am overlapping with marketing weekly 10:00-10:30am.
- **Suggestion strategy:** Identify the lower-priority overlapping event (heuristics: smaller attendee count, "sync" or "check-in" in title, no agenda, recurring vs one-off — recurring usually wins). Suggest moving the lower-priority one to its preferred slot. If both look equal-priority, flag for human review with both options.

### 5b. Buffer violations
- **Definition:** Two events less than the configured buffer apart (default 15 min) but not overlapping. Overlaps are handled by 5a above.
- **Default severity:** `warning`.
- **Examples:** 10:00-10:30am call followed by 10:30-11:00am call (zero buffer).
- **Suggestion strategy:** Suggest extending the buffer by shortening the earlier meeting (preferred) or moving the later one (fallback).

### 6. Missing-prep-block violations
- **Definition:** External or discovery call on the calendar without a prep block in front of it (per the ideal-week's prep requirement).
- **Default severity:** `warning`.
- **Examples:** External 30-min call at 10am with nothing on the calendar from 9:45-10am.
- **Suggestion strategy:** Suggest adding a 15-min prep block in the open slot directly before the call. If the slot is occupied, suggest an alternative open slot earlier in the day.

## Severity model

Three levels. Strict ordering — `block > warning > nudge`.

- **`block`** — Should not be on the calendar. Reschedule or escalate before the day starts.
- **`warning`** — Should probably not be on the calendar, but the user can apply judgment. Often appropriate to flag to the exec for a decision rather than acting unilaterally.
- **`nudge`** — Worth surfacing, not worth acting on without specific context. Most of these get dismissed.

The severity comes from the rule itself (extracted from the ideal-week document), not from the scan logic. The scan reads severities; it does not assign them.

## VIP override mechanism

VIPs in the ideal-week document have a list of rules they can override. When the scan flags an event:

1. Check the event's organizer/attendees against the VIP list.
2. If a VIP is involved AND the violated rule is in their override list, **downgrade severity by one level** (block → warning, warning → nudge, nudge → drop entirely).
3. Annotate the flag with `VIP override applied: <name>`.

**Why downgrade rather than skip:** A skipped flag tells the user nothing. A downgraded flag tells the user "this is a rule violation, but a VIP is involved — this is probably fine, but you should know." The exec's pattern of VIP overrides is also useful diagnostic data — if Jane is overriding rules every day, that's a signal the ideal week needs to update.

## Suggestion engine

Every flag MUST include a concrete suggestion. The suggestion is generated per-flag using the strategies listed above. General principles:

- **Be specific.** "Move to a better slot" is not a suggestion. "Move to Thursday 2:30pm (currently free)" is.
- **Use the ideal week as the source of valid slots.** Don't suggest a slot inside another protected block.
- **Prefer in-day fixes over multi-day moves.** Moving a meeting to tomorrow is harder than shortening it.
- **Decline > move** when the meeting violates a NEVER rule that's about category (e.g., status meeting). Suggest "decline; ask organizer to share async update" rather than rescheduling something the exec doesn't want to attend at all.
- **No suggestion possible? Flag with reason.** If the day is fully booked and no slot can be found in the window, the suggestion becomes "no clean reschedule available — consider declining or escalating to exec." Never silently drop a flag for "no suggestion".

## Why twice-daily

The scheduled cadence is part of the methodology, not just a default:

- **EOD scan (5pm) for tomorrow.** Leaves the evening to send "we need to move X" emails. Catches things that landed during today's last meeting block.
- **Morning scan (7am) for today.** Catches anything that landed overnight (international add-ons, urgent reschedules from the exec). Aligns with the exec's thinking-time block — flags can be addressed before the workday starts.

Real-time scanning was considered and rejected. Real-time generates noise during the workday and pulls the exec's attention to events that haven't happened yet, which violates the spirit of the ideal week.

## Dry-run mode

The scan supports dry-run for two scenarios:

1. **Initial wiring.** Confirms calendar read works without sending a message.
2. **Methodology changes.** Lets the team validate that a rule change produces the expected flags before going live.

In dry-run, the scan runs every step EXCEPT the notification send and the scan-log write. Output prints to terminal.

## What the scan does NOT do

These are explicit non-goals:

- **Auto-rescheduling.** The scan flags and suggests; it never moves events. Auto-moves cause more problems than they solve (lost context, surprised attendees, ignored constraints the scan doesn't know about).
- **Multi-day pattern detection.** The scan looks at the configured window only. "This is the third week in a row Tuesday got a meeting" is out of scope. Surface those patterns through scan-log analysis, not the scan itself.
- **Soft enforcement against non-rules.** If a behavior bothers the exec but isn't in the ideal-week document, the scan does not flag it. The fix is to update the ideal week, not to special-case the scan.
