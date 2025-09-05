"""
Greeum adapter module for connecting Greeum components to MCP server.

This module provides adapter classes to bridge between Greeum memory components
and MCP server components.
"""
from typing import Dict, List, Any, Optional, Union
import os
import time
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class GreeumAdapter:
    """
    Greeum adapter for interfacing with MCP.
    
    This adapter serves as a bridge between Greeum memory engine components
    and the MCP server, handling data conversion and proxy method calls.
    """
    
    def __init__(self, data_dir: str = "./data", greeum_config: Optional[Dict[str, Any]] = None):
        """
        Initialize Greeum adapter.
        
        Args:
            data_dir: Directory to store memory data
            greeum_config: Additional configuration for Greeum components
        """
        # Convert to absolute path to avoid issues across different hosts
        self.data_dir = str(Path(data_dir).absolute())
        self.config = greeum_config or {}
        self._initialized = False
        
        logger.info(f"GreeumAdapter initialized with data_dir: {self.data_dir}")
        
        # Initialize components on first use to avoid import issues
        self._block_manager = None
        self._stm_manager = None
        self._cache_manager = None
        self._prompt_wrapper = None
        self._temporal_reasoner = None
    
    def initialize(self):
        """Initialize Greeum components if not already initialized."""
        if self._initialized:
            return
        
        logger.info("Initializing Greeum components...")
        
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            logger.debug(f"Created/verified data directory: {self.data_dir}")
        except PermissionError as e:
            logger.error(f"Permission denied creating directory: {self.data_dir}")
            raise
        except Exception as e:
            logger.error(f"Failed to create data directory: {e}")
            raise
        
        try:
            from greeum.database_manager import DatabaseManager
            from greeum.block_manager import BlockManager
            from greeum.stm_manager import STMManager
            from greeum.cache_manager import CacheManager
            from greeum.prompt_wrapper import PromptWrapper
            from greeum.temporal_reasoner import TemporalReasoner
        except ImportError as e:
            logger.error(f"Failed to import Greeum components: {e}")
            logger.error("Please ensure Greeum is installed: pip install greeum>=0.6.0")
            raise ImportError(
                f"Greeum package not found or incorrectly installed. "
                f"Please install with: pip install greeum>=0.6.0\n"
                f"Error details: {e}"
            )
        
        # Initialize database manager
        db_path = os.path.join(self.data_dir, 'memory.db')
        self._db_manager = DatabaseManager(connection_string=db_path)
        
        # Initialize core components
        self._block_manager = BlockManager(
            db_manager=self._db_manager,
            use_faiss=self.config.get("use_faiss", True)
        )
        
        # STMManager expects ttl parameter (single value, not multiple)
        ttl = self.config.get("ttl_short", 3600)  # Use short TTL as default
        self._stm_manager = STMManager(
            db_manager=self._db_manager,
            ttl=ttl
        )
        
        # CacheManager initialization
        cache_path = os.path.join(self.data_dir, 'context_cache.json')
        self._cache_manager = CacheManager(
            data_path=cache_path,
            block_manager=self._block_manager,
            stm_manager=self._stm_manager
        )
        
        self._prompt_wrapper = PromptWrapper(
            cache_manager=self._cache_manager,
            stm_manager=self._stm_manager
        )
        
        # Set custom template if provided
        if "prompt_template" in self.config:
            self._prompt_wrapper.set_template(self.config["prompt_template"])
        
        self._temporal_reasoner = TemporalReasoner(
            db_manager=self._db_manager,
            default_language=self.config.get("default_language", "auto")
        )
        
        self._initialized = True
        logger.info("Greeum components initialized successfully")
    
    @property
    def block_manager(self):
        """Get the BlockManager instance, initializing if necessary."""
        if not self._initialized:
            self.initialize()
        return self._block_manager
    
    @property
    def stm_manager(self):
        """Get the STMManager instance, initializing if necessary."""
        if not self._initialized:
            self.initialize()
        return self._stm_manager
    
    @property
    def cache_manager(self):
        """Get the CacheManager instance, initializing if necessary."""
        if not self._initialized:
            self.initialize()
        return self._cache_manager
    
    @property
    def prompt_wrapper(self):
        """Get the PromptWrapper instance, initializing if necessary."""
        if not self._initialized:
            self.initialize()
        return self._prompt_wrapper
    
    @property
    def temporal_reasoner(self):
        """Get the TemporalReasoner instance, initializing if necessary."""
        if not self._initialized:
            self.initialize()
        return self._temporal_reasoner
    
    def convert_memory_to_dict(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Greeum memory block to a standardized dictionary format."""
        if not memory:
            return {}
        
        return {
            "id": memory.get("id", ""),
            "content": memory.get("context", memory.get("content", "")),
            "timestamp": memory.get("timestamp", ""),
            "keywords": memory.get("keywords", []),
            "tags": memory.get("tags", []),
            "importance": memory.get("importance", 0.5),
            "embedding": memory.get("embedding", [])
        }
    
    def convert_memory_list(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert a list of Greeum memory blocks to standardized format."""
        return [self.convert_memory_to_dict(memory) for memory in memories] 