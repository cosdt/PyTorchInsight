# PyTorch Community MCP

A domain-specific [MCP](https://modelcontextprotocol.io/) server that gives AI agents access to PyTorch community intelligence. Instead of juggling 120+ generic tools from separate GitHub and Discourse MCPs, this server provides **10 curated, PyTorch-focused tools** with a unified Markdown output format.

Data sources covered: **GitHub** (pytorch/pytorch, pytorch/rfcs), **Discourse** (discuss.pytorch.org), **PyTorch Events**, and the **PyTorch Blog RSS feed**.

## Tools

| Tool | Description | Source |
|------|-------------|--------|
| `get_prs` | Fetch pull requests by date range and module | GitHub |
| `get_issues` | Fetch issues by date range, module, and state | GitHub |
| `get_commits` | Fetch commits by date range and author | GitHub |
| `get_rfcs` | Fetch RFCs from pytorch/pytorch and pytorch/rfcs | GitHub |
| `get_pr_detail` | Get detailed info for a single PR | GitHub |
| `get_issue_detail` | Get detailed info for a single issue | GitHub |
| `get_discussions` | Search forum topics | Discourse |
| `get_events` | Fetch community events | pytorch.org |
| `get_blog_news` | Fetch blog posts from RSS feed | pytorch.org |
| `get_key_contributors_activity` | Cross-platform activity summary for a contributor | GitHub + Discourse |

## Deployment

### Prerequisites

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Install

```bash
# With uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

### Environment Variables

| Variable | Purpose | Required | Notes |
|----------|---------|----------|-------|
| `GITHUB_TOKEN` | GitHub API access | Yes | Personal access token with `repo` scope |
| `DISCOURSE_API_KEY` | Discourse API key | Optional | For authenticated forum access |
| `DISCOURSE_API_USERNAME` | Discourse username | Optional | Required with `DISCOURSE_API_KEY` |

### Run

```bash
# From the project directory (no pre-install needed)
uv run pytorch-community-mcp

# Or if already installed
pytorch-community-mcp
```

The server starts on **stdio** transport by default.

## Client Configuration

### Claude Code

Add to your Claude Code MCP settings (`~/.claude/settings.json` or project-level `.claude/settings.json`):

```json
{
  "mcpServers": {
    "pytorch-community": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/openinsight_mcp", "pytorch-community-mcp"],
      "env": {
        "GITHUB_TOKEN": "ghp_..."
      }
    }
  }
}
```

### OpenCode

Add to your OpenCode config (`opencode.json`):

```json
{
  "mcpServers": {
    "pytorch-community": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/openinsight_mcp", "pytorch-community-mcp"],
      "env": {
        "GITHUB_TOKEN": "ghp_..."
      }
    }
  }
}
```

> **Note:** Replace `/absolute/path/to/openinsight_mcp` with the actual path where you cloned this repo. `uv run --directory` handles dependency resolution automatically — no pre-installation needed, and the configuration works from any working directory.
>
> Adjust `env` to include whichever credentials you need. Only tools whose credentials are configured will function — the rest will return a clear error message.

## License

Apache-2.0
