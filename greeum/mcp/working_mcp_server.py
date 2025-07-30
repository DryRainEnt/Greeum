#!/usr/bin/env python3
"""
Working GreeumMCP Server with actual Greeum integration
"""
import json
import sys
import asyncio
import logging
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("working_mcp")

class WorkingGreeumMCPServer:
    """Working MCP server with actual Greeum integration"""
    
    def __init__(self, data_dir: str = "/Users/dryrain/greeum-global"):
        self.data_dir = data_dir
        self.initialized = False
        self.greeum_initialized = False
        
        # Greeum components (lazy initialization)
        self.block_manager = None
        self.stm_manager = None
        self.cache_manager = None
        self.prompt_wrapper = None
        
    def init_greeum(self):
        """Initialize Greeum components"""
        if self.greeum_initialized:
            return
            
        try:
            # Create data directory
            os.makedirs(self.data_dir, exist_ok=True)
            logger.info(f"Data directory: {self.data_dir}")
            
            # Import Greeum components (v2.0 structure)
            from greeum.core.database_manager import DatabaseManager
            from greeum.core.block_manager import BlockManager
            from greeum.core.stm_manager import STMManager
            from greeum.core.cache_manager import CacheManager
            from greeum.core.prompt_wrapper import PromptWrapper
            
            # Initialize database
            db_path = os.path.join(self.data_dir, 'memory.db')
            db_manager = DatabaseManager(connection_string=db_path)
            
            # Initialize components
            self.block_manager = BlockManager(db_manager=db_manager, use_faiss=False)
            self.stm_manager = STMManager(db_manager=db_manager, ttl=3600)
            
            cache_path = os.path.join(self.data_dir, 'context_cache.json')
            self.cache_manager = CacheManager(
                data_path=cache_path,
                block_manager=self.block_manager,
                stm_manager=self.stm_manager
            )
            
            self.prompt_wrapper = PromptWrapper(
                cache_manager=self.cache_manager,
                stm_manager=self.stm_manager
            )
            
            self.greeum_initialized = True
            logger.info("Greeum components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Greeum: {e}")
            raise
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP messages"""
        method = message.get("method", "")
        params = message.get("params", {})
        msg_id = message.get("id")
        
        logger.info(f"Handling method: {method}")
        
        if method == "initialize":
            return await self.handle_initialize(msg_id, params)
        elif method == "tools/list":
            return await self.handle_tools_list(msg_id)
        elif method == "tools/call":
            return await self.handle_tools_call(msg_id, params)
        elif method == "resources/list":
            return await self.handle_resources_list(msg_id)
        elif method == "resources/read":
            return await self.handle_resources_read(msg_id, params)
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    async def handle_initialize(self, msg_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        logger.info("Initializing Working Greeum MCP server")
        
        # Initialize Greeum components
        try:
            self.init_greeum()
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32603,
                    "message": f"Failed to initialize Greeum: {str(e)}"
                }
            }
        
        self.initialized = True
        
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {},
                    "logging": {}
                },
                "serverInfo": {
                    "name": "working-greeum-mcp",
                    "version": "1.0.0"
                }
            }
        }
    
    async def handle_tools_list(self, msg_id: int) -> Dict[str, Any]:
        """Handle tools/list request"""
        tools = [
            {
                "name": "add_memory",
                "description": "Add a new memory to Greeum long-term storage",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Memory content to store"},
                        "importance": {"type": "number", "description": "Importance score (0-1)", "default": 0.5}
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "search_memory",
                "description": "Search memories using keywords or semantic similarity",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Maximum results", "default": 5}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "add_short_term_memory",
                "description": "Add a short-term memory with TTL",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "STM content"},
                        "ttl": {"type": "integer", "description": "Time to live in seconds", "default": 3600}
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "get_enhanced_prompt",
                "description": "Get an enhanced prompt with relevant memories",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "User query"},
                        "max_tokens": {"type": "integer", "description": "Maximum tokens for context", "default": 1000}
                    },
                    "required": ["query"]
                }
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": tools
            }
        }
    
    async def handle_tools_call(self, msg_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        logger.info(f"Calling tool: {tool_name} with args: {arguments}")
        
        if not self.greeum_initialized:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32603,
                    "message": "Greeum not initialized"
                }
            }
        
        try:
            if tool_name == "add_memory":
                result = await self.add_memory(arguments)
            elif tool_name == "search_memory":
                result = await self.search_memory(arguments)
            elif tool_name == "add_short_term_memory":
                result = await self.add_short_term_memory(arguments)
            elif tool_name == "get_enhanced_prompt":
                result = await self.get_enhanced_prompt(arguments)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool execution failed: {str(e)}"
                }
            }
    
    async def add_memory(self, args: Dict[str, Any]) -> str:
        """Add a memory to Greeum"""
        content = args.get("content", "")
        importance = args.get("importance", 0.5)
        
        # Extract keywords from content (simple approach)
        keywords = content.split()[:5]  # First 5 words as keywords
        tags = ["mcp", "user_input"]  # Default tags
        embedding = [0.0] * 10  # Simple dummy embedding
        
        result = self.block_manager.add_block(
            context=content,
            keywords=keywords,
            tags=tags,
            embedding=embedding,
            importance=importance
        )
        
        if result:
            block_index = result.get('block_index', 'unknown')
            return f"Memory added successfully with block index: {block_index}"
        else:
            return "Failed to add memory"
    
    async def search_memory(self, args: Dict[str, Any]) -> str:
        """Search memories in Greeum"""
        query = args.get("query", "")
        limit = args.get("limit", 5)
        
        # Use basic keyword search
        results = self.block_manager.search_by_keywords(
            keywords=query.split(),
            limit=limit
        )
        
        if not results:
            return f"No memories found for query: {query}"
        
        result_text = f"Found {len(results)} memories for '{query}':\\n\\n"
        for i, memory in enumerate(results, 1):
            content = memory.get('context', memory.get('content', ''))[:100]
            timestamp = memory.get('timestamp', 'unknown')
            result_text += f"{i}. [{timestamp}] {content}...\\n"
        
        return result_text
    
    async def add_short_term_memory(self, args: Dict[str, Any]) -> str:
        """Add short-term memory"""
        content = args.get("content", "")
        ttl = args.get("ttl", 3600)
        
        self.stm_manager.add_memory(content, ttl=ttl)
        return f"Short-term memory added (TTL: {ttl}s): {content[:50]}..."
    
    async def get_enhanced_prompt(self, args: Dict[str, Any]) -> str:
        """Get enhanced prompt with relevant memories"""
        query = args.get("query", "")
        max_tokens = args.get("max_tokens", 1000)
        
        enhanced_prompt = self.prompt_wrapper.wrap_prompt(
            user_input=query,
            max_tokens=max_tokens
        )
        
        return f"Enhanced prompt:\\n\\n{enhanced_prompt}"
    
    async def handle_resources_list(self, msg_id: int) -> Dict[str, Any]:
        """Handle resources/list request"""
        resources = [
            {
                "uri": "greeum://status",
                "name": "Greeum Status",
                "description": "Current Greeum memory system status",
                "mimeType": "application/json"
            },
            {
                "uri": "greeum://stats",
                "name": "Memory Statistics",
                "description": "Memory usage statistics",
                "mimeType": "application/json"
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "resources": resources
            }
        }
    
    async def handle_resources_read(self, msg_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request"""
        uri = params.get("uri", "")
        
        try:
            if uri == "greeum://status":
                content = json.dumps({
                    "status": "healthy",
                    "initialized": self.initialized,
                    "greeum_initialized": self.greeum_initialized,
                    "data_dir": self.data_dir
                }, indent=2)
            elif uri == "greeum://stats":
                if self.greeum_initialized:
                    # Get actual stats from Greeum
                    stats = {
                        "long_term_memories": len(self.block_manager.get_all_memories()),
                        "short_term_memories": len(self.stm_manager.get_all_memories()),
                        "cache_size": len(self.cache_manager.cache)
                    }
                else:
                    stats = {"error": "Greeum not initialized"}
                content = json.dumps(stats, indent=2)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown resource: {uri}"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": content
                        }
                    ]
                }
            }
            
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32603,
                    "message": f"Resource read failed: {str(e)}"
                }
            }

async def main():
    """Main server loop"""
    data_dir = os.environ.get("GREEUM_DATA_DIR", "/Users/dryrain/greeum-global")
    server = WorkingGreeumMCPServer(data_dir=data_dir)
    logger.info(f"Working Greeum MCP Server started with data_dir: {data_dir}")
    
    try:
        while True:
            # Read from stdin
            line = sys.stdin.readline()
            if not line:
                break
                
            line = line.strip()
            if not line:
                continue
            
            try:
                # Parse JSON message
                message = json.loads(line)
                logger.info(f"Received message: {message.get('method', 'unknown')}")
                
                # Handle message
                response = await server.handle_message(message)
                
                # Send response
                response_str = json.dumps(response)
                print(response_str, flush=True)
                logger.info(f"Sent response for method: {message.get('method', 'unknown')}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                print(json.dumps(error_response), flush=True)
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)
    
    except KeyboardInterrupt:
        logger.info("Server interrupted")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        logger.info("Server shutting down")

if __name__ == "__main__":
    asyncio.run(main())