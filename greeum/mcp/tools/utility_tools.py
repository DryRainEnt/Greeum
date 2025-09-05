"""
Utility tools for GreeumMCP.

This module contains standalone utility tool functions that can be registered with the MCP server.
"""
from typing import Dict, List, Any, Optional
import asyncio
import os
import time

class UtilityTools:
    """Utility tools for GreeumMCP."""
    
    def __init__(self, block_manager, stm_manager, cache_manager, prompt_wrapper, data_dir):
        """
        Initialize UtilityTools with required Greeum components.
        
        Args:
            block_manager: BlockManager instance
            stm_manager: STMManager instance
            cache_manager: CacheManager instance
            prompt_wrapper: PromptWrapper instance
            data_dir: Data directory
        """
        self.block_manager = block_manager
        self.stm_manager = stm_manager
        self.cache_manager = cache_manager
        self.prompt_wrapper = prompt_wrapper
        self.data_dir = data_dir
        self.start_time = time.time()
    
    async def generate_prompt(self, user_input: str, include_stm: bool = True) -> str:
        """
        Generate a prompt that includes relevant memories.
        
        Args:
            user_input: The user input to construct a prompt for
            include_stm: Whether to include short-term memories
        
        Returns:
            Complete prompt with memory context
        """
        prompt = self.prompt_wrapper.compose_prompt(
            user_input=user_input,
            include_stm=include_stm,
            max_blocks=3,
            max_stm=5
        )
        
        return prompt
    
    async def extract_keywords(self, text: str, language: str = "auto", max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text.
        
        Args:
            text: The text to extract keywords from
            language: Language of the text ("ko", "en", or "auto")
            max_keywords: Maximum number of keywords to extract
        
        Returns:
            List of extracted keywords
        """
        from greeum.text_utils import extract_keywords as extract_kw
        
        keywords = extract_kw(
            text,
            language=language,
            max_keywords=max_keywords
        )
        
        return keywords
    
    async def extract_tags(self, text: str, language: str = "auto") -> List[str]:
        """
        Extract tags from text.
        
        Args:
            text: The text to extract tags from
            language: Language of the text ("ko", "en", or "auto")
        
        Returns:
            List of extracted tags
        """
        from greeum.text_utils import extract_tags as extract_t
        
        tags = extract_t(
            text,
            language=language
        )
        
        return tags
    
    async def compute_embedding(self, text: str) -> List[float]:
        """
        Compute embedding for text.
        
        Args:
            text: The text to compute embedding for
        
        Returns:
            Embedding vector
        """
        from greeum.text_utils import generate_simple_embedding as compute_emb
        
        embedding = compute_emb(text)
        
        return embedding
    
    async def estimate_importance(self, text: str) -> float:
        """
        Estimate importance of text.
        
        Args:
            text: The text to estimate importance for
        
        Returns:
            Importance score (0.0-1.0)
        """
        from greeum.text_utils import calculate_importance as estimate_imp
        
        importance = estimate_imp(text)
        
        return importance
    
    async def verify_chain(self) -> Dict[str, Any]:
        """
        Verify the integrity of the memory blockchain.
        
        Returns:
            Verification result
        """
        is_valid = self.block_manager.verify_chain()
        
        return {
            "valid": is_valid,
            "message": "Memory chain integrity verified" if is_valid else "Memory chain corrupted"
        }
    
    async def server_status(self) -> Dict[str, Any]:
        """
        Get the server status.
        
        Returns:
            Server status information
        """
        # Get block chain stats
        total_blocks = len(self.block_manager.blocks) if hasattr(self.block_manager, "blocks") else 0
        
        # Get STM stats
        total_stm = len(self.stm_manager.get_memories(include_expired=True))
        active_stm = len(self.stm_manager.get_memories(include_expired=False))
        
        # Get data directory size
        data_size = 0
        if os.path.exists(self.data_dir):
            for dirpath, _, filenames in os.walk(self.data_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        data_size += os.path.getsize(fp)
        
        # Calculate uptime
        uptime_seconds = time.time() - self.start_time
        uptime_str = self._format_uptime(uptime_seconds)
        
        return {
            "data_directory": self.data_dir,
            "total_memories": total_blocks,
            "total_stm": total_stm,
            "active_stm": active_stm,
            "data_size_bytes": data_size,
            "data_size_mb": round(data_size / (1024 * 1024), 2) if data_size > 0 else 0,
            "uptime_seconds": uptime_seconds,
            "uptime": uptime_str
        }
    
    async def clear_cache(self) -> Dict[str, Any]:
        """
        Clear the memory cache.
        
        Returns:
            Status of the clear operation
        """
        try:
            self.cache_manager.clear_cache()
            return {"success": True, "message": "Cache cleared successfully"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime seconds into a readable string."""
        days, remainder = divmod(int(seconds), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours > 0 or days > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        
        return " ".join(parts) 