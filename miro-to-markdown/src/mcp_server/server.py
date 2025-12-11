"""Backcasting MCP Server - Main entry point."""

import asyncio
import json
import os
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .tools import BackcastingTools

# Create MCP server instance
server = Server("backcasting")

# Initialize tools with repo root from environment or default
REPO_ROOT = Path(
    os.environ.get(
        "BACKCASTING_REPO_ROOT",
        Path(__file__).parent.parent.parent.parent,  # Default: up to repo root
    )
)
tools = BackcastingTools(REPO_ROOT)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Backcasting tools."""
    return [
        Tool(
            name="backcasting_get_template",
            description=(
                "Get a Markdown template for creating a new Backcasting node. "
                "Returns the template content and frontmatter schema."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "node_type": {
                        "type": "string",
                        "enum": ["root_cause", "symptom", "success_criteria"],
                        "description": "Type of node to get template for",
                    }
                },
                "required": ["node_type"],
            },
        ),
        Tool(
            name="backcasting_get_node",
            description=(
                "Fetch a single Backcasting node by ID. "
                "Returns parsed frontmatter, relations, and raw Markdown content."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": (
                            "Node ID (e.g., 'rc-001' for root cause, "
                            "'rf-001' for symptom, 'sc-001' for success criteria)"
                        ),
                    }
                },
                "required": ["id"],
            },
        ),
        Tool(
            name="backcasting_write_node",
            description=(
                "Create or update a Backcasting node on disk. "
                "Validates frontmatter structure and writes the file."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Node ID (must match the id in frontmatter)",
                    },
                    "markdown": {
                        "type": "string",
                        "description": "Full Markdown content including frontmatter",
                    },
                    "path": {
                        "type": "string",
                        "description": (
                            "Optional: relative path for the file. "
                            "If not provided, path is inferred from node ID."
                        ),
                    },
                },
                "required": ["id", "markdown"],
            },
        ),
        Tool(
            name="backcasting_get_chain_from_root",
            description=(
                "Return a causal chain from a Root Cause to Success Criteria. "
                "Traverses triggers and threatens relationships to find paths."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "root_id": {
                        "type": "string",
                        "description": "ID of the starting root_cause node (e.g., 'rc-006')",
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum traversal depth (default: 10)",
                        "default": 10,
                    },
                    "include_markdown": {
                        "type": "boolean",
                        "description": "Include markdown content in nodes (default: false)",
                        "default": False,
                    },
                },
                "required": ["root_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "backcasting_get_template":
            result = tools.get_template(arguments["node_type"])
        elif name == "backcasting_get_node":
            result = tools.get_node(arguments["id"])
        elif name == "backcasting_write_node":
            result = tools.write_node(
                node_id=arguments["id"],
                markdown=arguments["markdown"],
                path=arguments.get("path"),
            )
        elif name == "backcasting_get_chain_from_root":
            result = tools.get_chain_from_root(
                root_id=arguments["root_id"],
                max_depth=arguments.get("max_depth", 10),
                include_markdown=arguments.get("include_markdown", False),
            )
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False),
            )
        ]
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": str(e)}, ensure_ascii=False),
            )
        ]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def run():
    """Entry point for running the server."""
    asyncio.run(main())


if __name__ == "__main__":
    run()

