# course-design

> Six skills that walk an instructional designer through a full course-design workflow — from "I want to teach people something" to a complete course project tree with objectives, curriculum, lesson plans, and a grading rubric.
> v0.1.0

## What it does

Turns the vague request "design a course on X" into a structured, pedagogically sound learning experience. The plugin is built around the ADDIE framework (Analysis → Design → Development → Implementation → Evaluation), with a master orchestrator that walks the user through each phase and five specialist skills the user can also invoke directly.

Each skill produces a specific markdown artifact in a per-course folder under a configured courses root:

| Phase | Skill | Output |
|---|---|---|
| Analysis | `needs-analysis` | `overview.md` (audience profile, gap analysis, resources, constraints) |
| Design | `learning-objectives` | `objectives.md` (Bloom's-aligned, ABCD-formatted, with course → module → lesson alignment matrix) |
| Design | `curriculum-sequencer` | `curriculum.md` (dependency map, ordered module sequence, schedule, checkpoints) |
| Development | `lesson-planner` | `modules/XX-name/lesson-plan.md` (Gagné's Nine Events, time allocations, materials list) |
| Evaluation | `assessment-designer` | `modules/XX-name/assessment.md` and course-level `grading-rubric.md` |
| (orchestration) | `course-designer` | the full tree above, end-to-end |

The whole plugin is methodology-neutral — it encodes well-established instructional design frameworks (ADDIE, Bloom's Taxonomy, Backward Design, Gagné's Nine Events, ABCD objectives), not an Atlas-original method. The opinion is in the *combination* and the *workflow*, not in the underlying frameworks.

## Who it's for

Anyone who has to design a course, bootcamp, workshop, training program, or curriculum and wants the agent to drive the process rather than re-deriving instructional-design best practices each time. Atlas built this for ourselves to design internal training and client-facing programs (e.g. AI-savvy EA training). Useful for:

- **Educators / trainers** building structured curricula from scratch
- **Operators / founders** designing internal training for new hires or specific skills
- **L&D teams** translating subject-matter expert knowledge into teachable modules
- **Course creators** bringing rigor to a course they've been running on instinct

You don't need to know the frameworks — the skills handle that. You just need to know what you want to teach and to whom.

## Required capabilities

The plugin's skills depend on these capabilities. Each is named abstractly — wire it to whatever the host agent has access to.

- **Filesystem read + write** — read existing course material if any; write the course project tree (overview, objectives, curriculum, lesson plans, assessments, rubric) into the configured courses root.
- **Conversational interview** — each skill has interview-style steps that ask the user a small number of structured questions (audience, scope, constraints, tools, etc.). The agent must be able to ask follow-ups and synthesize free-text answers.
- **Markdown rendering of tables** — most outputs include rubric tables, dependency maps, and schedule tables. The host should render markdown tables.

That's it — no external services, APIs, or tools are required. The skills are self-contained guidance and authoring; the work is design and writing, not integration.

## Suggested tool wiring

| Capability | Common options |
|---|---|
| Filesystem read / write | Claude Code's `Read` / `Write` / `Edit`, Filesystem MCP, any agent runtime's filesystem tools |
| Conversational interview | Claude Code's `AskUserQuestion`, plain chat fallback |
| Markdown rendering | Any chat client / markdown viewer / Obsidian-style vault |

These are examples, not requirements. Pick what the host actually has.

## Installation

```
/plugin marketplace add colin-atlas/atlas-skills-library
/plugin install course-design@atlas
```

> **Note (Team Test phase):** until this plugin is promoted to `plugins/`, install directly from the `team-test/` path rather than via the marketplace. See [`docs/skill-lifecycle.md`](../../docs/skill-lifecycle.md) for the team-test installation pattern.

## First-run setup

There's no configuration file required. The orchestrator will ask once where to write the course project on first use, and you can either tell it (e.g. `~/work/training/courses/`) or let it default to a `courses/` directory at the current working root. The other skills inherit the same convention — they write into the per-course folder the orchestrator created.

If you want to predeclare the location for an unattended run:

1. **Pick a courses root.** Any directory the agent can write to. Common choices: a `courses/` folder at the project root, a `training/` folder in your knowledge base, or an Obsidian vault subfolder.
2. **Pre-create it (optional).** The skills will create missing folders, but creating it ahead lets you choose the exact path.
3. **Mention the path in your first message** to the orchestrator, e.g. *"Design a course on prompt engineering for our EAs. Write the project to `~/work/atlas-training/courses/prompt-engineering/`."*

Outputs use vanilla markdown. They render correctly in any markdown viewer (Obsidian, GitHub, IDE preview). The skills don't require a specific frontmatter convention — they suggest a `title:` line and adapt to whatever convention the host project already uses.

## Skills included

- **`course-designer`** — *neutral.* Master orchestrator. Walks the user through ADDIE phases in order, creates the course project tree, and delegates to the specialist skills phase by phase. Use this for end-to-end course design.
- **`needs-analysis`** — *neutral.* Phase 1 (Analysis). Builds a learner profile, runs a gap analysis (current → target → gap → priority), and inventories resources / constraints. Writes `overview.md`.
- **`learning-objectives`** — *neutral.* Phase 2 (Design). Writes measurable objectives at course / module / lesson granularity using Bloom's Taxonomy and the ABCD formula. Produces an alignment matrix. Writes `objectives.md`.
- **`curriculum-sequencer`** — *neutral.* Phase 3 (Design). Groups objectives into modules, maps prerequisite dependencies, applies scaffolding and spiral curriculum, and produces a delivery-format-appropriate schedule. Writes `curriculum.md`.
- **`lesson-planner`** — *neutral.* Phase 4 (Development). Designs per-module lesson plans using Gagné's Nine Events and Backward Design. Allocates time, picks activities, lists materials. References a Bloom's-indexed activity patterns library. Writes `modules/XX-name/lesson-plan.md`.
- **`assessment-designer`** — *neutral.* Phase 5 (Evaluation). Designs assessments aligned to objectives via Backward Design — picks the right method per Bloom's level, writes rubrics with observable level descriptors, and builds a weighted grading scheme. Writes `modules/XX-name/assessment.md` and `grading-rubric.md`.

The orchestrator can also delegate without you naming a phase — say "design a course on X" and it will invoke the others in order. The specialists are independently invokable, which is useful if you already have part of a course built and only need to flesh out one phase.

## Customization notes

This plugin is methodology-neutral by design — it uses widely-accepted instructional design frameworks rather than encoding Atlas-specific opinions. Common things to customize:

- **Bloom's verb lists.** The default verb tables in `learning-objectives` are generic. Add domain-specific verbs in your installed copy if your field has standard terms (e.g. medical or legal training).
- **Module-size defaults.** Default is "2-5 objectives per module, completable in one session." If your delivery format needs longer modules (e.g. multi-day workshops), edit `curriculum-sequencer/SKILL.md` step 1.
- **Time allocation rule of thumb.** `lesson-planner` step 4 has a 2-hour-session block schedule. Adjust the block durations if your default session length is different.
- **Rubric scale.** Default is 4 levels (Beginning → Developing → Proficient → Excellent). Some teams prefer 3 or 5 levels. Edit `assessment-designer/SKILL.md` step 3.
- **Output frontmatter.** Skills emit `title:`-only frontmatter by default. If your knowledge base has a richer convention (e.g. Obsidian vault with `type`, `tags`, `created`/`updated`), edit each skill's "Output format" block to match.
- **Activity patterns library.** `lesson-planner/references/activity-patterns.md` ships a baseline set indexed by Bloom's level. Add your own patterns there as you discover what works for your audience.

When customizing, edit the SKILL.md and reference files in your installed copy or your fork. The plugin is meant to be a starting point you adapt — not a black box.

## Atlas methodology

This plugin does **not** encode an opinionated Atlas methodology. It coordinates well-established instructional design frameworks:

- **ADDIE** (Analysis, Design, Development, Implementation, Evaluation) — process backbone
- **Bloom's Taxonomy** — cognitive levels and verb framework for objectives
- **ABCD formula** — objective writing structure (Audience, Behavior, Condition, Degree)
- **Backward Design** — assessment-first instructional alignment (Wiggins & McTighe)
- **Gagné's Nine Events of Instruction** — lesson structure
- **Spiral curriculum** (Bruner) — revisiting concepts at increasing depth

If Atlas develops an opinionated take on any of these (e.g. a specific module-size policy or assessment pattern that beats the default), it would be added here as a separate methodology reference doc and the relevant skill would be re-marked `opinionated`. Until then, treat this plugin as a well-organized harness around the standard frameworks rather than a proprietary method.

## Troubleshooting

**The orchestrator dives into ADDIE without asking enough about my context.** It's tuned to ask 6 questions in Step 1 (topic, audience, format, scope, outcome, constraints) before creating any files. If it skips ahead, prompt it: "Slow down — let's make sure we have the audience and scope nailed before you start writing files." The orchestrator's Step 1 guidance reminds it to have a conversation, not run a checklist.

**Objectives keep coming out vague ("understand X", "be familiar with Y").** The `learning-objectives` skill explicitly warns against these but the agent may slip. Push back: "These aren't measurable. Rewrite using Bloom's verbs from Apply or higher." The skill's "Common mistakes" table names the four most frequent vague-objective patterns and how to fix each.

**Modules end up unsequenced or the dependency map is missing.** The `curriculum-sequencer` skill's Step 2 requires an explicit dependency table before ordering. If the agent skipped to ordering, ask: "Show me the dependency map first — for each module, what must the learner already know?" The map prevents back-tracking.

**A lesson plan has 90 minutes of content for a 60-minute session.** Time inflation is a known failure mode. Lesson plans should be sanity-checked against the session duration declared in `curriculum.md`. Ask the agent: "Sum the time blocks — does this fit the session length, with the recommended 50% buffer on practice activities?"

**Rubric levels read like "good / okay / bad" with no observable criteria.** The `assessment-designer` skill's Step 3 has a "Bad criterion descriptions" table specifically for this. If the agent's rubric uses vague adjectives, ask: "What would I actually SEE at each level? Rewrite using observable criteria." Each cell should describe a specific behavior or output, not a quality judgment.

**Skill triggers when you didn't ask for it.** The skill descriptions and `when_to_use` blocks may be matching too broadly for your phrasing — e.g. mentioning a "training program" in an unrelated context can fire the orchestrator. Edit the `when_to_use` field of the offending skill to narrow the triggers, or invoke the specific skill you actually want by name.

**Output writes to an unexpected location.** Each skill writes into a course project folder under a courses root. The orchestrator asks once where that root is, but if you invoke a specialist skill directly (e.g. `learning-objectives` without the orchestrator), it may default to the current working directory. Tell it explicitly where the course folder is in your first message.
