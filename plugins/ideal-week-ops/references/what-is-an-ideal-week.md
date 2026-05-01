# What is an Ideal Week?

> Read this first. The `extract-ideal-week` skill loads it before asking any questions, because the term means different things to different people and the rest of the plugin only works if everyone is using the same definition.

## The short version

An **ideal week** is a written description of how your week should run when nothing goes wrong — what time you start, what days are for deep work versus meetings, what's protected, what gets declined, who's allowed to break the rules.

It's not a wish list. It's a defendable structure. Once it's written down, this plugin can compare it to your actual calendar and tell you when something is off.

## What it includes

A complete ideal week describes five things:

1. **Workday boundaries.** When the day starts. When it ends. What weekends look like.
2. **Day-by-day rhythm.** What each weekday is *for*. Monday might be leadership and ops; Tuesday might be untouchable deep work; Thursday might be 1on1s with direct reports.
3. **Protected blocks.** Specific time ranges that nothing should land on — thinking time, lunch, no-meeting days, family time.
4. **Rules.** Patterns that should hold across the week — meeting buffers, daily meeting caps, "no status meetings", "max two external calls a day".
5. **Overrides.** The list of people or contexts that can break the rules — co-founders, key clients, family.

You can also include a **zone of genius** section: what only you can do at the highest level, what drains you, what you should delegate. The plugin uses this as context when flagging meetings that consume your drain time.

## What it isn't

- **It isn't a strict calendar.** You're not blocking the entire week into rigid slots. You're describing the *shape* of the week — what's allowed where, what's protected, what's preferred.
- **It isn't permanent.** Re-extract or update when your role changes, when patterns of repeated calendar conflicts suggest a rule no longer fits, or about once a quarter.
- **It isn't optional.** This plugin can only enforce what's been written down. "I prefer fewer meetings on Tuesdays" doesn't survive a real meeting request from a senior person under pressure. "No meetings on Tuesdays except VIPs <list>" does.

## Why severity matters

Not every rule violation is the same. Some should block scheduling outright. Some should warn but proceed. Some are just preferences worth surfacing.

Atlas's framework uses three severities:

- **`block`** — should not be on the calendar; reschedule or escalate before the day starts
- **`warning`** — probably shouldn't be there; use judgment, often worth surfacing for a decision
- **`nudge`** — worth knowing about, not worth acting on without specific context

When you describe a rule during extraction, you'll be asked how strict it is. That answer determines the severity. Be honest — if a rule is really "I'd prefer it but won't insist," call it a `nudge`. If it's "do not let this happen," call it a `block`.

## The four rule buckets

When the extraction skill asks about your rules, your answers land in one of four buckets:

- **ALWAYS** — must hold for every event. Default `block`.
  Example: "Lunch is protected 11am–1pm window."
- **NEVER** — must not happen. Default `block`.
  Example: "No meetings on Tuesdays."
- **PREFER** — soft preferences. Default `warning` or `nudge`.
  Example: "Batch all 1on1s on Thursday afternoons."
- **FLEXIBLE** — exceptions for specific people. Default depends on the rule it overrides.
  Example: "Co-founder can override the Tuesday rule."

Rules that don't fit one of these buckets usually need rewording. If you find yourself unsure, the question to ask is: "is this an absolute, a strong default, or a preference I'd let slide for the right person?"

## Protected blocks vs rules

These get confused often:

- **Protected block** ties to a *specific time range* — "7-8am every day", "all of Tuesday", "11am-1pm window for lunch".
- **Rule** is about a *pattern or count* without a fixed time — "no back-to-back without 15-min buffer", "no more than 4 hours of meetings per day".

If a constraint has a time, it's a protected block (lives in the rhythm section). If it's about pattern or count, it's a rule (lives in a rule bucket).

## What happens after extraction

Once your ideal week is documented:

1. The plugin offers to schedule a recurring scan — typically end-of-day at 5pm (flags tomorrow's conflicts) and morning-of at 7am (flags today's).
2. Each scan compares your actual calendar to your ideal week and produces a single notification — Slack, iMessage, email, or a file.
3. The notification lists every rule violation, ordered by severity, with a concrete fix suggestion for each.
4. You decide what to act on.

The plugin never moves events on your calendar. It only surfaces and suggests.

## A note on "ideal"

The word "ideal" can sound aspirational. It's not. The version you describe should be the version you genuinely want to defend. If you describe an ideal you don't actually want to live by, the scan will produce flags you don't want to act on, and you'll start ignoring it. Calibrate to what you'll actually honor — not what sounds good on paper.
