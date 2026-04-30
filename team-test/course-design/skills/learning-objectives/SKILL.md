---
name: learning-objectives
description: Write measurable learning objectives at course, module, and lesson granularity, aligned to Bloom's Taxonomy cognitive levels (Remember → Understand → Apply → Analyze → Evaluate → Create) using observable action verbs and the ABCD formula (Audience, Behavior, Condition, Degree). Verifies objectives are specific enough to assess and produces an alignment matrix from course-level objectives down to module objectives. Writes the result to a course `objectives.md`.
when_to_use: |
  User has an audience and topic but hasn't defined measurable goals yet, or wants to convert vague aspirations ("understand AI", "be familiar with Python") into testable behaviors. Triggers on phrases like "write learning objectives", "what should learners be able to do", "define outcomes for this course", "create objectives using Bloom's", or "make my objectives measurable". Also fires when the orchestrator (`course-designer`) reaches Phase 2 / Design.
atlas_methodology: neutral
---

# learning-objectives

Learning objectives are the backbone of instructional design. Everything else — content, activities, assessments — flows from them. A well-written objective tells you exactly what to teach, how to teach it, and how to know if it worked.

## Bloom's Taxonomy

Bloom's Taxonomy organizes cognitive skills into six levels, from simple recall to complex creation. Each level has specific **action verbs** that make objectives measurable.

### The six levels

| Level | What it means | Example verbs | Example objective |
|-------|--------------|---------------|-------------------|
| **1. Remember** | Recall facts, terms, definitions | List, define, name, identify, recall, recognize, state | "List the five phases of the ADDIE model" |
| **2. Understand** | Explain ideas, interpret meaning | Explain, describe, summarize, paraphrase, classify, compare | "Explain the difference between synchronous and asynchronous communication" |
| **3. Apply** | Use knowledge in new situations | Apply, demonstrate, use, implement, solve, execute, operate | "Apply prompt engineering techniques to generate structured outputs from an LLM" |
| **4. Analyze** | Break down, find patterns, identify relationships | Analyze, compare, contrast, differentiate, examine, categorize, diagnose | "Analyze a failed automation workflow to identify the root cause" |
| **5. Evaluate** | Judge, justify, critique, make decisions | Evaluate, assess, justify, critique, recommend, prioritize, defend | "Evaluate three competing AI tools against a set of business requirements and recommend one" |
| **6. Create** | Produce something new, design, build | Design, create, build, develop, construct, compose, formulate, propose | "Design an end-to-end client onboarding workflow using AI automation tools" |

### How to choose the right level

The level depends on what learners need to DO with the knowledge in their real work:

- If they just need to **know it exists** → Remember or Understand
- If they need to **use it** → Apply
- If they need to **troubleshoot or compare** → Analyze
- If they need to **make decisions** → Evaluate
- If they need to **build something new** → Create

Most professional training should target Apply and above. Remember / Understand are supporting levels — necessary but not sufficient on their own.

## Writing good objectives

### The ABCD formula

Every objective should have four components:

- **A**udience — who is learning? (often implicit)
- **B**ehavior — what will they DO? (the verb — must be observable)
- **C**ondition — under what circumstances?
- **D**egree — how well? (criteria for success)

**Full example:**
> After completing this module, **learners** (A) will be able to **create a functional automation workflow** (B) **using Zapier and a provided template** (C) **that correctly triggers on the specified event and completes all 3 required actions without errors** (D).

**Simplified (common in practice):**
> Create a functional Zapier automation that triggers on a specified event and completes all required actions without errors.

The simplified form is fine when audience and conditions are established at the course level.

### Objective quality checklist

For each objective, verify:

- **Starts with a measurable verb** — not "understand" or "learn" or "know" (these aren't observable). Use Bloom's verbs instead.
- **Describes learner behavior** — what THEY do, not what the instructor does. "The instructor will demonstrate…" is not an objective.
- **Is specific enough to assess** — could you design a test question or task for this? If not, it's too vague.
- **Has one verb per objective** — "Explain and apply…" is two objectives. Split them.
- **Is realistic for the time available** — a 30-minute lesson can't achieve "Design a complete system."

### Common mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| "Understand AI concepts" | Not observable — how do you test "understanding"? | "Explain three types of machine learning and give an example of each" |
| "Learn about project management" | "Learn" is a process, not an outcome | "Apply the critical path method to schedule a project with 10+ tasks" |
| "Be familiar with Python" | "Familiar" is subjective | "Write a Python function that reads a CSV file and returns filtered rows" |
| "Appreciate the value of teamwork" | Attitudes are hard to measure directly | "Demonstrate collaborative problem-solving by completing a group debugging exercise" |

## Structuring objectives for a course

### Course-level vs. module-level vs. lesson-level

Objectives exist at different granularities:

```
Course-level objective (broad)
  └── Module-level objective (mid)
       └── Lesson-level objective (specific)
```

**Example:**

```
Course: "AI Operations Fundamentals"

Course objective:
  "Design and implement AI-augmented workflows for common business operations"

  Module 1: "Understanding AI Tools"
  Module objective:
    "Evaluate AI tools for specific business use cases"

    Lesson 1.1: "Types of AI Tools"
    Lesson objective:
      "Classify AI tools into categories (generative, analytical, automation)
       and identify one business application for each"

    Lesson 1.2: "Evaluating AI Tools"
    Lesson objective:
      "Compare two AI tools using a structured evaluation rubric"
```

Course-level objectives are typically at Bloom's levels 4-6. Module objectives are 3-5. Lesson objectives can be any level but should build toward the module objective.

### Alignment check

After writing objectives, verify the chain:

- Every **lesson objective** supports a **module objective**
- Every **module objective** supports a **course objective**
- Every **course objective** maps to a real-world skill from the gap analysis

If an objective doesn't connect to the chain, either it doesn't belong or you're missing a higher-level objective.

## Output format

Write objectives to the course project's `objectives.md`:

```markdown
# Learning objectives

## Course-level objectives

By the end of this course, learners will be able to:

1. [Bloom's verb] + [specific outcome] — (Bloom's level)
2. [Bloom's verb] + [specific outcome] — (Bloom's level)

## Module objectives

### Module 1: [Name]
By the end of this module, learners will be able to:
1. [objective] — (level)
2. [objective] — (level)

### Module 2: [Name]
…

## Alignment matrix

| Course objective | Supporting module objectives | Bloom's level |
|------------------|-----------------------------|---------------|
| [CO1] | M1.1, M1.2, M2.1 | Create |
| [CO2] | M2.2, M3.1 | Evaluate |
```

Use whatever frontmatter convention the host project uses. If none, a `title:` line is enough.

The alignment matrix is important — it proves every course objective has modules teaching toward it and catches orphaned objectives.
