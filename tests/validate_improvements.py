#!/usr/bin/env python
"""
Greeum 개선 검증 스크립트
"""

import os
import sys
import time
import random
import json
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

# 상위 디렉터리 추가하여 memory_engine 패키지 임포트
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

# 개선된 메모리 엔진 임포트
# from memory_engine import (
# DatabaseManager, BlockManager, STMManager, CacheManager, PromptWrapper,
# SimpleEmbeddingModel, embedding_registry, get_embedding,
# TemporalReasoner
# )
from greeum import (
    DatabaseManager, BlockManager, STMManager, CacheManager, PromptWrapper,
    TemporalReasoner
)
from greeum.embedding_models import SimpleEmbeddingModel, embedding_registry, get_embedding

# 개선된 모듈은 try-except로 임포트 (존재하지 않을 수 있음)
try:
    # from memory_engine import MemoryEvolutionManager, KnowledgeGraphManager # 수정
    from greeum import MemoryEvolutionManager, KnowledgeGraphManager # 수정
except ImportError:
    MemoryEvolutionManager = None
    KnowledgeGraphManager = None

# 테스트 결과 저장 경로
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

class MemoryEngineValidator:
    """메모리 엔진 개선 검증 클래스"""
    
    def __init__(self, db_path=None):
        """
        검증 초기화
        
        Args:
            db_path: 데이터베이스 경로 (기본: data/test_memory.db)
        """
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        if db_path is None:
            db_path = os.path.join(parent_dir, "data", "test_memory.db")
        if os.path.exists(db_path):
            os.remove(db_path)
            
        # 매니저 초기화 (항상 DB 사용)
        self.db_manager = DatabaseManager(db_path)
        simple_model = SimpleEmbeddingModel(dimension=256)
        embedding_registry.register_model("test_model", simple_model, set_as_default=True)
        
        # BlockManager와 STMManager는 이제 DatabaseManager를 통해 데이터를 관리하므로,
        # 이 클래스에서 직접 인스턴스화할 필요는 없을 수 있음.
        # 필요하다면 self.db_manager를 전달하여 생성.
        # 단, BlockManager/STMManager가 파일 I/O를 완전히 버렸다면, 생성자에서 db_manager를 필수로 받아야 함.
        # 현재 리팩토링된 BlockManager/STMManager는 db_manager를 필수로 받음.
        self.block_manager = BlockManager(self.db_manager) 
        self.stm_manager = STMManager(self.db_manager) 
        
        self.temporal_reasoner = TemporalReasoner(self.db_manager)
        
        if MemoryEvolutionManager is not None:
            self.memory_evolution = MemoryEvolutionManager(self.db_manager)
        else:
            self.memory_evolution = None
            
        if KnowledgeGraphManager is not None:
            self.knowledge_graph = KnowledgeGraphManager(self.db_manager)
        else:
            self.knowledge_graph = None
        
        # BlockManager가 DB를 쓰므로, CacheManager도 db_manager나 혹은 db_manager를 쓰는 block_manager를 받아야함.
        # 현재 CacheManager는 block_manager, stm_manager를 인자로 받음.
        self.cache_manager = CacheManager(block_manager=self.block_manager, stm_manager=self.stm_manager) 
        self.prompt_wrapper = PromptWrapper(cache_manager=self.cache_manager, stm_manager=self.stm_manager)
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("===== Greeum 개선 검증 시작 =====")
        
        try:
            # 1. 대량 기억 처리 테스트
            self.test_large_memory_insertion()
            
            # 2. 복잡한 맥락 이해 테스트
            self.test_complex_context_search()
            
            # 3. 시간적 추론 테스트
            self.test_temporal_reasoning()
            
            # 4. 대규모 임베딩 검색 테스트
            self.test_large_embedding_search()
            
            # 5. 기억 진화 테스트
            self.test_memory_evolution()
            
            # 결과 저장
            self.save_results()
            
            print("\n===== 검증 완료 =====")
            print(f"결과 저장 위치: {os.path.join(RESULTS_DIR, 'validation_results.json')}")
        except Exception as e:
            print(f"\n===== 오류 발생: {e} =====")
            import traceback
            traceback.print_exc()
            
            # 지금까지의 결과 저장
            try:
                self.save_results()
                print(f"부분적 결과 저장 위치: {os.path.join(RESULTS_DIR, 'validation_results.json')}")
            except Exception:
                print("결과 저장 실패")
    
    def test_large_memory_insertion(self, count=1000):
        """
        대량 기억 삽입 테스트
        
        Args:
            count: 삽입할 기억 수
        """
        print(f"\n[테스트 1] 대량 기억 삽입 ({count}개)")
        
        # 시간 측정 시작
        start_time = time.time()
        
        # 기억 데이터 생성 및 삽입
        for i in range(count):
            # 프로그레스 표시
            if i % 100 == 0:
                print(f"  진행중... {i}/{count}")
                
            # 임의 기억 생성
            block_data = self._generate_random_memory(i)
            
            # 데이터베이스에 추가
            self.block_manager.add_block(
                context=block_data["context"],
                keywords=block_data["keywords"],
                tags=block_data["tags"],
                embedding=block_data["embedding"],
                importance=block_data["importance"],
                metadata=block_data.get("metadata", {}),
                embedding_model=block_data.get("embedding_model", "test_model")
            )
        
        # 시간 측정 종료
        end_time = time.time()
        duration = end_time - start_time
        
        # 결과 저장
        self.results["tests"]["large_memory_insertion"] = {
            "count": count,
            "duration_seconds": duration,
            "average_insertion_time": duration / count,
            "insertions_per_second": count / duration
        }
        
        print(f"  완료: {count}개 기억 삽입")
        print(f"  총 소요 시간: {duration:.2f}초")
        print(f"  평균 삽입 시간: {(duration / count) * 1000:.2f}ms")
        print(f"  초당 삽입 수: {count / duration:.2f}개/초")
    
    def test_complex_context_search(self):
        """복잡한 맥락 이해 테스트"""
        print("\n[테스트 2] 복잡한 맥락 이해 테스트")
        
        # 테스트 쿼리 목록
        test_queries = [
            "인공지능 프로젝트에 관한 기억",
            "3년 전 기술 회의에서 결정한 사항",
            "마지막으로 만났던 사람에 대한 정보",
            "중요한 이벤트에 참석한 사람들",
            "프로젝트 마감일과 관련된 내용"
        ]
        
        # 임베딩 검색 결과
        results = {}
        
        for query in test_queries:
            print(f"\n  쿼리: '{query}'")
            
            # 임베딩 생성
            embedding = get_embedding(query)
            
            # 임베딩 기반 검색
            start_time = time.time()
            blocks = self.db_manager.search_blocks_by_embedding(embedding, top_k=5)
            duration = time.time() - start_time
            
            # 키워드 추출 및 키워드 기반 검색
            keywords = query.split()
            keyword_blocks = self.db_manager.search_blocks_by_keyword(keywords)
            
            # 하이브리드 검색 (개선된 기능)
            if self.temporal_reasoner:
                hybrid_results = self.temporal_reasoner.hybrid_search(
                    query, embedding, keywords
                )
                hybrid_blocks = hybrid_results.get("blocks", [])
            else:
                hybrid_blocks = []
            
            # 결과 기록
            print(f"  임베딩 검색 결과: {len(blocks)}개 블록 ({duration:.3f}초)")
            print(f"  키워드 검색 결과: {len(keyword_blocks)}개 블록")
            if hybrid_blocks:
                print(f"  하이브리드 검색 결과: {len(hybrid_blocks)}개 블록")
            
            results[query] = {
                "embedding_search": {
                    "count": len(blocks),
                    "duration": duration,
                    "blocks": [self._summarize_block(b) for b in blocks[:3]]
                },
                "keyword_search": {
                    "count": len(keyword_blocks),
                    "blocks": [self._summarize_block(b) for b in keyword_blocks[:3]]
                },
                "hybrid_search": {
                    "count": len(hybrid_blocks),
                    "blocks": [self._summarize_block(b) for b in hybrid_blocks[:3]]
                }
            }
        
        # 결과 저장
        self.results["tests"]["complex_context_search"] = {
            "queries": results
        }
    
    def test_temporal_reasoning(self):
        """시간적 추론 테스트"""
        print("\n[테스트 3] 시간적 추론 테스트")
        
        if not self.temporal_reasoner:
            print("  시간적 추론 테스트 건너뜀 (데이터베이스 모드가 아님)")
            self.results["tests"]["temporal_reasoning"] = {"skipped": True}
            return
        
        # 시간 표현이 포함된 테스트 쿼리
        temporal_queries = [
            "어제 있었던 회의",
            "지난주 프로젝트 진행 상황",
            "3일 전에 결정한 내용",
            "2023년 5월 1일 이벤트",
            "약 한 달 전에 논의했던 사항",
            "작년에 세운 계획"
        ]
        
        results = {}
        
        for query in temporal_queries:
            print(f"\n  쿼리: '{query}'")
            
            # 시간 참조 추출
            time_refs = self.temporal_reasoner.extract_time_references(query)
            
            if time_refs:
                best_ref = self.temporal_reasoner.get_most_specific_time_reference(time_refs)
                print(f"  감지된 시간 표현: '{best_ref['term']}'")
                
                # 시간 범위 출력
                from_date = best_ref.get('from_date')
                to_date = best_ref.get('to_date')
                if from_date and to_date:
                    print(f"  시간 범위: {from_date.strftime('%Y-%m-%d %H:%M')} ~ {to_date.strftime('%Y-%m-%d %H:%M')}")
                
                # 시간 기반 검색
                search_result = self.temporal_reasoner.search_by_time_reference(query)
                temporal_blocks = search_result.get("blocks", [])
                print(f"  시간 기반 검색 결과: {len(temporal_blocks)}개 블록")
                
                results[query] = {
                    "detected_time": best_ref['term'],
                    "time_range": {
                        "from_date": from_date.isoformat() if from_date else None,
                        "to_date": to_date.isoformat() if to_date else None
                    },
                    "blocks_count": len(temporal_blocks),
                    "blocks": [self._summarize_block(b) for b in temporal_blocks[:3]]
                }
            else:
                print("  시간 표현이 감지되지 않았습니다.")
                results[query] = {
                    "detected_time": None,
                    "blocks_count": 0
                }
        
        # 결과 저장
        self.results["tests"]["temporal_reasoning"] = {
            "queries": results
        }
    
    def test_large_embedding_search(self, count=1000, query_count=5):
        """대규모 임베딩 검색 테스트"""
        print(f"\n[테스트 4] 대규모 임베딩 검색 테스트 ({count}개 기억, {query_count}개 쿼리)")
        
        # 테스트 쿼리 목록
        test_queries = [
            "인공지능 프로젝트 계획",
            "데이터 분석 결과 요약",
            "사용자 인터페이스 디자인",
            "성능 최적화 방안",
            "팀 회의 결정사항"
        ]
        
        # 검색 성능 테스트
        results = {}
        
        for i, query in enumerate(test_queries[:query_count]):
            print(f"\n  쿼리 {i+1}/{query_count}: '{query}'")
            
            # 임베딩 생성
            start_time = time.time()
            embedding = get_embedding(query)
            embedding_time = time.time() - start_time
            
            # 임베딩 기반 검색
            search_start = time.time()
            if self.db_manager:
                search_start = time.time()
                blocks = self.db_manager.search_blocks_by_embedding(embedding, top_k=10)
                search_time = time.time() - search_start
            else:
                search_start = time.time()
                blocks = self.block_manager.search_by_embedding(embedding, top_k=10)
                search_time = time.time() - search_start
            
            # 결과 기록
            print(f"  임베딩 생성 시간: {embedding_time:.3f}초")
            print(f"  검색 시간: {search_time:.3f}초")
            print(f"  검색 결과: {len(blocks)}개 블록")
            
            results[query] = {
                "embedding_time": embedding_time,
                "search_time": search_time,
                "results_count": len(blocks),
                "top_results": [self._summarize_block(b) for b in blocks[:3]]
            }
        
        # 결과 저장
        self.results["tests"]["large_embedding_search"] = {
            "memory_count": count,
            "query_count": query_count,
            "queries": results
        }
    
    def test_memory_evolution(self):
        """기억 진화 테스트"""
        print("\n[테스트 5] 기억 진화 테스트")
        
        if not self.memory_evolution or MemoryEvolutionManager is None:
            print("  기억 진화 테스트 건너뜀 (메모리 진화 모듈 사용 불가)")
            self.results["tests"]["memory_evolution"] = {"skipped": True, "reason": "MemoryEvolutionManager 모듈 없음"}
            return
        
        # 1. 원본 기억 추가
        print("  1. 원본 기억 추가")
        original_data = {
            "block_index": 9000,
            "timestamp": datetime.now().isoformat(),
            "context": "처음에는 프로젝트 기한이 6월 15일로 예상됩니다.",
            "keywords": ["프로젝트", "기한", "예상"],
            "tags": ["계획", "일정"],
            "embedding": get_embedding("프로젝트 기한 예상"),
            "importance": 0.7,
            "prev_hash": "",
            "hash": "original_hash_123"
        }
        
        self.db_manager.add_block(original_data)
        print(f"    원본 기억 생성: 블록 #{original_data['block_index']}")
        
        # 2. 수정 기억 생성
        print("  2. 수정 기억 생성 (1차)")
        revision1 = self.memory_evolution.create_memory_revision(
            original_block_index=9000,
            new_context="프로젝트 기한이 변경되어 6월 말로 조정되었습니다.",
            reason="일정 변경"
        )
        
        if revision1:
            print(f"    1차 수정 기억 생성: 블록 #{revision1['block_index']}")
            
            # 3. 또 다른 수정 기억 생성
            print("  3. 수정 기억 생성 (2차)")
            revision2 = self.memory_evolution.create_memory_revision(
                original_block_index=9000,
                new_context="최종적으로 프로젝트 기한이 7월 10일로 확정되었습니다.",
                reason="일정 최종 확정"
            )
            
            if revision2:
                print(f"    2차 수정 기억 생성: 블록 #{revision2['block_index']}")
                
                # 4. 수정 이력 체인 가져오기
                print("  4. 수정 이력 확인")
                revision_chain = self.memory_evolution.get_revision_chain(9000)
                print(f"    수정 이력 개수: {len(revision_chain)}개")
                
                # 5. 원본과 수정본의 차이점 계산
                print("  5. 원본과 최종본 차이점")
                diff = self.memory_evolution.get_revision_diff(9000, revision2['block_index'])
                
                # 6. 여러 수정본 병합
                print("  6. 수정본 병합")
                merged = self.memory_evolution.merge_revisions(
                    [9000, revision1['block_index'], revision2['block_index']],
                    "모든 일정 정보 통합"
                )
                
                if merged:
                    print(f"    병합 기억 생성: 블록 #{merged['block_index']}")
                    
                    # 7. 결과 정리
                    self.results["tests"]["memory_evolution"] = {
                        "original": self._summarize_block(original_data),
                        "revision1": self._summarize_block(revision1),
                        "revision2": self._summarize_block(revision2),
                        "revision_chain_length": len(revision_chain),
                        "diff": diff,
                        "merged": self._summarize_block(merged)
                    }
                    return
        
        # 실패한 경우
        self.results["tests"]["memory_evolution"] = {
            "error": "기억 진화 테스트 실패"
        }
    
    def _generate_random_memory(self, index):
        """임의 기억 데이터 생성"""
        # 임의 주제 선택
        topics = ["프로젝트", "회의", "아이디어", "결정", "일정", "팀원", "목표", "성과", "문제", "해결책"]
        topic = random.choice(topics)
        
        # 임의 컨텍스트 생성
        contexts = [
            f"{topic}에 관한 중요한 정보를 기록합니다. 인덱스: {index}",
            f"{topic} 진행 상황이 예상보다 좋습니다. 인덱스: {index}",
            f"{topic}에 대한 새로운 접근 방식을 고려해야 합니다. 인덱스: {index}",
            f"{topic} 관련 이슈가 발생했으며 조치가 필요합니다. 인덱스: {index}",
            f"{topic}에 대한 팀원들의 피드백이 긍정적입니다. 인덱스: {index}"
        ]
        context = random.choice(contexts)
        
        # 임의 키워드 선택
        all_keywords = topics + ["진행", "검토", "분석", "개선", "평가", "기획", "구현", "피드백"]
        keywords = random.sample(all_keywords, k=random.randint(2, 5))
        
        # 임의 태그 선택
        tags = random.sample(["중요", "긴급", "참고", "완료", "진행중"], k=random.randint(1, 3))
        
        # 임의 타임스탬프 생성 (최근 1년 내)
        days_ago = random.randint(0, 365)
        timestamp = (datetime.now() - timedelta(days=days_ago)).isoformat()
        
        # 임의 임베딩 생성
        embedding = get_embedding(context)
        
        # 임의 중요도 생성
        importance = random.uniform(0.1, 1.0)
        
        # 임의 해시 생성
        import hashlib
        hash_input = f"{index}-{context}-{timestamp}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()
        
        # 블록 데이터 생성
        return {
            "block_index": index,
            "timestamp": timestamp,
            "context": context,
            "keywords": keywords,
            "tags": tags,
            "embedding": embedding,
            "importance": importance,
            "prev_hash": f"prev_hash_{index-1}" if index > 0 else "",
            "hash": hash_value,
            "metadata": {"source": "random_test_generation", "test_index": index},
            "embedding_model": "test_model"
        }
    
    def _summarize_block(self, block):
        """블록 정보 요약"""
        return {
            "block_index": block.get("block_index"),
            "timestamp": block.get("timestamp"),
            "context_snippet": block.get("context", "")[:50] + "..." if len(block.get("context", "")) > 50 else block.get("context", ""),
            "keywords": block.get("keywords", []),
            "tags": block.get("tags", []),
            "importance": block.get("importance"),
            "similarity": block.get("similarity", None),
            "relevance_score": block.get("relevance_score", None)
        }
    
    def save_results(self):
        """테스트 결과를 JSON 파일로 저장"""
        result_path = os.path.join(RESULTS_DIR, "validation_results.json")
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # 검증 실행
    validator = MemoryEngineValidator(use_db=True)
    validator.run_all_tests() 