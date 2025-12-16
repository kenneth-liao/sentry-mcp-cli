"""MCP stdio connection manager for Sentry MCP server"""
import asyncio
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from sentry_cli.config.settings import Settings


class SentryMCPConnector:
    """
    Manages connection to Sentry MCP server via stdio transport.

    Automatically spawns the Sentry MCP server as a subprocess using npx
    and establishes a stdio connection.
    """

    def __init__(self, settings: Settings):
        """
        Initialize the connector.

        Args:
            settings: Application settings with Sentry credentials
        """
        self.settings = settings
        self._session: Optional[ClientSession] = None

    def _build_server_params(self) -> StdioServerParameters:
        """
        Build server parameters for spawning Sentry MCP server.

        Returns:
            StdioServerParameters configured for Sentry MCP server
        """
        # Base command and args
        args = [
            "@sentry/mcp-server@latest",
            "--access-token",
            self.settings.sentry_access_token,
        ]

        # Add --host flag for self-hosted Sentry
        if self.settings.sentry_host != "sentry.io":
            args.extend(["--host", self.settings.sentry_host])

        # Build environment variables
        env = {
            "SENTRY_HOST": self.settings.sentry_host,
        }

        # Add OpenAI API key if available (enables AI-powered search tools)
        if self.settings.openai_api_key:
            env["OPENAI_API_KEY"] = self.settings.openai_api_key

        return StdioServerParameters(
            command="npx",
            args=args,
            env=env,
        )

    async def connect(self) -> ClientSession:
        """
        Establish stdio connection to Sentry MCP server.

        Spawns the server as a subprocess and initializes the MCP session.

        Returns:
            Initialized ClientSession ready for tool calls

        Raises:
            Exception: If server fails to start or connection fails
        """
        server_params = self._build_server_params()

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self._session = session
                return session

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool and return the result.

        Args:
            tool_name: Name of the MCP tool to call
            arguments: Tool arguments as a dictionary

        Returns:
            Tool execution result

        Raises:
            RuntimeError: If session is not initialized
            Exception: If tool call fails
        """
        if not self._session:
            raise RuntimeError("MCP session not initialized. Call connect() first.")

        result = await self._session.call_tool(tool_name, arguments)
        return result

    async def list_tools(self) -> List[Any]:
        """
        List all available MCP tools from the server.

        Returns:
            List of tool definitions with names, descriptions, and schemas

        Raises:
            RuntimeError: If session is not initialized
        """
        if not self._session:
            raise RuntimeError("MCP session not initialized. Call connect() first.")

        tools_response = await self._session.list_tools()
        return tools_response.tools


async def execute_tool(
    settings: Settings,
    tool_name: str,
    arguments: Dict[str, Any],
) -> Any:
    """
    Helper function to execute a single tool call with automatic connection management.

    This function handles the full lifecycle:
    1. Spawn MCP server subprocess
    2. Connect via stdio
    3. Call the tool
    4. Return result
    5. Clean up connection

    Args:
        settings: Application settings
        tool_name: Name of the MCP tool to call
        arguments: Tool arguments

    Returns:
        Tool execution result

    Example:
        >>> settings = get_settings()
        >>> result = await execute_tool(
        ...     settings,
        ...     "find_organizations",
        ...     {"query": "my-org"}
        ... )
    """
    connector = SentryMCPConnector(settings)

    async with stdio_client(connector._build_server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result


async def list_all_tools(settings: Settings) -> List[Any]:
    """
    Helper function to list all available tools with automatic connection management.

    Args:
        settings: Application settings

    Returns:
        List of tool definitions

    Example:
        >>> settings = get_settings()
        >>> tools = await list_all_tools(settings)
        >>> for tool in tools:
        ...     print(f"{tool.name}: {tool.description}")
    """
    connector = SentryMCPConnector(settings)

    async with stdio_client(connector._build_server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_response = await session.list_tools()
            return tools_response.tools
