"""
Memory Layer Interface for Greeum v2.6.0 Hierarchical Memory Architecture

Defines abstract interfaces for STM, LTM, and Working Memory layers
with clear separation of concerns and standardized communication protocols.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class MemoryLayerType(Enum):
    """메모리 계층 유형"""
    WORKING = "working"    # 임시 작업 공간 (AI Context Slots)
    STM = "stm"           # 단기 기억 (TTL 기반 세션 메모리)
    LTM = "ltm"           # 장기 기억 (영구 보존 블록체인 구조)


class MemoryPriority(Enum):
    """메모리 우선순위"""
    CRITICAL = 1.0    # 절대 삭제되지 않음
    HIGH = 0.8        # 높은 보존 우선순위
    MEDIUM = 0.6      # 중간 우선순위
    LOW = 0.4         # 낮은 우선순위
    DISPOSABLE = 0.2  # 언제든 삭제 가능


@dataclass
class MemoryItem:
    """통합 메모리 항목"""
    id: str
    content: str
    timestamp: datetime
    layer: MemoryLayerType
    priority: MemoryPriority
    metadata: Dict[str, Any]
    keywords: List[str] = None
    tags: List[str] = None
    embedding: List[float] = None
    importance: float = 0.5
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.tags is None:
            self.tags = []
        if self.embedding is None:
            self.embedding = []


@dataclass
class LayerTransferRequest:
    """계층 간 전송 요청"""
    source_layer: MemoryLayerType
    target_layer: MemoryLayerType
    memory_id: str
    reason: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MemoryLayerInterface(ABC):
    """메모리 계층 추상 인터페이스"""
    
    def __init__(self, layer_type: MemoryLayerType):
        self.layer_type = layer_type
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """계층 초기화"""
        pass
    
    @abstractmethod
    def add_memory(self, memory_item: MemoryItem) -> str:
        """메모리 추가"""
        pass
    
    @abstractmethod
    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """특정 메모리 조회"""
        pass
    
    @abstractmethod
    def search_memories(self, query: str, limit: int = 10, 
                       filters: Dict[str, Any] = None) -> List[MemoryItem]:
        """메모리 검색"""
        pass
    
    @abstractmethod
    def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """메모리 업데이트"""
        pass
    
    @abstractmethod
    def delete_memory(self, memory_id: str) -> bool:
        """메모리 삭제"""
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """만료된 메모리 정리"""
        pass
    
    @abstractmethod
    def get_layer_stats(self) -> Dict[str, Any]:
        """계층 통계 정보"""
        pass
    
    @abstractmethod
    def can_accept_transfer(self, transfer_request: LayerTransferRequest) -> bool:
        """다른 계층으로부터의 전송 요청 수락 가능 여부"""
        pass
    
    @abstractmethod
    def transfer_to_layer(self, transfer_request: LayerTransferRequest) -> bool:
        """다른 계층으로 메모리 전송"""
        pass


class MemoryLayerManager:
    """메모리 계층 관리자 - 계층 간 통신과 전송을 조정"""
    
    def __init__(self):
        self.layers: Dict[MemoryLayerType, MemoryLayerInterface] = {}
        self.transfer_history: List[LayerTransferRequest] = []
        
    def register_layer(self, layer: MemoryLayerInterface) -> bool:
        """메모리 계층 등록"""
        try:
            if not layer.initialize():
                return False
                
            self.layers[layer.layer_type] = layer
            return True
        except Exception as e:
            print(f"Layer registration failed: {e}")
            return False
    
    def get_layer(self, layer_type: MemoryLayerType) -> Optional[MemoryLayerInterface]:
        """특정 계층 조회"""
        return self.layers.get(layer_type)
    
    def transfer_memory(self, transfer_request: LayerTransferRequest) -> bool:
        """계층 간 메모리 전송 조정"""
        source_layer = self.layers.get(transfer_request.source_layer)
        target_layer = self.layers.get(transfer_request.target_layer)
        
        if not source_layer or not target_layer:
            return False
        
        # 대상 계층이 전송을 수락할 수 있는지 확인
        if not target_layer.can_accept_transfer(transfer_request):
            return False
        
        try:
            # 원본 메모리 조회
            memory_item = source_layer.get_memory(transfer_request.memory_id)
            if not memory_item:
                return False
            
            # 계층 정보 업데이트
            memory_item.layer = transfer_request.target_layer
            memory_item.metadata.update(transfer_request.metadata)
            
            # 대상 계층에 추가
            new_id = target_layer.add_memory(memory_item)
            if not new_id:
                return False
            
            # 원본에서 삭제 (Working → STM → LTM 승격의 경우)
            if self._should_remove_from_source(transfer_request):
                source_layer.delete_memory(transfer_request.memory_id)
            
            # 전송 이력 기록
            transfer_request.metadata['new_id'] = new_id
            self.transfer_history.append(transfer_request)
            
            return True
            
        except Exception as e:
            print(f"Memory transfer failed: {e}")
            return False
    
    def _should_remove_from_source(self, transfer_request: LayerTransferRequest) -> bool:
        """원본 계층에서 메모리를 삭제해야 하는지 판단"""
        # Working → STM, STM → LTM 승격의 경우 원본 삭제
        upgrade_paths = [
            (MemoryLayerType.WORKING, MemoryLayerType.STM),
            (MemoryLayerType.STM, MemoryLayerType.LTM),
            (MemoryLayerType.WORKING, MemoryLayerType.LTM)  # 직접 승격
        ]
        
        return (transfer_request.source_layer, transfer_request.target_layer) in upgrade_paths
    
    def suggest_memory_promotion(self, memory_item: MemoryItem) -> Optional[LayerTransferRequest]:
        """메모리 승격 제안"""
        current_layer = memory_item.layer
        
        # Working → STM 승격 조건
        if current_layer == MemoryLayerType.WORKING:
            if (memory_item.priority.value >= MemoryPriority.MEDIUM.value and 
                len(memory_item.content) > 50):
                return LayerTransferRequest(
                    source_layer=MemoryLayerType.WORKING,
                    target_layer=MemoryLayerType.STM,
                    memory_id=memory_item.id,
                    reason="High priority working memory with substantial content",
                    confidence=0.8
                )
        
        # STM → LTM 승격 조건
        elif current_layer == MemoryLayerType.STM:
            if (memory_item.priority.value >= MemoryPriority.HIGH.value and
                memory_item.importance >= 0.7):
                return LayerTransferRequest(
                    source_layer=MemoryLayerType.STM,
                    target_layer=MemoryLayerType.LTM,
                    memory_id=memory_item.id,
                    reason="High importance STM qualified for permanent storage",
                    confidence=0.9
                )
        
        return None
    
    def get_unified_search_results(self, query: str, limit: int = 10, 
                                 layer_preferences: List[MemoryLayerType] = None) -> List[MemoryItem]:
        """모든 계층에서 통합 검색"""
        if layer_preferences is None:
            layer_preferences = [MemoryLayerType.WORKING, MemoryLayerType.STM, MemoryLayerType.LTM]
        
        all_results = []
        
        for layer_type in layer_preferences:
            layer = self.layers.get(layer_type)
            if layer:
                try:
                    results = layer.search_memories(query, limit)
                    all_results.extend(results)
                except Exception as e:
                    print(f"Search failed in {layer_type}: {e}")
        
        # 우선순위와 관련성으로 정렬
        all_results.sort(key=lambda x: (x.priority.value, x.importance), reverse=True)
        
        return all_results[:limit]
    
    def get_system_overview(self) -> Dict[str, Any]:
        """전체 메모리 시스템 개요"""
        overview = {
            "layers": {},
            "total_memories": 0,
            "transfer_history_count": len(self.transfer_history)
        }
        
        for layer_type, layer in self.layers.items():
            try:
                stats = layer.get_layer_stats()
                overview["layers"][layer_type.value] = stats
                overview["total_memories"] += stats.get("total_count", 0)
            except Exception as e:
                overview["layers"][layer_type.value] = {"error": str(e)}
        
        return overview


# 유틸리티 함수들
def create_memory_item(content: str, layer: MemoryLayerType, 
                      priority: MemoryPriority = MemoryPriority.MEDIUM,
                      **kwargs) -> MemoryItem:
    """메모리 항목 생성 헬퍼"""
    import uuid
    
    return MemoryItem(
        id=str(uuid.uuid4()),
        content=content,
        timestamp=datetime.now(),
        layer=layer,
        priority=priority,
        metadata=kwargs.get('metadata', {}),
        keywords=kwargs.get('keywords', []),
        tags=kwargs.get('tags', []),
        embedding=kwargs.get('embedding', []),
        importance=kwargs.get('importance', 0.5)
    )


def memory_item_from_legacy(legacy_data: Dict[str, Any], 
                           target_layer: MemoryLayerType) -> MemoryItem:
    """레거시 데이터에서 메모리 항목 변환"""
    return MemoryItem(
        id=str(legacy_data.get('id', legacy_data.get('block_index', 'unknown'))),
        content=legacy_data.get('content', legacy_data.get('context', '')),
        timestamp=datetime.fromisoformat(legacy_data.get('timestamp', datetime.now().isoformat())),
        layer=target_layer,
        priority=MemoryPriority.MEDIUM,
        metadata=legacy_data.get('metadata', {}),
        keywords=legacy_data.get('keywords', []),
        tags=legacy_data.get('tags', []),
        embedding=legacy_data.get('embedding', []),
        importance=legacy_data.get('importance', 0.5)
    )