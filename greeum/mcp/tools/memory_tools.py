"""
Memory-related tools for GreeumMCP.

This module contains standalone tool functions that can be registered with the MCP server
and interact with Greeum memory components.
"""
from typing import Dict, List, Any, Optional
import asyncio

from ...worker import AsyncWriteQueue
from ...core.insight_judge import InsightJudge, get_insight_judge, StoreResult

import logging
import os

logger = logging.getLogger(__name__)

# Environment variable to control InsightJudge usage
# Set GREEUM_USE_INSIGHT_FILTER=0 to disable LLM-based filtering
_USE_INSIGHT_FILTER_DEFAULT = os.environ.get("GREEUM_USE_INSIGHT_FILTER", "1") == "1"


class MemoryTools:
    """Memory tools for GreeumMCP."""
    
    def __init__(
        self,
        block_manager,
        stm_manager,
        cache_manager,
        temporal_reasoner,
        write_queue: Optional[AsyncWriteQueue] = None,
        insight_judge: Optional[InsightJudge] = None,
        use_insight_filter: bool = _USE_INSIGHT_FILTER_DEFAULT,
    ):
        """
        Initialize MemoryTools with required Greeum components.

        Args:
            block_manager: BlockManager instance
            stm_manager: STMManager instance
            cache_manager: CacheManager instance
            temporal_reasoner: TemporalReasoner instance
            write_queue: Optional async write queue
            insight_judge: Optional InsightJudge for LLM-based filtering
            use_insight_filter: Whether to use LLM-based insight filtering (default: True)
        """
        self.block_manager = block_manager
        self.stm_manager = stm_manager
        self.cache_manager = cache_manager
        self.temporal_reasoner = temporal_reasoner
        self.write_queue = write_queue or AsyncWriteQueue(label="mcp")
        self.use_insight_filter = use_insight_filter

        # Initialize InsightJudge with search function
        if insight_judge:
            self.insight_judge = insight_judge
        elif use_insight_filter:
            self.insight_judge = get_insight_judge()
            # Set up search function from block_manager
            if hasattr(block_manager, 'search'):
                self.insight_judge.set_search_func(
                    lambda q, limit: block_manager.search(q, limit=limit)
                )
        else:
            self.insight_judge = None
    
    async def add_memory(
        self,
        content: str,
        importance: float = 0.5,
        project_tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Add a new memory to the long-term storage.

        Uses LLM-based InsightJudge to filter noise and determine if content is worth storing.
        Only stores content that has insight value (bug fixes, solutions, warnings, etc.).
        Pure acknowledgments and casual chat are filtered out.

        IMPORTANT: Always provide project_tags with the current project name to ensure
        proper memory organization and retrieval across different projects.

        Args:
            content: The content of the memory to store
            importance: The importance of the memory (0.0-1.0)
            project_tags: Optional list of project-related tags (e.g., ["Greeum", "v3.1"]).
                         Strongly recommended to include current project name.

        Returns:
            Dict with:
                - stored: bool - Whether content was stored
                - block_id: str - Memory ID if stored
                - reason: str - Why content was/wasn't stored
                - is_insight: bool - Whether content was judged as insight

        Raises:
            RuntimeError: If LLM server is unavailable (no fallback)

        Example:
            result = await add_memory(
                content="Fixed branch selection bug",
                importance=0.7,
                project_tags=["Greeum", "backend"]
            )
            # result = {"stored": True, "block_id": "123", "reason": "Bug fix noted", "is_insight": True}
        """
        from greeum.text_utils import process_user_input
        import os

        # Step 1: Use InsightJudge to determine if content is worth storing
        if self.use_insight_filter and self.insight_judge:
            try:
                judgment = self.insight_judge.judge(content)

                if not judgment.is_insight:
                    logger.info(f"Content filtered by InsightJudge: {judgment.insight_reason}")
                    return {
                        "stored": False,
                        "block_id": None,
                        "reason": judgment.insight_reason or "Content filtered as noise",
                        "is_insight": False,
                    }

                logger.info(f"Content approved by InsightJudge: {judgment.insight_reason}")

            except RuntimeError as e:
                # NO FALLBACK - explicit failure when LLM unavailable
                raise RuntimeError(f"InsightJudge failed: {e}") from e

        # Step 2: Process content for storage
        processed = process_user_input(content)

        # Merge project tags with auto-extracted tags
        all_tags = processed.get("tags", [])
        if project_tags:
            all_tags.extend(project_tags)

        # Auto-detect project from cwd if no tags provided (fallback)
        if not project_tags:
            cwd = os.getcwd()
            project_name = os.path.basename(cwd)
            if project_name and project_name not in ['.', '..', '']:
                all_tags.append(f"auto:{project_name}")

        # Add insight categories as tags if available
        if self.use_insight_filter and self.insight_judge:
            if judgment.categories:
                all_tags.extend([f"insight:{cat}" for cat in judgment.categories])

        # Prepare metadata
        metadata = {
            "project_tags": project_tags or [],
            "auto_detected_project": os.path.basename(os.getcwd())
        }

        # Add judgment metadata if available
        if self.use_insight_filter and self.insight_judge:
            metadata.update({
                "insight_reason": judgment.insight_reason,
                "branch_reason": judgment.branch_reason,
                "categories": judgment.categories,
                "judged_by": "InsightJudge",
            })

        def _write_sync():
            block = self.block_manager.add_block(
                context=processed.get("context", content),
                keywords=processed.get("keywords", []),
                tags=all_tags,
                importance=importance,
                embedding=processed.get("embedding", None),
                metadata=metadata
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

        # Return detailed result
        reason = "Memory stored successfully"
        if self.use_insight_filter and self.insight_judge:
            reason = judgment.insight_reason or reason

        return {
            "stored": True,
            "block_id": str(block.get("block_index", "")),
            "reason": reason,
            "is_insight": True,
        }
    
    async def query_memory(
        self,
        query: str,
        limit: int = 5,
        project_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search memories by query text with optional project filtering.

        Args:
            query: The search query
            limit: Maximum number of results to return
            project_filter: Optional list of project tags to filter by.
                          If provided, only memories with these project tags will be returned.
                          Use ["Greeum"] to get only Greeum project memories.

        Returns:
            List of matching memory blocks with relevance scores

        Example:
            # Search across all projects
            await query_memory("branch selection bug", limit=10)

            # Search only in Greeum project
            await query_memory("branch selection", limit=5, project_filter=["Greeum"])
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
            top_k=limit * 3  # Get more candidates for filtering
        )

        # Apply project filter if specified
        if project_filter:
            filtered_results = []
            for block in results:
                tags = block.get("tags", [])
                metadata = block.get("metadata", {})
                project_tags = metadata.get("project_tags", [])

                # Check if any project tag matches
                all_tags = tags + project_tags
                if any(tag in all_tags for tag in project_filter):
                    filtered_results.append(block)
                    if len(filtered_results) >= limit:
                        break
            results = filtered_results
        else:
            results = results[:limit]

        # Format results
        formatted_results = []
        for block in results:
            formatted_results.append({
                "id": block.get("id", ""),
                "content": block.get("context", ""),
                "timestamp": block.get("timestamp", ""),
                "keywords": block.get("keywords", []),
                "tags": block.get("tags", []),
                "importance": block.get("importance", 0.5),
                "project_tags": block.get("metadata", {}).get("project_tags", [])
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
