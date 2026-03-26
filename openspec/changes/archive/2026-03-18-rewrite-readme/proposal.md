## Why

Current README.md describes the old OpenInsight multi-agent delivery runtime, which no longer reflects this repository. The repo has been restructured as a standalone MCP server (`pytorch-community-mcp`) that provides PyTorch community intelligence tools. Users landing on this repo have no way to understand what it does, how to deploy it, or how to configure it in their MCP clients.

## What Changes

- **Rewrite README.md** with accurate project description: a FastMCP server providing 8 curated PyTorch community intelligence tools (PRs, issues, RFCs, Slack, Discourse, events, blog, contributor activity)
- **Add deployment section**: installation via `pip`/`uv`, running via `python -m pytorch_community_mcp`, environment variables for GitHub/Slack/Discourse credentials
- **Add client configuration section**: examples for Claude Code, OpenCode, and generic MCP client JSON config
- **Add tools overview**: brief table of the 8 available tools and what they do
- **Remove outdated content**: all references to the old multi-agent delivery runtime, opencode agents, daily reports, etc.

## Capabilities

### New Capabilities
- `readme-content`: Complete README.md rewrite covering project introduction, deployment guide, client configuration examples, and tools reference

### Modified Capabilities

## Impact

- `README.md` (root): full rewrite — old content entirely replaced
- No code changes, no API changes, no dependency changes
