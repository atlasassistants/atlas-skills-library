---
name: assessment-designer
description: Design assessments, rubrics, quizzes, and grading schemes that are aligned to learning objectives via Backward Design. Picks the right assessment method per Bloom's level (multiple choice for Remember, practical exercises for Apply, projects for Create), writes clear task instructions, builds rubrics with observable level descriptors, designs the overall grading scheme with weighted formative + summative components, and produces an objective-assessment alignment matrix to catch unmeasured objectives. Writes per-module `assessment.md` files plus a course-level `grading-rubric.md`.
when_to_use: |
  User has learning objectives and needs to figure out how to measure whether learners achieved them. Triggers on phrases like "create a rubric", "how should I assess this", "design a quiz", "build a grading scheme", "what's the grading criteria", or "how do I evaluate learners". Also fires when the orchestrator (`course-designer`) reaches Phase 5 / Evaluation.
atlas_methodology: neutral
---

# assessment-designer

Assessments answer the question: "Did the learners actually learn what we intended?" This skill designs assessments that are aligned to learning objectives, fair, and practical to administer.

## Assessment types

### Formative vs. summative

| Type | When | Purpose | Examples |
|------|------|---------|----------|
| **Formative** | During learning | Check understanding, guide instruction, give feedback | Quizzes, polls, practice exercises, peer review, reflections |
| **Summative** | End of module / course | Evaluate whether objectives were met | Final projects, exams, practical demonstrations, portfolios |

Both are necessary. Formative assessments catch problems early. Summative assessments prove competence.

### Assessment methods by Bloom's level

The assessment method should match the cognitive level of the objective:

| Bloom's level | Good assessment methods | Poor assessment methods |
|---------------|-------------------------|-------------------------|
| **Remember** | Multiple choice, matching, fill-in-the-blank | Essays, projects (overkill) |
| **Understand** | Short answer explanations, concept maps, "explain in your own words" | True / false (too shallow) |
| **Apply** | Practical exercises, simulations, case studies with known solutions | Multiple choice (can't show process) |
| **Analyze** | Case study analysis, compare / contrast tasks, data interpretation | Fill-in-the-blank (too narrow) |
| **Evaluate** | Critique tasks, decision justification, rubric-based peer review | Multiple choice (can't capture reasoning) |
| **Create** | Projects, portfolios, design tasks, build-something assignments | Any closed-ended format |

The general rule: **higher Bloom's levels need more open-ended assessments.**

## Designing assessments

### Step 1: Start from the objective

Every assessment item must map to a specific learning objective. Start with the objective and ask: "What would a learner need to DO to prove they can do this?"

| Objective | Assessment task |
|-----------|-----------------|
| "List the five phases of ADDIE" | Quiz: "Name the five phases of the ADDIE instructional design model" |
| "Apply prompt engineering to generate structured output" | Practical: "Given this scenario, write a prompt that produces valid JSON matching this schema" |
| "Evaluate AI tools against business requirements" | Project: "Compare 3 tools using the provided rubric and write a recommendation with justification" |

### Step 2: Write clear task instructions

Assessment instructions should be unambiguous. Include:

- What the learner must produce (format, length, deliverable)
- What resources they can use (open book? tools? peers?)
- How much time they have
- How it will be graded (point to the rubric)

**Bad:** "Write about AI tools."

**Good:** "Choose two AI tools from the approved list. For each, write a 200-word evaluation covering: (1) primary use case, (2) strengths for our workflow, (3) limitations. Then recommend one with a 100-word justification. Refer to the evaluation rubric for grading criteria."

### Step 3: Build the rubric

A rubric makes grading consistent and transparent. Learners should see the rubric before they start — it tells them what "good" looks like.

#### Rubric structure

```markdown
## Rubric: [Assessment name]

| Criterion | Excellent (4) | Proficient (3) | Developing (2) | Beginning (1) |
|-----------|---------------|----------------|----------------|---------------|
| [Criterion 1] | [description] | [description] | [description] | [description] |
| [Criterion 2] | [description] | [description] | [description] | [description] |
| [Criterion 3] | [description] | [description] | [description] | [description] |

**Total points:** XX
**Passing threshold:** XX points (XX%)
```

#### Writing rubric criteria

Each criterion should:

- Map to a learning objective or key skill
- Have observable, specific descriptions at each level
- Use parallel structure across levels (same dimensions, different quality)
- Avoid vague words like "good," "adequate," "poor" — describe what you'd actually see

**Bad criterion descriptions:**

| Criterion | Good | OK | Bad |
|-----------|------|----|----|
| Code quality | Good code | OK code | Bad code |

**Good criterion descriptions:**

| Criterion | Excellent (4) | Proficient (3) | Developing (2) | Beginning (1) |
|-----------|---------------|----------------|----------------|---------------|
| Code quality | Code runs without errors, uses meaningful variable names, includes comments on complex logic, follows consistent formatting | Code runs without errors, mostly readable, minor naming or formatting inconsistencies | Code runs but has minor bugs, inconsistent naming, minimal comments | Code has significant errors or does not run, difficult to read |

### Step 4: Design the grading scheme

The overall grading scheme shows how assessments combine into a final evaluation:

```markdown
## Grading scheme

| Component | Weight | Type | Frequency |
|-----------|--------|------|-----------|
| Module quizzes | 20% | Formative | After each module |
| Practice exercises | 30% | Formative | Weekly |
| Midpoint project | 20% | Summative | Week 6 |
| Final capstone | 30% | Summative | Final week |

**Passing grade:** 70% overall, with minimum 60% on capstone
```

Consider:

- **Weighting** — summative assessments usually carry more weight, but don't make any single assessment worth more than 40% (too high-stakes)
- **Completion vs. quality** — for formative assessments, sometimes completion credit (did they attempt it?) is better than quality grading (reduces anxiety, encourages experimentation)
- **Late policies** — if relevant for the delivery format
- **Retake policies** — especially for formative assessments, allowing retakes supports learning

## Formative assessment toolkit

Quick, low-stakes checks you can drop into any lesson:

| Technique | How it works | Best for |
|-----------|--------------|----------|
| **Exit ticket** | "Write one thing you learned and one question you still have" | End of any session |
| **Think-pair-share** | Individual thinking → discuss with partner → share with group | Checking understanding mid-lesson |
| **Muddiest point** | "What was the most confusing part?" | Identifying gaps in real-time |
| **Quick quiz** | 3-5 questions, auto-graded or self-checked | Recall and understanding checks |
| **Peer review** | Learners evaluate each other's work using a checklist | Apply and Evaluate level skills |
| **Reflection journal** | Short written reflection on learning progress | Self-awareness, metacognition |
| **Demonstrate** | "Show me how you would…" | Apply level skills |
| **One-minute paper** | "Summarize today's key concept in your own words" | Understanding check |

## Output format

### Module-level assessment

Write to `modules/XX-name/assessment.md`:

```markdown
# Module X: [Name] — assessment

## Assessed objectives
- [List objectives this assessment measures]

## Formative assessments

### [Assessment name]
- **Type:** [quiz / exercise / reflection / peer review]
- **When:** [during which part of the lesson]
- **Task:** [what learners do]
- **Grading:** [completion / rubric / auto-graded]

## Summative assessment

### [Assessment name]
- **Type:** [project / exam / practical / presentation]
- **Task:** [detailed instructions]
- **Time:** [how long / due date]
- **Resources:** [what they can use]
- **Rubric:** [see below]

## Rubric

| Criterion | Excellent (4) | Proficient (3) | Developing (2) | Beginning (1) |
|-----------|---------------|----------------|----------------|---------------|
| … | … | … | … | … |
```

### Course-level grading

Write to `grading-rubric.md`:

```markdown
# Grading scheme

## Components

| Component | Weight | Description |
|-----------|--------|-------------|
| … | … | … |

## Passing criteria
[What constitutes passing — overall and per-component]

## Policies
[Late work, retakes, academic integrity, accommodations]

## Objective-assessment alignment

| Learning objective | Assessed by | Assessment type |
|--------------------|-------------|-----------------|
| [CO1] | Module 3 project, Final capstone | Summative |
| [CO2] | Module 2 quiz, Module 5 exercise | Formative + Summative |
```

Use whatever frontmatter convention the host project uses. If none, a `title:` line is enough.

The alignment table at the bottom is the final check — every course-level objective should appear at least once. If an objective has no assessment, either add one or question whether the objective is actually needed.
