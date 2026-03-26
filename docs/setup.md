# PyTorch Community MCP Server — Setup Guide

## Installation

```bash
# With uv (recommended)
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

## Environment Variables

Configure the following environment variables for each platform:

### GitHub (Required for PR/Issue/RFC tools)

```bash
export GITHUB_TOKEN="ghp_..."
```

Create a [Personal Access Token](https://github.com/settings/tokens) with `repo` scope (read-only is sufficient).

### Discourse (Optional — public data accessible without auth)

```bash
export DISCOURSE_API_KEY="your-api-key"
export DISCOURSE_API_USERNAME="your-username"
```

Generate an API key at [discuss.pytorch.org admin settings](https://discuss.pytorch.org/admin/api/keys).

### Events & Blog

No authentication required. These tools work out of the box.

## Running the Server

### Standalone (stdio transport)

```bash
# From the project directory (no pre-install needed)
uv run pytorch-community-mcp

# Or if already installed
pytorch-community-mcp
```

### With Claude Code / OpenCode

Add to your MCP settings (works from any directory):

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

> Replace `/absolute/path/to/openinsight_mcp` with the actual path where you cloned this repo.

## Available Tools

| Tool | Description | Required Config |
|------|-------------|-----------------|
| `get_prs` | PyTorch PRs by date/module | GITHUB_TOKEN |
| `get_issues` | PyTorch issues by date/module/state | GITHUB_TOKEN |
| `get_commits` | PyTorch commits by date/author | GITHUB_TOKEN |
| `get_rfcs` | PyTorch RFCs from pytorch/pytorch + pytorch/rfcs | GITHUB_TOKEN |
| `get_pr_detail` | Detailed info for a single PR | GITHUB_TOKEN |
| `get_issue_detail` | Detailed info for a single issue | GITHUB_TOKEN |
| `get_discussions` | Discourse forum topics | None (optional DISCOURSE_API_KEY) |
| `get_events` | PyTorch community events | None |
| `get_blog_news` | PyTorch blog RSS feed | None |
| `get_key_contributors_activity` | Cross-platform contributor summary | GITHUB_TOKEN (Discourse optional) |

## Running Tests

```bash
pytest tests/
```
