"""PyTorch Community MCP Server."""


def main() -> None:
    """CLI entry point for pytorch-community-mcp."""
    from pytorch_community_mcp.server import mcp

    mcp.run()
