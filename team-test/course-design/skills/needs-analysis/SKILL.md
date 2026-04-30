---
name: needs-analysis
description: Conduct audience analysis and instructional needs assessment for a course or training program. Builds a learner profile (role, experience, motivation, context), runs a gap analysis (current state → target state → gap → priority), inventories available resources, and maps design-shaping constraints. Writes the result into a course `overview.md` with structured sections (audience, gap, format, resources, prerequisites, success criteria).
when_to_use: |
  User is starting a course design and hasn't yet defined who it's for or what learners need. Triggers on phrases like "who is this course for", "analyze my audience", "what do my learners need", "training needs assessment", or any course-design task where the audience and gap are still vague. Also fires when the orchestrator (`course-designer`) reaches Phase 1 / Analysis.
atlas_methodology: neutral
---

# needs-analysis

The foundation of good instructional design. Before writing a single objective or lesson, understand who you're teaching, where they are now, and where they need to be.

## What this produces

An audience and needs profile that feeds directly into the course `overview.md`. This analysis answers:

1. **Who are the learners?** — demographics, roles, experience level
2. **Where are they now?** — current knowledge, skills, and attitudes
3. **Where do they need to be?** — target competencies and outcomes
4. **What's the gap?** — the delta between current and target state
5. **What resources exist?** — available materials, tools, SMEs, platforms
6. **What are the constraints?** — time, budget, tech requirements, org culture

## How to conduct the analysis

### Learner profile

Build a concrete picture of the target audience. Ask the user (or extract from context):

| Dimension | Questions to answer |
|-----------|---------------------|
| **Role / title** | What do these people do? What's their job or position? |
| **Experience level** | Beginner, intermediate, advanced? In what specifically? |
| **Prior knowledge** | What can you assume they already know? |
| **Motivation** | Why are they taking this? Required? Career growth? Curiosity? |
| **Learning context** | Where / when will they learn? Work hours? Evenings? Mobile? |
| **Tech comfort** | What tools / platforms are they comfortable with? |
| **Group size** | How many learners? This affects format choices. |
| **Diversity** | Range of skill levels? Language considerations? Accessibility needs? |

Don't force the user to answer every question. Fill in reasonable defaults where the user doesn't have strong opinions, and flag assumptions explicitly so they can correct them.

### Gap analysis

The gap is the core justification for the course. Structure it as:

```markdown
## Gap analysis

### Current state
What learners can do / know / believe today:
- [specific observable skill or knowledge]
- [specific observable skill or knowledge]

### Target state
What learners should be able to do / know / believe after the course:
- [specific measurable outcome]
- [specific measurable outcome]

### Gap
The delta — what the course needs to bridge:
- [gap 1: description of what's missing]
- [gap 2: description of what's missing]

### Priority
Which gaps are most critical to close?
1. [highest priority gap — why]
2. [next priority — why]
```

Prioritization matters because you almost never have enough time to teach everything. Help the user identify the 20% of content that drives 80% of the value.

### Resource inventory

Map what's available to build with:

- **Existing content** — are there slides, docs, videos that can be reused or adapted?
- **Subject matter experts** — who knows this stuff and can review content?
- **Platform / tools** — where will the course live? What tools can learners access?
- **Budget** — is there money for tools, platforms, guest speakers, materials?
- **Timeline** — when does this need to be ready?
- **Reference materials** — books, articles, courses that cover similar ground?

### Constraint mapping

Constraints shape design decisions. Common ones:

| Constraint | How it affects design |
|-----------|-----------------------|
| Limited time (e.g. 2-hour workshop) | Narrow scope, focus on highest-priority gaps |
| Async delivery | Need more self-assessment, clearer written instructions |
| Mixed skill levels | Need differentiated paths or pre-assessment |
| No budget for tools | Use free / open-source alternatives |
| Mandatory training | Address motivation — learners may be resistant |
| Large group (50+) | Less individual feedback, more peer-based activities |

## Output format

Write the analysis into the course project's `overview.md` under these sections:

```markdown
# <Course name>

## Course summary
One-paragraph description of what this course is and why it exists.

## Audience profile
[Learner profile from analysis]

## Gap analysis
[Current state → Target state → Gap → Priority]

## Delivery format
[Format, duration, platform, schedule]

## Resources & constraints
[Resource inventory and constraint mapping]

## Prerequisites
[What learners must know / have before starting]

## Success criteria
[How you'll know the course achieved its goals]
```

Use whatever frontmatter convention the host project uses. If none, a `title:` line is enough.

## When you don't have full information

The user may not know all the answers. That's fine — the analysis is still valuable because it surfaces the questions they need to answer. Flag unknowns explicitly:

```markdown
> **Assumption:** Learners have basic spreadsheet skills. Verify with first cohort — if not, add a prerequisites module.
```

Identifying assumptions early prevents expensive redesigns later.
