---
name: course-designer
description: Master orchestrator for designing structured courses, bootcamps, curriculums, and training programs. Coordinates the full instructional design process — needs analysis, learning objectives, curriculum sequencing, lesson planning, and assessment — using the ADDIE framework with Bloom's Taxonomy and Backward Design alignment. Writes a course project tree (overview, objectives, curriculum, per-module lesson plans and assessments, grading rubric) into a configured courses root.
when_to_use: |
  User wants to design a new course, training program, bootcamp, curriculum, or learning path end-to-end. Triggers on phrases like "design a course for…", "build a curriculum", "create a bootcamp", "put together a training module", or "I need to train people on…". Do NOT use this skill if the user only wants to work on a single phase (objectives only, lesson plan only, assessment only) — invoke the specific phase skill instead.
atlas_methodology: neutral
---

# course-designer — master orchestrator

Guide the user through designing a complete, pedagogically sound learning experience. This skill coordinates the full instructional design process using the ADDIE framework, with Bloom's Taxonomy for objectives, Backward Design for alignment, and Gagné's Nine Events for lesson structure.

## How this skill works

This is the **orchestrator**. It walks the user through each phase of course design in sequence, invoking the specialized phase skills as needed. Think of it as the project manager for building a course.

The user may not know instructional design terminology — meet them where they are. If they say "I want to teach people how to use AI tools," that's a course design request. Start here.

## The ADDIE framework

ADDIE is the backbone process. Each phase maps to a specialized skill in this plugin:

| Phase | What happens | Skill |
|-------|-------------|-------|
| **Analysis** | Who are the learners? What do they need? What resources exist? | `needs-analysis` |
| **Design** | What will learners be able to do? How is content sequenced? | `learning-objectives` + `curriculum-sequencer` |
| **Development** | What does each lesson look like? What activities and materials? | `lesson-planner` |
| **Implementation** | Delivery — outside scope of these skills | — |
| **Evaluation** | How do we measure learning? Rubrics, assessments, grading. | `assessment-designer` |

## Workflow

### Step 1: Understand the request

Before jumping into any framework, get clarity on what the user is building. Extract or ask for:

- **Topic / domain** — what is this course about?
- **Target audience** — who are the learners? what's their starting level?
- **Delivery format** — online async? live cohort? hybrid? in-person workshop? self-paced?
- **Scope** — is this a 1-hour workshop, a 6-week course, a 12-week bootcamp?
- **Desired outcome** — what should learners be able to DO after completing this?
- **Constraints** — timeline, budget, tools available, platform requirements?

Don't ask all of these as a checklist. Have a conversation. Many of these will be implicit in what the user already told you.

### Step 2: Locate the courses root and create the project tree

This skill writes its output into a per-course folder under a configured "courses root" directory. To find it:

1. If the user has told you (or a previous session recorded) the courses root, use it.
2. Otherwise, ask the user where the course should live. Default convention is a `courses/` directory at the project root, but any directory the host agent can write to is fine.
3. If neither is available, write into a `courses/<course-name>/` directory at the current working root and tell the user where you put it.

Then create the per-course folder:

```
<courses_root>/<course-name>/
├── state.md              # project state (active / paused / completed)
├── plan.md               # implementation plan for building this course
├── overview.md           # audience, prerequisites, goals, format
├── objectives.md         # Bloom's-aligned learning objectives
├── curriculum.md         # module sequence with dependencies
├── modules/
│   ├── 01-<module-name>/
│   │   ├── lesson-plan.md
│   │   └── assessment.md
│   ├── 02-<module-name>/
│   │   ├── lesson-plan.md
│   │   └── assessment.md
│   └── …
└── grading-rubric.md     # overall grading scheme
```

Create `state.md` and `overview.md` first; the rest gets built as you move through the phases.

`state.md` is a short status file. Use whatever frontmatter convention the host project uses (e.g. `type: project`, `status: active`, dates) — if the project has no convention, a minimal title + status line is enough. `overview.md` should capture all the context from Step 1 in a structured format.

### Step 3: Run through the phases

Walk the user through each phase in order. For each phase, you can either:

- Handle it directly using the guidance below, or
- Tell the user they can invoke the specialized skill for deeper work (e.g. "If you want to dive deep into objectives, you can use the `learning-objectives` skill")

**Phase 1: Needs analysis**
- Define the target audience profile (demographics, prior knowledge, motivation)
- Identify the gap between current state and desired state
- Map available resources and constraints
- Output: updated `overview.md` with audience analysis section

**Phase 2: Learning objectives**
- Write objectives using Bloom's Taxonomy verb framework
- Organize by cognitive level (Remember → Understand → Apply → Analyze → Evaluate → Create)
- Ensure objectives are measurable and specific
- Output: `objectives.md`

**Phase 3: Curriculum sequencing**
- Group objectives into logical modules
- Sequence modules based on prerequisite dependencies
- Apply scaffolding — each module builds on the last
- Balance theory and practice within each module
- Output: `curriculum.md`

**Phase 4: Lesson planning**
- For each module, design detailed lesson plans
- Use Gagné's Nine Events as the structural framework
- Include instructional activities, materials, and timing
- Output: `modules/XX-name/lesson-plan.md` for each module

**Phase 5: Assessment design**
- Design assessments aligned to learning objectives (Backward Design)
- Create rubrics with clear criteria and performance levels
- Mix formative (during learning) and summative (end of unit) assessments
- Output: `modules/XX-name/assessment.md` + `grading-rubric.md`

### Step 4: Review and refine

After all phases are complete:

- Check alignment: every objective should have content that teaches it AND an assessment that measures it
- Identify gaps: objectives without assessments, modules without clear outcomes
- Verify scaffolding: prerequisites are met before they're needed
- Estimate total time and compare against scope constraints

## Backward Design principle

This is the most important pedagogical idea in this system: **start with the end in mind**.

1. First, define what learners should be able to demonstrate (objectives)
2. Then, design assessments that prove they can do it
3. Finally, plan the instruction that prepares them for the assessment

This prevents the common trap of building slides / content first and then trying to figure out what was learned. Every piece of content should exist because it helps learners meet a specific objective that will be assessed.

## Tips for working with the user

- **Don't dump frameworks on them.** Use ADDIE, Bloom's, Gagné internally to structure your work. Explain the concepts in plain language when relevant, but don't make the user feel like they're in a pedagogy lecture.
- **One phase at a time.** Don't try to do everything in one pass. After each phase, pause and get the user's input before moving on.
- **Be concrete.** Instead of "What cognitive level are you targeting?", say "Should learners just understand the concept, or should they be able to apply it to real problems?"
- **Adapt to scope.** A 1-hour workshop doesn't need the same depth as a 12-week bootcamp. Scale the process to fit.
