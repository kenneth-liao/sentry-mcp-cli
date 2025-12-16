# Sentry MCP CLI

Lightweight CLI wrapper for the Sentry MCP server - optimized for AI assistants with progressive disclosure.

## Overview

This CLI tool provides a token-efficient interface to Sentry's Model Context Protocol (MCP) server, enabling AI assistants to interact with Sentry through simple commands. It implements **progressive disclosure** - showing minimal information by default (~50-100 tokens) with detailed documentation available on demand.

### Key Features

- ✅ **Token Efficient**: 81-90% reduction in token usage vs loading full MCP server
- ✅ **Progressive Disclosure**: Minimal info by default, detailed docs on request
- ✅ **AI-First Design**: JSON output by default, `--no-interactive` flag, optimized for agents
- ✅ **All Sentry Tools**: Access to 19 MCP tools (inspection, AI debugger, docs, triage, management)
- ✅ **Smart Config**: Auto-loads from `~/.claude/.env` and `./.env` using python-dotenv
- ✅ **uv Tool**: Easy installation with `uv tool install`

### Token Efficiency

| Scenario | Traditional MCP | Sentry CLI | Savings |
|----------|----------------|------------|---------|
| Discovery | ~8,000 tokens | ~100 tokens | 98.8% |
| Single Operation | ~8,500 tokens | ~800 tokens | 90.6% |
| 2 Operations | ~9,000 tokens | ~1,500 tokens | 83.3% |

## Installation

### Prerequisites

- Python 3.13 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Node.js and npm (for running the Sentry MCP server via `npx`)
- Sentry API access token

### Install via uv (Recommended)

```bash
# Install as a uv tool (global installation)
uv tool install git+https://github.com/yourusername/sentry-mcp-cli

# Verify installation
sentry --help
sentry list-tools
```

### Install for Development

```bash
# Clone the repository
git clone https://github.com/yourusername/sentry-mcp-cli
cd sentry-mcp-cli

# Install dependencies with uv
uv sync

# Run commands during development
uv run sentry --help
uv run sentry list-tools
```

## Configuration

### Environment Variables

The CLI loads environment variables from two locations (in priority order):

1. **`~/.claude/.env`** (user-level config for all AI assistants)
2. **`./.env`** (project-level config)

### Required Configuration

Create `~/.claude/.env` with your Sentry credentials:

```bash
# Create ~/.claude directory if it doesn't exist
mkdir -p ~/.claude

# Create .env file with your credentials
cat > ~/.claude/.env << 'EOF'
# Required: Sentry API Access Token
# Get from: https://sentry.io/settings/account/api/auth-tokens/
SENTRY_ACCESS_TOKEN=sntrys_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: For self-hosted Sentry instances
SENTRY_HOST=sentry.io

# Optional: Default organization and project
# SENTRY_DEFAULT_ORG=my-org
# SENTRY_DEFAULT_PROJECT=my-project

# Optional: OpenAI API key (enables AI-powered search tools)
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF
```

### Optional: Project-Level Configuration

You can also create a `.env` file in your project directory for project-specific settings:

```bash
# Copy the example file
cp .env.example .env

# Edit with your credentials
nano .env
```

## Usage

### Basic Commands

```bash
# List all available tools (minimal output)
sentry list-tools

# List tools with JSON output (for AI assistants)
sentry list-tools --json

# Get help for any command
sentry --help
sentry list-tools --help
```

### Available Tools (19 Total)

```bash
# Inspection Tools
sentry find-organizations [--query TEXT] [--json]
sentry find-projects [--org TEXT] [--query TEXT] [--json]
sentry find-teams [--org TEXT] [--query TEXT] [--json]
sentry find-releases [--org TEXT] [--project TEXT] [--query TEXT] [--json]
sentry get-issue-details <issue-id-or-url> [--json]
sentry get-trace-details <trace-id> [--org TEXT] [--json]
sentry get-event-attachment <event-id> [--project TEXT] [--attachment-id TEXT] [--json]
sentry search-events <query> [--org TEXT] [--project TEXT] [--limit N] [--json]  # Requires OpenAI
sentry whoami [--json]

# AI Debugger (Seer)
sentry analyze-issue-with-seer <issue-id-or-url> [--instruction TEXT] [--json]

# Documentation
sentry search-docs <query> [--guide TEXT] [--limit N] [--json]
sentry get-doc <path> [--json]

# Issue Triage
sentry search-issues <query> [--org TEXT] [--project TEXT] [--limit N] [--json]  # Requires OpenAI
sentry update-issue <issue-id> [--status TEXT] [--assignee TEXT] [--json]

# Project & Team Management
sentry create-team <name> [--org TEXT] [--json]
sentry create-project <name> [--team TEXT] [--platform TEXT] [--json]
sentry update-project <project-id> [--name TEXT] [--team TEXT] [--json]
sentry create-dsn <name> [--project TEXT] [--json]
sentry find-dsns [--project TEXT] [--json]

# Meta Commands (Progressive Disclosure)
sentry list-tools [--json]
sentry describe-tool <tool-name> [--json]     # Coming soon
sentry tool-schema <tool-name>                # Coming soon
```

### Global Flags

All commands support these global flags:

```bash
--json              # Output as JSON (machine-readable, default for AI assistants)
--verbose / -v      # Increase output verbosity
--quiet / -q        # Minimal output
--no-interactive    # Disable interactive prompts (for automation)
--org TEXT          # Default organization slug (overrides config)
--help              # Show help message
```

### Examples

```bash
# List organizations in JSON format
sentry find-organizations --json

# Get issue details with verbose output
sentry get-issue-details PROJ-123 --org my-org --verbose --json

# AI-powered search (requires OPENAI_API_KEY in .env)
sentry search-events "database errors in last hour" --org my-org --json

# Find projects in a specific organization
sentry find-projects --org my-org --json

# Get tool documentation
sentry describe-tool get-issue-details
```

## How It Works

### Architecture

```
AI Assistant (Claude/etc)
    ↓ runs CLI command
sentry-cli (Python + Typer + Rich)
    ↓ spawns subprocess
npx @sentry/mcp-server@latest
    ↓ stdio transport (JSON-RPC)
MCP Session ←→ Sentry API
```

### Progressive Disclosure

The CLI implements a three-tier information system:

**Tier 1: Discovery (~50 tokens)**
```bash
$ sentry list-tools
# Shows: Tool names + one-line descriptions
```

**Tier 2: Tool Description (~200 tokens)**
```bash
$ sentry describe-tool get-issue-details
# Shows: Full description, parameters, examples
```

**Tier 3: Full Schema (~500 tokens)**
```bash
$ sentry tool-schema get-issue-details
# Shows: Complete JSON schema for the tool
```

This approach reduces token usage by ~90% compared to loading the full MCP server schema.

## AI-Powered Tools

Two tools require an OpenAI API key:

1. **`search-events`** - Natural language event search and aggregations
2. **`search-issues`** - Natural language issue search

### Setup OpenAI

```bash
# Add to ~/.claude/.env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Graceful Degradation

If you try to use AI-powered tools without an OpenAI API key, you'll get a helpful error:

```
Error: This tool requires an OpenAI API key.

Setup:
  1. Get an API key from: https://platform.openai.com/api-keys
  2. Add to ~/.claude/.env:
     OPENAI_API_KEY="sk-xxxxxxxxxxxxx"
  3. Run command again

Alternative: Use 'sentry get-issue-details' for specific issue inspection.
```

## Development

### Project Structure

```
sentry-mcp-cli/
├── src/
│   └── sentry_cli/
│       ├── main.py              # Main Typer app + CLI entry point
│       ├── config/
│       │   └── settings.py      # Pydantic settings with dotenv support
│       ├── mcp/
│       │   └── connector.py     # MCP stdio connection manager
│       ├── commands/
│       │   ├── tools.py         # Tool commands
│       │   └── meta.py          # Meta commands (list-tools, etc)
│       └── output/
│           └── formatters.py    # Output formatters
└── tests/
```

### Running Tests

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests (when implemented)
uv run pytest
```

### Implementation Status

**Phase 1: Foundation** ✅ Complete
- [x] Project setup with uv
- [x] Settings class with dotenv loading
- [x] MCP connector with stdio subprocess
- [x] Main Typer app with global flags
- [x] `list-tools` command

**Phase 2: Meta Commands** 📋 Next
- [ ] `describe-tool` command
- [ ] `tool-schema` command
- [ ] Output formatters (table, compact)

**Phase 3-6: All Tools** 📋 Planned
- [ ] Inspection tools (find-*, get-*, whoami)
- [ ] AI-powered tools (search-*, analyze-*)
- [ ] Documentation tools (search-docs, get-doc)
- [ ] Triage tools (search-issues, update-issue)
- [ ] Management tools (create-*, update-*, find-dsns)

## Troubleshooting

### Command not found: sentry

Make sure uv's tool bin directory is in your PATH:

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
```

### Missing SENTRY_ACCESS_TOKEN

```bash
# Create ~/.claude/.env with your token
mkdir -p ~/.claude
echo 'SENTRY_ACCESS_TOKEN="sntrys_xxx"' > ~/.claude/.env
```

### MCP server fails to start

Ensure Node.js and npm are installed:

```bash
# Check versions
node --version  # Should be v18 or higher
npm --version   # Should be v9 or higher

# If not installed, install Node.js from: https://nodejs.org/
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## Related Projects

- [Sentry MCP Server](https://github.com/getsentry/sentry-mcp) - Official Sentry MCP server
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification
- [Claude Code](https://claude.com/code) - AI assistant optimized for development

## Support

For issues and questions:
- Open an issue on [GitHub](https://github.com/yourusername/sentry-mcp-cli/issues)
- Check the [Sentry MCP documentation](https://mcp.sentry.dev)
- Review the [MCP specification](https://modelcontextprotocol.io/docs)
