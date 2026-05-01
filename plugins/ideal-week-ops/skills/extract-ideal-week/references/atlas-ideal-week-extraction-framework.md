# Atlas Ideal Week Extraction Framework

The methodology behind `extract-ideal-week`. Read this before customizing the extraction flow.

## What the ideal week is *for*

An ideal week document is not a wish list. It is **the artifact the calendar is defended against.** Two consequences follow:

1. **Every field must be enforceable.** "I'd like more focus time" is not enforceable. "No meetings 8:45am–12pm Tuesday/Wednesday" is. Extraction's job is to convert the first into the second, on the spot, by asking follow-up questions.
2. **Every rule needs a severity.** Some violations should block scheduling outright; others should warn but proceed; others are just preferences. The exec's tolerance for each rule is part of the data — extract it explicitly, don't assume.

## Why these 13 questions

The question set isn't arbitrary. It maps to the four things the scan skill needs to evaluate any calendar event:

| Question(s) | What the scan needs |
|---|---|
| 1, 2, 3 | Where the deep-work blocks go on the weekly grid |
| 4 | When the workday starts and ends (boundary checks) |
| 5 | Recurring fixtures (don't flag what's already known and accepted) |
| 6, 7, 8 | Protected blocks — the hardest enforcement |
| 9 | Default meeting length (so the scan can flag overruns) |
| 10 | NEVER + PREFER rules |
| 11, 12, 13 | Zone of genius — surfaces as context in flag explanations, not as direct rules |

If a client asks to add a 14th question, ask first: which scan check does it feed? If none, the question is probably collecting nice-to-have context, not enforceable data — push back before adding.

## The four rule buckets

Output rules into one of four buckets. The bucket determines default severity at scan time:

- **ALWAYS** — must hold for every event. Default severity `block`. Examples: "lunch is protected", "no meetings before 9am".
- **NEVER** — must not happen. Default severity `block`. Examples: "no meetings on Tuesdays", "no back-to-back without 15-min buffer".
- **PREFER** — soft preferences. Default severity `warning` or `nudge`. Examples: "batch 1on1s on Thursdays", "no more than 2 external calls per day".
- **FLEXIBLE** — exceptions to the above for specific people or contexts. Examples: "VIP X can override Tuesday rule", "Atlas clients get same-week priority".

When extracting, every rule the exec states should land in one of these buckets explicitly. If you find yourself unsure, ask: "is this an absolute, a strong default, or a preference you'd let slide for the right person?"

## Protected blocks vs rules

These are different and should not be conflated:

- **Protected block** = a specific time range that must stay clear (e.g., 7-8am thinking time, all of Tuesday, 11am-1pm lunch window). Lives in the rhythm section, not in rule buckets. The scan checks every event against every protected block.
- **Rule** = a constraint that doesn't tie to a specific time range (e.g., "no back-to-back meetings", "max 4 hours of meetings per day"). Lives in the rule buckets.

Confusion between the two is the most common extraction mistake. If a constraint has a time, it's a protected block. If it's about pattern or count, it's a rule.

## VIP overrides

The exec almost always has a list of people who can break the rules. Extract this list explicitly. Common categories:

- **Internal high-priority** — co-founders, board members, direct reports in crisis mode
- **External clients** — paying customers, partners with active deals
- **Family / personal** — spouse, kids' school, doctor

For each VIP, capture: name, relationship, what they can override (everything? Tuesday rule only? after-hours only?). The scan skill uses this list to downgrade severities at flag time, not to skip flags entirely — the user still sees that a VIP overrode a rule.

## Zone of genius — why it's separate

Questions 11–13 don't produce rules. They produce **context**. When the scan flags a meeting that consumes the exec's drain-time work, the flag includes a note: "this falls in your drain category — consider delegating to <person> per zone-of-genius doc." This is softer than a rule but more useful than no context.

Don't try to convert zone-of-genius answers into hard rules. The exec's relationship to drain work is too situational.

## Resumability

Long interviews lose execs. The skill saves to a marker file (`.extract-in-progress.json`) after every answered question for two reasons:

1. The exec gets pulled away mid-interview and resumes the next day.
2. Answers are collected asynchronously — some from the exec in person, some from the AM, some from the assistant who scheduled the kickoff.

Resume detection lives in the skill's step 0 (phase detection). If the marker exists, skip already-answered questions and pick up where the file left off. Don't re-ask anything.

## Confirmation is non-negotiable

The skill must show the synthesized document and get the user's explicit "this is right" before saving. Three reasons:

1. Synthesis errors are the highest-impact bug — a wrong rule produces wrong flags every day forever.
2. Execs often realize what they actually meant only when they see it written down.
3. Confirmation creates buy-in. The exec is more likely to honor the rules in a document they signed off on.

Never auto-save without confirmation. Even if the exec says "trust me, it's fine" — show it first.

## When to re-extract

The ideal week is not static. Re-run extraction when:

- The exec's role changes materially (new responsibilities, more direct reports, new product line)
- A pattern of repeated flags suggests a rule no longer fits ("we keep flagging the Wednesday team sync — is Wednesday no longer a no-meeting day?")
- A quarter has passed since the last extraction and the exec hasn't had a calendar conversation recently
- The exec asks for it

The skill's step 0 handles "ideal week already exists" by offering update vs re-extract. Re-extract is heavy — prefer update for small changes.
