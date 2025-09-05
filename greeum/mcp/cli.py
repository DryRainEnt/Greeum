import typer
from typing import Optional, List
from .server import GreeumMCPServer, check_dependencies
from . import __version__
import logging
import sys

logger = logging.getLogger("greeummcp")

app = typer.Typer(
    add_completion=False, 
    help="GreeumMCP command-line interface",
    invoke_without_command=True  # Allow running without subcommand
)

@app.callback()
def main(
    ctx: typer.Context,
    data_dir: Optional[str] = typer.Argument(None, help="Memory data directory (default: ./data)"),
    transport: str = typer.Option("stdio", "--transport", "-t", help="Transport type: stdio|http|websocket"),
    port: int = typer.Option(8000, "--port", "-p", help="Port for http/websocket"),
    skip_check: bool = typer.Option(False, "--skip-check", help="Skip dependency check"),
):
    """
    GreeumMCP - Memory Engine for LLMs
    
    Usage:
      greeummcp                    # Run with default settings
      greeummcp /path/to/data      # Run with custom data directory
      greeummcp --transport http   # Run with HTTP transport
    """
    # If no command is specified, run the server
    if ctx.invoked_subcommand is None:
        # Use provided data_dir or default
        if data_dir is None:
            data_dir = "./data"
        
        # Check dependencies unless skipped
        if not skip_check:
            logger.info("Checking dependencies...")
            check_dependencies()
        
        # Run server with simplified defaults
        server = GreeumMCPServer(
            data_dir=data_dir,
            server_name="greeum_mcp",
            port=port,
            transport=transport,
        )
        server.run()

@app.command()
def version():
    """Print GreeumMCP version."""
    typer.echo(__version__)

@app.command("list-tools")
def list_tools(data_dir: str = typer.Option("./data")):
    """Show available MCP tool names."""
    server = GreeumMCPServer(data_dir=data_dir, transport="stdio")
    tool_names = list(server.mcp._tools.keys())  # FastMCP internal registry
    typer.echo("\n".join(tool_names))

@app.command()
def run(
    data_dir: str = typer.Option("./data", help="Memory data directory"),
    server_name: str = typer.Option("greeum_mcp", help="Server name"),
    port: int = typer.Option(8000, help="Port for http/websocket"),
    transport: str = typer.Option("stdio", help="Transport type: stdio|http|websocket"),
    skip_dependency_check: bool = typer.Option(False, help="Skip dependency version check"),
):
    """Run GreeumMCP server (legacy command - use 'greeummcp' directly instead)."""
    # Check dependencies unless explicitly skipped
    if not skip_dependency_check:
        logger.info("Checking dependencies...")
        check_dependencies()
    
    server = GreeumMCPServer(
        data_dir=data_dir,
        server_name=server_name,
        port=port,
        transport=transport,
    )
    server.run()

if __name__ == "__main__":
    app() 