import os
import json
import hashlib
import datetime
from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path
from .database_manager import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class BlockManager:
    """장기 기억 블록을 관리하는 클래스 (DatabaseManager 사용)"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """BlockManager 초기화
        Args:
            db_manager: DatabaseManager (없으면 기본 SQLite 파일 생성)
        """
        self.db_manager = db_manager or DatabaseManager()
        logger.info("BlockManager initialization completed")
        
    def _compute_hash(self, block_data: Dict[str, Any]) -> str:
        """블록의 해시값 계산. 해시 계산에 포함되지 않아야 할 필드는 이 함수 호출 전에 정리되어야 함."""
        block_copy = block_data.copy()
        block_copy.pop('hash', None)
        block_str = json.dumps(block_copy, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(block_str.encode('utf-8')).hexdigest()
    
    def add_block(self, context: str, keywords: List[str], tags: List[str], 
                 embedding: List[float], importance: float, 
                 metadata: Optional[Dict[str, Any]] = None,
                 embedding_model: Optional[str] = 'default') -> Optional[Dict[str, Any]]:
        """
        새 블록 추가 (DatabaseManager 사용)
        """
        logger.debug(f"add_block called: context='{context[:20]}...'")
        last_block_info = self.db_manager.get_last_block_info()
        
        new_block_index: int
        prev_h: str

        if last_block_info:
            new_block_index = last_block_info.get('block_index', -1) + 1
            prev_h = last_block_info.get('hash', '')
        else:
            new_block_index = 0
            prev_h = ''
        
        current_timestamp = datetime.datetime.now().isoformat()
        
        # 해시 계산 대상이 되는 핵심 블록 데이터 구성
        # keywords, tags, embedding, metadata 등은 별도 테이블 관리되므로 해시 대상에서 제외 (설계 결정 사항)
        block_data_for_hash = {
            "block_index": new_block_index,
            "timestamp": current_timestamp,
            "context": context,
            "importance": importance,
            "prev_hash": prev_h,
        }
        current_hash = self._compute_hash(block_data_for_hash)

        # M2: Add optional links.neighbors cache for anchor-based graph system
        links = {}
        if metadata and 'links' in metadata:
            links = metadata['links']
        
        # v2.4.0a2: 액탄트 분석 정보 자동 추가
        enhanced_metadata = self._enhance_metadata_with_actants(context, metadata or {})
        
        block_to_store_in_db = {
            "block_index": new_block_index,
            "timestamp": current_timestamp,
            "context": context,
            "keywords": keywords,
            "tags": tags,
            "embedding": embedding,
            "importance": importance,
            "hash": current_hash,
            "prev_hash": prev_h,
            "metadata": enhanced_metadata,
            "embedding_model": embedding_model,
            "links": links  # M2: Store neighbor links cache
        }
        
        try:
            added_idx = self.db_manager.add_block(block_to_store_in_db)
            # add_block이 실제 추가된 블록의 index를 반환한다고 가정 (DB auto-increment 시 유용)
            # 현재 DatabaseManager.add_block은 전달된 block_data.get('block_index')를 사용하므로, added_idx는 new_block_index와 같음.
            added_block = self.db_manager.get_block(new_block_index)
            logger.info(f"Block added successfully: index={new_block_index}, hash={current_hash[:10]}...")
            return added_block
        except Exception as e:
            logger.error(f"BlockManager: Error adding block to DB - {e}", exc_info=True)
            return None
    
    def get_blocks(self, start_idx: Optional[int] = None, end_idx: Optional[int] = None,
                     limit: int = 100, offset: int = 0, 
                     sort_by: str = 'block_index', order: str = 'asc') -> List[Dict[str, Any]]:
        """블록 범위 조회 (DatabaseManager 사용)"""
        logger.debug(f"get_blocks called: start={start_idx}, end={end_idx}, limit={limit}, offset={offset}, sort_by={sort_by}, order={order}")
        blocks = self.db_manager.get_blocks(start_idx=start_idx, end_idx=end_idx, limit=limit, offset=offset, sort_by=sort_by, order=order)
        logger.debug(f"get_blocks result: {len(blocks)} blocks returned")
        return blocks
    
    def _enhance_metadata_with_actants(self, context: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """v2.4.0a2: 메타데이터에 액탄트 분석 정보 추가 (그레마스 6개 액탄트 역할 분석)"""
        
        # 기존 메타데이터 보존
        enhanced_metadata = metadata.copy()
        
        # 이미 액탄트 분석이 있으면 건너뛰기
        if "actant_analysis" in enhanced_metadata:
            return enhanced_metadata
        
        # 그레마스 6개 액탄트 역할 분석
        actants = {}
        
        # Subject (주체) - 행동의 주체, 묵시적 화자 포함
        subject_patterns = ["나는", "내가", "우리가", "팀이", "사용자가"]
        subject_found = False
        for pattern in subject_patterns:
            if pattern in context:
                actants["subject"] = {
                    "entity": pattern.replace("는", "").replace("가", ""),
                    "confidence": 0.8,
                    "extraction_method": "explicit_pattern"
                }
                subject_found = True
                break
        
        # 묵시적 주체 (1인칭 동사 활용형 감지)
        if not subject_found and any(word in context for word in ["했고", "했다", "했어요", "시작했", "느껴요", "생각해"]):
            actants["subject"] = {
                "entity": "화자",
                "confidence": 0.7,
                "extraction_method": "implicit_first_person"
            }
        
        # Object (객체) - 추구하거나 획득하려는 대상
        object_patterns = ["프로젝트", "작업", "기능", "문제", "목표", "결과", "경험", "기회"]
        for pattern in object_patterns:
            if pattern in context:
                # 수식어가 있는 경우 함께 추출 (예: "AI 프로젝트")
                words = context.split()
                for i, word in enumerate(words):
                    if pattern in word:
                        if i > 0 and words[i-1] not in ["는", "가", "을", "를", "의"]:
                            combined = f"{words[i-1]} {pattern}"
                        else:
                            combined = pattern
                        actants["object"] = {
                            "entity": combined,
                            "confidence": 0.8,
                            "extraction_method": "contextual_extraction"
                        }
                        break
                break
        
        # Sender (발신자) - 목표를 부여하거나 동기를 제공하는 존재
        if any(word in context for word in ["해야", "요청", "지시", "부탁"]):
            actants["sender"] = {
                "entity": "외부 요청자",
                "confidence": 0.6,
                "extraction_method": "obligation_pattern"
            }
        elif actants.get("subject", {}).get("entity") in ["화자", "나"]:
            actants["sender"] = {
                "entity": "자기동기",
                "confidence": 0.7,
                "extraction_method": "self_motivation"
            }
        
        # Receiver (수신자) - 목표 달성의 수혜자
        if actants.get("subject"):
            actants["receiver"] = {
                "entity": actants["subject"]["entity"],
                "confidence": 0.7,
                "extraction_method": "subject_beneficiary"
            }
        
        # Helper (조력자) - 목표 달성을 돕는 요소
        helper_patterns = ["도구", "기술", "팀", "지원", "도움", "흥미", "동기", "열정"]
        for pattern in helper_patterns:
            if pattern in context or (pattern == "흥미" and "흥미로" in context):
                actants["helper"] = {
                    "entity": pattern if pattern in context else "흥미",
                    "confidence": 0.6,
                    "extraction_method": "supportive_element"
                }
                break
        
        # Opponent (적대자) - 목표 달성을 방해하는 요소
        opponent_patterns = ["문제", "어려움", "장애물", "실패", "걱정", "우려"]
        for pattern in opponent_patterns:
            if pattern in context:
                actants["opponent"] = {
                    "entity": pattern,
                    "confidence": 0.7,
                    "extraction_method": "obstacle_detection"
                }
                break
        
        # 서사 패턴 추론 (더 정밀한 분류)
        narrative_pattern = "other"
        if any(word in context for word in ["시작했", "새로운", "처음"]):
            narrative_pattern = "initiation"  # 개시/시작
        elif any(word in context for word in ["시작", "계획", "목표"]) and not any(word in context for word in ["시작했"]):
            narrative_pattern = "quest"  # 탐구/추구
        elif any(word in context for word in ["문제", "어려움", "실패", "걱정"]):
            narrative_pattern = "conflict"  # 갈등
        elif any(word in context for word in ["완료", "성공", "달성", "해결"]):
            narrative_pattern = "acquisition"  # 획득/완성
        elif any(word in context for word in ["흥미로", "좋아", "만족", "기뻐"]):
            narrative_pattern = "satisfaction"  # 만족/긍정
        
        # 액탄트 분석 정보 추가
        enhanced_metadata["actant_analysis"] = {
            "actants": actants,
            "narrative_pattern": narrative_pattern,
            "action_sequence": [],
            "analysis_quality": {
                "actant_count": len(actants),
                "quality_level": "medium" if len(actants) > 0 else "low"
            },
            "analysis_timestamp": datetime.datetime.now().isoformat(),
            "analysis_method": "pattern_matching_v240a2"
        }
        
        # 처리 정보 추가
        enhanced_metadata["actant_processing"] = {
            "version": "2.4.0a2",
            "processed_at": datetime.datetime.now().isoformat(),
            "auto_generated": True
        }
        
        return enhanced_metadata
    
    def get_block_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """인덱스로 블록 조회 (DatabaseManager 사용)"""
        return self.db_manager.get_block(index)
    
    def verify_blocks(self) -> bool:
        """블록체인 무결성 검증 (DatabaseManager 사용). prev_hash 연결 및 개별 해시 (단순화된 방식) 검증."""
        logger.debug("verify_blocks called")
        all_blocks = self.get_blocks(limit=100000, sort_by='block_index', order='asc')
        if not all_blocks:
            logger.info("No blocks to verify, returning True for integrity")
            return True

        for i, block in enumerate(all_blocks):
            if i > 0:
                if block.get('prev_hash') != all_blocks[i-1].get('hash'):
                    logger.warning(f"BlockManager: prev_hash mismatch! index {i}, block_hash {block.get('hash')}, prev_expected {all_blocks[i-1].get('hash')}, prev_actual {block.get('prev_hash')}")
                    return False
            
            # 개별 블록 해시 검증
            # 저장 시 해시된 필드와 동일한 필드로 재계산하여 비교해야 함.
            # 현재 add_block에서 block_data_for_hash 기준으로 해시했으므로, 동일하게 구성하여 비교.
            expected_data_for_hash = {
                "block_index": block.get('block_index'),
                "timestamp": block.get('timestamp'),
                "context": block.get('context'),
                "importance": block.get('importance'),
                "prev_hash": block.get('prev_hash'),
            }
            recalculated_hash = self._compute_hash(expected_data_for_hash)
            if recalculated_hash != block.get('hash'):
                logger.warning(f"BlockManager: Hash mismatch! block_index {block.get('block_index')}. Recalculated: {recalculated_hash}, Stored: {block.get('hash')}")
                return False
        logger.info("All blocks integrity verification passed")
        return True
    
    def search_by_keywords(self, keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """키워드로 블록 검색 (DatabaseManager 사용)"""
        return self.db_manager.search_blocks_by_keyword(keywords, limit=limit)
    
    def search_by_embedding(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """임베딩 유사도로 블록 검색"""
        return self.db_manager.search_blocks_by_embedding(query_embedding, top_k=top_k)
    
    def filter_by_importance(self, threshold: float = 0.7, limit: int = 100) -> List[Dict[str, Any]]:
        """중요도 기준으로 블록 필터링. DatabaseManager의 기능을 직접 호출."""
        # 현재 DatabaseManager에 해당 기능이 없으므로 get_blocks 후 필터링 (정렬 활용).
        # DB에서 직접 필터링 및 정렬하는 것이 훨씬 효율적임.
        # 예: self.db_manager.filter_blocks_by_importance(threshold, limit, sort_by='importance', order='desc')
        
        # 임시방편: 중요도로 정렬된 모든 블록을 가져온 후, Python에서 필터링 및 limit 적용
        # 이 방식은 DB에서 모든 데이터를 가져오므로 여전히 비효율적일 수 있음.
        # DB에 중요도 필터링 조건 + 정렬 + limit 기능을 구현해야 함.
        # all_important_blocks = self.db_manager.get_blocks(limit=limit*5, sort_by='importance', order='desc') # 더 많은 데이터를 가져와서 필터링
        # 
        # result = []
        # for block in all_important_blocks:
        #     if block.get('importance', 0.0) >= threshold:
        #         result.append(block)
        #     if len(result) >= limit:
        #         break
        # return result 
        return self.db_manager.filter_blocks_by_importance(threshold=threshold, limit=limit, order='desc')
    
    def verify_integrity(self) -> bool:
        """
        블록체인 무결성 검증
        
        Returns:
            bool: 블록체인이 무결성을 유지하면 True
        """
        try:
            # 1. 모든 블록 조회 (인덱스 순)
            blocks = self.db_manager.get_blocks()
            if not blocks:
                logger.info("No blocks to verify")
                return True
            
            # 2. 정렬 및 연속성 확인
            sorted_blocks = sorted(blocks, key=lambda x: x['block_index'])
            
            prev_hash = ""
            for i, block in enumerate(sorted_blocks):
                # 인덱스 연속성 확인
                expected_index = i
                if block['block_index'] != expected_index:
                    logger.error(f"Block index discontinuity: expected {expected_index}, got {block['block_index']}")
                    return False
                
                # 해시 체인 검증
                if block['prev_hash'] != prev_hash:
                    logger.error(f"Hash chain broken at block {i}: expected prev_hash '{prev_hash}', got '{block['prev_hash']}'")
                    return False
                
                # 현재 블록 해시 재계산 및 검증 (keywords, tags, embedding은 해시 계산에서 제외)
                calculated_hash = self._compute_hash({
                    'block_index': block['block_index'],
                    'timestamp': block['timestamp'],
                    'context': block['context'],
                    'importance': block['importance'],
                    'prev_hash': block['prev_hash']
                })
                
                if calculated_hash != block['hash']:
                    logger.error(f"Block {i} hash mismatch: calculated '{calculated_hash}', stored '{block['hash']}'")
                    return False
                
                prev_hash = block['hash']
            
            # 3. 메타데이터 일관성 확인 (블록 개수)
            total_blocks = len(sorted_blocks)
            last_block_index = sorted_blocks[-1]['block_index'] if sorted_blocks else -1
            
            logger.info(f"Blockchain integrity verified: {total_blocks} blocks")
            return True
        
        except Exception as e:
            logger.error(f"Integrity verification failed: {e}")
            return False
    
    def update_block_links(self, block_index: int, neighbors: List[Dict[str, Any]]) -> bool:
        """
        Update neighbor links cache for a block (M2 Implementation).
        
        Args:
            block_index: Block index to update
            neighbors: List of neighbor info [{"id": "block_123", "w": 0.61}, ...]
            
        Returns:
            bool: True if update successful
        """
        try:
            # Get current block
            block = self.db_manager.get_block_by_index(block_index)
            if not block:
                logger.warning(f"Block {block_index} not found for links update")
                return False
            
            # Update links in metadata
            metadata = block.get('metadata', {})
            metadata['links'] = {"neighbors": neighbors}
            
            # Update block in database
            success = self.db_manager.update_block_metadata(block_index, metadata)
            if success:
                logger.debug(f"Updated links for block {block_index}: {len(neighbors)} neighbors")
            else:
                logger.warning(f"Failed to update links for block {block_index}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error updating block links: {e}")
            return False
    
    def get_block_neighbors(self, block_index: int) -> List[Dict[str, Any]]:
        """
        Get cached neighbor links for a block.
        
        Args:
            block_index: Block index
            
        Returns:
            List of neighbor info or empty list if no cache
        """
        try:
            block = self.db_manager.get_block_by_index(block_index)
            if not block:
                return []
                
            metadata = block.get('metadata', {})
            links = metadata.get('links', {})
            return links.get('neighbors', [])
            
        except Exception as e:
            logger.debug(f"Error getting block neighbors: {e}")
            return []
    
    # v2.5.1: AI Context Slots 통합 검색 기능
    def search_with_slots(self, query: str, limit: int = 5, use_slots: bool = True, 
                         include_relationships: bool = False, **options) -> List[Dict[str, Any]]:
        """
        v2.5.1 슬롯 시스템을 활용한 향상된 검색
        
        Args:
            query: 검색 쿼리
            limit: 반환할 결과 수
            use_slots: 슬롯 우선 검색 활성화
            include_relationships: 관계 기반 확장 검색 (v2.5.2+)
            **options: 추가 검색 옵션
            
        Returns:
            검색 결과 리스트 (슬롯 + LTM 통합)
        """
        from datetime import datetime
        search_start_time = datetime.utcnow()
        
        logger.debug(f"Enhanced search: query='{query}', use_slots={use_slots}")
        
        all_results = []
        slots_results_count = 0
        ltm_results_count = 0
        
        # Analytics 추적을 위한 변수
        analytics = None
        try:
            from .usage_analytics import UsageAnalytics
            analytics = UsageAnalytics()
        except ImportError:
            pass
        
        # Phase 1: 슬롯 우선 검색 (빠른 응답)
        if use_slots:
            try:
                from .working_memory import AIContextualSlots
                # 임시 슬롯 인스턴스 (실제로는 싱글톤이나 세션 기반으로 관리)
                slots = AIContextualSlots()
                active_slots = slots.get_all_active_slots()
                
                for slot_name, slot in active_slots.items():
                    if slot.matches_query(query):
                        # 슬롯 결과를 LTM 형식으로 변환
                        slot_result = {
                            'block_index': f"slot_{slot_name}",
                            'context': slot.content,
                            'timestamp': slot.timestamp.isoformat(),
                            'importance': slot.importance_score,
                            'source': 'working_memory',
                            'slot_type': slot.slot_type.value,
                            'keywords': self._extract_keywords_from_content(slot.content)
                        }
                        
                        # LTM 앵커인 경우 관련 블록 정보 추가
                        if slot.is_ltm_anchor():
                            slot_result['ltm_anchor_block'] = slot.ltm_anchor_block
                            slot_result['search_radius'] = slot.search_radius
                        
                        all_results.append(slot_result)
                        slots_results_count += 1
                        
                logger.debug(f"Found {slots_results_count} results from slots")
                        
            except ImportError:
                logger.warning("AIContextualSlots not available, skipping slot search")
            except Exception as e:
                logger.error(f"Error in slot search: {e}")
        
        # Phase 2: 기존 LTM 검색
        try:
            # 슬롯에서 찾은 만큼 제외하고 검색
            remaining_limit = max(1, limit - len(all_results))
            ltm_results = self.search_by_keywords(
                self._extract_keywords_from_content(query), 
                limit=remaining_limit
            )
            
            # 중복 제거 (슬롯 결과와 LTM 결과 간)
            unique_ltm_results = []
            for ltm_result in ltm_results:
                # 내용 유사성으로 중복 검사 (간단한 방식)
                is_duplicate = False
                for slot_result in all_results:
                    if self._is_content_similar(
                        ltm_result.get('context', ''), 
                        slot_result.get('context', '')
                    ):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    ltm_result['source'] = 'long_term_memory'
                    unique_ltm_results.append(ltm_result)
            
            all_results.extend(unique_ltm_results)
            ltm_results_count = len(unique_ltm_results)
            logger.debug(f"Added {ltm_results_count} unique LTM results")
            
        except Exception as e:
            logger.error(f"Error in LTM search: {e}")
        
        # Phase 3: 결과 랭킹 및 제한
        ranking_start_time = datetime.utcnow()
        ranked_results = self._rank_search_results(all_results, query)
        final_results = ranked_results[:limit]
        
        # Analytics 추적: 검색 성능 비교
        if analytics:
            search_end_time = datetime.utcnow()
            total_search_time = (search_end_time - search_start_time).total_seconds() * 1000
            ranking_time = (search_end_time - ranking_start_time).total_seconds() * 1000
            
            # 기존 검색과 비교를 위해 기존 방식도 실행 (성능 측정용)
            baseline_start_time = datetime.utcnow()
            try:
                keywords = self._extract_keywords_from_content(query)
                baseline_results = self.search_by_keywords(keywords, limit=limit)
                baseline_end_time = datetime.utcnow()
                baseline_time = (baseline_end_time - baseline_start_time).total_seconds() * 1000
            except Exception:
                baseline_time = 0
                baseline_results = []
            
            analytics.track_search_comparison(
                query_text=query[:100],  # 프라이버시를 위해 첫 100자만
                slots_enabled=use_slots,
                response_time_ms=total_search_time,
                results_count=len(final_results),
                slot_hits=slots_results_count,
                ltm_hits=ltm_results_count,
                top_result_source=final_results[0].get('source', 'unknown') if final_results else None
            )
        
        logger.info(f"Enhanced search completed: {len(final_results)}/{len(all_results)} results returned")
        return final_results
    
    def _extract_keywords_from_content(self, content: str, max_keywords: int = 5) -> List[str]:
        """컨텐츠에서 간단한 키워드 추출"""
        try:
            from ..text_utils import extract_keywords_from_text
            return extract_keywords_from_text(content)[:max_keywords]
        except ImportError:
            # 간단한 폴백: 공백으로 분할
            words = content.split()
            return [word.strip('.,!?') for word in words if len(word) > 2][:max_keywords]
    
    def _is_content_similar(self, content1: str, content2: str, threshold: float = 0.7) -> bool:
        """두 컨텐츠의 유사성 검사 (간단한 방식)"""
        if not content1 or not content2:
            return False
            
        # 간단한 자카드 유사도
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return False
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union)
        return similarity >= threshold
    
    def _rank_search_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """검색 결과 랭킹 (슬롯 우선, 중요도, 최신성 고려)"""
        def calculate_score(result):
            score = 0.0
            
            # 슬롯 결과 우선순위 (빠른 응답)
            if result.get('source') == 'working_memory':
                score += 10.0
                
                # 슬롯 타입별 가중치
                slot_type = result.get('slot_type', 'context')
                if slot_type == 'anchor':
                    score += 5.0  # 앵커 슬롯 높은 우선순위
                elif slot_type == 'context':
                    score += 3.0  # 활성 컨텍스트
                else:  # buffer
                    score += 1.0
            
            # 중요도 점수
            importance = result.get('importance', 0.5)
            score += importance * 5.0
            
            # 최신성 점수 (간단화)
            try:
                timestamp_str = result.get('timestamp', '')
                if timestamp_str:
                    # 최근일수록 높은 점수 (세부 구현은 생략)
                    score += 1.0
            except:
                pass
            
            return score
        
        return sorted(results, key=calculate_score, reverse=True) 