#!/usr/bin/env python3
"""
Greeum Native MCP Server - JSON-RPC Protocol Processor
Handles JSON-RPC 2.0 and MCP protocol messages

Core Features:
- Full JSON-RPC 2.0 specification compliance
- MCP protocol message routing
- Safe error handling and response generation
- Pydantic-based type safety
"""

import logging
from typing import Any, Dict, Optional, Union
from .types import (
    SessionMessage, JSONRPCRequest, JSONRPCResponse, JSONRPCErrorResponse,
    JSONRPCNotification, JSONRPCError, ErrorCodes,
    InitializeParams, InitializeResult, Capabilities, ServerInfo,
    ToolsListResult, ToolCallParams, ToolResult, TextContent
)

logger = logging.getLogger("greeum_native_protocol")


# Known protocol versions observed across Claude, Codex, Gemini, and OpenAI MCP clients.
# Codex is unhappy unless the server echoes the version string it requested, so we keep a
# small compatibility table and fall back to the latest version if we see an unknown value.
SUPPORTED_PROTOCOL_VERSIONS = {
    "2025-03-26",
    "2024-12-17",
    "2024-08-05",
    "2024-06-17",
    "2024-02-01",
    "1.0",
}
DEFAULT_PROTOCOL_VERSION = "2025-03-26"

class JSONRPCProcessor:
    """
    JSON-RPC 2.0 message processor

    Supported MCP protocol methods:
    - initialize: Server initialization
    - initialized: Initialization complete notification
    - tools/list: List available tools
    - tools/call: Execute tool
    """
    
    def __init__(self, tool_handler):
        self.tool_handler = tool_handler
        self.initialized = False
        
    async def process_message(self, session_message: SessionMessage) -> Optional[SessionMessage]:
        """
        Main JSON-RPC message processing router

        Args:
            session_message: Received session message

        Returns:
            Optional[SessionMessage]: Response message (None for notifications)
        """
        message = session_message.message
        
        # Notification message (no response)
        if isinstance(message, JSONRPCNotification):
            await self._handle_notification(message)
            return None
            
        # Request message (response required)
        if isinstance(message, JSONRPCRequest):
            return await self._handle_request(message)
            
        # Response/error message (client response - typically not processed)
        logger.warning(f"Unexpected message type: {type(message)}")
        return None
    
    async def _handle_notification(self, notification: JSONRPCNotification) -> None:
        """Handle notification messages"""
        method = notification.method
        params = notification.params or {}
        
        if method == "initialized":
            # Client notifies initialization complete
            self.initialized = True
            logger.info("Client initialization completed")
        else:
            logger.warning(f"Unknown notification method: {method}")
    
    async def _handle_request(self, request: JSONRPCRequest) -> SessionMessage:
        """Handle request messages"""
        method = request.method
        params = request.params or {}
        request_id = request.id
        
        try:
            # MCP protocol method routing
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "tools/list":
                result = await self._handle_tools_list(params)
            elif method == "tools/call":
                result = await self._handle_tools_call(params)
            else:
                # Unsupported method
                return self._create_error_response(
                    request_id, 
                    ErrorCodes.METHOD_NOT_FOUND,
                    f"Method not found: {method}"
                )
            
            # Generate success response
            return self._create_success_response(request_id, result)
            
        except ValueError as e:
            # Parameter validation failed
            return self._create_error_response(
                request_id,
                ErrorCodes.INVALID_PARAMS,
                str(e)
            )
        except Exception as e:
            # Internal server error
            logger.error(f"Internal error in {method}: {e}")
            return self._create_error_response(
                request_id,
                ErrorCodes.INTERNAL_ERROR,
                "Internal server error"
            )
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle initialize method

        MCP initialization protocol:
        1. Client sends protocol version and capabilities
        2. Server responds with supported features and server info
        """
        try:
            # Validate parameters
            init_params = InitializeParams.model_validate(params)
            logger.info(
                "Initialize request from %s v%s (protocol %s)",
                init_params.clientInfo.name,
                init_params.clientInfo.version,
                init_params.protocolVersion,
            )

            requested_version = (init_params.protocolVersion or "").strip()
            negotiated_version = DEFAULT_PROTOCOL_VERSION

            if requested_version:
                alias_map = {
                    "1": "1.0",
                    "latest": DEFAULT_PROTOCOL_VERSION,
                }
                if requested_version in SUPPORTED_PROTOCOL_VERSIONS:
                    negotiated_version = requested_version
                elif requested_version.lower() in alias_map:
                    negotiated_version = alias_map[requested_version.lower()]
                elif requested_version.replace(".", "", 1).isdigit():
                    negotiated_version = requested_version
                elif requested_version.startswith("2024-") or requested_version.startswith("2025-"):
                    negotiated_version = requested_version
                else:
                    logger.warning(
                        "Unknown protocol version '%s'; falling back to %s",
                        requested_version,
                        DEFAULT_PROTOCOL_VERSION,
                    )
            else:
                logger.warning(
                    "Empty protocol version received; defaulting to %s",
                    DEFAULT_PROTOCOL_VERSION,
                )

            # Define server capabilities
            server_capabilities = Capabilities(
                tools={
                    "listChanged": False  # Tool list does not change dynamically
                },
                resources={},  # Resources not supported
                prompts={},    # Prompts not supported
                logging={}     # Logging not supported
            )
            
            # Generate initialization result
            result = InitializeResult(
                protocolVersion=negotiated_version,
                capabilities=server_capabilities,
                serverInfo=ServerInfo()
            )
            
            logger.info("Server initialization completed (protocol %s)", negotiated_version)
            return result.model_dump()
            
        except Exception as e:
            logger.error(f"Initialize failed: {e}")
            raise ValueError(f"Invalid initialize parameters: {e}")
    
    async def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tools/list method

        Returns Greeum MCP tool list:
        - add_memory: Add memory
        - search_memory: Search memories
        - get_memory_stats: Memory statistics
        - usage_analytics: Usage analysis
        - system_doctor: System health check
        """
        # Define tool list (OpenAPI schema format)
        tools = [
            {
                "name": "add_memory",
                "description": "Add a new memory to Greeum's long-term storage. Automatically checks for duplicates, validates quality, assigns to appropriate context slot using similarity-based routing, and maintains branch-aware storage for context preservation. Returns the block ID and routing information.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Content to store in memory"
                        },
                        "importance": {
                            "type": "number",
                            "description": "Importance score (0.0-1.0)",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "default": 0.5
                        }
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "search_memory",
                "description": "Search memories using semantic similarity and DFS-based branch traversal. Prioritizes contextually related memories through slot-aware search, falls back to global search when needed. Returns relevance-ranked results with metadata including timestamps, importance scores, and branch relationships.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "minimum": 1,
                            "maximum": 50,
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_memory_stats",
                "description": "Get comprehensive memory system statistics including total blocks, active branches, slot utilization, embedding model distribution, database size, and system health metrics. Useful for monitoring system status and performance.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "usage_analytics",
                "description": "Analyze memory system usage patterns over a specified period. Provides insights on memory creation rate, search patterns, quality metrics, duplicate detection rates, and system performance trends. Supports multiple report types for different analytical perspectives.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Analysis period in days",
                            "minimum": 1,
                            "maximum": 90,
                            "default": 7
                        },
                        "report_type": {
                            "type": "string",
                            "description": "Report type",
                            "enum": ["usage", "quality", "performance", "all"],
                            "default": "usage"
                        }
                    }
                }
            },
            {
                "name": "analyze",
                "description": "Summarize STM slots, branch activity, and recent memory usage for quick situational awareness.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Look-back window for recent activity",
                            "minimum": 1,
                            "maximum": 90,
                            "default": 7
                        }
                    }
                }
            },
            {
                "name": "system_doctor",
                "description": "Perform comprehensive system health check and maintenance. Diagnoses database integrity, embedding consistency, dependency availability, and performance metrics. Can automatically fix issues including orphaned embeddings cleanup, database fragmentation repair, index optimization, and embedding model migration. Creates automatic backups before repairs. Returns detailed health report with scores and recommendations.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "check_only": {
                            "type": "boolean",
                            "description": "Only run diagnostics without fixing",
                            "default": False
                        },
                        "auto_fix": {
                            "type": "boolean",
                            "description": "Automatically fix found issues",
                            "default": True
                        },
                        "include_backup": {
                            "type": "boolean",
                            "description": "Create backup before fixes",
                            "default": True
                        }
                    }
                }
            }
        ]
        
        result = {"tools": tools}
        logger.info(f"Listed {len(tools)} tools")
        return result
    
    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tools/call method

        Tool execution:
        1. Validate parameters
        2. Delegate to tool handler
        3. Wrap result in MCP format
        """
        try:
            # Validate parameters
            tool_call = ToolCallParams.model_validate(params)
            tool_name = tool_call.name
            tool_args = tool_call.arguments or {}
            
            logger.info(f"Calling tool: {tool_name}")
            
            # Execute tool
            result_text = await self.tool_handler.execute_tool(tool_name, tool_args)
            
            # Generate MCP format result
            result = ToolResult(
                content=[TextContent(text=result_text)],
                isError=False
            )
            
            logger.info(f"Tool {tool_name} executed successfully")
            return result.model_dump()
            
        except ValueError as e:
            # Execute tool 실패 - 에러 결과 반환
            error_text = f"Tool execution failed: {e}"
            result = ToolResult(
                content=[TextContent(text=error_text)],
                isError=True
            )
            logger.error(error_text)
            return result.model_dump()
        except Exception as e:
            # Unexpected error
            error_text = f"Unexpected error: {e}"
            result = ToolResult(
                content=[TextContent(text=error_text)],
                isError=True
            )
            logger.error(error_text)
            return result.model_dump()
    
    def _create_success_response(self, request_id: Any, result: Any) -> SessionMessage:
        """Generate success response"""
        response = JSONRPCResponse(id=request_id, result=result)
        return SessionMessage(message=response)
    
    def _create_error_response(self, request_id: Any, code: int, message: str, data: Any = None) -> SessionMessage:
        """Generate error response"""
        error = JSONRPCError(code=code, message=message, data=data)
        response = JSONRPCErrorResponse(id=request_id, error=error)
        return SessionMessage(message=response)
