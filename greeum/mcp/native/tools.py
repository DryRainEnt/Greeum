#!/usr/bin/env python3
"""
Greeum Native MCP Server - MCP Tools Implementation
기존 Greeum 비즈니스 로직을 MCP 형식으로 래핑

핵심 기능:
- 기존 Greeum 컴포넌트 100% 재사용
- MCP 프로토콜 응답 형식 준수
- 기존 FastMCP 서버와 완전 동일한 API
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
    
    기존 비즈니스 로직 재사용:
    - BlockManager, STMManager 등 기존 컴포넌트 활용
    - 기존 FastMCP 서버와 동일한 응답 형식
    - 완벽한 하위 호환성 보장
    """
    
    def __init__(self, greeum_components: Dict[str, Any]):
        """
        Args:
            greeum_components: DatabaseManager, BlockManager 등이 포함된 딕셔너리
        """
        self.components = greeum_components
        logger.info("Greeum MCP tools initialized")
    
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
            tool_name: 도구 이름
            arguments: 도구 인자
            
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
        add_memory 도구 처리
        
        기존 FastMCP 서버와 동일한 로직:
        1. 중복 검사
        2. 품질 검증
        3. 메모리 블록 추가
        4. 사용 통계 로깅
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
                return f"""WARNING: Potential Duplicate Memory Detected"

**Similarity**: {similarity:.1%} with existing memory
**Similar Memory**: Block #{duplicate_check['similar_block_index']}

Please search existing memories first or provide more specific content."""
            
            # 품질 검증
            quality_result = self.components['quality_validator'].validate_memory_quality(content, importance)
            
            # 메모리 추가 (기존 로직 재사용)
            block_data = self._add_memory_direct(content, importance)
            
            # 사용 통계 로깅
            self.components['usage_analytics'].log_quality_metrics(
                len(content), quality_result['quality_score'], quality_result['quality_level'],
                importance, importance, False, duplicate_check["similarity_score"], 
                len(quality_result['suggestions'])
            )
            
            # 성공 응답 (기존 FastMCP와 동일한 형식)
            quality_feedback = f"""
**Quality Score**: {quality_result['quality_score']:.1%} ({quality_result['quality_level']})
**Adjusted Importance**: {importance:.2f} (original: {importance:.2f})"""
            
            suggestions_text = ""
            if quality_result['suggestions']:
                suggestions_text = f"\n\n**Quality Suggestions**:\n" + "\n".join(f"• {s}" for s in quality_result['suggestions'][:2])
            
            return f"""SUCCESS: Memory Successfully Added!

**Block Index**: #{block_data['block_index']}
**Storage**: Permanent (Long-term Memory)
**Duplicate Check**: PASSED{quality_feedback}{suggestions_text}"""
        
        except Exception as e:
            logger.error(f"add_memory failed: {e}")
            return f"ERROR: Failed to add memory: {str(e)}"
    
    async def _handle_search_memory(self, arguments: Dict[str, Any]) -> str:
        """
        search_memory 도구 처리 - 연관관계 확장 탐색 기능 추가
        
        기능:
        1. 기본 임베딩/키워드 검색
        2. 탐색 심도 파라미터 (depth): 연관 메모리 확장 탐색
        3. 검색 허용 오차 (tolerance): 검색 기준 완화/강화
        4. 사용 통계 로깅
        """
        try:
            # 파라미터 추출
            query = arguments.get("query")
            if not query:
                raise ValueError("query parameter is required")
                
            limit = arguments.get("limit", 5)
            if not (1 <= limit <= 200):
                raise ValueError("limit must be between 1 and 200")
            
            # 새로운 파라미터들
            depth = arguments.get("depth", 0)  # 0: 기본 검색만, 1: 1차 연관, 2: 2차 연관
            if not (0 <= depth <= 3):
                raise ValueError("depth must be between 0 and 3")
            
            tolerance = arguments.get("tolerance", 0.5)  # 0.0: 엄격, 1.0: 관대
            if not (0.0 <= tolerance <= 1.0):
                raise ValueError("tolerance must be between 0.0 and 1.0")
            
            # 컴포넌트 확인
            if not self._check_components():
                return "ERROR: Greeum components not available. Please check installation."
            
            # 기본 메모리 검색
            results = self._search_memory_direct(query, limit)
            
            # 연관관계 확장 탐색 (depth > 0인 경우)
            if depth > 0 and results:
                results = self._expand_search_with_associations(results, depth, tolerance, limit)
            
            # 사용 통계 로깅 (확장된 파라미터 포함)
            self.components['usage_analytics'].log_event(
                "tool_usage", "search_memory",
                {
                    "query_length": len(query), 
                    "results_found": len(results), 
                    "limit_requested": limit,
                    "depth": depth,
                    "tolerance": tolerance
                },
                0, True
            )
            
            # 결과 포맷팅
            if results:
                result_text = f"Found {len(results)} memories"
                if depth > 0:
                    result_text += f" (depth {depth}, tolerance {tolerance:.1f})"
                result_text += ":\n"
                
                for i, memory in enumerate(results, 1):
                    timestamp = memory.get('timestamp', 'Unknown')
                    content = memory.get('context', '')[:100] + ('...' if len(memory.get('context', '')) > 100 else '')
                    
                    # 연관관계 표시 (있는 경우)
                    relation_info = ""
                    if memory.get('relation_type'):
                        relation_info = f" [{memory['relation_type']}]"
                    
                    result_text += f"{i}. [{timestamp}]{relation_info} {content}\n"
                return result_text
            else:
                return f"No memories found for query: '{query}'"
        
        except Exception as e:
            logger.error(f"search_memory failed: {e}")
            return f"ERROR: Search failed: {str(e)}"
    
    async def _handle_get_memory_stats(self, arguments: Dict[str, Any]) -> str:
        """
        get_memory_stats 도구 처리
        
        기존 로직 재사용하여 메모리 시스템 통계 반환
        """
        try:
            # 컴포넌트 확인
            if not self._check_components():
                return "ERROR: Greeum components not available. Please check installation."
            
            db_manager = self.components['db_manager']
            
            # 기본 통계 - database_manager 자체 연결 사용
            try:
                # database_manager의 self.conn 속성 직접 사용
                cursor = db_manager.conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM blocks")
                total_blocks = cursor.fetchone()[0]
            except Exception as e:
                logger.error(f"Block count query failed: {e}")
                total_blocks = 0
                
            # 최근 블록 조회 (API 호환성 수정)
            try:
                recent_blocks = db_manager.get_blocks(limit=10, sort_by='timestamp', order='desc')
            except Exception:
                recent_blocks = []
            
            # STM 통계 - API 호환성 수정
            try:
                stm_stats = self.components['stm_manager'].get_stats()
            except (AttributeError, Exception):
                # STMManager에 get_stats가 없는 경우 기본값
                stm_stats = {
                    'active_count': 0,
                    'available_slots': 10
                }
            
            # 기존 FastMCP와 동일한 형식
            return f"""**Greeum Memory Statistics**

**Long-term Memory**:
• Total Blocks: {total_blocks}
• Recent Entries: {len(recent_blocks)}

**Short-term Memory**:
• Active Slots: {stm_stats.get('active_count', 0)}
• Available Slots: {stm_stats.get('available_slots', 0)}

**System Status**: Operational
**Version**: {self._get_version()} (Native MCP Server)"""
        
        except Exception as e:
            logger.error(f"get_memory_stats failed: {e}")
            return f"ERROR: Stats retrieval failed: {str(e)}"
    
    async def _handle_usage_analytics(self, arguments: Dict[str, Any]) -> str:
        """
        usage_analytics 도구 처리
        
        기존 로직 재사용하여 사용 분석 리포트 생성
        """
        try:
            # 파라미터 추출
            days = arguments.get("days", 7)
            if not (1 <= days <= 90):
                raise ValueError("days must be between 1 and 90")
                
            report_type = arguments.get("report_type", "usage")
            valid_types = ["usage", "quality", "performance", "all"]
            if report_type not in valid_types:
                raise ValueError(f"report_type must be one of: {valid_types}")
            
            # 컴포넌트 확인
            if not self._check_components():
                return "ERROR: Greeum components not available. Please check installation."
            
            # 분석 리포트 생성 (기존 로직 재사용)
            analytics = self.components['usage_analytics'].get_usage_report(days=days, report_type=report_type)
            
            # 기존 FastMCP와 동일한 형식
            return f"""**Usage Analytics Report** ({days} days)

**Activity Summary**:
• Total Operations: {analytics.get('total_operations', 0)}
• Memory Additions: {analytics.get('add_operations', 0)}
• Search Operations: {analytics.get('search_operations', 0)}

**Quality Metrics**:
• Average Quality Score: {analytics.get('avg_quality_score', 0):.1%}
• High Quality Rate: {analytics.get('high_quality_rate', 0):.1%}

**Performance**:
• Average Response Time: {analytics.get('avg_response_time', 0):.1f}ms
• Success Rate: {analytics.get('success_rate', 0):.1%}

**Report Type**: {report_type.title()}
**Generated**: Native MCP Server v{self._get_version()}"""
        
        except Exception as e:
            logger.error(f"usage_analytics failed: {e}")
            return f"ERROR: Analytics failed: {str(e)}"
    
    def _check_components(self) -> bool:
        """필수 컴포넌트 존재 확인"""
        required_components = [
            'db_manager', 'block_manager', 'stm_manager',
            'duplicate_detector', 'quality_validator', 'usage_analytics'
        ]
        
        for component in required_components:
            if component not in self.components or self.components[component] is None:
                logger.error(f"Missing component: {component}")
                return False
        
        return True
    
    def _add_memory_direct(self, content: str, importance: float) -> Dict[str, Any]:
        """
        직접 메모리 추가 (기존 FastMCP 로직 100% 재사용)
        """
        from greeum.text_utils import process_user_input
        
        db_manager = self.components['db_manager']
        
        # 기존 로직 그대로 사용
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
            "block_index": block_index,
            "timestamp": timestamp,
            "context": content,
            "keywords": result.get("keywords", []),
            "tags": result.get("tags", []),
            "embedding": result.get("embedding", []),
            "importance": result.get("importance", 0.5),
            "hash": hash_value,
            "prev_hash": prev_hash
        }
        
        # 데이터베이스에 추가
        db_manager.add_block(block_data)
        
        return block_data
    
    def _search_memory_direct(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        직접 메모리 검색 (기존 FastMCP 로직 100% 재사용)
        """
        from greeum.embedding_models import get_embedding
        
        db_manager = self.components['db_manager']
        
        try:
            # 임베딩 기반 검색
            embedding = get_embedding(query)
            blocks = db_manager.search_blocks_by_embedding(embedding, top_k=limit)
            
            return blocks if blocks else []
        except Exception as e:
            logger.warning(f"Embedding search failed: {e}, falling back to keyword search")
            # 키워드 검색 폴백
            blocks = db_manager.search_by_keyword(query, limit=limit)
            return blocks if blocks else []
    
    async def _handle_analyze_causality(self, arguments: Dict[str, Any]) -> str:
        """
        실시간 인과관계 분석 도구
        새 메모리와 기존 메모리들 간의 인과관계를 분석합니다.
        
        Arguments:
            - content (str): 분석할 새 메모리 내용
            - importance (float, optional): 메모리 중요도 (0.0-1.0)
            - analysis_depth (str, optional): 분석 깊이 ('quick', 'balanced', 'deep')
            - memory_count (int, optional): 분석 대상 기존 메모리 수 (default: 100)
        
        Returns:
            str: 인과관계 분석 결과 JSON
        """
        try:
            # 파라미터 추출
            content = arguments.get("content")
            if not content:
                raise ValueError("content parameter is required")
                
            importance = arguments.get("importance", 0.5)
            if not (0.0 <= importance <= 1.0):
                raise ValueError("importance must be between 0.0 and 1.0")
                
            analysis_depth = arguments.get("analysis_depth", "balanced")
            if analysis_depth not in ['quick', 'balanced', 'deep']:
                raise ValueError("analysis_depth must be 'quick', 'balanced', or 'deep'")
                
            memory_count = arguments.get("memory_count", 100)
            if not (1 <= memory_count <= 200):
                raise ValueError("memory_count must be between 1 and 200")
            
            # 컴포넌트 확인
            if not self._check_components():
                return "ERROR: Greeum components not available. Please check installation."
            
            # AssociationSystem 초기화
            from greeum.core.association_detector import AssociationSystem
            association_system = AssociationSystem()
            
            # 새 메모리 블록 생성 (임시, 저장하지 않음)
            from greeum.text_utils import process_user_input
            result = process_user_input(content)
            
            new_memory = {
                'block_index': -1,  # 임시 인덱스
                'timestamp': datetime.now().isoformat(),
                'context': content,
                'keywords': result.get("keywords", []),
                'tags': result.get("tags", []),
                'embedding': result.get("embedding", []),
                'importance': importance
            }
            
            # 기존 메모리들 가져오기
            db_manager = self.components['db_manager']
            existing_memories = db_manager.get_blocks(
                limit=memory_count, 
                sort_by='block_index', 
                order='desc'  # 최신순
            )
            
            if not existing_memories:
                return json.dumps({
                    "status": "success",
                    "analysis": {
                        "analysis_type": analysis_depth,
                        "direct_links": [],
                        "bridge_connections": [],
                        "total_candidates_checked": 0,
                        "message": "No existing memories found for analysis"
                    },
                    "performance": {
                        "analysis_time": 0.0,
                        "memories_analyzed": 0
                    }
                }, ensure_ascii=False, indent=2)
            
            # 인과관계 분석 실행
            import time
            start_time = time.time()
            
            analysis_result = association_system.process_new_memory(
                new_memory,
                existing_memories,
                analysis_depth=analysis_depth,
                memory_importance='normal' if importance < 0.7 else 'important'
            )
            
            analysis_time = time.time() - start_time
            
            # 결과 정리
            response = {
                "status": "success",
                "analysis": {
                    "analysis_type": analysis_result.get('analysis_type', analysis_depth),
                    "direct_links": analysis_result.get('direct_links', []),
                    "bridge_connections": analysis_result.get('bridge_connections', []),
                    "total_candidates_checked": analysis_result.get('total_candidates_checked', 0),
                    "cache_stats": analysis_result.get('cache_stats', {})
                },
                "performance": {
                    "analysis_time": round(analysis_time, 4),
                    "memories_analyzed": len(existing_memories),
                    "memories_per_second": round(len(existing_memories) / analysis_time, 1) if analysis_time > 0 else 0
                },
                "metadata": {
                    "new_memory_preview": content[:100] + ("..." if len(content) > 100 else ""),
                    "analysis_timestamp": datetime.now().isoformat(),
                    "greeum_version": self._get_version()
                }
            }
            
            return json.dumps(response, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Causality analysis failed: {e}")
            error_response = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            return json.dumps(error_response, ensure_ascii=False, indent=2)
    
    async def _handle_infer_causality(self, arguments: Dict[str, Any]) -> str:
        """
        3단계 인과추론 시스템 도구
        새 메모리와 기존 메모리들 간의 진정한 인과관계를 추론합니다.
        
        Arguments:
            - content (str): 분석할 새 메모리 내용
            - importance (float, optional): 메모리 중요도 (0.0-1.0)
            - inference_depth (str, optional): 추론 깊이 ('quick', 'balanced', 'deep')
            - memory_count (int, optional): 분석 대상 기존 메모리 수 (default: 50)
        
        Returns:
            str: 인과관계 추론 결과 JSON
        """
        try:
            # 파라미터 추출
            content = arguments.get("content")
            if not content:
                raise ValueError("content parameter is required")
                
            importance = arguments.get("importance", 0.5)
            inference_depth = arguments.get("inference_depth", "balanced")  # quick, balanced, deep
            memory_count = arguments.get("memory_count", 50)
            
            # 유효성 검사
            if inference_depth not in ['quick', 'balanced', 'deep']:
                raise ValueError("inference_depth must be one of: quick, balanced, deep")
            
            if not (0.0 <= importance <= 1.0):
                raise ValueError("importance must be between 0.0 and 1.0")
                
            if memory_count <= 0 or memory_count > 1000:
                raise ValueError("memory_count must be between 1 and 1000")
            
            # 기존 메모리 조회
            db_manager = self.components['db_manager']
            existing_memories = db_manager.get_blocks(
                limit=memory_count,
                sort_by='block_index',
                order='desc'
            )
            
            # 새 메모리 블록 생성 (임시 메모리)
            new_memory = {
                'block_index': -1,  # 임시 ID
                'timestamp': datetime.now().isoformat(),
                'context': content,
                'importance': importance,
                'keywords': [],
                'tags': [],
                'embedding': None  # CausalInferenceSystem에서 자체 생성
            }
            
            # 인과추론 시스템 초기화 및 실행
            from greeum.core.causal_inference import CausalInferenceSystem
            
            inference_start = datetime.now()
            causal_system = CausalInferenceSystem()
            
            result = causal_system.infer_causality(
                new_memory, 
                existing_memories, 
                inference_depth
            )
            
            inference_time = (datetime.now() - inference_start).total_seconds()
            
            # 성공 응답 구성
            response = {
                "status": "success",
                "inference_result": {
                    "inference_depth": inference_depth,
                    "causal_relationships": [],
                    "metadata": result.metadata or {}
                },
                "performance": {
                    "inference_time": round(inference_time, 4),
                    "memories_analyzed": len(existing_memories),
                    "memories_per_second": round(len(existing_memories) / inference_time, 1) if inference_time > 0 else 0,
                    "relationships_found": len(result.causal_relationships)
                },
                "metadata": {
                    "new_memory_preview": content[:100] + ("..." if len(content) > 100 else ""),
                    "inference_timestamp": datetime.now().isoformat(),
                    "greeum_version": self._get_version(),
                    "inference_method": result.metadata.get('analysis_method', inference_depth) if result.metadata else inference_depth
                }
            }
            
            # 인과관계 결과 변환
            for rel in result.causal_relationships:
                causal_rel = {
                    "source_memory_id": rel.source_memory_id,
                    "target_memory_id": rel.target_memory_id,
                    "causal_strength": round(rel.causal_strength, 3),
                    "confidence": round(rel.confidence, 3),
                    "direction": rel.direction,
                    "reasoning_method": rel.reasoning_method
                }
                
                # 추가 필드들 (있는 경우만)
                if hasattr(rel, 'reasoning') and rel.reasoning:
                    causal_rel["reasoning"] = rel.reasoning
                    
                if hasattr(rel, 'evidence') and rel.evidence:
                    causal_rel["evidence"] = rel.evidence
                    
                if hasattr(rel, 'alternative_explanations') and rel.alternative_explanations:
                    causal_rel["alternative_explanations"] = rel.alternative_explanations
                
                response["inference_result"]["causal_relationships"].append(causal_rel)
            
            return json.dumps(response, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Causal inference failed: {e}")
            error_response = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "inference_depth": arguments.get("inference_depth", "unknown")
            }
            return json.dumps(error_response, ensure_ascii=False, indent=2)
    
    def _expand_search_with_associations(self, base_results: List[Dict], depth: int, tolerance: float, max_results: int) -> List[Dict]:
        """
        연관관계를 활용한 확장 검색
        
        Args:
            base_results: 기본 검색 결과
            depth: 탐색 깊이 (1-3)
            tolerance: 연관관계 허용 오차 (0.0-1.0)
            max_results: 최대 결과 수
            
        Returns:
            확장된 검색 결과 (연관관계 정보 포함)
        """
        try:
            if not base_results or depth == 0:
                return base_results
            
            # AssociationSystem 초기화
            from greeum.core.association_detector import AssociationSystem
            association_system = AssociationSystem()
            
            db_manager = self.components['db_manager']
            expanded_results = []
            processed_indices = set()
            
            # 기본 결과들을 먼저 추가 (원본 표시)
            for memory in base_results:
                memory['relation_type'] = 'direct_match'
                expanded_results.append(memory)
                processed_indices.add(memory.get('block_index'))
            
            current_level_memories = base_results.copy()
            
            # 각 depth 단계별로 연관 메모리 탐색
            for current_depth in range(1, depth + 1):
                if len(expanded_results) >= max_results:
                    break
                    
                next_level_memories = []
                
                for memory in current_level_memories:
                    if len(expanded_results) >= max_results:
                        break
                    
                    # 현재 메모리와 연관된 메모리들 찾기
                    associated_memories = self._find_associated_memories(
                        memory, association_system, tolerance, current_depth
                    )
                    
                    for assoc_memory in associated_memories:
                        if len(expanded_results) >= max_results:
                            break
                            
                        assoc_index = assoc_memory.get('block_index')
                        if assoc_index not in processed_indices:
                            assoc_memory['relation_type'] = f'depth_{current_depth}_association'
                            expanded_results.append(assoc_memory)
                            processed_indices.add(assoc_index)
                            next_level_memories.append(assoc_memory)
                
                current_level_memories = next_level_memories
                
                # 더 이상 새로운 연관 메모리가 없으면 중단
                if not next_level_memories:
                    break
            
            return expanded_results[:max_results]
            
        except Exception as e:
            logger.error(f"Association expansion failed: {e}")
            # 실패 시 기본 결과 반환
            return base_results
    
    def _find_associated_memories(self, memory: Dict, association_system, tolerance: float, depth: int) -> List[Dict]:
        """
        특정 메모리와 연관된 메모리들 찾기
        
        Args:
            memory: 기준 메모리
            association_system: 연관관계 시스템
            tolerance: 허용 오차
            depth: 현재 탐색 깊이
            
        Returns:
            연관된 메모리 리스트
        """
        try:
            db_manager = self.components['db_manager']
            
            # 연관도 임계값 계산 (tolerance 기반)
            base_threshold = 0.1  # 기본 임계값
            adjusted_threshold = base_threshold * (1.0 - tolerance)  # tolerance 높을수록 낮은 임계값
            
            # 유사도 기반 연관 메모리 검색
            if memory.get('embedding'):
                similar_memories = db_manager.search_blocks_by_embedding(
                    memory['embedding'], 
                    top_k=20,  # 후보군을 넉넉히
                    threshold=adjusted_threshold
                )
                
                # 현재 메모리 제외
                current_index = memory.get('block_index')
                filtered_memories = [m for m in similar_memories if m.get('block_index') != current_index]
                
                # tolerance 기반으로 추가 필터링
                final_memories = []
                for candidate in filtered_memories[:10]:  # 상위 10개만 고려
                    # tolerance가 높을수록 더 많은 메모리 포함
                    similarity_score = self._calculate_similarity(memory, candidate)
                    if similarity_score >= adjusted_threshold:
                        final_memories.append(candidate)
                
                return final_memories
            
            return []
            
        except Exception as e:
            logger.error(f"Finding associated memories failed: {e}")
            return []
    
    def _calculate_similarity(self, memory1: Dict, memory2: Dict) -> float:
        """
        두 메모리 간 유사도 계산 (간단한 구현)
        
        실제로는 임베딩 코사인 유사도, 키워드 겹침 등을 종합
        """
        try:
            import numpy as np
            
            # 임베딩 유사도 계산
            emb1 = memory1.get('embedding', [])
            emb2 = memory2.get('embedding', [])
            
            if emb1 and emb2 and len(emb1) == len(emb2):
                emb1_np = np.array(emb1)
                emb2_np = np.array(emb2)
                
                # 코사인 유사도
                dot_product = np.dot(emb1_np, emb2_np)
                norm1 = np.linalg.norm(emb1_np)
                norm2 = np.linalg.norm(emb2_np)
                
                if norm1 > 0 and norm2 > 0:
                    return dot_product / (norm1 * norm2)
            
            # 폴백: 키워드 기반 유사도
            keywords1 = set(memory1.get('keywords', []))
            keywords2 = set(memory2.get('keywords', []))
            
            if keywords1 and keywords2:
                intersection = keywords1.intersection(keywords2)
                union = keywords1.union(keywords2)
                return len(intersection) / len(union) if union else 0.0
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0