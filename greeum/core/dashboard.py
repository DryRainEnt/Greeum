#!/usr/bin/env python3
"""
Greeum v2.6.2 - Memory Dashboard System
메모리 시스템 시각화 및 관리 대시보드
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

from .context_memory import ContextMemorySystem
from .memory_layer import MemoryLayerType, MemoryPriority
from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """메모리 통계 데이터"""
    total_memories: int
    working_memory_count: int
    stm_count: int
    ltm_count: int
    
    # 우선순위별 분포
    priority_distribution: Dict[str, int]
    
    # 시간대별 통계
    daily_additions: Dict[str, int]
    weekly_trend: List[int]
    
    # 용량 정보
    total_size_mb: float
    avg_memory_size_kb: float
    
    # 활용도 통계
    search_frequency: Dict[str, int]
    popular_keywords: List[Tuple[str, int]]


@dataclass
class LayerAnalytics:
    """계층별 상세 분석"""
    layer_type: MemoryLayerType
    count: int
    avg_importance: float
    retention_rate: float  # STM→LTM 승급률 등
    
    # 시간 분석
    avg_age_days: float
    oldest_memory_days: float
    newest_memory_hours: float
    
    # 내용 분석
    avg_content_length: int
    keyword_diversity: int  # 고유 키워드 수
    tag_usage: Dict[str, int]


@dataclass
class SystemHealth:
    """시스템 건강도 지표"""
    overall_health: float  # 0-1 스케일
    
    # 성능 지표
    avg_search_time_ms: float
    memory_usage_mb: float
    database_size_mb: float
    
    # 품질 지표
    duplicate_rate: float
    avg_quality_score: float
    promotion_success_rate: float
    
    # 경고 및 권장사항
    warnings: List[str]
    recommendations: List[str]


class MemoryDashboard:
    """메모리 시스템 대시보드"""
    
    def __init__(self, hierarchical_system: ContextMemorySystem):
        self.system = hierarchical_system
        self.db_manager = hierarchical_system.db_manager
    
    def get_overview(self) -> Dict[str, Any]:
        """대시보드 전체 개요 생성"""
        logger.info("대시보드 개요 생성 중...")
        
        overview = self.system.get_system_overview()
        stats = self.get_memory_stats()
        health = self.get_system_health()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "version": "2.6.2",
            "system_overview": overview,
            "memory_stats": asdict(stats),
            "system_health": asdict(health),
            "quick_actions": self._get_quick_actions()
        }
    
    def get_memory_stats(self) -> MemoryStats:
        """메모리 통계 계산"""
        logger.debug("메모리 통계 계산 중...")
        
        # 기본 카운트
        overview = self.system.get_system_overview()
        
        # Working Memory 카운트 (임시로 0으로 설정, 추후 구현)
        working_count = 0
        try:
            if hasattr(self.system.working_memory_adapter, 'get_all_memories'):
                working_count = len(self.system.working_memory_adapter.get_all_memories())
            elif hasattr(self.system.working_memory_adapter, 'slot_to_memory'):
                working_count = len(self.system.working_memory_adapter.slot_to_memory)
        except:
            working_count = 0
            
        # STM 카운트
        stm_count = 0
        try:
            if hasattr(self.system.stm_layer, 'get_all_memories'):
                stm_count = len(self.system.stm_layer.get_all_memories())
            elif hasattr(self.system.stm_layer, 'memory_cache'):
                stm_count = len(self.system.stm_layer.memory_cache)
            elif hasattr(self.system.stm_layer, 'get_session_memories'):
                stm_count = len(self.system.stm_layer.get_session_memories())
        except:
            stm_count = 0
            
        # LTM 카운트
        ltm_count = 0
        try:
            if hasattr(self.system.ltm_layer, 'get_total_count'):
                ltm_count = self.system.ltm_layer.get_total_count()
            elif hasattr(self.system.ltm_layer, 'blocks'):
                ltm_count = len(self.system.ltm_layer.blocks)
        except:
            ltm_count = 0
        
        # 우선순위별 분포 계산
        priority_dist = self._calculate_priority_distribution()
        
        # 시간대별 통계
        daily_additions = self._calculate_daily_additions()
        weekly_trend = self._calculate_weekly_trend()
        
        # 용량 정보
        total_size, avg_size = self._calculate_size_stats()
        
        # 활용도 통계
        search_freq = self._get_search_frequency()
        popular_keywords = self._get_popular_keywords()
        
        return MemoryStats(
            total_memories=overview['total_memories'],
            working_memory_count=working_count,
            stm_count=stm_count,
            ltm_count=ltm_count,
            priority_distribution=priority_dist,
            daily_additions=daily_additions,
            weekly_trend=weekly_trend,
            total_size_mb=total_size,
            avg_memory_size_kb=avg_size,
            search_frequency=search_freq,
            popular_keywords=popular_keywords
        )
    
    def get_layer_analytics(self, layer: MemoryLayerType) -> LayerAnalytics:
        """특정 계층의 상세 분석"""
        logger.debug(f"{layer.value} 계층 분석 중...")
        
        if layer == MemoryLayerType.WORKING:
            # Working Memory 처리 (임시로 빈 리스트)
            memories = []
            try:
                if hasattr(self.system.working_memory_adapter, 'get_all_memories'):
                    memories = self.system.working_memory_adapter.get_all_memories()
                elif hasattr(self.system.working_memory_adapter, 'slot_to_memory'):
                    memories = list(self.system.working_memory_adapter.slot_to_memory.values())
            except:
                memories = []
        elif layer == MemoryLayerType.STM:
            # STM 메모리 가져오기
            memories = []
            try:
                if hasattr(self.system.stm_layer, 'get_all_memories'):
                    memories = self.system.stm_layer.get_all_memories()
                elif hasattr(self.system.stm_layer, 'get_session_memories'):
                    memories = self.system.stm_layer.get_session_memories()
                elif hasattr(self.system.stm_layer, 'memory_cache'):
                    memories = list(self.system.stm_layer.memory_cache.values())
            except:
                memories = []
        else:  # LTM
            # LTM 메모리 가져오기 (블록에서 변환)
            memories = []
            try:
                if hasattr(self.system.ltm_layer, 'get_recent_memories'):
                    memories = self.system.ltm_layer.get_recent_memories(limit=1000)
                elif hasattr(self.system.ltm_layer, 'blocks'):
                    # 블록을 MemoryItem으로 변환 (최대 1000개)
                    block_items = list(self.system.ltm_layer.blocks.items())
                    recent_blocks = sorted(block_items, key=lambda x: x[1].timestamp, reverse=True)[:1000]
                    for block_index, block in recent_blocks:
                        # LTMBlock을 MemoryItem으로 변환
                        from .memory_layer import MemoryPriority
                        priority = MemoryPriority.HIGH if block.importance > 0.8 else MemoryPriority.MEDIUM
                        
                        memory_item = MemoryItem(
                            id=block.memory_id,
                            content=block.context,
                            timestamp=block.timestamp,
                            layer=MemoryLayerType.LTM,
                            priority=priority,
                            metadata=block.metadata or {},
                            keywords=block.keywords or [],
                            tags=block.tags or [],
                            embedding=block.embedding or [],
                            importance=block.importance
                        )
                        memories.append(memory_item)
            except Exception as e:
                logger.warning(f"LTM 메모리 가져오기 실패: {e}")
                memories = []
        
        if not memories:
            return LayerAnalytics(
                layer_type=layer,
                count=0,
                avg_importance=0.0,
                retention_rate=0.0,
                avg_age_days=0.0,
                oldest_memory_days=0.0,
                newest_memory_hours=0.0,
                avg_content_length=0,
                keyword_diversity=0,
                tag_usage={}
            )
        
        # 분석 데이터 계산
        count = len(memories)
        avg_importance = sum(m.importance for m in memories) / count
        
        # 시간 분석
        now = datetime.now()
        ages = [(now - m.timestamp).days for m in memories]
        avg_age = sum(ages) / len(ages)
        oldest_age = max(ages) if ages else 0
        newest_hours = min([(now - m.timestamp).total_seconds() / 3600 for m in memories])
        
        # 내용 분석
        avg_length = sum(len(m.content) for m in memories) / count
        all_keywords = set()
        tag_usage = {}
        
        for memory in memories:
            if memory.keywords:
                all_keywords.update(memory.keywords)
            if memory.tags:
                for tag in memory.tags:
                    tag_usage[tag] = tag_usage.get(tag, 0) + 1
        
        # 보존율 계산 (STM의 경우)
        retention_rate = 0.0
        if layer == MemoryLayerType.STM:
            retention_rate = self._calculate_stm_retention_rate()
        
        return LayerAnalytics(
            layer_type=layer,
            count=count,
            avg_importance=avg_importance,
            retention_rate=retention_rate,
            avg_age_days=avg_age,
            oldest_memory_days=oldest_age,
            newest_memory_hours=newest_hours,
            avg_content_length=int(avg_length),
            keyword_diversity=len(all_keywords),
            tag_usage=tag_usage
        )
    
    def get_system_health(self) -> SystemHealth:
        """시스템 건강도 분석"""
        logger.debug("시스템 건강도 분석 중...")
        
        # 기본 지표 수집
        overview = self.system.get_system_overview()
        
        # 성능 지표 (모의 데이터, 실제로는 메트릭 수집 시스템 필요)
        avg_search_time = 45.2  # ms
        memory_usage = 128.5  # MB
        db_size = self._get_database_size_mb()
        
        # 품질 지표
        duplicate_rate = 0.03  # 3%
        avg_quality_score = 0.82
        promotion_success_rate = 0.75
        
        # 건강도 계산 (여러 지표의 가중 평균)
        health_score = self._calculate_overall_health(
            performance_score=0.85,  # 성능
            quality_score=avg_quality_score,  # 품질
            stability_score=0.90,  # 안정성
            usage_score=0.78  # 활용도
        )
        
        # 경고 및 권장사항
        warnings = []
        recommendations = []
        
        if duplicate_rate > 0.05:
            warnings.append("중복 메모리 비율이 높습니다 (5% 초과)")
            recommendations.append("중복 검출 및 정리를 실행해보세요")
        
        if db_size > 500:  # 500MB 초과
            warnings.append("데이터베이스 크기가 큽니다")
            recommendations.append("백업 후 구형 데이터 아카이브를 고려하세요")
        
        if overview['total_memories'] > 10000:
            recommendations.append("대용량 데이터에 최적화된 검색 옵션을 활용하세요")
        
        return SystemHealth(
            overall_health=health_score,
            avg_search_time_ms=avg_search_time,
            memory_usage_mb=memory_usage,
            database_size_mb=db_size,
            duplicate_rate=duplicate_rate,
            avg_quality_score=avg_quality_score,
            promotion_success_rate=promotion_success_rate,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def export_dashboard_report(self, output_path: str, include_details: bool = True) -> bool:
        """대시보드 리포트를 파일로 내보내기"""
        try:
            logger.info(f"대시보드 리포트 생성: {output_path}")
            
            report = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "greeum_version": "2.6.2",
                    "report_type": "dashboard_overview"
                },
                "overview": self.get_overview()
            }
            
            if include_details:
                report["layer_analytics"] = {
                    "working_memory": asdict(self.get_layer_analytics(MemoryLayerType.WORKING)),
                    "stm": asdict(self.get_layer_analytics(MemoryLayerType.STM)),
                    "ltm": asdict(self.get_layer_analytics(MemoryLayerType.LTM))
                }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"대시보드 리포트 생성 완료: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"대시보드 리포트 생성 실패: {e}")
            return False
    
    # 내부 헬퍼 메서드들
    
    def _calculate_priority_distribution(self) -> Dict[str, int]:
        """우선순위별 메모리 분포 계산"""
        distribution = {priority.name: 0 for priority in MemoryPriority}
        
        # 실제 구현에서는 DB 쿼리로 효율적으로 계산
        # 여기서는 간단한 예시
        distribution["CRITICAL"] = 45
        distribution["HIGH"] = 123
        distribution["MEDIUM"] = 267
        distribution["LOW"] = 89
        distribution["DISPOSABLE"] = 23
        
        return distribution
    
    def _calculate_daily_additions(self) -> Dict[str, int]:
        """일일 메모리 추가 통계"""
        daily_stats = {}
        
        # 최근 30일간의 데이터
        for i in range(30):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            # 실제로는 DB에서 날짜별 count 조회
            daily_stats[date] = max(0, 10 - abs(i - 15))  # 모의 데이터
        
        return daily_stats
    
    def _calculate_weekly_trend(self) -> List[int]:
        """주간 추세 계산 (최근 12주)"""
        # 실제로는 주별 집계 데이터
        return [45, 52, 38, 61, 47, 55, 49, 58, 43, 67, 51, 59]
    
    def _calculate_size_stats(self) -> Tuple[float, float]:
        """용량 통계 계산"""
        # 실제로는 DB 메타데이터에서 계산
        total_size_mb = 87.5
        avg_size_kb = 2.3
        return total_size_mb, avg_size_kb
    
    def _get_search_frequency(self) -> Dict[str, int]:
        """검색 빈도 통계"""
        # 실제로는 검색 로그에서 집계
        return {
            "프로젝트": 45,
            "AI": 38,
            "개발": 32,
            "메모리": 28,
            "시스템": 25
        }
    
    def _get_popular_keywords(self) -> List[Tuple[str, int]]:
        """인기 키워드 목록"""
        # 실제로는 키워드 사용 빈도 집계
        return [
            ("프로젝트", 156),
            ("개발", 134),
            ("AI", 128),
            ("시스템", 97),
            ("구현", 89),
            ("테스트", 76),
            ("백업", 45)
        ]
    
    def _calculate_stm_retention_rate(self) -> float:
        """STM에서 LTM으로의 승급률 계산"""
        # 실제로는 프로모션 로그 분석
        return 0.68  # 68%
    
    def _get_database_size_mb(self) -> float:
        """데이터베이스 파일 크기 조회"""
        try:
            import os
            if hasattr(self.db_manager, 'db_path') and os.path.exists(self.db_manager.db_path):
                size_bytes = os.path.getsize(self.db_manager.db_path)
                return size_bytes / (1024 * 1024)
        except:
            pass
        return 45.8  # 모의 데이터
    
    def _calculate_overall_health(self, performance_score: float, quality_score: float, 
                                stability_score: float, usage_score: float) -> float:
        """전체 건강도 점수 계산"""
        weights = {
            'performance': 0.3,
            'quality': 0.3,
            'stability': 0.25,
            'usage': 0.15
        }
        
        return (
            performance_score * weights['performance'] +
            quality_score * weights['quality'] +
            stability_score * weights['stability'] +
            usage_score * weights['usage']
        )
    
    def _get_quick_actions(self) -> List[Dict[str, str]]:
        """빠른 액션 목록"""
        return [
            {
                "title": "메모리 백업",
                "command": "greeum backup export",
                "description": "전체 메모리를 안전하게 백업합니다"
            },
            {
                "title": "중복 메모리 정리",
                "command": "greeum memory cleanup --duplicates",
                "description": "중복된 메모리를 찾아 정리합니다"
            },
            {
                "title": "시스템 최적화",
                "command": "greeum optimize --rebuild-index",
                "description": "검색 인덱스를 재구축하여 성능을 향상시킵니다"
            },
            {
                "title": "메모리 검색",
                "command": "greeum memory search",
                "description": "메모리 내용을 검색합니다"
            }
        ]


def get_dashboard_system(db_manager: Optional[DatabaseManager] = None) -> MemoryDashboard:
    """대시보드 시스템 인스턴스 생성"""
    if db_manager is None:
        db_manager = DatabaseManager()
    
    from .context_memory import ContextMemorySystem
    hierarchical_system = ContextMemorySystem(db_manager)
    hierarchical_system.initialize()
    
    return MemoryDashboard(hierarchical_system)