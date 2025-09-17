"""
Greeum - Context-Dependent Neural Memory System for LLMs
"""

__version__ = "3.1.1rc2.dev5"
__author__ = "DryRainEnt"

# Core components (commented out until core modules are available)
# from .core.database_manager import DatabaseManager
# from .core.block_manager import BlockManager
# from .core.stm_manager import STMManager
# from .core.cache_manager import CacheManager
# from .core.prompt_wrapper import PromptWrapper

# MCP components
from .mcp.native.server import GreeumNativeMCPServer

__all__ = [
    "GreeumNativeMCPServer"
    # "DatabaseManager",
    # "BlockManager", 
    # "STMManager",
    # "CacheManager",
    # "PromptWrapper",
]
