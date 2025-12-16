"""Main entry point for Sentry MCP CLI"""
import asyncio
import json
import sys
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from sentry_cli.config.settings import Settings, get_settings
from sentry_cli.mcp.connector import list_all_tools

# Helper function to find a specific tool
async def get_tool_by_name(settings: Settings, tool_name: str):
    """Get a specific tool by name from the MCP server"""
    tools = await list_all_tools(settings)

    # Find exact match first
    for tool in tools:
        if tool.name == tool_name:
            return tool

    # Try fuzzy match (replace hyphens with underscores and vice versa)
    normalized_name = tool_name.replace("-", "_")
    for tool in tools:
        if tool.name.replace("-", "_") == normalized_name:
            return tool

    return None

# Create the main Typer app
app = typer.Typer(
    name="sentry",
    help="Lightweight CLI wrapper for Sentry MCP server - optimized for AI assistants",
    add_completion=False,
)

# Global console for rich output
console = Console()


# Callback for global options
@app.callback()
def main(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON (machine-readable)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Increase output verbosity",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Minimal output",
    ),
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Disable interactive prompts",
    ),
    org: Optional[str] = typer.Option(
        None,
        "--org",
        help="Default organization slug (overrides config)",
    ),
):
    """
    Global options for all commands.

    These options are available for every command in the CLI.
    """
    # Store global options in context for use by commands
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["no_interactive"] = no_interactive
    ctx.obj["org"] = org


@app.command(name="list-tools")
def list_tools(
    ctx: typer.Context,
):
    """
    List all available Sentry MCP tools.

    This command provides progressive disclosure - showing minimal information
    about available tools to reduce token usage. Use 'describe-tool' for details.

    Example:
        sentry list-tools --json
    """
    try:
        # Get settings
        settings = get_settings()

        # Override settings with global options
        if ctx.obj.get("org"):
            settings.sentry_default_org = ctx.obj["org"]

        # Run async function to list tools
        tools = asyncio.run(list_all_tools(settings))

        # Output based on format
        if ctx.obj.get("json"):
            # JSON output for AI assistants
            output = {
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                    }
                    for tool in tools
                ],
                "total": len(tools),
            }
            print(json.dumps(output, indent=2))
        else:
            # Human-readable output
            rprint(f"\n[bold]Available Sentry MCP Tools ({len(tools)}):[/bold]\n")

            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Tool Name", style="green")
            table.add_column("Description")

            for tool in tools:
                table.add_row(
                    tool.name,
                    tool.description[:80] + "..." if len(tool.description) > 80 else tool.description
                )

            console.print(table)
            rprint("\n[dim]Use 'sentry describe-tool <name>' for detailed information.[/dim]\n")

    except Exception as e:
        if ctx.obj.get("json"):
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            rprint(f"[red]Error:[/red] {e}")
        sys.exit(1)


@app.command(name="describe-tool")
def describe_tool(
    ctx: typer.Context,
    tool_name: str = typer.Argument(..., help="Name of the tool to describe"),
):
    """
    Show detailed documentation for a specific Sentry MCP tool.

    This command provides Tier 2 progressive disclosure - showing full description,
    parameters, and usage examples for a specific tool (~200 tokens).

    Example:
        sentry describe-tool find-organizations
        sentry describe-tool get-issue-details --json
    """
    try:
        # Get settings
        settings = get_settings()

        # Find the tool
        tool = asyncio.run(get_tool_by_name(settings, tool_name))

        if not tool:
            if ctx.obj.get("json"):
                print(json.dumps({
                    "error": f"Tool '{tool_name}' not found",
                    "hint": "Run 'sentry list-tools' to see available tools"
                }, indent=2))
            else:
                rprint(f"[red]Error:[/red] Tool '{tool_name}' not found")
                rprint(f"[dim]Run 'sentry list-tools' to see available tools[/dim]")
            sys.exit(1)

        # Output based on format
        if ctx.obj.get("json"):
            # JSON output for AI assistants
            output = {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema if hasattr(tool, "inputSchema") else None,
            }
            print(json.dumps(output, indent=2))
        else:
            # Human-readable output
            rprint(f"\n[bold cyan]Tool:[/bold cyan] {tool.name}\n")
            rprint(f"[bold]Description:[/bold]")
            rprint(f"{tool.description}\n")

            if hasattr(tool, "inputSchema") and tool.inputSchema:
                schema = tool.inputSchema
                if isinstance(schema, dict) and "properties" in schema:
                    rprint("[bold]Parameters:[/bold]")
                    for param_name, param_info in schema.get("properties", {}).items():
                        required = param_name in schema.get("required", [])
                        req_marker = "[red]*[/red]" if required else " "
                        param_desc = param_info.get("description", "No description")
                        param_type = param_info.get("type", "any")
                        rprint(f"  {req_marker} [green]{param_name}[/green] ({param_type}): {param_desc}")

            rprint(f"\n[dim]Full schema: sentry tool-schema {tool.name}[/dim]\n")

    except Exception as e:
        if ctx.obj.get("json"):
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            rprint(f"[red]Error:[/red] {e}")
        sys.exit(1)


@app.command(name="tool-schema")
def tool_schema(
    ctx: typer.Context,
    tool_name: str = typer.Argument(..., help="Name of the tool to get schema for"),
):
    """
    Show the complete JSON schema for a specific Sentry MCP tool.

    This command provides Tier 3 progressive disclosure - showing the full
    JSON schema including all parameters, types, and constraints (~500 tokens).

    Example:
        sentry tool-schema find-organizations
        sentry tool-schema get-issue-details
    """
    try:
        # Get settings
        settings = get_settings()

        # Find the tool
        tool = asyncio.run(get_tool_by_name(settings, tool_name))

        if not tool:
            if ctx.obj.get("json"):
                print(json.dumps({
                    "error": f"Tool '{tool_name}' not found",
                    "hint": "Run 'sentry list-tools' to see available tools"
                }, indent=2))
            else:
                rprint(f"[red]Error:[/red] Tool '{tool_name}' not found")
                rprint(f"[dim]Run 'sentry list-tools' to see available tools[/dim]")
            sys.exit(1)

        # Always output JSON schema
        schema = {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema if hasattr(tool, "inputSchema") else {},
        }
        print(json.dumps(schema, indent=2))

    except Exception as e:
        if ctx.obj.get("json"):
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            rprint(f"[red]Error:[/red] {e}")
        sys.exit(1)


# Entry point for CLI
if __name__ == "__main__":
    app()
