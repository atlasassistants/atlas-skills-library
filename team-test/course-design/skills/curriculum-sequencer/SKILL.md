---
name: curriculum-sequencer
description: Organize learning objectives into modules and sequence the modules into a logical teaching order. Maps prerequisite dependencies between modules, applies scaffolding (simple → complex, theory → practice), uses spiral curriculum to revisit core concepts at increasing depth, and produces a delivery-format-appropriate schedule (weekly synchronous, async pacing, daily bootcamp). Writes the result to a course `curriculum.md` with dependency map, ordered module sequence, schedule, and checkpoint placement.
when_to_use: |
  User has a list of learning objectives or topics and needs to organize them into a teaching order. Triggers on phrases like "organize this into modules", "what order should I teach this", "structure this curriculum", "create a course outline", "map the dependencies", or "plan the weekly schedule for this bootcamp". Also fires when the orchestrator (`course-designer`) reaches Phase 3 / Design.
atlas_methodology: neutral
---

# curriculum-sequencer

Once you have learning objectives, you need to organize them into a logical teaching sequence. This skill handles the structural design of a course — grouping objectives into modules, ordering modules by prerequisite dependencies, and creating a schedule that fits the delivery format.

## Core principles

### 1. Prerequisite chains

Content must be sequenced so learners have the foundational knowledge before encountering concepts that depend on it. This sounds obvious but it's the #1 structural mistake in course design.

Map dependencies explicitly:

```
Module A: "Data Types and Variables"
    ↓ (prerequisite for)
Module B: "Control Flow and Logic"
    ↓ (prerequisite for)
Module C: "Functions and Modularity"
    ↓ (prerequisite for)
Module D: "Building a Complete Script"
```

If Module D assumes knowledge from Module A but a learner skipped A, they'll fail. Make the chain visible.

### 2. Scaffolding (simple → complex)

Within each module and across the course:

- Start with concrete, tangible concepts before abstract ones
- Start with guided practice before independent application
- Start with simple examples before complex, multi-variable scenarios

**Example scaffolding pattern:**

1. See a worked example (instructor demonstrates)
2. Do a guided exercise (instructor walks through, learner follows)
3. Do a supported exercise (learner attempts, hints available)
4. Do an independent exercise (learner solves alone)
5. Do a transfer exercise (learner applies to a new context)

### 3. Spiral curriculum

Important concepts should appear multiple times at increasing depth, not just once. If "prompt engineering" is a core skill:

- Module 2: Introduce basic prompting (Remember / Understand)
- Module 4: Apply prompting to a specific workflow (Apply)
- Module 7: Analyze why prompts succeed or fail (Analyze)
- Module 10: Design a prompting strategy for a novel problem (Create)

This reinforces learning and helps learners build deeper understanding over time.

### 4. Theory-practice balance

Every module should mix conceptual content with hands-on application. A common ratio:

- **30% theory** — concepts, frameworks, "why this matters"
- **70% practice** — exercises, projects, application

Adjust based on audience and topic, but never let a module be 100% theory. Learners need to DO something with what they learned in the same session.

## Sequencing process

### Step 1: List all modules

Pull from the learning objectives. Each module should:

- Have 2-5 learning objectives
- Be completable in a single session or time block
- Have a clear, specific title (not "Advanced Topics" or "Miscellaneous")

### Step 2: Map dependencies

For each module, ask: "What must the learner already know to succeed here?"

Create a dependency map:

```markdown
## Dependency map

| Module | Depends on | Enables |
|--------|------------|---------|
| M1: Intro to AI Tools | (none) | M2, M3 |
| M2: Prompt Engineering Basics | M1 | M4, M5 |
| M3: Data & Spreadsheets | M1 | M5, M6 |
| M4: Building Automations | M2 | M7 |
| M5: AI for Data Analysis | M2, M3 | M7 |
| M6: Reporting & Dashboards | M3 | M8 |
| M7: Integrated Workflows | M4, M5 | M8 |
| M8: Capstone Project | M7, M6 | (none) |
```

### Step 3: Determine module order

Use the dependency map to find a valid sequence (topological sort). Where multiple valid orderings exist, prefer:

1. **Motivation first** — put engaging, high-impact modules early to build momentum
2. **Quick wins** — early modules should produce visible results fast
3. **Hard stuff in the middle** — don't front-load the hardest content (learners drop off) or back-load it (they're fatigued)
4. **Capstone at the end** — a culminating project that integrates everything

### Step 4: Add schedule and pacing

Map modules to the delivery format.

**For a synchronous course (live sessions):**

```markdown
## Weekly schedule

| Week | Module | Session format | Duration |
|------|--------|----------------|----------|
| 1 | M1: Intro to AI Tools | Live lecture + demo | 2 hours |
| 2 | M2: Prompt Engineering | Workshop (hands-on) | 2 hours |
| 3 | M3: Data & Spreadsheets | Workshop | 2 hours |
| … |
```

**For async / self-paced:**

```markdown
## Module pacing

| Module | Estimated time | Includes |
|--------|----------------|----------|
| M1: Intro to AI Tools | 1.5 hours | Video (30m), reading (20m), exercise (40m) |
| M2: Prompt Engineering | 2 hours | Video (40m), lab (1h20m) |
| … |
```

**For a bootcamp:**

```markdown
## Daily schedule (Week 1)

| Day | Morning (theory) | Afternoon (practice) |
|-----|------------------|---------------------|
| Mon | M1: Intro to AI Tools | Lab: Tool exploration |
| Tue | M2: Prompt Engineering | Lab: Prompt challenges |
| Wed | M3: Data & Spreadsheets | Lab: Data cleanup exercise |
| Thu | Review + catch-up | Mini-project: combine M1-M3 |
| Fri | Guest speaker / Q&A | Peer review + retrospective |
```

### Step 5: Add checkpoints

Place assessments and review points at natural boundaries:

- **After each module:** quick formative check (quiz, reflection, peer review)
- **After every 3-4 modules:** milestone assessment or mini-project
- **At the end:** capstone or final assessment

Checkpoints serve two purposes: they verify learning, and they give learners a sense of progress.

## Output format

Write the curriculum structure to `curriculum.md`:

```markdown
# Curriculum structure

## Course overview
[Brief description of the course structure and approach]

## Dependency map
[Table showing module prerequisites]

## Module sequence

### Module 1: [Name]
- **Objectives:** [list from objectives.md]
- **Duration:** [estimated time]
- **Key topics:** [bullet list]
- **Hands-on:** [what learners build or practice]
- **Assessment:** [formative check type]

### Module 2: [Name]
- **Depends on:** Module 1
- …

[repeat for all modules]

## Schedule
[Format-appropriate schedule — weekly, daily, or self-paced pacing guide]

## Checkpoints
[Where milestone assessments occur and what they cover]
```

Use whatever frontmatter convention the host project uses. If none, a `title:` line is enough.

## Common patterns

**The Sandwich:** theory → practice → reflection (works for any module).

**The Project Arc:** modules 1-3 build isolated skills → modules 4-6 combine them → modules 7-8 apply to a real project.

**The Cohort Rhythm:** learn → practice → share → feedback (works well for live cohorts with peer learning).

Choose a pattern that fits the delivery format and stick with it for consistency. Learners benefit from predictable structure.
