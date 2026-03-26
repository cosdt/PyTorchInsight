## Context

The repository has transitioned from an OpenCode multi-agent delivery runtime to a standalone FastMCP server (`pytorch-community-mcp`). The current README.md still describes the old architecture. Users (AI agent developers, PyTorch community managers) need clear documentation to deploy and integrate this MCP server.

## Goals / Non-Goals

**Goals:**
- Provide a self-contained README that lets a new user go from zero to a working MCP integration
- Cover: what the server does, how to install/run it, how to configure credentials, and how to wire it into MCP clients (Claude Code, OpenCode)
- Include a quick-reference table of all 8 tools

**Non-Goals:**
- Detailed API documentation for each tool's parameters (belongs in dedicated docs)
- Contributing guide or development setup (can be added later)
- Internals/architecture explanation (covered in `docs/mcp.md`)

## Decisions

1. **Language: English** — MCP is an international ecosystem; English README maximizes reach. Chinese-specific notes can go in `docs/` if needed.

2. **Structure: 4 main sections** — Introduction → Tools Overview → Deployment → Client Configuration. This mirrors the user's journey: understand → install → configure.

3. **Client examples: Claude Code + OpenCode** — These are the two most common MCP clients in use. Show JSON config snippets for both.

4. **Credential docs inline** — Environment variables table directly in README rather than linking to a separate file, since there are only 5-6 variables.

## Risks / Trade-offs

- [Stale docs] README may drift from code as tools evolve → Mitigation: keep tool table minimal (name + one-liner), detailed docs elsewhere
- [Token complexity] Slack token setup has 3 paths (xoxc/xoxd, xoxp, auto-extract) → Mitigation: show simplest path first (xoxp), mention alternatives briefly
