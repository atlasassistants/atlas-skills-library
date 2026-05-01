---
exec_name: <Executive's display name>
extracted_at: <YYYY-MM-DD>
extracted_by: <user name, or "self">
version: 1
timezone: <IANA timezone, e.g., America/New_York>
workday_start: "<HH:MM, e.g., 08:00>"
workday_end: "<HH:MM, e.g., 17:00>"
buffer_minutes: 15
weekend_policy: "<off | on-call | available>"
---

# <Executive Name> — Ideal Week

> Empty template. Either fill in by hand using the schema below, or run the `extract-ideal-week` skill to populate it through an interview.

**Theme:** <one-line description of how this week should run>

---

## Monday

**Theme:** <what Monday is for>

| Time | Block Type | Activity |
|------|------------|----------|
| <HH:MM-HH:MM> | <Protected | Recurring | Strategic | Ops | Available> | <description> |

**Protected blocks:** <list any non-negotiable ranges within Monday>

---

## Tuesday

**Theme:** <what Tuesday is for>

| Time | Block Type | Activity |
|------|------------|----------|

**Protected blocks:**

---

## Wednesday

**Theme:**

| Time | Block Type | Activity |
|------|------------|----------|

**Protected blocks:**

---

## Thursday

**Theme:**

| Time | Block Type | Activity |
|------|------------|----------|

**Protected blocks:**

---

## Friday

**Theme:**

| Time | Block Type | Activity |
|------|------------|----------|

**Protected blocks:**

---

## Saturday & Sunday

**Theme:** <off | on-call | available>

---

## Recurring commitments

- **<event name>** — <day(s) HH:MM-HH:MM> (<duration>)
- ...

---

## Protected blocks

| Block | Day/Time | Severity | Reason |
|-------|----------|----------|--------|
| <name> | <when> | <block | warning | nudge> | <why this is protected> |

---

## Rules

### ALWAYS
- <rule statement> (<severity>)

### NEVER
- <rule statement> (<severity>)

### PREFER
- <rule statement> (<severity>)

### FLEXIBLE
- <exception or override condition>

---

## Default meeting lengths

| Meeting type | Default | Scheduling window | Buffer required |
|--------------|---------|-------------------|-----------------|
| <type> | <duration> | <preferred days/times> | <yes/no, how much> |

---

## VIP overrides

| Name | Relationship | Can override | Notes |
|------|--------------|--------------|-------|
| <name> | <role> | <which rules> | <special conditions> |

---

## Zone of genius

**Highest-and-best (only <Exec>):**
- <work that genuinely requires the exec>

**Drains (capable but costly):**
- <work the exec can do but shouldn't>

**Delegate or stop:**
- <work to hand off, with destination>
