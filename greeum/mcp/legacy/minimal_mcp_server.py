#!/usr/bin/env python3
"""
Minimal MCP Server for GreeumMCP debugging
"""
import json
import sys
import asyncio
import logging
from typing import Dict, Any, List

# 로깅 설정
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("minimal_mcp")

class MinimalMCPServer:
    """Minimal MCP server implementation for debugging"""
    
    def __init__(self):
        self.capabilities = {
            "tools": ["add_memory", "search_memory", "get_memory_list"],
            "resources": ["memory_status"]
        }
        self.initialized = False
    
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
        logger.info("Initializing MCP server")
        
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
                    "name": "minimal-greeum-mcp",
                    "version": "1.0.0"
                }
            }
        }
    
    async def handle_tools_list(self, msg_id: int) -> Dict[str, Any]:
        """Handle tools/list request"""
        tools = [
            {
                "name": "add_memory",
                "description": "Add a new memory to Greeum",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Memory content"}
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "search_memory",
                "description": "Search memories in Greeum",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
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
        
        if tool_name == "add_memory":
            content = arguments.get("content", "")
            result = f"Memory added: {content}"
        elif tool_name == "search_memory":
            query = arguments.get("query", "")
            result = f"Search results for: {query} (mock data)"
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
    
    async def handle_resources_list(self, msg_id: int) -> Dict[str, Any]:
        """Handle resources/list request"""
        resources = [
            {
                "uri": "memory://status",
                "name": "Memory Status",
                "description": "Current memory system status",
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
        
        if uri == "memory://status":
            content = json.dumps({
                "status": "healthy",
                "initialized": self.initialized,
                "memory_count": 0
            })
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

async def main():
    """Main server loop"""
    server = MinimalMCPServer()
    logger.info("Minimal MCP Server started")
    
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
                logger.info(f"Received message: {message}")
                
                # Handle message
                response = await server.handle_message(message)
                
                # Send response
                response_str = json.dumps(response)
                print(response_str, flush=True)
                logger.info(f"Sent response: {response_str}")
                
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