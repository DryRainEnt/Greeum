"""
Memory-related tools for GreeumMCP.

This module contains standalone tool functions that can be registered with the MCP server
and interact with Greeum memory components.
"""
from typing import Dict, List, Any, Optional
import asyncio

from ...worker import AsyncWriteQueue

class MemoryTools:
    """Memory tools for GreeumMCP."""
    
    def __init__(self, block_manager, stm_manager, cache_manager, temporal_reasoner, write_queue: Optional[AsyncWriteQueue] = None):
        """
        Initialize MemoryTools with required Greeum components.
        
        Args:
            block_manager: BlockManager instance
            stm_manager: STMManager instance
            cache_manager: CacheManager instance
            temporal_reasoner: TemporalReasoner instance
        """
        self.block_manager = block_manager
        self.stm_manager = stm_manager
        self.cache_manager = cache_manager
        self.temporal_reasoner = temporal_reasoner
        self.write_queue = write_queue or AsyncWriteQueue(label="mcp")
    
    async def add_memory(self, content: str, importance: float = 0.5) -> str:
        """
        Add a new memory to the long-term storage.
        
        Args:
            content: The content of the memory to store
            importance: The importance of the memory (0.0-1.0)
        
        Returns:
            Memory ID of the created memory
        """
        from greeum.text_utils import process_user_input
        
        processed = process_user_input(content)

        def _write_sync():
            block = self.block_manager.add_block(
                context=processed.get("context", content),
                keywords=processed.get("keywords", []),
                tags=processed.get("tags", []),
                importance=importance,
                embedding=processed.get("embedding", None),
            )

            if not block:
                raise RuntimeError("Failed to add memory block")

            self.stm_manager.add_memory({
                "content": content,
                "metadata": {
                    "keywords": processed.get("keywords", []),
                    "importance": importance,
                },
            })
            return block

        block = await self.write_queue.run(_write_sync)

        # Return the block index as the memory ID
        return str(block.get("block_index", ""))
    
    async def query_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search memories by query text.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
        
        Returns:
            List of matching memory blocks
        """
        from greeum.text_utils import process_user_input, generate_simple_embedding
        
        processed = process_user_input(query)
        query_embedding = processed.get("embedding", generate_simple_embedding(query))
        query_keywords = processed.get("keywords", [])
        
        # Update cache and get relevant blocks
        results = self.cache_manager.update_cache(
            user_input=query,
            query_embedding=query_embedding,
            extracted_keywords=query_keywords,
            top_k=limit
        )
        
        # Format results
        formatted_results = []
        for block in results:
            formatted_results.append({
                "id": block.get("id", ""),
                "content": block.get("context", ""),
                "timestamp": block.get("timestamp", ""),
                "keywords": block.get("keywords", []),
                "importance": block.get("importance", 0.5)
            })
        
        return formatted_results
    
    async def retrieve_memory(self, memory_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific memory by ID.
        
        Args:
            memory_id: The ID of the memory to retrieve
        
        Returns:
            Memory block data
        """
        try:
            block_index = int(memory_id)
            memory = self.block_manager.get_block_by_index(block_index)
            if not memory:
                return {"error": "Memory not found"}
            
            return {
                "id": memory_id,
                "content": memory.get("context", ""),
                "timestamp": memory.get("timestamp", ""),
                "keywords": memory.get("keywords", []),
                "importance": memory.get("importance", 0.5)
            }
        except ValueError:
            return {"error": "Invalid memory ID format"}
    
    async def update_memory(self, memory_id: str, content: str) -> Dict[str, Any]:
        """
        Update an existing memory.
        
        Note: BlockManager uses blockchain-like storage, so memories cannot be updated.
        This method will add a new memory with the updated content instead.
        
        Args:
            memory_id: The ID of the memory to update (for reference)
            content: The new content for the memory
        
        Returns:
            Status of the update operation
        """
        # Since blockchain doesn't support updates, we add a new memory
        # that references the old one
        new_memory_id = await self.add_memory(
            content=f"[Update of memory {memory_id}] {content}",
            importance=0.7
        )
        return {
            "success": True, 
            "message": "New memory created as update",
            "new_memory_id": new_memory_id,
            "original_memory_id": memory_id
        }
    
    async def delete_memory(self, memory_id: str) -> Dict[str, Any]:
        """
        Delete a memory by ID.
        
        Note: BlockManager uses blockchain-like storage, so memories cannot be deleted.
        This method will add a deletion marker instead.
        
        Args:
            memory_id: The ID of the memory to delete
        
        Returns:
            Status of the delete operation
        """
        # Since blockchain doesn't support deletion, we add a deletion marker
        new_memory_id = await self.add_memory(
            content=f"[DELETED: memory {memory_id}]",
            importance=0.1
        )
        return {
            "success": True,
            "message": "Deletion marker created",
            "deletion_marker_id": new_memory_id,
            "deleted_memory_id": memory_id
        }
    
    async def search_time(self, time_query: str, language: str = "auto") -> List[Dict[str, Any]]:
        """
        Search memories based on time references.
        
        Args:
            time_query: Query containing time references (e.g., "yesterday", "3 days ago")
            language: Language of the query ("ko", "en", or "auto")
        
        Returns:
            List of memories matching the time reference
        """
        results = self.temporal_reasoner.search_by_time_reference(
            time_query,
            margin_hours=12
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result.get("id", ""),
                "content": result.get("context", ""),
                "timestamp": result.get("timestamp", ""),
                "time_relevance": result.get("time_relevance", 0.0),
                "keywords": result.get("keywords", [])
            })
        
        return formatted_results
    
    async def get_stm_memories(self, limit: int = 10, include_expired: bool = False) -> List[Dict[str, Any]]:
        """
        Get short-term memories.
        
        Args:
            limit: Maximum number of memories to return
            include_expired: Whether to include expired memories
        
        Returns:
            List of short-term memories
        """
        # Clean expired memories if not including them
        if not include_expired:
            self.stm_manager.clean_expired()
        
        memories = self.stm_manager.get_recent_memories(count=limit)
        
        # Format results
        formatted_results = []
        for memory in memories:
            formatted_results.append({
                "id": memory.get("id", ""),
                "content": memory.get("content", ""),
                "timestamp": memory.get("timestamp", ""),
                "ttl": memory.get("ttl", 0),
                "expired": memory.get("expired", False)
            })
        
        return formatted_results
    
    async def forget_stm(self, memory_id: str) -> Dict[str, Any]:
        """
        Forget a short-term memory.
        
        Args:
            memory_id: The ID of the short-term memory to forget
        
        Returns:
            Status of the forget operation
        """
        # STMManager doesn't have a forget method, memories expire automatically
        return {
            "success": False, 
            "message": "Short-term memories cannot be manually forgotten. They expire automatically based on TTL."
        }
    
    async def cleanup_expired_memories(self) -> Dict[str, Any]:
        """
        Clean up expired short-term memories.
        
        Returns:
            Number of memories cleaned up
        """
        try:
            count = self.stm_manager.clean_expired()
            return {"success": True, "count": count, "message": f"Cleaned up {count} expired memories"}
        except Exception as e:
            return {"success": False, "message": str(e)} 
