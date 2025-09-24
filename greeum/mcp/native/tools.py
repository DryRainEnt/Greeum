#!/usr/bin/env python3
"""
Greeum Native MCP Server - MCP Tools Implementation
Direct implementation for v3 features

Core Features:
- Direct v3 slot/branch system implementation
- Smart routing and metadata support
- DFS-first search
- MCP protocol response format compliance
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
import hashlib

try:
    import anyio
except ImportError:  # pragma: no cover - anyio는 서버 초기화에서 이미 강제됨
    anyio = None

logger = logging.getLogger("greeum_native_tools")
# Enable DEBUG logging temporarily with file output
import os
debug_log_path = os.path.join(os.path.expanduser('~'), 'greeum_mcp_debug.log')
try:
    debug_handler = logging.FileHandler(debug_log_path)
    debug_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    debug_handler.setFormatter(formatter)
    logger.addHandler(debug_handler)
    logger.setLevel(logging.DEBUG)
except (OSError, PermissionError):
    # Fallback to console logging if file logging fails
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.setLevel(logging.DEBUG)

class GreeumMCPTools:
    """
    Greeum MCP tools handler

    Direct v3 implementation:
    - Slot/branch system
    - Smart routing
    - DFS-first search
    - All latest features included
    """

    def __init__(self, greeum_components: Dict[str, Any], write_queue_send: Optional[Any] = None):
        """
        Args:
            greeum_components: Dictionary containing DatabaseManager, BlockManager, etc.
        """
        self.components = greeum_components
        self._add_lock = anyio.Lock() if anyio else None
        self._write_queue_send = write_queue_send
        logger.info("Greeum MCP tools initialized with direct v3 implementation")

    def enable_write_queue(self, write_queue_send: Optional[Any]) -> None:
        """Update the write queue send stream used for serialized writes."""

        self._write_queue_send = write_queue_send

    def _get_version(self) -> str:
        """Centralized version reference"""
        try:
            from greeum import __version__
            return __version__
        except ImportError:
            return "unknown"

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Main tool execution router

        Args:
            tool_name: Tool name to execute (add_memory, search_memory, etc.)
            arguments: Parameters to pass to the tool

        Returns:
            str: MCP format response text
        """
        try:
            if tool_name == "add_memory" and self._write_queue_send is not None and anyio is not None:
                reply_send, reply_receive = anyio.create_memory_object_stream(1)
                await self._write_queue_send.send(
                    {
                        "name": tool_name,
                        "arguments": arguments,
                        "reply": reply_send,
                    }
                )
                try:
                    return await reply_receive.receive()
                finally:
                    await reply_receive.aclose()

            return await self.execute_tool_internal(tool_name, arguments)

        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            raise ValueError(f"Tool execution failed: {e}")

    async def execute_tool_internal(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute tool without routing through the write queue (used by worker)."""

        if tool_name == "add_memory":
            return await self._handle_add_memory(arguments)
        elif tool_name == "search_memory":
            return await self._handle_search_memory(arguments)
        elif tool_name == "get_memory_stats":
            return await self._handle_get_memory_stats(arguments)
        elif tool_name == "usage_analytics":
            return await self._handle_usage_analytics(arguments)
        elif tool_name == "warmup_embeddings":
            return await self._handle_warmup_embeddings(arguments)
        elif tool_name == "analyze_causality":
            return await self._handle_analyze_causality(arguments)
        elif tool_name == "infer_causality":
            return await self._handle_infer_causality(arguments)
        elif tool_name == "system_doctor":
            return await self._handle_system_doctor(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _handle_add_memory(self, arguments: Dict[str, Any]) -> str:
        if self._add_lock is not None:
            async with self._add_lock:
                return await self._add_memory_impl(arguments)
        return await self._add_memory_impl(arguments)

    async def _add_memory_impl(self, arguments: Dict[str, Any]) -> str:
        """
        Handle add_memory tool - direct v3 implementation

        v3 features included:
        1. Duplicate checking
        2. Quality validation
        3. Slot/branch based memory addition
        4. Smart routing
        5. Usage statistics logging
        """
        try:
            # Extract parameters
            content = arguments.get("content")
            if not content:
                raise ValueError("content parameter is required")

            importance = arguments.get("importance", 0.5)
            if not (0.0 <= importance <= 1.0):
                raise ValueError("importance must be between 0.0 and 1.0")

            # Check components
            if not self._check_components():
                return "ERROR: Greeum components not available. Please check installation."

            # DEBUG: DB status check before processing
            try:
                db_manager = self.components['db_manager']
                cursor = db_manager.conn.cursor()
                cursor.execute("BEGIN")
                cursor.execute("SELECT COUNT(*) FROM blocks")
                block_count = cursor.fetchone()[0]
                cursor.execute("ROLLBACK")
                logger.info(f"[DEBUG] DB accessible, current block count: {block_count}")
            except Exception as db_error:
                logger.error(f"[DEBUG] DB access error before processing: {db_error}")
                return f"ERROR: Database access failed: {db_error}"

            # Check for duplicates
            duplicate_check = self.components['duplicate_detector'].check_duplicate(content)
            if duplicate_check["is_duplicate"]:
                similarity = duplicate_check["similarity_score"]

                # Get block index from similar_memories (safe access)
                block_index = 'unknown'
                if duplicate_check.get('similar_memories'):
                    first_similar = duplicate_check['similar_memories'][0]
                    block_index = first_similar.get('block_index', 'unknown')

                return f"""**WARNING: Potential Duplicate Memory Detected**

**Similarity**: {similarity:.1%} with existing memory
**Similar Memory**: Block #{block_index}

Please search existing memories first or provide more specific content."""

            # Validate quality
            quality_result = self.components['quality_validator'].validate_memory_quality(content, importance)

            # Add memory via v3 BlockManager
            block_result = self._add_memory_via_v3_core(content, importance)

            # Log usage statistics
            self.components['usage_analytics'].log_quality_metrics(
                len(content), quality_result['quality_score'], quality_result['quality_level'],
                importance, importance, False, duplicate_check["similarity_score"],
                len(quality_result.get('suggestions', []))
            )

            # v3.1.0rc7: Check if save actually succeeded
            if block_result is None:
                return f"""**ERROR: Memory Save Failed!**

**Error**: Block could not be saved to database
**Content**: {content[:50]}...
**Possible Cause**: Database transaction failure or index conflict

Please try again or check database status."""

            # Get block index from result
            block_index: Optional[Union[int, str]] = None
            if isinstance(block_result, int):
                block_index = block_result
                logger.info(f"[DEBUG] Extracted block_index from int: {block_index}")
            elif isinstance(block_result, dict):
                # v3.1.1rc2.dev7: _add_memory_via_v3_core returns full block dict
                # Try multiple keys for compatibility
                block_index = block_result.get('block_index') or block_result.get('id')
                if block_index is None:
                    # Log available keys for debugging
                    logger.error(f"[DEBUG] No block_index or id in dict. Keys: {list(block_result.keys())}")
                    block_index = 'unknown'
                else:
                    logger.info(f"[DEBUG] Successfully extracted block_index from dict: {block_index}")
            else:
                logger.error(f"[DEBUG] Unexpected block_result type: {type(block_result)}, value: {block_result}")
                block_index = 'unknown'

            # Verify save if we have an index
            if block_index is not None and block_index != 'unknown':
                verify_block = self.components['db_manager'].get_block(block_index)
                if not verify_block:
                    return f"""**WARNING: Memory Save Uncertain!**

**Reported Index**: #{block_index}
**Status**: Block not found in database after save
**Action Required**: Please verify with search_memory

This may indicate a transaction rollback or database issue."""

            # Success response - include slot info
            quality_feedback = f"""
**Quality Score**: {quality_result['quality_score']:.1%} ({quality_result['quality_level']})
**Adjusted Importance**: {importance:.2f} (original: {importance:.2f})"""

            suggestions_text = ""
            if quality_result.get('suggestions'):
                suggestions_text = f"\n\n**Quality Suggestions**:\n" + "\n".join(f"• {s}" for s in quality_result['suggestions'][:2])

            # Display slot/branch info
            slot_info = ""
            routing_info = ""

            if isinstance(block_result, dict):
                # Slot information
                if block_result.get('slot'):
                    slot_info = f"\n**STM Slot**: {block_result['slot']}"
                if block_result.get('branch_root'):
                    slot_info += f"\n**Branch Root**: {block_result['branch_root'][:8]}..."
                if block_result.get('parent_block'):
                    slot_info += f"\n**Parent Block**: #{block_result['parent_block']}"

                # Before node information (parent content)
                if block_result.get('before'):
                    try:
                        # Get before block content by hash
                        before_hash = block_result['before']
                        db_manager = self.components['db_manager']
                        cursor = db_manager.conn.cursor()
                        cursor.execute("SELECT context FROM blocks WHERE hash = ? LIMIT 1", (before_hash,))
                        result = cursor.fetchone()
                        if result and result[0]:
                            before_content = result[0][:50] + "..." if len(result[0]) > 50 else result[0]
                            slot_info += f"\n**Before Node**: {before_content}"
                    except Exception as e:
                        slot_info += f"\n**Before Node**: [Error retrieving: {e}]"

                # Smart routing information
                if block_result.get('metadata', {}).get('smart_routing'):
                    sr = block_result['metadata']['smart_routing']
                    routing_info = f"\n\n**Smart Routing Applied**:"
                    if sr.get('slot_updated'):
                        routing_info += f"\n• Selected Slot: {sr['slot_updated']}"
                    if sr.get('similarity_score') is not None:
                        routing_info += f"\n• Similarity: {sr['similarity_score']:.2%}"
                    if sr.get('placement'):
                        routing_info += f"\n• Placement: {sr['placement']}"
                    if sr.get('reason'):
                        routing_info += f"\n• Reason: {sr['reason']}"

            return f"""**SUCCESS: Memory Successfully Added!**

**Block Index**: #{block_index if block_index is not None else 'unknown'}
**Storage**: Branch-based (v3 System){slot_info}
**Duplicate Check**: Passed{quality_feedback}{suggestions_text}{routing_info}"""

        except Exception as e:
            import traceback
            logger.error(f"[DEBUG] add_memory failed: {e}")
            logger.error(f"[DEBUG] Full traceback: {traceback.format_exc()}")
            return f"ERROR: Failed to add memory: {str(e)}"

    def _add_memory_via_v3_core(self, content: str, importance: float = 0.5) -> Dict[str, Any]:
        """Save memory through v3 core path"""
        from greeum.text_utils import process_user_input
        import time

        block_manager = self.components['block_manager']
        stm_manager = self.components.get('stm_manager')

        # Process text
        result = process_user_input(content)

        # Select slot via smart routing
        slot, smart_routing_info = self._auto_select_slot(stm_manager, content, result.get('embedding'))

        # v3.1.1rc2.dev9: Add retry logic for DB lock issues
        MAX_RETRIES = 3
        RETRY_DELAY = 0.5  # Start with 500ms

        for attempt in range(MAX_RETRIES):
            try:
                # DEBUG: Before add_block call
                if attempt > 0:
                    logger.info(f"[DEBUG] Retry attempt {attempt + 1}/{MAX_RETRIES} for add_block")
                else:
                    logger.info(f"[DEBUG] Starting add_block - Content: {content[:50]}..., Slot: {slot}")
                    logger.info(f"[DEBUG] Keywords: {result.get('keywords', [])}, Tags: {result.get('tags', [])}")

                # Use v3 BlockManager.add_block
                block_result = block_manager.add_block(
                    context=content,
                    keywords=result.get("keywords", []),
                    tags=result.get("tags", []),
                    embedding=result.get("embedding", []),
                    importance=importance,
                    metadata={'source': 'mcp', 'smart_routing': smart_routing_info} if smart_routing_info else {'source': 'mcp'},
                    slot=slot
                )

                # If successful, break out of retry loop
                if block_result is not None:
                    break

            except Exception as retry_error:
                logger.warning(f"add_block attempt {attempt + 1} failed: {retry_error}")
                if attempt < MAX_RETRIES - 1:
                    # Exponential backoff
                    import time
                    time.sleep(RETRY_DELAY * (2 ** attempt))
                else:
                    # Final attempt failed, will go to fallback
                    logger.error(f"All {MAX_RETRIES} attempts failed, using fallback")
                    raise retry_error

        # Check if all retries failed with None result
        if block_result is None:
            logger.error("All add_block attempts returned None, using fallback")
            return self._add_memory_fallback(content, importance, slot, smart_routing_info)

        # DEBUG: After add_block call
        logger.info(f"[DEBUG] add_block returned: {type(block_result)} = {block_result}")

        # Normalize result
        try:
            if isinstance(block_result, int):
                return {
                    'id': block_result,
                    'block_index': block_result,
                    'slot': slot,
                    'metadata': {'smart_routing': smart_routing_info} if smart_routing_info else {}
                }
            elif isinstance(block_result, dict):
                block_result['slot'] = slot
                if smart_routing_info:
                    if 'metadata' not in block_result:
                        block_result['metadata'] = {}
                    block_result['metadata']['smart_routing'] = smart_routing_info
                return block_result
            else:
                return {'id': 'unknown', 'slot': slot}
        except Exception as e:
            logger.warning(f"Core path normalization failed, using fallback: {e}")
            return self._add_memory_fallback(content, importance, slot, smart_routing_info)

    def _auto_select_slot(self, stm_manager, content: str, embedding: Optional[List[float]]):
        """Auto-select slot via smart routing - v3.1.0rc7 improvement"""
        if not stm_manager:
            return "A", None

        MINIMUM_THRESHOLD = 0.4  # Minimum similarity threshold

        try:
            # Calculate similarity via DFS search engine
            dfs_engine = self.components.get('dfs_search')
            if dfs_engine and embedding:
                # 현재 슬롯 헤드들과 유사도 비교
                slot_similarities = {}
                empty_slots = []

                for slot_name in ["A", "B", "C"]:
                    head_block_id = stm_manager.branch_heads.get(slot_name)
                    if head_block_id:
                        try:
                            # 해당 슬롯의 헤드 블록과 직접 유사도 계산
                            # Get the head block's embedding
                            cursor = self.components['db_manager'].conn.cursor()
                            cursor.execute("""
                                SELECT e.embedding, e.embedding_dim
                                FROM blocks b
                                JOIN block_embeddings e ON b.block_index = e.block_index
                                WHERE b.hash = ?
                            """, (head_block_id,))
                            result = cursor.fetchone()

                            if result and embedding:
                                # Calculate cosine similarity
                                import numpy as np
                                head_embedding = np.frombuffer(result[0], dtype=np.float32)
                                query_embedding = np.array(embedding, dtype=np.float32)

                                # IMPORTANT: Only use first 384 dimensions (actual model output)
                                # The rest is zero-padding for compatibility
                                ACTUAL_DIM = 384  # paraphrase-multilingual-MiniLM-L12-v2 dimension

                                # Use only the meaningful part (first 384 dimensions)
                                head_embedding = head_embedding[:ACTUAL_DIM]
                                query_embedding = query_embedding[:ACTUAL_DIM]

                                # Normalize vectors
                                head_norm_val = np.linalg.norm(head_embedding)
                                query_norm_val = np.linalg.norm(query_embedding)

                                if head_norm_val > 0 and query_norm_val > 0:
                                    head_norm = head_embedding / head_norm_val
                                    query_norm = query_embedding / query_norm_val

                                    # Calculate cosine similarity
                                    similarity = float(np.dot(head_norm, query_norm))
                                    slot_similarities[slot_name] = similarity
                                else:
                                    slot_similarities[slot_name] = 0.0
                            else:
                                slot_similarities[slot_name] = 0.0
                        except Exception as e:
                            logger.debug(f"Error calculating similarity for slot {slot_name}: {e}")
                            slot_similarities[slot_name] = 0.0
                    else:
                        empty_slots.append(slot_name)

                # 최고 유사도 슬롯 찾기
                if slot_similarities:
                    best_slot = max(slot_similarities, key=slot_similarities.get)
                    best_similarity = slot_similarities[best_slot]

                    # 최소 임계값 체크
                    if best_similarity >= MINIMUM_THRESHOLD:
                        # 임계값 이상이면 해당 슬롯 사용
                        if best_similarity > 0.7:
                            placement_type = 'existing_branch'
                        else:
                            placement_type = 'divergence'

                        smart_routing_info = {
                            'enabled': True,
                            'slot_updated': best_slot,
                            'similarity_score': best_similarity,
                            'placement': placement_type
                        }
                        return best_slot, smart_routing_info

                    # 임계값 미달시 - 새 슬롯 또는 글로벌 재할당
                    if empty_slots:
                        # 빈 슬롯이 있으면 새 맥락으로 할당
                        new_slot = empty_slots[0]
                        smart_routing_info = {
                            'enabled': True,
                            'slot_updated': new_slot,
                            'similarity_score': 0.0,
                            'placement': 'new_context',
                            'reason': f'Below threshold ({best_similarity:.2f} < {MINIMUM_THRESHOLD})'
                        }
                        return new_slot, smart_routing_info
                    else:
                        # 모든 슬롯이 사용중이면 가장 연관도 낮은 슬롯을 재할당
                        least_relevant_slot = min(slot_similarities, key=slot_similarities.get)

                        # 글로벌 검색으로 더 나은 위치 찾기
                        smart_routing_info = {
                            'enabled': True,
                            'slot_updated': least_relevant_slot,
                            'similarity_score': slot_similarities[least_relevant_slot],
                            'placement': 'global_reallocation',
                            'reason': f'All below threshold, reallocating least relevant ({least_relevant_slot})'
                        }
                        return least_relevant_slot, smart_routing_info

                # 모든 슬롯이 비어있는 경우
                if empty_slots:
                    return empty_slots[0], {'enabled': True, 'placement': 'initial', 'slot_updated': empty_slots[0]}

        except Exception as e:
            logger.debug(f"Smart routing failed: {e}")

        # Fallback: 첫 번째 빈 슬롯 또는 A
        for slot in ["A", "B", "C"]:
            if not stm_manager.branch_heads.get(slot):
                return slot, {'enabled': False, 'placement': 'fallback_empty'}
        return "A", {'enabled': False, 'placement': 'fallback_default'}

    def _add_memory_fallback(self, content: str, importance: float, slot: str, smart_routing_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fallback 메모리 저장 (v3.1.1rc2.dev9: smart_routing_info 파라미터 추가)"""
        from greeum.text_utils import process_user_input
        from datetime import datetime
        import json
        import hashlib

        db_manager = self.components['db_manager']

        # Process text
        result = process_user_input(content)
        result["importance"] = importance

        timestamp = datetime.now().isoformat()
        result["timestamp"] = timestamp

        # 블록 인덱스 생성
        last_block_info = db_manager.get_last_block_info()
        if last_block_info is None:
            last_block_info = {"block_index": -1}
        block_index = last_block_info.get("block_index", -1) + 1

        # 이전 해시
        prev_hash = ""
        if block_index > 0:
            prev_block = db_manager.get_block(block_index - 1)
            if prev_block:
                prev_hash = prev_block.get("hash", "")

        # 해시 계산
        hash_data = {
            "block_index": block_index,
            "timestamp": timestamp,
            "context": content,
            "prev_hash": prev_hash
        }
        hash_str = json.dumps(hash_data, sort_keys=True)
        hash_value = hashlib.sha256(hash_str.encode()).hexdigest()

        # 최종 블록 데이터
        block_data = {
            "id": block_index,
            "block_index": block_index,
            "timestamp": timestamp,
            "context": content,
            "keywords": result.get("keywords", []),
            "tags": result.get("tags", []),
            "embedding": result.get("embedding", []),
            "importance": result.get("importance", 0.5),
            "hash": hash_value,
            "prev_hash": prev_hash,
            "slot": slot,
            "before": prev_hash,  # Add before node hash for parent retrieval
            "metadata": {
                "smart_routing": smart_routing_info if smart_routing_info else {'enabled': False, 'placement': 'fallback'}
            }
        }

        # DB 직접 저장
        db_manager.add_block(block_data)

        # v3.1.1rc2.dev7: Verify block was saved and return with confirmed index
        verify_cursor = db_manager.conn.cursor()
        verify_cursor.execute("SELECT block_index FROM blocks WHERE block_index = ?", (block_index,))
        if not verify_cursor.fetchone():
            logger.error(f"Block {block_index} not found after save")
            return None

        return block_data

    async def _handle_search_memory(self, arguments: Dict[str, Any]) -> str:
        """search_memory 도구 처리 - v3 검색 직접 구현"""
        try:
            query = arguments.get("query")
            if not query:
                raise ValueError("query parameter is required")

            limit = arguments.get("limit", 5)
            if not (1 <= limit <= 200):
                raise ValueError("limit must be between 1 and 200")

            depth = arguments.get("depth", 0)
            tolerance = arguments.get("tolerance", 0.5)
            entry = arguments.get("entry", "cursor")

            # Check components
            if not self._check_components():
                return "ERROR: Greeum components not available"

            # 검색 실행
            results = self._search_memory_v3(query, limit, entry, depth)

            # Log usage statistics
            self.components['usage_analytics'].log_event(
                "tool_usage", "search_memory",
                {"query_length": len(query), "results_found": len(results), "limit_requested": limit},
                0, True
            )

            if results:
                search_info = f"Found {len(results)} memories"
                if depth > 0:
                    search_info += f" (depth {depth}, tolerance {tolerance:.1f})"
                search_info += ":\n"

                for i, memory in enumerate(results, 1):
                    timestamp = memory.get('timestamp', 'Unknown')
                    content = memory.get('context', '')[:100] + ('...' if len(memory.get('context', '')) > 100 else '')
                    search_info += f"{i}. [{timestamp}] {content}\n"

                return search_info
            else:
                return f"No memories found for query: '{query}'"

        except Exception as e:
            logger.error(f"search_memory failed: {e}")
            return f"ERROR: Search failed: {str(e)}"

    def _search_memory_v3(self, query: str, limit: int, entry: str, depth: int) -> List[Dict[str, Any]]:
        """v3 검색 엔진 사용 - BlockManager.search_with_slots() 우선"""
        try:
            # BlockManager의 DFS 검색 우선 사용
            block_manager = self.components.get('block_manager')
            if block_manager:
                result = block_manager.search_with_slots(
                    query=query,
                    limit=limit,
                    use_slots=True,
                    entry=entry,
                    depth=depth,
                    fallback=True  # MCP에서는 항상 글로벌 폴백 활성화
                )
                # search_with_slots는 dict 반환 {'items': [...], 'meta': {...}}
                if isinstance(result, dict):
                    return result.get('items', [])
                return result

            # SearchEngine fallback
            search_engine = self.components.get('search_engine')
            if search_engine:
                result = search_engine.search(query, top_k=limit)
                if isinstance(result, dict):
                    return result.get('blocks', [])
                return result

            # DB 직접 검색
            return self._search_memory_fallback(query, limit)
        except Exception as e:
            logger.warning(f"v3 search failed, using fallback: {e}")
            return self._search_memory_fallback(query, limit)

    def _search_memory_fallback(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback 검색"""
        db_manager = self.components['db_manager']
        blocks = db_manager.get_blocks(limit=limit)

        # 간단한 키워드 매칭
        results = []
        for block in blocks:
            if query.lower() in block.get('context', '').lower():
                results.append(block)
                if len(results) >= limit:
                    break

        return results

    async def _handle_get_memory_stats(self, arguments: Dict[str, Any]) -> str:
        """get_memory_stats 도구 처리"""
        try:
            if not self._check_components():
                return "ERROR: Greeum components not available"

            db_manager = self.components['db_manager']
            last_block_info = db_manager.get_last_block_info()
            total_blocks = last_block_info.get('block_index', 0) + 1 if last_block_info else 0

            return f"""**Memory System Statistics**

**Total Blocks**: {total_blocks}
**Database**: SQLite (ThreadSafe)
**Version**: {self._get_version()}
**Status**: Active"""

        except Exception as e:
            logger.error(f"get_memory_stats failed: {e}")
            return f"ERROR: Failed to get memory stats: {str(e)}"

    async def _handle_usage_analytics(self, arguments: Dict[str, Any]) -> str:
        """usage_analytics 도구 처리"""
        try:
            days = arguments.get("days", 7)
            report_type = arguments.get("report_type", "usage")

            if not self._check_components():
                return "ERROR: Greeum components not available"

            usage_analytics = self.components.get('usage_analytics')
            if not usage_analytics:
                return "ERROR: Usage analytics not available"

            # 기본 분석 리포트
            return f"""📈 **Usage Analytics ({days} days)**

**Report Type**: {report_type}
**Period**: Last {days} days
**Status**: Analytics tracking active

*Detailed analytics implementation in progress*"""

        except Exception as e:
            logger.error(f"usage_analytics failed: {e}")
            return f"ERROR: Failed to get usage analytics: {str(e)}"

    async def _handle_warmup_embeddings(self, arguments: Dict[str, Any]) -> str:
        """Pre-load the SentenceTransformer model for faster first use."""

        model_name = arguments.get("model")
        try:
            from greeum.embedding_models import init_sentence_transformer

            init_sentence_transformer(model_name=model_name, set_as_default=True)
            chosen = model_name or os.environ.get(
                "GREEUM_ST_MODEL",
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            )
            return f"✅ Warm-up complete for {chosen}"
        except Exception as exc:
            logger.warning(f"Warm-up failed: {exc}")
            return f"WARNING: Warm-up failed: {exc}"

    async def _handle_analyze_causality(self, arguments: Dict[str, Any]) -> str:
        """analyze_causality 도구 처리"""
        return "ERROR: Causal analysis not available in current configuration"

    async def _handle_infer_causality(self, arguments: Dict[str, Any]) -> str:
        """infer_causality 도구 처리"""
        return "ERROR: Causal inference not available in current configuration"

    async def _handle_system_doctor(self, arguments: Dict[str, Any]) -> str:
        """
        system_doctor 도구 처리 - 시스템 진단 및 자동 복구

        Arguments:
            check_only: bool - 진단만 수행 (기본: False)
            auto_fix: bool - 자동 복구 실행 (기본: True)
            include_backup: bool - 백업 생성 (기본: True)

        Returns:
            진단 보고서 및 복구 결과
        """
        try:
            # Import doctor module
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).parent.parent.parent))
            from greeum.cli.doctor import GreeumDoctor

            # Extract parameters
            check_only = arguments.get("check_only", False)
            auto_fix = arguments.get("auto_fix", not check_only)
            include_backup = arguments.get("include_backup", True)

            # Doctor 인스턴스 생성
            doctor = GreeumDoctor()

            # 백업 생성 (필요시)
            backup_path = None
            if auto_fix and include_backup:
                try:
                    backup_path = doctor.backup_database()
                except Exception as e:
                    logger.warning(f"Backup failed: {e}")

            # 시스템 진단
            health = doctor.check_health()

            # 보고서 생성
            report = []
            report.append("**Greeum System Diagnostics**\n")

            # 종합 점수
            score = health['total_score']
            if score >= 90:
                status = "🟢 Healthy"
            elif score >= 70:
                status = "🟡 Warning"
            elif score >= 50:
                status = "🟠 Critical"
            else:
                status = "🔴 Emergency"

            report.append(f"**Overall Status**: {status} (Score: {score:.0f}/100)\n")

            # 각 카테고리별 상태
            for category, data in health.items():
                if category == 'total_score':
                    continue

                report.append(f"\n**{category.upper()}**")
                report.append(f"Score: {data['score']}/100")

                if data.get('stats'):
                    for key, value in data['stats'].items():
                        report.append(f"• {key}: {value}")

                if data.get('issues'):
                    report.append("Issues:")
                    for issue in data['issues']:
                        report.append(f"  WARNING: {issue}")

            # 복구 수행 (필요시)
            if auto_fix and not check_only and doctor.issues:
                report.append("\n🔧 **Auto-Repair Results**\n")

                fixes = doctor.fix_issues(force=False)
                if fixes:
                    report.append(f"Successfully fixed {len(fixes)} issues:")
                    for fix in fixes:
                        report.append(f"  • {fix}")

                    # 재진단
                    health_after = doctor.check_health()
                    report.append(f"\n**Final Score**: {health_after['total_score']:.0f}/100")
                else:
                    report.append("No issues could be automatically fixed.")

            # 권장사항
            if doctor.issues and check_only:
                report.append("\n📌 **Recommendations**:")
                report.append("Run with `auto_fix: true` to fix issues automatically")

            # 백업 정보
            if backup_path:
                report.append(f"\n**Backup**: {backup_path}")

            return "\n".join(report)

        except Exception as e:
            logger.error(f"system_doctor failed: {e}")
            return f"**ERROR: System Doctor Failed**\n\nFailed to run diagnostics: {str(e)}\n\nPlease check system installation."

    def _check_components(self) -> bool:
        """컴포넌트 가용성 확인"""
        required = ['db_manager', 'duplicate_detector', 'quality_validator', 'usage_analytics']
        for comp in required:
            if comp not in self.components or self.components[comp] is None:
                logger.error(f"Required component missing: {comp}")
                return False
        return True
