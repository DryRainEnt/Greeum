"""
Memory resources for GreeumMCP.

This module implements MCP resources for accessing Greeum memory structures.
"""
from typing import Dict, List, Any, Optional
import json
import os

class MemoryResources:
    """Memory resources implementation for GreeumMCP."""
    
    def __init__(self, greeum_adapter):
        """
        Initialize memory resources.
        
        Args:
            greeum_adapter: GreeumAdapter instance
        """
        self.adapter = greeum_adapter
    
    def get_memory_block(self, memory_id: str) -> bytes:
        """
        Get a memory block as a resource.
        
        Args:
            memory_id: ID of the memory block to retrieve
        
        Returns:
            JSON-encoded memory block
        """
        memory = self.adapter.block_manager.get_memory(memory_id)
        if not memory:
            return json.dumps({"error": "Memory not found"}).encode('utf-8')
        
        formatted_memory = self.adapter.convert_memory_to_dict(memory)
        return json.dumps(formatted_memory, ensure_ascii=False).encode('utf-8')
    
    def get_memory_chain(self, limit: int = 100) -> bytes:
        """
        Get the memory blockchain as a resource.
        
        Args:
            limit: Maximum number of blocks to return
        
        Returns:
            JSON-encoded memory blockchain
        """
        blocks = self.adapter.block_manager.blocks[-limit:] if hasattr(self.adapter.block_manager, "blocks") else []
        
        formatted_blocks = self.adapter.convert_memory_list(blocks)
        chain_info = {
            "blocks": formatted_blocks,
            "count": len(formatted_blocks),
            "last_block_id": formatted_blocks[-1]["id"] if formatted_blocks else None
        }
        
        return json.dumps(chain_info, ensure_ascii=False).encode('utf-8')
    
    def get_stm_list(self, include_expired: bool = False, limit: int = 200) -> bytes:
        """
        Get the short-term memory list as a resource.
        
        Args:
            include_expired: Whether to include expired memories
            limit: Maximum number of memories to return
        
        Returns:
            JSON-encoded STM list
        """
        memories = self.adapter.stm_manager.get_memories(
            include_expired=include_expired,
            limit=limit
        )
        
        stm_info = {
            "memories": memories,
            "count": len(memories)
        }
        
        return json.dumps(stm_info, ensure_ascii=False).encode('utf-8')
    
    def get_server_config(self) -> bytes:
        """
        Get server configuration as a resource.
        
        Returns:
            JSON-encoded server configuration
        """
        import time
        import os
        from ..__init__ import __version__
        
        # Get data directory size
        data_size = 0
        if os.path.exists(self.adapter.data_dir):
            for dirpath, _, filenames in os.walk(self.adapter.data_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        data_size += os.path.getsize(fp)
        
        config_info = {
            "version": __version__,
            "settings": {
                "data_directory": self.adapter.data_dir,
                "ttl_short": self.adapter.config.get("ttl_short", 3600),
                "ttl_medium": self.adapter.config.get("ttl_medium", 86400),
                "ttl_long": self.adapter.config.get("ttl_long", 604800),
                "cache_capacity": self.adapter.config.get("cache_capacity", 10),
                "default_language": self.adapter.config.get("default_language", "auto")
            },
            "storage": {
                "total_memories": len(self.adapter.block_manager.blocks) if hasattr(self.adapter.block_manager, "blocks") else 0,
                "data_size_bytes": data_size,
                "data_size_mb": round(data_size / (1024 * 1024), 2) if data_size > 0 else 0
            }
        }
        
        return json.dumps(config_info, ensure_ascii=False).encode('utf-8') 