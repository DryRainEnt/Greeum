from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import json
from .text_utils import extract_keywords_advanced, calculate_importance, generate_simple_embedding

class MemoryEvolutionManager:
    """기억 진화 및 재해석 관리 클래스"""
    
    def __init__(self, db_manager=None):
        """
        기억 진화 관리자 초기화
        
        Args:
            db_manager: 데이터베이스 관리자 (없으면 작동 불가)
        """
        self.db_manager = db_manager
    
    def create_memory_revision(self, original_block_index: int, new_context: str, 
                              reason: str, keywords: Optional[List[str]] = None,
                              tags: Optional[List[str]] = None, 
                              embedding: Optional[List[float]] = None,
                              importance: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        기존 기억의 수정본 생성
        
        Args:
            original_block_index: 원본 블록 인덱스
            new_context: 새로운 컨텍스트
            reason: 변경 이유
            keywords: 키워드 (None이면 원본 + 자동 추출)
            tags: 태그 (None이면 원본 + 자동 추출)
            embedding: 임베딩 (None이면 자동 생성)
            importance: 중요도 (None이면 원본과 같거나 높게)
            
        Returns:
            새로 생성된 수정 블록 (실패 시 None)
        """
        if not self.db_manager:
            print("데이터베이스 관리자가 설정되지 않았습니다.")
            return None
        
        # 원본 블록 가져오기
        original_block = self.db_manager.get_block(original_block_index)
        if not original_block:
            print(f"블록 {original_block_index}를 찾을 수 없습니다.")
            return None
        
        # 수정 메타데이터 준비
        revision_metadata = {
            "original_block_index": original_block_index,
            "revision_reason": reason,
            "revision_timestamp": datetime.now().isoformat(),
            "revision_type": "update",
            "revision_number": self._get_next_revision_number(original_block_index)
        }
        
        # 키워드 및 태그 처리
        try:
            from .text_utils import process_user_input
            processed = process_user_input(new_context)
        except ImportError:
            # 텍스트 처리 유틸리티가 없는 경우 간단한 처리
            processed = {
                "context": new_context,
                "keywords": [],
                "tags": [],
                "embedding": [],
                "importance": original_block.get("importance", 0.5)
            }
        
        # 원본 키워드와 병합 (옵션)
        if keywords is None:
            final_keywords = list(set(processed["keywords"] + original_block.get("keywords", [])))
        else:
            final_keywords = keywords
            
        # 원본 태그와 병합 (옵션)
        if tags is None:
            final_tags = list(set(processed["tags"] + original_block.get("tags", [])))
        else:
            final_tags = tags
            
        # 수정 태그 추가
        if "revision" not in final_tags:
            final_tags.append("revision")
            
        # 임베딩 처리
        final_embedding = embedding if embedding is not None else processed["embedding"]
        
        # 중요도 처리 (원본보다 낮아지지 않도록)
        original_importance = original_block.get("importance", 0.5)
        if importance is None:
            final_importance = max(processed["importance"], original_importance)
        else:
            final_importance = max(importance, original_importance)
        
        # 이전 블록 인덱스 확인 (전체 블록 개수)
        last_block_index = self._get_last_block_index()
        new_block_index = last_block_index + 1 if last_block_index is not None else 0
        
        # 마지막 블록의 해시 가져오기
        prev_hash = ""
        if last_block_index is not None:
            last_block = self.db_manager.get_block(last_block_index)
            if last_block:
                prev_hash = last_block.get("hash", "")
        
        # 새 블록 데이터 준비
        block_data = {
            "block_index": new_block_index,
            "timestamp": datetime.now().isoformat(),
            "context": new_context,
            "keywords": final_keywords,
            "tags": final_tags,
            "embedding": final_embedding,
            "importance": final_importance,
            "prev_hash": prev_hash,
            "hash": "",  # 임시 (db_manager에서 계산)
            "metadata": revision_metadata
        }
        
        # 블록 해시 계산 추가 (필요시)
        try:
            from hashlib import sha256
            import json
            
            # 해시 계산에서 제외할 필드
            hash_data = block_data.copy()
            hash_data.pop("hash", None)
            
            # 정렬된 문자열로 변환하여 해시 계산
            block_str = json.dumps(hash_data, sort_keys=True)
            block_data["hash"] = sha256(block_str.encode('utf-8')).hexdigest()
        except ImportError:
            # 해시 계산 모듈 없는 경우 빈 해시
            pass
        
        # 데이터베이스에 새 블록 추가
        try:
            block_index = self.db_manager.add_block(block_data)
            return self.db_manager.get_block(block_index)
        except Exception as e:
            print(f"블록 추가 중 오류 발생: {e}")
            return None
    
    def _get_next_revision_number(self, original_block_index: int) -> int:
        """
        다음 수정 번호 가져오기
        
        Args:
            original_block_index: 원본 블록 인덱스
            
        Returns:
            다음 수정 번호 (1부터 시작)
        """
        revisions = self.get_revision_chain(original_block_index)
        return len(revisions) + 1
    
    def _get_last_block_index(self) -> Optional[int]:
        """
        마지막 블록 인덱스 가져오기
        
        Returns:
            마지막 블록 인덱스 (없으면 None)
        """
        if not self.db_manager:
            return None
            
        # 간단한 방법 - 최근 블록 1개만 가져와서 인덱스 확인
        blocks = self.db_manager.get_blocks(limit=1, sort_by='block_index', order='desc')
        if not blocks:
            return None
            
        return blocks[0].get("block_index")
    
    def get_revision_chain(self, block_index: int) -> List[Dict[str, Any]]:
        """
        블록의 수정 이력 체인 가져오기
        
        Args:
            block_index: 블록 인덱스
            
        Returns:
            관련된 모든 수정 블록 체인 (시간순 정렬)
        """
        if not self.db_manager:
            return []
        
        revisions = []
        
        # 현재 블록 정보
        current_block = self.db_manager.get_block(block_index)
        if not current_block:
            return []
        
        # 메타데이터 추출
        metadata = current_block.get("metadata", {})
        
        # 현재 블록이 수정본인 경우
        original_index = metadata.get("original_block_index")
        
        if original_index is not None:
            # 1. 원본 블록
            original = self.db_manager.get_block(original_index)
            if original:
                revisions.append(original)
            
            # 2. 다른 수정본들 (같은 원본을 가진)
            similar_revisions = self._find_revisions_by_original(original_index)
            
            # 자기 자신 제외하고 추가
            for rev in similar_revisions:
                if rev.get("block_index") != block_index:
                    revisions.append(rev)
                    
            # 3. 현재 블록 추가
            revisions.append(current_block)
        else:
            # 현재 블록이 원본인 경우
            # 1. 현재 블록 (원본) 추가
            revisions.append(current_block)
            
            # 2. 이 블록의 모든 수정본 추가
            revisions.extend(self._find_revisions_by_original(block_index))
        
        # 시간순 정렬
        revisions.sort(key=lambda x: x.get("timestamp", ""))
        
        return revisions
    
    def _find_revisions_by_original(self, original_index: int) -> List[Dict[str, Any]]:
        """
        원본 인덱스로 수정본 검색
        
        Args:
            original_index: 원본 블록 인덱스
            
        Returns:
            해당 원본의 모든 수정본
        """
        if not self.db_manager:
            return []
            
        # 데이터베이스 검색 기능이 있다면 활용
        if hasattr(self.db_manager, "search_blocks_by_metadata_field"):
            return self.db_manager.search_blocks_by_metadata_field(
                "original_block_index", original_index
            )
        
        # 없으면 모든 블록을 가져와서 필터링 (비효율적)
        all_blocks = self.db_manager.get_blocks(limit=1000)  # 제한 설정 필요
        
        revisions = []
        for block in all_blocks:
            metadata = block.get("metadata", {})
            if metadata.get("original_block_index") == original_index:
                revisions.append(block)
                
        return revisions
    
    def get_revision_diff(self, original_index: int, revision_index: int) -> Dict[str, Any]:
        """
        원본과 수정본의 차이점 계산
        
        Args:
            original_index: 원본 블록 인덱스
            revision_index: 수정본 블록 인덱스
            
        Returns:
            차이점 정보
        """
        if not self.db_manager:
            return {"error": "데이터베이스 관리자가 설정되지 않았습니다."}
            
        # 블록 가져오기
        original = self.db_manager.get_block(original_index)
        revision = self.db_manager.get_block(revision_index)
        
        if not original or not revision:
            return {
                "error": "원본 또는 수정본 블록을 찾을 수 없습니다.",
                "original_exists": original is not None,
                "revision_exists": revision is not None
            }
            
        # 텍스트 차이 계산 (간단한 비교)
        orig_text = original.get("context", "")
        rev_text = revision.get("context", "")
        
        # 키워드/태그 차이 계산
        orig_keywords = set(original.get("keywords", []))
        rev_keywords = set(revision.get("keywords", []))
        
        orig_tags = set(original.get("tags", []))
        rev_tags = set(revision.get("tags", []))
        
        # 중요도 변화
        orig_importance = original.get("importance", 0)
        rev_importance = revision.get("importance", 0)
        
        # 타임스탬프 추출
        try:
            orig_time = datetime.fromisoformat(original.get("timestamp", ""))
            rev_time = datetime.fromisoformat(revision.get("timestamp", ""))
            time_diff = rev_time - orig_time
            time_diff_days = time_diff.days
        except ValueError:
            time_diff_days = None
        
        return {
            "original_index": original_index,
            "revision_index": revision_index,
            "time_diff_days": time_diff_days,
            "context_changed": orig_text != rev_text,
            "keywords_added": list(rev_keywords - orig_keywords),
            "keywords_removed": list(orig_keywords - rev_keywords),
            "tags_added": list(rev_tags - orig_tags),
            "tags_removed": list(orig_tags - rev_tags),
            "importance_change": rev_importance - orig_importance,
            "revision_reason": revision.get("metadata", {}).get("revision_reason", "")
        }
    
    def merge_revisions(self, block_indices: List[int], merge_reason: str) -> Optional[Dict[str, Any]]:
        """
        여러 수정본을 병합하여 새 블록 생성
        
        Args:
            block_indices: 병합할 블록 인덱스 목록
            merge_reason: 병합 이유
            
        Returns:
            병합된 새 블록 (실패 시 None)
        """
        if not self.db_manager or len(block_indices) < 2:
            return None
            
        # 블록 가져오기
        blocks = []
        for idx in block_indices:
            block = self.db_manager.get_block(idx)
            if block:
                blocks.append(block)
                
        if not blocks or len(blocks) < 2:
            return None
            
        # 가장 최근 블록을 기준으로 사용
        blocks.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        latest_block = blocks[0]
        
        # 원본 블록 정보 확인
        original_indices = set()
        for block in blocks:
            metadata = block.get("metadata", {})
            original_idx = metadata.get("original_block_index")
            if original_idx is not None:
                original_indices.add(original_idx)
            else:
                original_indices.add(block.get("block_index"))
                
        # 병합된 컨텍스트 생성 (간단한 방법: 최신 블록 사용)
        merged_context = latest_block.get("context", "")
        
        # 모든 키워드/태그 병합
        all_keywords = set()
        all_tags = set()
        
        for block in blocks:
            all_keywords.update(block.get("keywords", []))
            all_tags.update(block.get("tags", []))
            
        # 중요도는 최대값 사용
        max_importance = max(block.get("importance", 0) for block in blocks)
        
        # 수정 메타데이터 생성
        revision_metadata = {
            "revision_type": "merge",
            "revision_reason": merge_reason,
            "revision_timestamp": datetime.now().isoformat(),
            "merged_block_indices": block_indices,
            "original_block_indices": list(original_indices)
        }
        
        # 태그에 병합 표시 추가
        if "merged" not in all_tags:
            all_tags.add("merged")
        if "revision" not in all_tags:
            all_tags.add("revision")
        
        # 임베딩은 최신 블록의 것 사용
        embedding = latest_block.get("embedding", [])
        
        # 최신 블록의 원본 인덱스를 사용 (있는 경우)
        latest_metadata = latest_block.get("metadata", {})
        primary_original = latest_metadata.get("original_block_index", latest_block.get("block_index"))
        
        # 수정본 생성
        return self.create_memory_revision(
            original_block_index=primary_original,
            new_context=merged_context,
            reason=merge_reason,
            keywords=list(all_keywords),
            tags=list(all_tags),
            embedding=embedding,
            importance=max_importance
        )
        
    def create_contradiction_note(self, block_indices: List[int], 
                                 note: str) -> Optional[Dict[str, Any]]:
        """
        상충되는 기억들에 대한 해석 노트 추가
        
        Args:
            block_indices: 상충되는 블록 인덱스 목록
            note: 상충 내용 해석 노트
            
        Returns:
            생성된 노트 블록 (실패 시 None)
        """
        if not self.db_manager or not block_indices:
            return None
            
        # 블록 가져오기
        blocks = []
        for idx in block_indices:
            block = self.db_manager.get_block(idx)
            if block:
                blocks.append(block)
                
        if not blocks:
            return None
            
        # 가장 최근 블록 선택
        blocks.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        latest_block = blocks[0]
        
        # 키워드/태그 병합
        all_keywords = set()
        all_tags = set()
        
        for block in blocks:
            all_keywords.update(block.get("keywords", []))
            all_tags.update(block.get("tags", []))
            
        # 상충 태그 추가
        if "contradiction" not in all_tags:
            all_tags.add("contradiction")
        if "note" not in all_tags:
            all_tags.add("note")
        
        # 상충 노트 메타데이터
        note_metadata = {
            "note_type": "contradiction",
            "referenced_block_indices": block_indices,
            "timestamp": datetime.now().isoformat()
        }
        
        # 중요도는 평균보다 약간 높게
        avg_importance = sum(block.get("importance", 0) for block in blocks) / len(blocks)
        note_importance = min(1.0, avg_importance * 1.2)  # 20% 증가 (최대 1.0)
        
        # 이전 블록 인덱스 확인 (전체 블록 개수)
        last_block_index = self._get_last_block_index()
        new_block_index = last_block_index + 1 if last_block_index is not None else 0
        
        # 마지막 블록의 해시 가져오기
        prev_hash = ""
        if last_block_index is not None:
            last_block = self.db_manager.get_block(last_block_index)
            if last_block:
                prev_hash = last_block.get("hash", "")
        
        # 새 블록 데이터 준비
        block_data = {
            "block_index": new_block_index,
            "timestamp": datetime.now().isoformat(),
            "context": note,
            "keywords": list(all_keywords),
            "tags": list(all_tags),
            "embedding": latest_block.get("embedding", []),  # 임시로 최신 블록 임베딩 사용
            "importance": note_importance,
            "prev_hash": prev_hash,
            "hash": "",  # 임시 (db_manager에서 계산)
            "metadata": note_metadata
        }
        
        # 블록 해시 계산 추가 (필요시)
        try:
            from hashlib import sha256
            import json
            
            # 해시 계산에서 제외할 필드
            hash_data = block_data.copy()
            hash_data.pop("hash", None)
            
            # 정렬된 문자열로 변환하여 해시 계산
            block_str = json.dumps(hash_data, sort_keys=True)
            block_data["hash"] = sha256(block_str.encode('utf-8')).hexdigest()
        except ImportError:
            # 해시 계산 모듈 없는 경우 빈 해시
            pass
            
        # 데이터베이스에 새 블록 추가
        try:
            block_index = self.db_manager.add_block(block_data)
            return self.db_manager.get_block(block_index)
        except Exception as e:
            print(f"블록 추가 중 오류 발생: {e}")
            return None
    
    def summarize_blocks(self, block_indices: List[int], summary_reason: str = "auto_summary") -> Optional[Dict[str, Any]]:
        """여러 블록을 요약해 하나의 요약 블록을 생성한다 (간단 heuristic).
        Args:
            block_indices: 요약 대상 블록 ids
            summary_reason: metadata reason
        Returns: 새 요약 블록 dict
        """
        if not self.db_manager or not block_indices:
            return None
        # 컨텍스트 연결 후 앞 120자만 유지 (간단 요약)
        contexts = []
        for idx in block_indices:
            b = self.db_manager.get_block(idx)
            if b:
                contexts.append(b.get("context", ""))
        if not contexts:
            return None
        merged_context = " ".join(contexts)
        summary_text = merged_context[:120] + ("…" if len(merged_context) > 120 else "")
        # 키워드/태그 재추출
        keywords = extract_keywords_advanced(summary_text, max_keywords=5)
        tags = ["summary"]
        embedding = generate_simple_embedding(summary_text)
        importance = calculate_importance(summary_text)
        return self.create_memory_revision(
            original_block_index=block_indices[0],
            new_context=summary_text,
            reason=summary_reason,
            keywords=keywords,
            tags=tags,
            embedding=embedding,
            importance=importance,
        ) 