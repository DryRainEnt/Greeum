"""
GreeumMCP - Greeum Memory Engine as MCP Server
"""

__version__ = "1.0.0"

from .server import GreeumMCPServer

# Convenience function to create and run a server
def run_server(data_dir="./data", server_name="greeum_mcp", port=8000, transport="stdio", greeum_config=None):
    """
    Create and run a GreeumMCP server.
    
    Args:
        data_dir: Directory to store memory data
        server_name: Name of the MCP server
        port: Port for HTTP transport (if used)
        transport: Transport type ('stdio', 'http', 'websocket')
        greeum_config: Additional configuration for Greeum components
    """
    server = GreeumMCPServer(
        data_dir=data_dir,
        server_name=server_name,
        port=port,
        transport=transport,
        greeum_config=greeum_config or {}
    )
    server.run() 