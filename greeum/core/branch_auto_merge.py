"""
Auto-Merge System for Branch-based Memory
브랜치 자동 머지 시스템 (PR#3)
"""

import time
import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class MergeProposal:
    """머지 제안"""
    slot_i: str
    slot_j: str
    checkpoint_id: str
    score: float
    ema: float
    reason: Dict[str, Any]
    created_at: float = field(default_factory=time.time)
    reversible: bool = True

@dataclass
class MergeHistory:
    """머지 이력"""
    checkpoint_id: str
    original_heads: Dict[str, str]  # slot -> original_head
    merged_at: float
    reverted_at: Optional[float] = None

class AutoMergeEngine:
    """자동 머지 엔진"""
    
    # 최적화된 설정값 (Phase 2)
    ALPHA = 0.8  # 0.7→0.8: 더 빠른 EMA 학습
    THETA_HIGH = 0.65  # 0.75→0.65: 더 관대한 머지 임계값
    R = 3  # 5→3: 더 짧은 평가 윈도우
    M = 2  # 3→2: 더 빠른 머지 결정
    COOLDOWN = 15 * 60  # 30→15분: 더 짧은 휴지기
    DIVERGENCE_MAX = 5  # 4→5: 더 관대한 발산도
    N_MIN = 2  # 3→2: 더 빠른 머지 시작
    
    # 스코어 가중치
    W1 = 0.4  # 헤드 유사도
    W2 = 0.3  # 중심점 유사도
    W3 = 0.2  # 태그 Jaccard
    W4 = 0.1  # 시간 근접성
    W5 = 0.05  # 발산도 페널티
    
    def __init__(self, branch_manager):
        self.branch_manager = branch_manager
        
        # 상태 추적
        self.ema_scores: Dict[Tuple[str, str], float] = {}  # (slot_i, slot_j) -> EMA
        self.evaluation_history: Dict[Tuple[str, str], List[float]] = {}  # 평가 이력
        self.merge_history: List[MergeHistory] = []
        self.last_merge_time = 0
        
        # 통계
        self.stats = {
            'merge_suggested': 0,
            'merge_accepted': 0,
            'merge_reverted': 0,
            'false_positive_rate': 0.0
        }
        
    def evaluate_auto_merge(self, active_slots: List[str] = None) -> List[MergeProposal]:
        """
        자동 머지 평가
        
        Args:
            active_slots: 평가할 슬롯들 (기본: A, B, C)
            
        Returns:
            List of merge proposals
        """
        if active_slots is None:
            active_slots = ["A", "B", "C"]
            
        # 휴지기 확인
        if time.time() - self.last_merge_time < self.COOLDOWN:
            logger.debug(f"Auto-merge in cooldown period")
            return []
            
        proposals = []
        
        # 활성 슬롯 헤드 쌍 평가
        for i, slot_i in enumerate(active_slots):
            for slot_j in active_slots[i+1:]:
                head_i = self.branch_manager.stm_slots.get(slot_i)
                head_j = self.branch_manager.stm_slots.get(slot_j)
                
                if not head_i or not head_j or head_i not in self.branch_manager.blocks or head_j not in self.branch_manager.blocks:
                    continue
                    
                block_i = self.branch_manager.blocks[head_i]
                block_j = self.branch_manager.blocks[head_j]
                
                # 같은 루트만 머지 가능
                if block_i.root != block_j.root:
                    continue
                    
                # 최소 노드 수 확인
                branch_size = self.branch_manager.branches[block_i.root].size
                if branch_size < self.N_MIN:
                    continue
                    
                # 머지 스코어 계산
                score = self._calculate_merge_score(block_i, block_j)
                
                # EMA 업데이트
                pair_key = (slot_i, slot_j)
                old_ema = self.ema_scores.get(pair_key, 0.0)
                new_ema = self.ALPHA * old_ema + (1 - self.ALPHA) * score
                self.ema_scores[pair_key] = new_ema
                
                # 평가 이력 업데이트
                if pair_key not in self.evaluation_history:
                    self.evaluation_history[pair_key] = []
                self.evaluation_history[pair_key].append(score)
                
                # 최근 R회 이력 유지
                if len(self.evaluation_history[pair_key]) > self.R:
                    self.evaluation_history[pair_key] = self.evaluation_history[pair_key][-self.R:]
                    
                # 히스테리시스 확인
                if self._check_hysteresis(pair_key, new_ema):
                    proposal = self._create_merge_proposal(slot_i, slot_j, block_i, block_j, score, new_ema)
                    if proposal:
                        proposals.append(proposal)
                        
        return proposals
    
    def _calculate_merge_score(self, block_i, block_j) -> float:
        """
        머지 스코어 계산
        MS = w1*cos(head_i, head_j) + w2*cos(centroid_i, centroid_j) + w3*Jaccard + w4*exp(-Δt/τ) - w5*divergence
        """
        # 1) 헤드 유사도 (내용 기반)
        cos_heads = self._content_similarity(
            block_i.content.get('text', ''),
            block_j.content.get('text', '')
        )
        
        # 2) 중심점 유사도 (브랜치 중심점)
        centroid_i = self._calculate_branch_centroid(block_i.root, block_i.id)
        centroid_j = self._calculate_branch_centroid(block_j.root, block_j.id)
        cos_centroids = self._vector_similarity(centroid_i, centroid_j) if centroid_i is not None and centroid_j is not None else 0
        
        # 3) 태그 Jaccard 유사도
        tags_i = set(block_i.tags.get('labels', []))
        tags_j = set(block_j.tags.get('labels', []))
        jaccard = len(tags_i & tags_j) / max(len(tags_i | tags_j), 1)
        
        # 4) 시간 근접성
        time_diff = abs(block_i.created_at - block_j.created_at)
        time_similarity = np.exp(-time_diff / (7 * 24 * 3600))  # 1주일 반감기
        
        # 5) 발산도 페널티
        divergence = self._calculate_divergence(block_i, block_j)
        
        # 6) Opposition 감점 (부정/반전 신호)
        opposition = self._detect_opposition(block_i, block_j)
        
        # 최종 스코어
        score = (
            self.W1 * cos_heads +
            self.W2 * cos_centroids +
            self.W3 * jaccard +
            self.W4 * time_similarity -
            self.W5 * (divergence / self.DIVERGENCE_MAX) -
            0.1 * opposition
        )
        
        return max(0.0, score)  # 음수 방지
    
    def _check_hysteresis(self, pair_key: Tuple[str, str], ema: float) -> bool:
        """히스테리시스 조건 확인"""
        if ema < self.THETA_HIGH:
            return False
            
        # 최근 R회 중 M회 이상 충족 확인
        history = self.evaluation_history.get(pair_key, [])
        if len(history) < self.M:
            return False
            
        recent_high_count = sum(1 for score in history[-self.R:] if score >= self.THETA_HIGH)
        return recent_high_count >= self.M
    
    def _create_merge_proposal(self, slot_i: str, slot_j: str, 
                             block_i, block_j, score: float, ema: float) -> Optional[MergeProposal]:
        """머지 제안 생성"""
        # 체크포인트 생성 (소프트 머지)
        lca = self._find_lca(block_i, block_j)
        if not lca:
            return None
            
        checkpoint_id = str(uuid.uuid4())
        
        return MergeProposal(
            slot_i=slot_i,
            slot_j=slot_j,
            checkpoint_id=checkpoint_id,
            score=score,
            ema=ema,
            reason={
                'head_similarity': self._content_similarity(
                    block_i.content.get('text', ''),
                    block_j.content.get('text', '')
                ),
                'jaccard_similarity': len(set(block_i.tags.get('labels', [])) & set(block_j.tags.get('labels', []))) / max(len(set(block_i.tags.get('labels', [])) | set(block_j.tags.get('labels', []))), 1),
                'divergence': self._calculate_divergence(block_i, block_j),
                'lca': lca.id if lca else None
            }
        )
    
    def apply_merge(self, proposal: MergeProposal, dry_run: bool = False) -> Dict[str, Any]:
        """
        머지 적용
        
        Args:
            proposal: 머지 제안
            dry_run: 실제 적용 없이 시뮬레이션
            
        Returns:
            결과 딕셔너리
        """
        if dry_run:
            return {
                'success': True,
                'checkpoint_id': proposal.checkpoint_id,
                'reversible': proposal.reversible,
                'reason': proposal.reason
            }
            
        # 실제 머지 수행
        head_i = self.branch_manager.stm_slots.get(proposal.slot_i)
        head_j = self.branch_manager.stm_slots.get(proposal.slot_j)
        
        if not head_i or not head_j:
            return {'success': False, 'error': 'Invalid slots'}
            
        block_i = self.branch_manager.blocks.get(head_i)
        block_j = self.branch_manager.blocks.get(head_j)
        
        if not block_i or not block_j:
            return {'success': False, 'error': 'Invalid blocks'}
            
        # LCA 찾기
        lca = self._find_lca(block_i, block_j)
        
        # 체크포인트 노드 생성
        from .branch_manager import BranchBlock
        checkpoint = BranchBlock(
            id=proposal.checkpoint_id,
            root=block_i.root,
            before=lca.id if lca else None,
            after=[head_i, head_j],
            content={'text': f'Merge checkpoint: {proposal.slot_i} + {proposal.slot_j}', 'type': 'checkpoint'},
            tags={'merge': True, 'slots': [proposal.slot_i, proposal.slot_j]},
            stats={'importance': max(block_i.stats.get('importance', 0), block_j.stats.get('importance', 0))}
        )
        
        # 블록 저장
        self.branch_manager.blocks[checkpoint.id] = checkpoint
        
        # LCA의 after에 추가
        if lca and lca.id in self.branch_manager.blocks:
            self.branch_manager.blocks[lca.id].after.append(checkpoint.id)
            
        # 선택된 슬롯을 체크포인트로 이동 (여기서는 slot_i 선택)
        original_heads = {
            proposal.slot_i: head_i,
            proposal.slot_j: head_j
        }
        
        self.branch_manager.update_stm_slot(proposal.slot_i, checkpoint.id)
        
        # 머지 이력 저장
        history = MergeHistory(
            checkpoint_id=checkpoint.id,
            original_heads=original_heads,
            merged_at=time.time()
        )
        self.merge_history.append(history)
        self.last_merge_time = time.time()
        
        # 통계 업데이트
        self.stats['merge_suggested'] += 1
        self.stats['merge_accepted'] += 1
        
        logger.info(f"Applied soft merge: {proposal.slot_i} + {proposal.slot_j} -> checkpoint {checkpoint.id}")
        
        return {
            'success': True,
            'checkpoint_id': checkpoint.id,
            'reversible': True,
            'reason': proposal.reason,
            'original_heads': original_heads
        }
    
    def revert_merge(self, checkpoint_id: str) -> Dict[str, Any]:
        """머지 되돌리기 (소프트 머지만 가능)"""
        # 머지 이력 찾기
        history = None
        for h in self.merge_history:
            if h.checkpoint_id == checkpoint_id and h.reverted_at is None:
                history = h
                break
                
        if not history:
            return {'success': False, 'error': 'Merge history not found'}
            
        # 체크포인트 제거
        if checkpoint_id in self.branch_manager.blocks:
            checkpoint = self.branch_manager.blocks[checkpoint_id]
            
            # 부모의 after에서 제거
            if checkpoint.before and checkpoint.before in self.branch_manager.blocks:
                parent = self.branch_manager.blocks[checkpoint.before]
                if checkpoint_id in parent.after:
                    parent.after.remove(checkpoint_id)
                    
            # 블록 제거
            del self.branch_manager.blocks[checkpoint_id]
            
        # 원래 헤드로 복원
        for slot, original_head in history.original_heads.items():
            self.branch_manager.update_stm_slot(slot, original_head)
            
        # 이력 업데이트
        history.reverted_at = time.time()
        self.stats['merge_reverted'] += 1
        
        logger.info(f"Reverted merge: checkpoint {checkpoint_id}")
        
        return {
            'success': True,
            'reverted_at': history.reverted_at,
            'restored_heads': history.original_heads
        }
    
    def _content_similarity(self, text1: str, text2: str) -> float:
        """내용 유사도 (간이 구현)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_branch_centroid(self, root: str, exclude_id: str = None) -> Optional[np.ndarray]:
        """브랜치 중심점 계산 (간이 구현)"""
        # TODO: 실제 벡터 기반 중심점 계산
        return None
    
    def _vector_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """벡터 유사도"""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def _calculate_divergence(self, block_i, block_j) -> float:
        """발산도 계산 (LCA 거리 + 깊이 차)"""
        lca = self._find_lca(block_i, block_j)
        if not lca:
            return self.DIVERGENCE_MAX
            
        depth_i = self._calculate_depth_from_lca(block_i, lca)
        depth_j = self._calculate_depth_from_lca(block_j, lca)
        
        return depth_i + depth_j + abs(depth_i - depth_j)
    
    def _detect_opposition(self, block_i, block_j) -> float:
        """부정/반전 신호 감지"""
        text_i = block_i.content.get('text', '').lower()
        text_j = block_j.content.get('text', '').lower()
        
        # 간단한 부정어 감지
        negatives = ['not', '아니', '안', '못', '없', 'no', 'never']
        
        neg_i = any(neg in text_i for neg in negatives)
        neg_j = any(neg in text_j for neg in negatives)
        
        # 하나는 긍정, 하나는 부정인 경우
        if neg_i != neg_j:
            return 1.0
            
        return 0.0
    
    def _find_lca(self, block_i, block_j):
        """최근 공통 조상 찾기"""
        # 간단한 구현: 같은 루트의 첫 번째 노드를 LCA로 가정
        if block_i.root != block_j.root:
            return None
            
        # 브랜치의 루트 노드를 찾아 반환
        for block in self.branch_manager.blocks.values():
            if block.root == block_i.root and block.before is None:
                return block
                
        return block_i  # fallback
    
    def _calculate_depth_from_lca(self, block, lca) -> int:
        """LCA로부터의 깊이"""
        depth = 0
        current = block
        
        while current and current.id != lca.id and depth < 100:
            if current.before and current.before in self.branch_manager.blocks:
                current = self.branch_manager.blocks[current.before]
                depth += 1
            else:
                break
                
        return depth
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        stats = self.stats.copy()
        if stats['merge_suggested'] > 0:
            stats['false_positive_rate'] = stats['merge_reverted'] / stats['merge_suggested']
        return stats
