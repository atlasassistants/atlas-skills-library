# Extraction Questions

Atlas's standard question set for extracting an executive's ideal week. **10 rhythm questions + 3 zone-of-genius questions = 13 total.**

Use this list verbatim when running the extraction interview in `extract-ideal-week`. Ask one at a time. Paraphrase the answer back before moving on. Anyone with the answer may provide it (the exec, an assistant, an AM) — mark which person each answer came from.

> **When NOT to run this interview:** If the exec already has an ideal week documented (in onboarding assets, with the AM, in their workspace), use that instead. Always confirm with the AM and check existing onboarding materials before scheduling extraction time with the exec.

---

## Part 1 — Week rhythm (10 questions)

1. **Deep work timing.** What time of day is best for your deep work and strategic thinking?
2. **Energy curve.** When does your energy typically peak, and when does it dip?
3. **Meeting days vs focus days.** Which days do you prefer for meetings versus focused work?
4. **Workday boundaries.** What time do you typically start and end your workday?
5. **Recurring commitments.** Do you have any recurring meetings or standing commitments? (List them — day, time, who, why.)
6. **Lunch.** When do you usually take lunch, and should it be protected?
7. **Off-limits times.** What times or days are completely off limits for meetings or work?
8. **Non-negotiables.** What must be protected no matter what? (Family, health, thinking time, anything else.)
9. **Default meeting length.** What should the default meeting length be? Does it vary by meeting type?
10. **Avoid list.** What types of meetings do you want to avoid? (E.g., status updates that could be async, large meetings without an agenda, calls without prep, etc.)

## Part 2 — Zone of Genius (3 questions)

11. **Highest-and-best.** What work can only you do at the highest level? (The work that genuinely requires you, not someone else.)
12. **Drains.** What work are you great at but drains you? (You're capable, but the cost is high.)
13. **Delegate / stop.** What work should you stop doing or delegate immediately?

---

## Synthesis rules

After collecting all 13 answers:

- **Rhythm questions (1–8) → day-by-day rhythm + protected blocks.** Map energy curve and meeting-vs-focus preferences onto specific weekdays. Convert non-negotiables and off-limits into protected blocks with severity `block`.
- **Question 5 (recurring commitments) → recurring blocks** in the rhythm, not in the rule buckets. They're calendar fixtures.
- **Question 9 (default length) → default meeting lengths section.** Create a small table by meeting type if the answer varies.
- **Question 10 (avoid) → NEVER + PREFER buckets.** If the exec said "no status update meetings," that's a NEVER. If "prefer fewer than 2 external calls per day," that's a PREFER.
- **Zone of genius (11–13) → standalone section in the ideal-week document.** Surfaces in the scan output as context when flagging meetings that consume the exec's drain time.

See `../../../references/ideal-week-format.md` for the exact output schema and `../../../references/example-ideal-week.md` for a worked example.

## Interview tips

- **Don't batch.** One question per turn. Batched questions get shallow answers because the exec answers the easy one and forgets the rest.
- **Paraphrase.** After each answer, summarize what you heard in one sentence and ask "did I get that right?" before continuing. Catches misunderstandings early.
- **Allow "I don't know."** If the exec genuinely doesn't have a strong preference for a question, capture that as `null` in the document — don't pressure for an answer. The scan skill tolerates missing fields.
- **Ask for examples.** Abstract preferences are weaker than examples. "What's a recent week where the calendar felt right?" is sometimes more productive than "what's your ideal day?"
- **Watch for contradictions.** If question 3 says "no meetings on Tuesday" and question 5 lists a Tuesday standup, surface the contradiction explicitly: "you mentioned no meetings on Tuesday but also a Tuesday standup — should the standup move, or is it the exception?"
