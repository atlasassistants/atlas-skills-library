# Using Skills Outside Claude Code

Atlas runs production agents in more than one environment. Some of our work lives in Claude Code; some lives in custom agents on a VPS; some lives in other runtimes entirely. The skills in this library are designed to be usable in **any** of those environments, not just Claude Code. This doc explains why that matters, what makes a skill portable, and how a non–Claude-Code agent should consume a skill from this repo.

## 1. Why portable

The Atlas Skills Library is a GitHub-hosted Claude Code plugin marketplace, but that's the **distribution** mechanism, not the **only** consumer. Atlas operates agents outside Claude Code — custom agents running on a VPS, embedded assistants in client products, experimental harnesses — and the methodology encoded in these skills should be just as valuable to those agents as it is inside Claude Code. If a skill is only readable by Claude Code, it's locked to one runtime, and Atlas has to rewrite the method every time it mounts the work somewhere else. That's wasteful and it fragments the source of truth.

Treat portability as a first-class constraint, not a nice-to-have.

## 2. What makes a skill portable

Three things, all of which should be true for every skill in this library unless it's explicitly marked Claude-Code-only:

1. **SKILL.md is plain markdown with YAML frontmatter.** No Claude-Code-specific directives, no embedded commands, no hook metadata in the skill body itself. Any agent that can read markdown can load the file.
2. **The skill body refers to capabilities abstractly.** Instead of saying "use the `Read` tool to load the file" or "use `WebFetch` to get the page", the skill says "read the file at the given path" or "fetch the contents of the URL". The capability is named; the specific tool is not. This lets a non-CC agent wire the capability to whatever its runtime provides.
3. **Required capabilities are listed in the plugin README.** The README's "Required capabilities" section enumerates what the host agent needs to be able to do — read files, list calendar events, send email, search the web — so any agent runtime knows what to wire up before mounting the skill.

Together these three rules mean a non-CC agent can take a plugin from this repo, read the capability list, map each capability to an equivalent tool in its own runtime, and run the skill without modification.

## 3. How a non–Claude-Code agent consumes a skill

The practical flow for a custom agent (or any non-CC runtime):

1. **Clone the repo, or just the plugin you need.** `git clone https://github.com/colin-atlas/atlas-skills-library` gives you the full library; `git sparse-checkout` or a direct download works if you only want one plugin.
2. **Read the plugin README.** Pay attention to "Required capabilities" and "Suggested tool wiring". The README tells you exactly what your agent needs to be able to do before it can run the skills.
3. **Load the `SKILL.md` content into your agent.** How depends on your runtime. Common approaches: inject the SKILL.md body into the system prompt when the skill activates; load it as a system message at session start; or use it as a tool/skill definition in whatever skill system your runtime provides.
4. **Wire the capabilities to real tools.** For each capability the skill expects (read file, list calendar, send message), map it to a concrete tool your agent has. MCP servers, custom tools, direct API calls — whatever your stack uses.
5. **Load reference docs as additional context.** Reference docs under `references/` are also plain markdown. When an opinionated skill references one of these files, your agent should load it the same way Claude Code would — as additional context injected when the skill activates.

A non-CC agent gets exactly the same methodology and the same skill body as a Claude Code agent. The only difference is the tool wiring, and that's explicitly factored out into the README for this reason.

## 4. What to avoid in skill bodies

When authoring a skill for this library, avoid baking in things that would break portability:

- **Hardcoded tool names.** Don't write "use the `Read` tool", "use `Grep` to search", "use `WebFetch` to load the page". These are Claude Code built-ins; they don't exist in other runtimes. Write the capability abstractly instead.
- **Assumptions about directory structure specific to one agent.** Don't assume the agent has access to a specific file layout (e.g., `~/.claude/`) unless the plugin is explicitly Claude-Code-only.
- **Claude-Code-specific slash commands in skill bodies.** Slash commands belong in plugin command definitions, not inside SKILL.md. A non-CC agent has no way to execute `/plugin` from inside a skill body.
- **Hook-based logic inside skill bodies.** Hooks are a Claude Code plumbing feature; they shouldn't shape how a skill's content is written.

The one exception to "no hardcoded tool names" is when you genuinely, literally mean that specific tool — usually because the plugin is Claude-Code-only and there's no way around it. In that case, see the next section.

## 5. When a plugin is Claude-Code-only

Some plugins will legitimately need Claude-Code-specific features — a custom slash command, a hook, or a built-in tool that has no analogue elsewhere. For those cases, the convention is to declare the plugin Claude-Code-only in `plugin.json`:

```json
{
  "name": "some-plugin",
  "version": "0.1.0",
  "claude_code_only": true
}
```

When `claude_code_only: true` is set, reviewers relax the portability rules: the skill body can reference Claude Code tool names directly, and the README's "Required capabilities" section may say "Claude Code with built-in tools". Clients filtering for portable plugins can skip these by reading the flag.

> **v1 note:** `claude_code_only` is a **forward-looking convention**. No plugin in v1 uses it — every v1 plugin (including `meeting-ops`) is written to be portable. The flag exists so future plugins that need CC-specific features have a clear, honest way to declare themselves without pretending to be portable.
