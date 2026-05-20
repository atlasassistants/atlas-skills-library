# Connecting your tools with Composio

Most Atlas plugins use Composio to connect to your apps (calendar, email, project management, etc.). Install our shared plugin `composio-connect` once, and every Atlas plugin you install uses it.

## What to do

1. Install `composio-connect`:
   ```
   /plugin marketplace add colin-atlas/atlas-skills-library
   /plugin install composio-connect@atlas
   ```
2. Run any Atlas plugin's setup — it'll walk you through Composio automatically if you haven't set it up yet.
3. That's it. The same Composio account works across every Atlas plugin and every AI tool that supports MCP.

## FAQ

**Do I need this for every plugin?**
Install it once. After that, any Atlas plugin you install reuses the same Composio connection.

**What if I already have Composio set up?**
Install `composio-connect` anyway. It'll detect your existing setup and skip the install steps.

**Why MCP and not the Composio CLI?**
MCP works on every operating system and every AI tool that supports it. The CLI is faster for advanced users on macOS / Linux, but is not currently supported on Windows. We standardize on MCP for everyone. Advanced users can use the CLI directly if they prefer — Atlas doesn't manage that path.

**Where does the plugin live?**
During initial team validation: [team-test/composio-connect/](team-test/composio-connect/). After promotion: `plugins/composio-connect/`.
