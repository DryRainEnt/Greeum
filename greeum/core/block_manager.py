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
        logger.info("BlockManager 초기화 완료")
        
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
        logger.debug(f"add_block 호출: context='{context[:20]}...'")
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
            "metadata": metadata or {},
            "embedding_model": embedding_model,
            "links": links  # M2: Store neighbor links cache
        }
        
        try:
            added_idx = self.db_manager.add_block(block_to_store_in_db)
            # add_block이 실제 추가된 블록의 index를 반환한다고 가정 (DB auto-increment 시 유용)
            # 현재 DatabaseManager.add_block은 전달된 block_data.get('block_index')를 사용하므로, added_idx는 new_block_index와 같음.
            added_block = self.db_manager.get_block(new_block_index)
            logger.info(f"블록 추가 성공: index={new_block_index}, hash={current_hash[:10]}...")
            return added_block
        except Exception as e:
            logger.error(f"BlockManager: DB에 블록 추가 오류 - {e}", exc_info=True)
            return None
    
    def get_blocks(self, start_idx: Optional[int] = None, end_idx: Optional[int] = None,
                     limit: int = 100, offset: int = 0, 
                     sort_by: str = 'block_index', order: str = 'asc') -> List[Dict[str, Any]]:
        """블록 범위 조회 (DatabaseManager 사용)"""
        logger.debug(f"get_blocks 호출: start={start_idx}, end={end_idx}, limit={limit}, offset={offset}, sort_by={sort_by}, order={order}")
        blocks = self.db_manager.get_blocks(start_idx=start_idx, end_idx=end_idx, limit=limit, offset=offset, sort_by=sort_by, order=order)
        logger.debug(f"get_blocks 결과: {len(blocks)}개 블록 반환")
        return blocks
    
    def get_block_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """인덱스로 블록 조회 (DatabaseManager 사용)"""
        return self.db_manager.get_block(index)
    
    def verify_blocks(self) -> bool:
        """블록체인 무결성 검증 (DatabaseManager 사용). prev_hash 연결 및 개별 해시 (단순화된 방식) 검증."""
        logger.debug("verify_blocks 호출")
        all_blocks = self.get_blocks(limit=100000, sort_by='block_index', order='asc')
        if not all_blocks:
            logger.info("검증할 블록 없음, 무결성 True 반환")
            return True

        for i, block in enumerate(all_blocks):
            if i > 0:
                if block.get('prev_hash') != all_blocks[i-1].get('hash'):
                    logger.warning(f"BlockManager: prev_hash 불일치! index {i}, block_hash {block.get('hash')}, prev_expected {all_blocks[i-1].get('hash')}, prev_actual {block.get('prev_hash')}")
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
                logger.warning(f"BlockManager: 해시 불일치! block_index {block.get('block_index')}. Recalculated: {recalculated_hash}, Stored: {block.get('hash')}")
                return False
        logger.info("모든 블록 무결성 검증 통과")
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