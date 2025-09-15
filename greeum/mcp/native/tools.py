#!/usr/bin/env python3
"""
Greeum Native MCP Server - MCP Tools Implementation
임시로 직접 구현하여 v3 기능 지원

핵심 기능:
- v3 슬롯/브랜치 시스템 직접 구현
- 스마트 라우팅 및 메타데이터 지원
- DFS 우선 검색
- MCP 프로토콜 응답 형식 준수
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import hashlib

logger = logging.getLogger("greeum_native_tools")

class GreeumMCPTools:
    """
    Greeum MCP 도구 핸들러

    v3 기능 직접 구현:
    - 슬롯/브랜치 시스템
    - 스마트 라우팅
    - DFS 우선 검색
    - 모든 최신 기능 포함
    """

    def __init__(self, greeum_components: Dict[str, Any]):
        """
        Args:
            greeum_components: DatabaseManager, BlockManager 등이 포함된 딕셔너리
        """
        self.components = greeum_components
        logger.info("Greeum MCP tools initialized with direct v3 implementation")

    def _get_version(self) -> str:
        """중앙화된 버전 참조"""
        try:
            from greeum import __version__
            return __version__
        except ImportError:
            return "unknown"

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        도구 실행 메인 라우터

        Args:
            tool_name: 실행할 도구 이름 (add_memory, search_memory 등)
            arguments: 도구에 전달할 파라미터

        Returns:
            str: MCP 형식의 응답 텍스트
        """
        try:
            if tool_name == "add_memory":
                return await self._handle_add_memory(arguments)
            elif tool_name == "search_memory":
                return await self._handle_search_memory(arguments)
            elif tool_name == "get_memory_stats":
                return await self._handle_get_memory_stats(arguments)
            elif tool_name == "usage_analytics":
                return await self._handle_usage_analytics(arguments)
            elif tool_name == "analyze_causality":
                return await self._handle_analyze_causality(arguments)
            elif tool_name == "infer_causality":
                return await self._handle_infer_causality(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            raise ValueError(f"Tool execution failed: {e}")

    async def _handle_add_memory(self, arguments: Dict[str, Any]) -> str:
        """
        add_memory 도구 처리 - v3 기능 직접 구현

        v3 기능 포함:
        1. 중복 검사
        2. 품질 검증
        3. 슬롯/브랜치 기반 메모리 추가
        4. 스마트 라우팅
        5. 사용 통계 로깅
        """
        try:
            # 파라미터 추출
            content = arguments.get("content")
            if not content:
                raise ValueError("content parameter is required")

            importance = arguments.get("importance", 0.5)
            if not (0.0 <= importance <= 1.0):
                raise ValueError("importance must be between 0.0 and 1.0")

            # 컴포넌트 확인
            if not self._check_components():
                return "ERROR: Greeum components not available. Please check installation."

            # 중복 검사
            duplicate_check = self.components['duplicate_detector'].check_duplicate(content)
            if duplicate_check["is_duplicate"]:
                similarity = duplicate_check["similarity_score"]
                return f"""⚠️  **Potential Duplicate Memory Detected**

**Similarity**: {similarity:.1%} with existing memory
**Similar Memory**: Block #{duplicate_check['similar_block_index']}

Please search existing memories first or provide more specific content."""

            # 품질 검증
            quality_result = self.components['quality_validator'].validate_memory_quality(content, importance)

            # v3 BlockManager를 통한 메모리 추가
            block_result = self._add_memory_via_v3_core(content, importance)

            # 사용 통계 로깅
            self.components['usage_analytics'].log_quality_metrics(
                len(content), quality_result['quality_score'], quality_result['quality_level'],
                importance, importance, False, duplicate_check["similarity_score"],
                len(quality_result.get('suggestions', []))
            )

            # v3.1.0rc7: Check if save actually succeeded
            if block_result is None:
                return f"""❌ **Memory Save Failed!**

**Error**: Block could not be saved to database
**Content**: {content[:50]}...
**Possible Cause**: Database transaction failure or index conflict

Please try again or check database status."""

            # Get block index from result
            block_index = None
            if isinstance(block_result, int):
                block_index = block_result
            elif isinstance(block_result, dict):
                block_index = block_result.get('id', block_result.get('block_index'))

            # Verify save if we have an index
            if block_index and block_index != 'unknown':
                verify_block = self.components['db_manager'].get_block(block_index)
                if not verify_block:
                    return f"""⚠️ **Memory Save Uncertain!**

**Reported Index**: #{block_index}
**Status**: Block not found in database after save
**Action Required**: Please verify with search_memory

This may indicate a transaction rollback or database issue."""

            # 성공 응답 - 슬롯 정보 포함
            quality_feedback = f"""
**Quality Score**: {quality_result['quality_score']:.1%} ({quality_result['quality_level']})
**Adjusted Importance**: {importance:.2f} (original: {importance:.2f})"""

            suggestions_text = ""
            if quality_result.get('suggestions'):
                suggestions_text = f"\n\n**Quality Suggestions**:\n" + "\n".join(f"• {s}" for s in quality_result['suggestions'][:2])

            # 슬롯/브랜치 정보 표시
            slot_info = ""
            routing_info = ""

            if isinstance(block_result, dict):
                # 슬롯 정보
                if block_result.get('slot'):
                    slot_info = f"\n**STM Slot**: {block_result['slot']}"
                if block_result.get('branch_root'):
                    slot_info += f"\n**Branch Root**: {block_result['branch_root'][:8]}..."
                if block_result.get('parent_block'):
                    slot_info += f"\n**Parent Block**: #{block_result['parent_block']}"

                # 스마트 라우팅 정보
                if block_result.get('metadata', {}).get('smart_routing'):
                    sr = block_result['metadata']['smart_routing']
                    routing_info = f"\n\n🎯 **Smart Routing Applied**:"
                    if sr.get('slot_updated'):
                        routing_info += f"\n• Selected Slot: {sr['slot_updated']}"
                    if sr.get('similarity_score') is not None:
                        routing_info += f"\n• Similarity: {sr['similarity_score']:.2%}"
                    if sr.get('placement'):
                        routing_info += f"\n• Placement: {sr['placement']}"
                    if sr.get('reason'):
                        routing_info += f"\n• Reason: {sr['reason']}"

            return f"""✅ **Memory Successfully Added!**

**Block Index**: #{block_index if block_index else 'unknown'}
**Storage**: Branch-based (v3 System){slot_info}
**Duplicate Check**: ✅ Passed{quality_feedback}{suggestions_text}{routing_info}"""

        except Exception as e:
            logger.error(f"add_memory failed: {e}")
            return f"ERROR: Failed to add memory: {str(e)}"

    def _add_memory_via_v3_core(self, content: str, importance: float = 0.5) -> Dict[str, Any]:
        """v3 핵심 경로를 통한 메모리 저장"""
        from greeum.text_utils import process_user_input
        import time

        block_manager = self.components['block_manager']
        stm_manager = self.components.get('stm_manager')

        # 텍스트 처리
        result = process_user_input(content)

        # 스마트 라우팅을 통한 슬롯 선택
        slot, smart_routing_info = self._auto_select_slot(stm_manager, content, result.get('embedding'))

        try:
            # v3 BlockManager.add_block 사용
            block_result = block_manager.add_block(
                context=content,
                keywords=result.get("keywords", []),
                tags=result.get("tags", []),
                embedding=result.get("embedding", []),
                importance=importance,
                metadata={'source': 'mcp', 'smart_routing': smart_routing_info} if smart_routing_info else {'source': 'mcp'},
                slot=slot
            )

            # 결과 정규화
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
            logger.warning(f"Core path failed, using fallback: {e}")
            return self._add_memory_fallback(content, importance, slot)

    def _auto_select_slot(self, stm_manager, content: str, embedding: Optional[List[float]]):
        """스마트 라우팅을 통한 슬롯 자동 선택 - v3.1.0rc7 개선"""
        if not stm_manager:
            return "A", None

        MINIMUM_THRESHOLD = 0.4  # 최소 유사도 임계값

        try:
            # DFS 검색 엔진을 통한 유사도 계산
            dfs_engine = self.components.get('dfs_search')
            if dfs_engine and embedding:
                # 현재 슬롯 헤드들과 유사도 비교
                slot_similarities = {}
                empty_slots = []

                for slot_name in ["A", "B", "C"]:
                    head_block_id = stm_manager.branch_heads.get(slot_name)
                    if head_block_id:
                        try:
                            # 해당 슬롯의 컨텍스트와 유사도 계산
                            slot_blocks = dfs_engine.search_from_block(head_block_id, content, limit=3)
                            if slot_blocks:
                                similarity = slot_blocks[0].get('similarity', 0.0)
                                slot_similarities[slot_name] = similarity
                        except Exception:
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

    def _add_memory_fallback(self, content: str, importance: float, slot: str) -> Dict[str, Any]:
        """Fallback 메모리 저장"""
        from greeum.text_utils import process_user_input
        from datetime import datetime
        import json
        import hashlib

        db_manager = self.components['db_manager']

        # 텍스트 처리
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
            "slot": slot
        }

        # DB 직접 저장
        db_manager.add_block(block_data)
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

            # 컴포넌트 확인
            if not self._check_components():
                return "ERROR: Greeum components not available"

            # 검색 실행
            results = self._search_memory_v3(query, limit, entry, depth)

            # 사용 통계 로깅
            self.components['usage_analytics'].log_event(
                "tool_usage", "search_memory",
                {"query_length": len(query), "results_found": len(results), "limit_requested": limit},
                0, True
            )

            if results:
                search_info = f"🔍 Found {len(results)} memories"
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

            return f"""📊 **Memory System Statistics**

**Total Blocks**: {total_blocks}
**Database**: SQLite (ThreadSafe)
**Version**: {self._get_version()}
**Status**: ✅ Active"""

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
**Status**: ✅ Analytics tracking active

*Detailed analytics implementation in progress*"""

        except Exception as e:
            logger.error(f"usage_analytics failed: {e}")
            return f"ERROR: Failed to get usage analytics: {str(e)}"

    async def _handle_analyze_causality(self, arguments: Dict[str, Any]) -> str:
        """analyze_causality 도구 처리"""
        return "ERROR: Causal analysis not available in current configuration"

    async def _handle_infer_causality(self, arguments: Dict[str, Any]) -> str:
        """infer_causality 도구 처리"""
        return "ERROR: Causal inference not available in current configuration"

    def _check_components(self) -> bool:
        """컴포넌트 가용성 확인"""
        required = ['db_manager', 'duplicate_detector', 'quality_validator', 'usage_analytics']
        for comp in required:
            if comp not in self.components or self.components[comp] is None:
                logger.error(f"Required component missing: {comp}")
                return False
        return True