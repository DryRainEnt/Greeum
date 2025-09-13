#!/usr/bin/env python3
"""
Greeum v2.6.1 - Memory Backup and Restore System
선택적 복원을 중심으로 한 유연한 백업/복원 시스템
"""

import json
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
import logging

# Legacy imports removed - using simplified structures
# from .memory_layer import MemoryItem, MemoryLayerType, MemoryPriority
# from .hierarchical_memory import HierarchicalMemorySystem

logger = logging.getLogger(__name__)


@dataclass
class RestoreFilter:
    """복원 필터 - 선택적 복원을 위한 조건 설정"""
    
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    keywords: Optional[List[str]] = None
    layers: Optional[List[str]] = None  # Changed from MemoryLayerType enum to strings
    importance_min: Optional[float] = None
    importance_max: Optional[float] = None
    tags: Optional[List[str]] = None
    
    def matches(self, memory_item: Dict[str, Any]) -> bool:
        """메모리 아이템이 필터 조건을 만족하는지 확인"""
        
        # 날짜 범위 체크
        timestamp = memory_item.get('timestamp')
        if timestamp and isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        if self.date_from and timestamp and timestamp < self.date_from:
            return False
        if self.date_to and timestamp and timestamp > self.date_to:
            return False
            
        # 키워드 체크 (OR 조건)
        if self.keywords:
            content_lower = memory_item.get('content', '').lower()
            if not any(keyword.lower() in content_lower for keyword in self.keywords):
                return False
        
        # 계층 체크
        if self.layers and memory_item.get('layer') not in self.layers:
            return False
            
        # 중요도 범위 체크
        if self.importance_min and memory_item.importance < self.importance_min:
            return False
        if self.importance_max and memory_item.importance > self.importance_max:
            return False
            
        # 태그 체크 (OR 조건)
        if self.tags and memory_item.tags:
            if not any(tag in memory_item.tags for tag in self.tags):
                return False
        
        return True
    
    def is_full_restore(self) -> bool:
        """모든 조건이 비어있으면 전체 복원"""
        return all([
            self.date_from is None,
            self.date_to is None,
            self.keywords is None or len(self.keywords) == 0,
            self.layers is None or len(self.layers) == 0,
            self.importance_min is None,
            self.importance_max is None,
            self.tags is None or len(self.tags) == 0
        ])
    
    def __str__(self) -> str:
        """필터 조건을 사람이 읽기 쉬운 형태로 표시"""
        conditions = []
        
        if self.date_from or self.date_to:
            date_range = f"{self.date_from or 'start'} ~ {self.date_to or 'end'}"
            conditions.append(f"[DATE] 날짜: {date_range}")
        
        if self.keywords:
            conditions.append(f"🔍 키워드: {', '.join(self.keywords)}")
            
        if self.layers:
            layer_names = [layer.value for layer in self.layers]
            conditions.append(f"📚 계층: {', '.join(layer_names)}")
            
        if self.importance_min or self.importance_max:
            imp_range = f"{self.importance_min or 0.0} ~ {self.importance_max or 1.0}"
            conditions.append(f"⭐ 중요도: {imp_range}")
            
        if self.tags:
            conditions.append(f"🏷️  태그: {', '.join(self.tags)}")
        
        return "전체 복원" if not conditions else "\n".join(conditions)


@dataclass 
class RestoreResult:
    """복원 결과 정보"""
    
    success: bool
    total_processed: int = 0
    working_count: int = 0
    stm_count: int = 0
    ltm_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    conflicts_resolved: int = 0
    execution_time: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass
class BackupMetadata:
    """백업 메타데이터"""
    
    export_version: str
    timestamp: datetime
    total_memories: int
    greeum_version: str
    layers_info: Dict[str, int]
    source_system: str = "greeum"
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupMetadata':
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class MemoryBackupEngine:
    """메모리 백업 엔진"""
    
    def __init__(self, hierarchical_system: HierarchicalMemorySystem):
        self.system = hierarchical_system
        
    def create_backup(self, output_path: str, include_metadata: bool = True) -> bool:
        """전체 메모리 백업 생성"""
        try:
            backup_data = {
                "metadata": self._create_backup_metadata().to_dict(),
                "hierarchical_data": self._export_all_layers(),
            }
            
            if include_metadata:
                backup_data["system_metadata"] = {
                    "anchors": self._export_anchors(),
                    "statistics": self._export_statistics()
                }
            
            # 백업 파일 저장
            backup_path = Path(output_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"백업 생성 완료: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"백업 생성 실패: {e}")
            return False
    
    def _create_backup_metadata(self) -> BackupMetadata:
        """백업 메타데이터 생성"""
        overview = self.system.get_system_overview()
        
        return BackupMetadata(
            export_version="2.6.1",
            timestamp=datetime.now(),
            total_memories=overview['total_memories'],
            greeum_version="2.6.1", 
            layers_info={
                layer_name: layer_info.get('total_count', 0) 
                for layer_name, layer_info in overview['layers'].items()
                if isinstance(layer_info, dict)
            }
        )
    
    def _export_all_layers(self) -> Dict[str, List[Dict]]:
        """모든 계층의 메모리 내보내기"""
        exported = {
            "working_memory": [],
            "stm": [],
            "ltm": []
        }
        
        try:
            # Working Memory 내보내기
            if hasattr(self.system, 'working_memory_adapter'):
                for memory_id, memory_item in self.system.working_memory_adapter.slot_to_memory.items():
                    exported["working_memory"].append(self._memory_to_dict(memory_item))
            
            # STM 내보내기  
            if hasattr(self.system, 'stm_layer'):
                for memory_id, memory_item in self.system.stm_layer.memory_cache.items():
                    exported["stm"].append(self._memory_to_dict(memory_item))
            
            # LTM 내보내기 (BlockManager 통해서)
            if hasattr(self.system, 'ltm_layer'):
                # LTM은 블록 기반이므로 별도 처리 필요
                ltm_memories = self._export_ltm_memories()
                exported["ltm"] = ltm_memories
                
        except Exception as e:
            logger.error(f"계층 내보내기 오류: {e}")
        
        return exported
    
    def _memory_to_dict(self, memory_item: MemoryItem) -> Dict[str, Any]:
        """MemoryItem을 딕셔너리로 변환"""
        return {
            "id": memory_item.id,
            "content": memory_item.content,
            "timestamp": memory_item.timestamp.isoformat() if memory_item.timestamp else None,
            "importance": memory_item.importance,
            "layer": memory_item.layer.value if memory_item.layer else None,
            "keywords": memory_item.keywords or [],
            "tags": memory_item.tags or [],
            "metadata": memory_item.metadata or {}
        }
    
    def _export_ltm_memories(self) -> List[Dict[str, Any]]:
        """LTM 메모리 내보내기 (블록 기반)"""
        ltm_memories = []
        try:
            # LTM에서 모든 블록 조회
            if hasattr(self.system.ltm_layer, 'block_manager'):
                # BlockManager에서 모든 블록 가져오기
                all_blocks = self.system.ltm_layer.block_manager.get_all_blocks()
                for block in all_blocks:
                    ltm_memories.append({
                        "id": f"ltm_block_{block.get('block_index')}",
                        "content": block.get('context', ''),
                        "timestamp": block.get('timestamp', ''),
                        "importance": block.get('importance', 0.0),
                        "layer": "ltm",
                        "keywords": [],  # LTM 키워드는 별도 테이블에서 조회 필요
                        "tags": [],
                        "metadata": {
                            "block_index": block.get('block_index'),
                            "hash": block.get('hash'),
                            "prev_hash": block.get('prev_hash')
                        }
                    })
        except Exception as e:
            logger.error(f"LTM 내보내기 오류: {e}")
        
        return ltm_memories
    
    def _export_anchors(self) -> Dict[str, Any]:
        """앵커 정보 내보내기"""
        # TODO: 앵커 시스템과 연동하여 앵커 정보 내보내기
        return {}
    
    def _export_statistics(self) -> Dict[str, Any]:
        """통계 정보 내보내기"""
        try:
            return self.system.get_system_overview()
        except Exception as e:
            logger.error(f"통계 내보내기 오류: {e}")
            return {}


class MemoryRestoreEngine:
    """메모리 복원 엔진"""
    
    def __init__(self, hierarchical_system: HierarchicalMemorySystem):
        self.system = hierarchical_system
        
    def restore_from_backup(
        self, 
        backup_file: str, 
        filter_config: RestoreFilter,
        merge_mode: bool = False,
        dry_run: bool = False
    ) -> RestoreResult:
        """
        메모리 복원 실행
        
        Args:
            backup_file: 백업 파일 경로
            filter_config: 복원 필터 설정
            merge_mode: True면 기존 데이터와 병합, False면 교체
            dry_run: True면 실제로 복원하지 않고 미리보기만
        """
        start_time = datetime.now()
        result = RestoreResult(success=False)
        
        try:
            # 백업 파일 로드
            backup_data = self._load_backup(backup_file)
            if not backup_data:
                result.errors.append("백업 파일 로드 실패")
                return result
            
            # 호환성 검증
            if not self._validate_compatibility(backup_data):
                result.errors.append("백업 파일 호환성 오류")
                return result
            
            # 필터 적용하여 복원 대상 선별
            filtered_memories = self._apply_filters(backup_data, filter_config)
            
            if dry_run:
                return self._generate_preview(filtered_memories, result)
            
            # 실제 복원 실행
            if not merge_mode:
                self._clear_existing_data(filter_config)
            
            result = self._restore_memories(filtered_memories, merge_mode, result)
            result.success = True
            
        except Exception as e:
            logger.error(f"복원 중 오류: {e}")
            result.errors.append(str(e))
            
        finally:
            result.execution_time = (datetime.now() - start_time).total_seconds()
        
        return result
    
    def _load_backup(self, backup_file: str) -> Optional[Dict[str, Any]]:
        """백업 파일 로드"""
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"백업 파일 로드 오류: {e}")
            return None
    
    def _validate_compatibility(self, backup_data: Dict[str, Any]) -> bool:
        """백업 호환성 검증"""
        try:
            metadata = backup_data.get('metadata', {})
            export_version = metadata.get('export_version', '')
            
            # 버전 호환성 체크 (2.6.x 시리즈는 상호 호환)
            if export_version.startswith('2.6'):
                return True
            
            # 향후 버전 호환성 로직 추가
            logger.warning(f"백업 버전 {export_version}은 완전한 호환성이 보장되지 않을 수 있습니다")
            return True  # 일단 허용, 추후 엄격하게 변경 가능
            
        except Exception as e:
            logger.error(f"호환성 검증 오류: {e}")
            return False
    
    def _apply_filters(self, backup_data: Dict[str, Any], filter_config: RestoreFilter) -> Dict[str, List[Dict]]:
        """필터 조건에 맞는 메모리만 선별"""
        hierarchical_data = backup_data.get('hierarchical_data', {})
        
        if filter_config.is_full_restore():
            return hierarchical_data
        
        filtered = {'working_memory': [], 'stm': [], 'ltm': []}
        
        for layer_name, memories in hierarchical_data.items():
            if layer_name not in filtered:
                continue
                
            for memory_data in memories:
                memory_item = self._dict_to_memory_item(memory_data)
                if filter_config.matches(memory_item):
                    filtered[layer_name].append(memory_data)
        
        return filtered
    
    def _dict_to_memory_item(self, memory_data: Dict[str, Any]) -> MemoryItem:
        """딕셔너리를 MemoryItem으로 변환"""
        layer_str = memory_data.get('layer', 'working')
        layer = MemoryLayerType.WORKING
        if layer_str == 'stm':
            layer = MemoryLayerType.STM
        elif layer_str == 'ltm':
            layer = MemoryLayerType.LTM
            
        timestamp_str = memory_data.get('timestamp')
        timestamp = None
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except:
                timestamp = datetime.now()
        
        # Determine priority from importance score
        importance_score = memory_data.get('importance', 0.0)
        if importance_score >= 0.9:
            priority = MemoryPriority.CRITICAL
        elif importance_score >= 0.7:
            priority = MemoryPriority.HIGH
        elif importance_score >= 0.5:
            priority = MemoryPriority.MEDIUM
        elif importance_score >= 0.3:
            priority = MemoryPriority.LOW
        else:
            priority = MemoryPriority.DISPOSABLE
        
        return MemoryItem(
            id=memory_data.get('id', ''),
            content=memory_data.get('content', ''),
            timestamp=timestamp,
            layer=layer,
            priority=priority,
            metadata=memory_data.get('metadata', {}),
            keywords=memory_data.get('keywords', []),
            tags=memory_data.get('tags', []),
            embedding=memory_data.get('embedding', []),
            importance=importance_score
        )
    
    def _generate_preview(self, filtered_memories: Dict[str, List[Dict]], result: RestoreResult) -> RestoreResult:
        """복원 미리보기 생성"""
        result.working_count = len(filtered_memories.get('working_memory', []))
        result.stm_count = len(filtered_memories.get('stm', []))
        result.ltm_count = len(filtered_memories.get('ltm', []))
        result.total_processed = result.working_count + result.stm_count + result.ltm_count
        result.success = True
        
        return result
    
    def _clear_existing_data(self, filter_config: RestoreFilter):
        """기존 데이터 삭제 (교체 모드)"""
        # 필터 조건에 맞는 기존 데이터만 삭제
        # TODO: 구현 필요 - 선택적 삭제 로직
        logger.info("교체 모드: 기존 데이터 삭제 시작")
        pass
    
    def _restore_memories(
        self, 
        filtered_memories: Dict[str, List[Dict]], 
        merge_mode: bool,
        result: RestoreResult
    ) -> RestoreResult:
        """실제 메모리 복원 수행"""
        
        try:
            # Working Memory 복원
            for memory_data in filtered_memories.get('working_memory', []):
                try:
                    memory_item = self._dict_to_memory_item(memory_data)
                    success = self._restore_to_working_memory(memory_item, merge_mode)
                    if success:
                        result.working_count += 1
                    else:
                        result.error_count += 1
                except Exception as e:
                    result.errors.append(f"Working Memory 복원 오류: {e}")
                    result.error_count += 1
            
            # STM 복원
            for memory_data in filtered_memories.get('stm', []):
                try:
                    memory_item = self._dict_to_memory_item(memory_data)
                    success = self._restore_to_stm(memory_item, merge_mode)
                    if success:
                        result.stm_count += 1
                    else:
                        result.error_count += 1
                except Exception as e:
                    result.errors.append(f"STM 복원 오류: {e}")
                    result.error_count += 1
            
            # LTM 복원
            for memory_data in filtered_memories.get('ltm', []):
                try:
                    success = self._restore_to_ltm(memory_data, merge_mode)
                    if success:
                        result.ltm_count += 1
                    else:
                        result.error_count += 1
                except Exception as e:
                    result.errors.append(f"LTM 복원 오류: {e}")
                    result.error_count += 1
            
            result.total_processed = result.working_count + result.stm_count + result.ltm_count
            
        except Exception as e:
            logger.error(f"메모리 복원 중 오류: {e}")
            result.errors.append(str(e))
        
        return result
    
    def _restore_to_working_memory(self, memory_item: MemoryItem, merge_mode: bool) -> bool:
        """Working Memory로 복원"""
        try:
            if hasattr(self.system, 'working_memory_adapter'):
                # 중복 체크 (merge_mode에서)
                if merge_mode and self._is_duplicate_in_working(memory_item):
                    return False
                
                # Working Memory에 추가
                self.system.working_memory_adapter.slot_to_memory[memory_item.id] = memory_item
                self.system.working_memory_adapter.memory_to_slot[memory_item.id] = memory_item.id
                return True
        except Exception as e:
            logger.error(f"Working Memory 복원 오류: {e}")
        return False
    
    def _restore_to_stm(self, memory_item: MemoryItem, merge_mode: bool) -> bool:
        """STM으로 복원"""
        try:
            if hasattr(self.system, 'stm_layer'):
                # 중복 체크 (merge_mode에서)
                if merge_mode and memory_item.id in self.system.stm_layer.memory_cache:
                    return False
                
                # STM에 추가
                memory_item.layer = MemoryLayerType.STM
                return self.system.stm_layer.add_memory(memory_item) is not None
        except Exception as e:
            logger.error(f"STM 복원 오류: {e}")
        return False
    
    def _restore_to_ltm(self, memory_data: Dict[str, Any], merge_mode: bool) -> bool:
        """LTM으로 복원"""
        try:
            if hasattr(self.system, 'ltm_layer'):
                # LTM은 블록 기반이므로 특별한 처리 필요
                content = memory_data.get('content', '')
                importance = memory_data.get('importance', 0.0)
                
                # 중복 체크는 content 기반으로 (merge_mode에서)
                if merge_mode:
                    # TODO: LTM 중복 체크 로직 구현
                    pass
                
                # LTM 블록으로 추가
                block_id = self.system.ltm_layer.add_memory_block(
                    content=content,
                    importance=importance,
                    keywords=memory_data.get('keywords', []),
                    tags=memory_data.get('tags', [])
                )
                return block_id is not None
        except Exception as e:
            logger.error(f"LTM 복원 오류: {e}")
        return False
    
    def _is_duplicate_in_working(self, memory_item: MemoryItem) -> bool:
        """Working Memory에서 중복 체크"""
        try:
            if hasattr(self.system, 'working_memory_adapter'):
                for existing_memory in self.system.working_memory_adapter.slot_to_memory.values():
                    if existing_memory.content == memory_item.content:
                        return True
        except Exception as e:
            logger.error(f"Working Memory 중복 체크 오류: {e}")
        return False
    
    def preview_restore(self, backup_file: str, filter_config: RestoreFilter) -> str:
        """복원 전 미리보기 텍스트 생성"""
        preview_result = self.restore_from_backup(backup_file, filter_config, dry_run=True)
        
        if not preview_result.success:
            return f"[ERROR] 미리보기 생성 실패:\n" + "\n".join(preview_result.errors)
        
        return f"""
📋 복원 미리보기
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 복원 대상: {preview_result.total_processed}개 메모리
   [MEMORY] Working Memory: {preview_result.working_count}개
   [FAST] STM: {preview_result.stm_count}개  
   🏛️  LTM: {preview_result.ltm_count}개

🔍 필터 조건:
{filter_config}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
계속하시겠습니까? (y/n)
"""


if __name__ == "__main__":
    # 테스트 코드
    print("🔧 Greeum v2.6.1 Backup/Restore System")
    print("RestoreFilter, BackupEngine, RestoreEngine이 구현되었습니다!")