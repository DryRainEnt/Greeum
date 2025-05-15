import os
import json
import hashlib
import datetime
from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path

class BlockManager:
    """장기 기억 블록을 관리하는 클래스"""
    
    def __init__(self, data_path: str = "data/block_memory.jsonl"):
        """
        블록 매니저 초기화
        
        Args:
            data_path: 블록 메모리 파일 경로
        """
        self.data_path = data_path
        self._ensure_data_file()
        self.blocks = self._load_blocks()
        
    def _ensure_data_file(self) -> None:
        """데이터 파일이 존재하는지 확인하고 없으면 생성"""
        data_dir = os.path.dirname(self.data_path)
        os.makedirs(data_dir, exist_ok=True)
        
        if not os.path.exists(self.data_path):
            with open(self.data_path, 'w', encoding='utf-8') as f:
                pass  # 빈 파일 생성
    
    def _load_blocks(self) -> List[Dict[str, Any]]:
        """블록 데이터 로드"""
        blocks = []
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:  # 빈 줄 무시
                        blocks.append(json.loads(line))
        except json.JSONDecodeError:
            # 파일이 비어있거나 손상된 경우
            pass
        
        return blocks
    
    def _compute_hash(self, block: Dict[str, Any]) -> str:
        """블록의 해시값 계산"""
        # 해시 계산에서 제외할 필드
        block_copy = block.copy()
        if 'hash' in block_copy:
            del block_copy['hash']
        if 'prev_hash' in block_copy:
            del block_copy['prev_hash']
        
        # 정렬된 문자열로 변환하여 해시 계산
        block_str = json.dumps(block_copy, sort_keys=True)
        return hashlib.sha256(block_str.encode('utf-8')).hexdigest()
    
    def add_block(self, context: str, keywords: List[str], tags: List[str], 
                 embedding: List[float], importance: float) -> Dict[str, Any]:
        """
        새 블록 추가
        
        Args:
            context: 전체 발화 내용
            keywords: 핵심 키워드 목록
            tags: 태그 목록
            embedding: 벡터 임베딩
            importance: 중요도 (0~1)
            
        Returns:
            생성된 블록
        """
        # 이전 블록의 해시값 가져오기
        prev_hash = ""
        if self.blocks:
            prev_hash = self.blocks[-1].get('hash', '')
        
        # 새 블록 생성
        block = {
            "block_index": len(self.blocks),
            "timestamp": datetime.datetime.now().isoformat(),
            "context": context,
            "keywords": keywords,
            "tags": tags,
            "embedding": embedding,
            "importance": importance,
            "prev_hash": prev_hash
        }
        
        # 해시값 계산 및 설정
        block["hash"] = self._compute_hash(block)
        
        # 블록 저장
        self.blocks.append(block)
        with open(self.data_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(block) + '\n')
        
        return block
    
    def get_blocks(self, start_idx: Optional[int] = None, end_idx: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        블록 범위 조회
        
        Args:
            start_idx: 시작 인덱스 (None이면 처음부터)
            end_idx: 종료 인덱스 (None이면 끝까지)
            
        Returns:
            블록 목록
        """
        if start_idx is None:
            start_idx = 0
        if end_idx is None:
            end_idx = len(self.blocks)
            
        return self.blocks[start_idx:end_idx]
    
    def get_block_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """인덱스로 블록 조회"""
        if 0 <= index < len(self.blocks):
            return self.blocks[index]
        return None
    
    def verify_blocks(self) -> bool:
        """
        블록체인 무결성 검증
        
        Returns:
            검증 결과 (True/False)
        """
        for i, block in enumerate(self.blocks):
            # 해시값 검증
            computed_hash = self._compute_hash(block)
            if computed_hash != block.get('hash'):
                return False
            
            # 이전 해시값 검증 (첫 블록 제외)
            if i > 0 and block.get('prev_hash') != self.blocks[i-1].get('hash'):
                return False
                
        return True
    
    def search_by_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """키워드로 블록 검색"""
        result = []
        for block in self.blocks:
            block_keywords = block.get('keywords', []) + block.get('tags', [])
            
            # 부분 일치 검색으로 변경
            for kw in keywords:
                kw_lower = kw.lower()
                found = False
                
                # 블록 키워드에서 부분 일치 검색
                for bk in block_keywords:
                    if kw_lower in bk.lower() or bk.lower() in kw_lower:
                        found = True
                        break
                
                # 컨텍스트에서도 검색
                if not found and 'context' in block:
                    if kw_lower in block['context'].lower():
                        found = True
                
                if found:
                    result.append(block)
                    break
                    
        return result
    
    def search_by_embedding(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        임베딩 유사도로 블록 검색
        
        Args:
            query_embedding: 쿼리 임베딩
            top_k: 상위 k개 결과 반환
            
        Returns:
            유사도가 높은 상위 k개 블록
        """
        if not self.blocks:
            return []
            
        # 유사도 계산
        query_embedding = np.array(query_embedding)
        blocks_with_similarity = []
        
        for block in self.blocks:
            block_embedding = np.array(block.get('embedding', []))
            if len(block_embedding) > 0:
                # 코사인 유사도 계산
                similarity = np.dot(query_embedding, block_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(block_embedding)
                )
                blocks_with_similarity.append((block, similarity))
        
        # 유사도 기준 정렬
        blocks_with_similarity.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 k개 반환
        return [block for block, _ in blocks_with_similarity[:top_k]]
    
    def filter_by_importance(self, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """중요도 기준으로 블록 필터링"""
        return [block for block in self.blocks if block.get('importance', 0) >= threshold] 