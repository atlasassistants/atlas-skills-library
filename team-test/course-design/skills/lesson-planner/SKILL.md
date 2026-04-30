---
name: lesson-planner
description: Design detailed lesson plans for individual course modules using Gagné's Nine Events of Instruction (gain attention → state objectives → recall prior → present content → provide guidance → practice → feedback → assess → enhance transfer) combined with Backward Design (assessment first, then instruction). Allocates time, picks delivery-format-appropriate activities, lists materials and prep, and adapts the structure for live sync, async self-paced, or hybrid delivery. Writes a per-module `lesson-plan.md`. References a library of reusable activity patterns by Bloom's level.
when_to_use: |
  User has a curriculum structure and needs to detail what happens during each lesson. Triggers on phrases like "plan this lesson", "what activities should I use", "design a workshop session", "flesh out this module", or "create a lesson plan for…". Also fires when the orchestrator (`course-designer`) reaches Phase 4 / Development.
atlas_methodology: neutral
---

# lesson-planner

Design what actually happens during a lesson. This is where the curriculum plan turns into a concrete instructional experience — what the instructor does, what learners do, what materials are needed, and how time is allocated.

## Gagné's Nine Events of Instruction

This framework structures a lesson so that each phase supports learning. Not every lesson needs all nine events explicitly, but they provide a reliable template — especially when you're unsure how to structure a session.

| # | Event | Purpose | What it looks like |
|---|-------|---------|--------------------|
| 1 | **Gain attention** | Focus learners, create curiosity | Provocative question, surprising demo, real-world problem, short story |
| 2 | **State objectives** | Set expectations for what they'll learn | "By the end of this session, you'll be able to…" |
| 3 | **Recall prior knowledge** | Activate what they already know | Quick review, warm-up quiz, "What do you remember about…?" |
| 4 | **Present content** | Deliver the new material | Lecture, demo, video, reading, worked examples |
| 5 | **Provide guidance** | Help them process the content | Tips, mnemonics, analogies, step-by-step walkthroughs, common pitfalls |
| 6 | **Practice** | Let them try it themselves | Exercises, labs, group activities, simulations |
| 7 | **Give feedback** | Tell them how they're doing | Instructor review, peer review, automated checks, self-assessment |
| 8 | **Assess** | Verify they can do it | Quiz, practical task, demonstration, reflection |
| 9 | **Enhance transfer** | Help them apply it beyond the lesson | Real-world scenarios, "try this at work" challenges, connect to next module |

### How to use the nine events

- **Short sessions (30-60 min):** combine events. Events 1-3 can be one 5-minute opener. Events 6-7 often overlap.
- **Workshops (2-4 hours):** full nine events, with the bulk of time on events 4-7 (content + practice + feedback).
- **Self-paced modules:** events translate to content sections. Event 6 becomes a hands-on exercise. Event 7 might be an answer key or self-check rubric.

The framework is a guide, not a straitjacket. Adapt it to what makes sense for your content and format.

## Lesson plan design process

### Step 1: Start from the objective

Pull the learning objectives for this module from `objectives.md`. Every activity in the lesson should serve at least one objective. If an activity doesn't connect to an objective, question whether it belongs.

### Step 2: Design the assessment first (Backward Design)

Before planning instruction, decide: **how will you know learners achieved the objective?**

This is the Backward Design principle — the assessment shapes the instruction, not the other way around. If the objective is "Apply prompt engineering techniques to generate structured output," the assessment might be:

> "Given a business scenario, write a prompt that produces a correctly formatted JSON output."

Now you know exactly what the lesson needs to prepare learners for.

### Step 3: Plan the activities

For each Gagné event, choose an appropriate activity.

**Attention grabbers (Event 1):**

- Show a before / after (bad prompt → good prompt, messy data → clean dashboard)
- Ask a question they can't yet answer but will be able to by the end
- Share a real failure story or case study
- Do a live demo of the end result

**Content delivery (Event 4):**

| Format | Best for | Watch out for |
|--------|----------|---------------|
| Live lecture / demo | Conceptual content, showing process | Keep under 15 min before switching to activity |
| Video | Async courses, repeatable demos | Keep under 10 min per segment |
| Reading | Reference material, detailed procedures | Pair with a task — "read then do" |
| Worked example | Technical skills, problem-solving | Walk through the thinking, not just the steps |
| Interactive tutorial | Tool skills, software training | Provide sandbox environment |

**Practice activities (Event 6):**

| Activity type | Best for | Group size |
|--------------|----------|------------|
| **Guided exercise** | First attempt at a new skill | Individual |
| **Pair programming / pair work** | Technical skills, building confidence | Pairs |
| **Case study** | Analysis, decision-making | Small groups (3-5) |
| **Role play / simulation** | Soft skills, client scenarios | Small groups |
| **Lab / sandbox** | Tool skills, experimentation | Individual |
| **Mini-project** | Synthesis of multiple skills | Individual or pairs |
| **Peer review** | Evaluation skills, multiple perspectives | Pairs |
| **Discussion / debate** | Complex topics with multiple viewpoints | Full group |

**Feedback mechanisms (Event 7):**

- Instructor walks around during practice and gives real-time tips
- Peer review with a provided checklist
- Self-assessment rubric ("check your work against these criteria")
- Automated tests or checks (for technical skills)
- Group debrief: "What worked? What was tricky?"

### Step 4: Allocate time

Be realistic. Common time allocation mistakes:

- Overestimating how fast learners will complete exercises (add 50% buffer)
- Underestimating transition time between activities (add 5 min between blocks)
- Front-loading lecture and leaving too little practice time

**Rule of thumb for a 2-hour session:**

| Block | Time | Events |
|-------|------|--------|
| Opening | 10 min | Gain attention, state objectives, recall prior |
| Content delivery | 20 min | Present content, provide guidance |
| Practice round 1 | 25 min | Guided practice + feedback |
| Content delivery | 15 min | Next concept or deeper dive |
| Practice round 2 | 30 min | Independent / group practice + feedback |
| Wrap-up | 15 min | Assessment, transfer, preview next session |
| Buffer | 5 min | Questions, overrun |

### Step 5: List materials and prep

For each lesson, specify:

- **Instructor materials:** slides, demo scripts, answer keys, discussion prompts
- **Learner materials:** handouts, exercise files, templates, starter code, readings
- **Tools / environment:** software, accounts, sandbox environments, equipment
- **Prep tasks:** what needs to be set up before the session?

## Output format

Write each lesson plan to `modules/XX-name/lesson-plan.md`:

```markdown
# Module X: [Name]

## Learning objectives
- [Pulled from objectives.md]

## Session overview
- **Duration:** [total time]
- **Format:** [lecture, workshop, lab, etc.]
- **Prerequisites:** [what learners should have completed]

## Lesson flow

### 1. Opening (X min)
**Gain attention:** [activity]
**State objectives:** [what you'll tell learners]
**Recall prior:** [connection to previous module]

### 2. Content block 1: [Topic] (X min)
**Present:** [how content is delivered]
**Guide:** [tips, examples, analogies]

### 3. Practice 1: [Activity name] (X min)
**Task:** [what learners do]
**Format:** [individual / pairs / groups]
**Feedback:** [how they get feedback]

### 4. Content block 2: [Topic] (X min)
…

### 5. Practice 2: [Activity name] (X min)
…

### 6. Wrap-up (X min)
**Assess:** [how you check understanding]
**Transfer:** [how this connects to real work or next module]
**Preview:** [what's coming next]

## Materials
- **Instructor:** [list]
- **Learner:** [list]
- **Environment:** [tools / setup needed]

## Instructor notes
[Tips, common student questions, things to watch for, timing adjustments]
```

Use whatever frontmatter convention the host project uses. If none, a `title:` line is enough.

## Adapting to delivery format

**Live synchronous:** full interactivity — discussions, live demos, real-time feedback. Plan for energy management (mix active and passive).

**Async self-paced:** replace discussions with reflection prompts. Replace live demos with recorded walkthroughs. Practice activities need clear instructions since there's no instructor to clarify. Feedback comes from self-check rubrics or automated tools.

**Hybrid:** live sessions focus on practice, discussion, and feedback. Async portions handle content delivery (watch before class → "flipped classroom" model).

See `references/activity-patterns.md` for a library of reusable activity patterns organized by Bloom's level and delivery format.
