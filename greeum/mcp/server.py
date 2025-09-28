"""
Greeum MCP Server Implementation
"""
from typing import Dict, Any, Optional, List
from mcp.server.fastmcp import FastMCP
from .adapters.greeum_adapter import GreeumAdapter
from .tools.memory_tools import MemoryTools
from .tools.utility_tools import UtilityTools
from .resources.memory_resources import MemoryResources
import asyncio
import logging
import sys

logger = logging.getLogger("greeummcp")
if not logger.handlers:
    _h = logging.StreamHandler(sys.stderr)
    _h.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s %(name)s - %(message)s'))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)

def check_dependencies():
    """Check if all required dependencies are installed with correct versions."""
    import importlib
    import sys
    
    errors = []
    
    # Check Greeum
    try:
        import greeum
        logger.info(f"Greeum version: {greeum.__version__}")
    except ImportError:
        errors.append("Greeum package not found. Please install with: pip install greeum>=0.6.0")
    
    # Check MCP
    try:
        import mcp
        # MCP package doesn't have __version__ attribute
        logger.info("MCP package: installed")
    except ImportError:
        errors.append("MCP package not found. Please install with: pip install mcp>=1.0.0")
    
    # Check FastAPI (for HTTP transport)
    try:
        import fastapi
        logger.info(f"FastAPI version: {fastapi.__version__}")
    except ImportError:
        logger.warning("FastAPI not found. HTTP transport will not be available.")
    
    # Check Uvicorn (for HTTP transport)
    try:
        import uvicorn
        logger.info(f"Uvicorn version: {uvicorn.__version__}")
    except ImportError:
        logger.warning("Uvicorn not found. HTTP transport will not be available.")
    
    if errors:
        logger.error("Dependency check failed:")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)
    
    logger.info("All required dependencies are installed.")
    return True

class GreeumMCPServer:
    """
    GreeumMCP main server class that wraps Greeum memory engine with Model Context Protocol.
    
    This server provides tools to interact with Greeum's memory capabilities including:
    - Managing long-term memories (BlockManager)
    - Managing short-term memories (STMManager)
    - Cache management (CacheManager)
    - Temporal reasoning (TemporalReasoner)
    - Text processing utilities
    """
    
    def __init__(
        self,
        data_dir: str = "./data",
        server_name: str = "greeum_mcp",
        port: int = 8000,
        transport: str = "stdio",
        greeum_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize GreeumMCP server.
        
        Args:
            data_dir: Directory to store memory data
            server_name: Name of the MCP server
            port: Port for HTTP transport (if used)
            transport: Transport type ('stdio', 'http', 'websocket')
            greeum_config: Additional configuration for Greeum components
        """
        self.data_dir = data_dir
        self.server_name = server_name
        self.port = port
        self.transport = transport
        self.greeum_config = greeum_config or {}
        
        # Initialize MCP server with description
        from greeummcp import __version__
        self.mcp = FastMCP(
            self.server_name, 
            description="Greeum Memory Engine - Memory management for LLMs"
        )
        
        # Initialize Greeum adapter
        self.adapter = GreeumAdapter(
            data_dir=self.data_dir,
            greeum_config=self.greeum_config
        )

        # Lazily initialize Greeum core components (BlockManager 등)
        # Adapter 자체가 내부에서 initialize() 호출하도록 설계돼 있으므로 필요 시 자동 초기화됨.

        # Prepare tools instances
        self._memory_tools = MemoryTools(
            self.adapter.block_manager,
            self.adapter.stm_manager,
            self.adapter.cache_manager,
            self.adapter.temporal_reasoner
        )
        self._utility_tools = UtilityTools(
            self.adapter.block_manager,
            self.adapter.stm_manager,
            self.adapter.cache_manager,
            self.adapter.prompt_wrapper,
            self.data_dir
        )

        # Prepare resources instance
        self._memory_resources = MemoryResources(self.adapter)

        # Register MCP tools
        self._register_tools()
        # Register MCP resources
        self._register_resources()
        
        logger.info(f"GreeumMCPServer initialized (transport={self.transport})")
    
    def _register_tools(self):
        """Register all MCP tools from MemoryTools and UtilityTools dynamically."""

        def _register_from(obj):
            for attr_name in dir(obj):
                if attr_name.startswith("_"):
                    continue
                fn = getattr(obj, attr_name)
                if callable(fn) and asyncio.iscoroutinefunction(fn):
                    # Use existing docstring for tool description if present
                    self.mcp.tool(name=attr_name)(fn)

        # Register tools from both utility classes
        _register_from(self._memory_tools)
        _register_from(self._utility_tools)
    
    def _register_resources(self):
        """Register MCP resources from MemoryResources."""
        # Map resource method names to endpoint names
        resource_mappings = {
            "get_memory_block": "memory_block",
            "get_memory_chain": "memory_chain",
            "get_stm_list": "stm_list",
            "get_server_config": "server_config",
        }
        for method_name, resource_name in resource_mappings.items():
            fn = getattr(self._memory_resources, method_name, None)
            if fn and callable(fn):
                # FastMCP resource decorator expects bytes return
                self.mcp.resource(name=resource_name)(fn)
    
    def run(self):
        """Run the MCP server with the configured transport."""
        if self.transport == "stdio":
            logger.info("Starting server (stdio)")
            self.mcp.run(transport="stdio")
        elif self.transport == "http":
            logger.info(f"Starting server (http) :{self.port}")
            self.mcp.run(transport="http", port=self.port)
        elif self.transport == "websocket":
            logger.info(f"Starting server (websocket) :{self.port}")
            self.mcp.run(transport="websocket", port=self.port)
        else:
            raise ValueError(f"Unsupported transport: {self.transport}")

# CLI entry point
def main():
    """CLI entry point for running the server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="GreeumMCP Server")
    parser.add_argument("--data-dir", default="./data", help="Data directory")
    parser.add_argument("--server-name", default="greeum_mcp", help="Server name")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP/WS transport")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "http", "websocket"], 
                        help="Transport type")
    parser.add_argument("--skip-dependency-check", action="store_true", 
                        help="Skip dependency version check")
    
    args = parser.parse_args()
    
    # Check dependencies unless explicitly skipped
    if not args.skip_dependency_check:
        logger.info("Checking dependencies...")
        check_dependencies()
    
    server = GreeumMCPServer(
        data_dir=args.data_dir,
        server_name=args.server_name,
        port=args.port,
        transport=args.transport
    )
    
    server.run()

if __name__ == "__main__":
    main() 
