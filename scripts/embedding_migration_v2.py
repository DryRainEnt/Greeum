#!/usr/bin/env python3
"""
임베딩 시스템 마이그레이션 스크립트 v2.0
SimpleEmbeddingModel → SentenceTransformer 안전 마이그레이션

Features:
- 안전한 백업 및 롤백
- 배치 처리 및 진행 상황 모니터링
- 검증 및 테스트 통합
- 에러 처리 및 복구

Usage:
    python scripts/embedding_migration_v2.py [options]
    
Options:
    --db-path PATH          데이터베이스 경로
    --backup-path PATH      백업 경로 (기본: db_path.backup)
    --batch-size N          배치 크기 (기본: 100)
    --dry-run              실제 마이그레이션 없이 시뮬레이션
    --verify-only          검증만 수행
    --rollback             백업에서 롤백
    --force                강제 실행 (확인 없이)
"""

import sys
import os
import time
import argparse
import sqlite3
import shutil
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from greeum.core.database_manager import DatabaseManager
from greeum.embedding_models import (
    init_sentence_transformer, 
    embedding_registry,
    SimpleEmbeddingModel,
    SentenceTransformerModel
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('embedding_migration.log')
    ]
)
logger = logging.getLogger(__name__)


class EmbeddingMigrator:
    """임베딩 마이그레이션 관리자"""
    
    def __init__(self, db_path: str, backup_path: Optional[str] = None):
        self.db_path = Path(db_path)
        self.backup_path = Path(backup_path) if backup_path else self.db_path.with_suffix('.backup')
        self.migration_log_path = self.db_path.with_suffix('.migration.json')
        
        # 마이그레이션 상태
        self.migration_state = {
            'started_at': None,
            'completed_at': None,
            'total_blocks': 0,
            'migrated_blocks': 0,
            'failed_blocks': 0,
            'errors': [],
            'backup_created': False,
            'rollback_available': False
        }
        
        # 모델 초기화
        self.old_model = SimpleEmbeddingModel(dimension=768)
        self.new_model = None
        
        # 데이터베이스 연결
        self.db_manager = None
        
    def initialize(self) -> bool:
        """마이그레이션 초기화"""
        try:
            # 데이터베이스 연결
            self.db_manager = DatabaseManager(connection_string=str(self.db_path))
            
            # Sentence-Transformers 모델 초기화
            try:
                self.new_model = init_sentence_transformer()
                logger.info("✅ Sentence-Transformers 모델 초기화 성공")
            except ImportError:
                logger.error("❌ Sentence-Transformers가 설치되지 않았습니다.")
                logger.error("다음 명령어로 설치하세요: pip install sentence-transformers")
                return False
            except Exception as e:
                logger.error(f"❌ Sentence-Transformers 초기화 실패: {e}")
                return False
            
            # 마이그레이션 상태 로드
            self._load_migration_state()
            
            logger.info("✅ 마이그레이션 초기화 완료")
            return True
            
        except Exception as e:
            logger.error(f"❌ 마이그레이션 초기화 실패: {e}")
            return False
    
    def _load_migration_state(self):
        """마이그레이션 상태 로드"""
        if self.migration_log_path.exists():
            try:
                with open(self.migration_log_path, 'r', encoding='utf-8') as f:
                    self.migration_state = json.load(f)
                logger.info("📄 기존 마이그레이션 상태 로드됨")
            except Exception as e:
                logger.warning(f"⚠️ 마이그레이션 상태 로드 실패: {e}")
    
    def _save_migration_state(self):
        """마이그레이션 상태 저장"""
        try:
            with open(self.migration_log_path, 'w', encoding='utf-8') as f:
                json.dump(self.migration_state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ 마이그레이션 상태 저장 실패: {e}")
    
    def create_backup(self) -> bool:
        """데이터베이스 백업 생성"""
        try:
            if self.backup_path.exists():
                logger.warning(f"⚠️ 백업 파일이 이미 존재합니다: {self.backup_path}")
                response = input("덮어쓰시겠습니까? (y/N): ")
                if response.lower() != 'y':
                    return False
            
            logger.info(f"📦 백업 생성 중: {self.db_path} → {self.backup_path}")
            shutil.copy2(self.db_path, self.backup_path)
            
            self.migration_state['backup_created'] = True
            self.migration_state['rollback_available'] = True
            self._save_migration_state()
            
            logger.info("✅ 백업 생성 완료")
            return True
            
        except Exception as e:
            logger.error(f"❌ 백업 생성 실패: {e}")
            return False
    
    def rollback(self) -> bool:
        """백업에서 롤백"""
        try:
            if not self.backup_path.exists():
                logger.error("❌ 백업 파일이 존재하지 않습니다.")
                return False
            
            if not self.migration_state.get('rollback_available', False):
                logger.error("❌ 롤백이 불가능합니다.")
                return False
            
            logger.info(f"🔄 롤백 중: {self.backup_path} → {self.db_path}")
            shutil.copy2(self.backup_path, self.db_path)
            
            # 마이그레이션 상태 초기화
            self.migration_state = {
                'started_at': None,
                'completed_at': None,
                'total_blocks': 0,
                'migrated_blocks': 0,
                'failed_blocks': 0,
                'errors': [],
                'backup_created': True,
                'rollback_available': True
            }
            self._save_migration_state()
            
            logger.info("✅ 롤백 완료")
            return True
            
        except Exception as e:
            logger.error(f"❌ 롤백 실패: {e}")
            return False
    
    def analyze_migration_scope(self) -> Dict[str, Any]:
        """마이그레이션 범위 분석"""
        try:
            cursor = self.db_manager.connection.cursor()
            
            # 전체 블록 수
            cursor.execute("SELECT COUNT(*) FROM blocks")
            total_blocks = cursor.fetchone()[0]
            
            # 마이그레이션 대상 블록 수
            cursor.execute("""
                SELECT COUNT(*)
                FROM blocks b
                LEFT JOIN block_embeddings e ON b.block_index = e.block_index
                WHERE (e.embedding_model IN ('simple_hash_768', 'default', 'simple', 'simple_768')
                       OR e.embedding_model IS NULL
                       OR e.embedding_model NOT LIKE 'st_%')
            """)
            blocks_to_migrate = cursor.fetchone()[0]
            
            # 이미 마이그레이션된 블록 수
            cursor.execute("""
                SELECT COUNT(*)
                FROM blocks b
                LEFT JOIN block_embeddings e ON b.block_index = e.block_index
                WHERE e.embedding_model LIKE 'st_%'
            """)
            already_migrated = cursor.fetchone()[0]
            
            analysis = {
                'total_blocks': total_blocks,
                'blocks_to_migrate': blocks_to_migrate,
                'already_migrated': already_migrated,
                'migration_percentage': (blocks_to_migrate / total_blocks * 100) if total_blocks > 0 else 0
            }
            
            logger.info(f"📊 마이그레이션 분석 결과:")
            logger.info(f"   전체 블록: {total_blocks:,}")
            logger.info(f"   마이그레이션 대상: {blocks_to_migrate:,}")
            logger.info(f"   이미 마이그레이션됨: {already_migrated:,}")
            logger.info(f"   마이그레이션 비율: {analysis['migration_percentage']:.1f}%")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ 마이그레이션 범위 분석 실패: {e}")
            return {}
    
    def get_blocks_to_migrate(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """마이그레이션 대상 블록 조회"""
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute("""
                SELECT b.block_index, b.context, b.keywords, b.tags, b.importance,
                       e.embedding_model, e.embedding_dim, e.embedding
                FROM blocks b
                LEFT JOIN block_embeddings e ON b.block_index = e.block_index
                WHERE (e.embedding_model IN ('simple_hash_768', 'default', 'simple', 'simple_768')
                       OR e.embedding_model IS NULL
                       OR e.embedding_model NOT LIKE 'st_%')
                ORDER BY b.block_index
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            columns = [desc[0] for desc in cursor.description]
            blocks = []
            
            for row in cursor.fetchall():
                block = dict(zip(columns, row))
                # embedding을 numpy 배열로 변환
                if block['embedding']:
                    try:
                        block['embedding'] = np.frombuffer(block['embedding'], dtype=np.float32).tolist()
                    except:
                        block['embedding'] = None
                blocks.append(block)
            
            return blocks
            
        except Exception as e:
            logger.error(f"❌ 마이그레이션 대상 블록 조회 실패: {e}")
            return []
    
    def migrate_blocks(self, blocks: List[Dict[str, Any]]) -> Tuple[int, int]:
        """블록 배치 마이그레이션"""
        migrated = 0
        failed = 0
        
        for block in blocks:
            try:
                # 새 임베딩 생성
                new_embedding = self.new_model.encode(block['context'])
                
                # 데이터베이스 업데이트
                cursor = self.db_manager.connection.cursor()
                
                # 기존 임베딩 정보 삭제
                cursor.execute("DELETE FROM block_embeddings WHERE block_index = ?", (block['block_index'],))
                
                # 새 임베딩 정보 삽입
                embedding_bytes = np.array(new_embedding, dtype=np.float32).tobytes()
                cursor.execute("""
                    INSERT INTO block_embeddings 
                    (block_index, embedding, embedding_model, embedding_dim, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    block['block_index'],
                    embedding_bytes,
                    self.new_model.get_model_name(),
                    self.new_model.get_dimension(),
                    datetime.now().isoformat()
                ))
                
                self.db_manager.connection.commit()
                migrated += 1
                
                if migrated % 10 == 0:
                    logger.info(f"🔄 마이그레이션 진행: {migrated}/{len(blocks)}")
                
            except Exception as e:
                logger.error(f"❌ 블록 {block['block_index']} 마이그레이션 실패: {e}")
                self.migration_state['errors'].append({
                    'block_index': block['block_index'],
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                failed += 1
        
        return migrated, failed
    
    def run_migration(self, batch_size: int = 100, dry_run: bool = False) -> bool:
        """마이그레이션 실행"""
        try:
            # 분석
            analysis = self.analyze_migration_scope()
            if not analysis:
                return False
            
            if analysis['blocks_to_migrate'] == 0:
                logger.info("✅ 마이그레이션할 블록이 없습니다.")
                return True
            
            if dry_run:
                logger.info("🔍 드라이런 모드: 실제 마이그레이션을 수행하지 않습니다.")
                return True
            
            # 백업 생성
            if not self.migration_state.get('backup_created', False):
                if not self.create_backup():
                    return False
            
            # 마이그레이션 시작
            self.migration_state['started_at'] = datetime.now().isoformat()
            self.migration_state['total_blocks'] = analysis['blocks_to_migrate']
            
            logger.info(f"🚀 마이그레이션 시작: {analysis['blocks_to_migrate']:,}개 블록")
            
            offset = 0
            total_migrated = 0
            total_failed = 0
            
            while True:
                # 배치 조회
                blocks = self.get_blocks_to_migrate(batch_size, offset)
                if not blocks:
                    break
                
                # 배치 마이그레이션
                migrated, failed = self.migrate_blocks(blocks)
                total_migrated += migrated
                total_failed += failed
                
                # 진행 상황 업데이트
                self.migration_state['migrated_blocks'] = total_migrated
                self.migration_state['failed_blocks'] = total_failed
                self._save_migration_state()
                
                # 진행률 출력
                progress = (total_migrated + total_failed) / analysis['blocks_to_migrate'] * 100
                logger.info(f"📈 진행률: {progress:.1f}% ({total_migrated + total_failed:,}/{analysis['blocks_to_migrate']:,})")
                
                offset += batch_size
            
            # 마이그레이션 완료
            self.migration_state['completed_at'] = datetime.now().isoformat()
            self._save_migration_state()
            
            logger.info(f"✅ 마이그레이션 완료!")
            logger.info(f"   성공: {total_migrated:,}개")
            logger.info(f"   실패: {total_failed:,}개")
            
            return total_failed == 0
            
        except Exception as e:
            logger.error(f"❌ 마이그레이션 실행 실패: {e}")
            return False
    
    def verify_migration(self) -> bool:
        """마이그레이션 검증"""
        try:
            logger.info("🔍 마이그레이션 검증 중...")
            
            # 샘플 블록 검증
            cursor = self.db_manager.connection.cursor()
            cursor.execute("""
                SELECT b.block_index, b.context, e.embedding_model, e.embedding_dim
                FROM blocks b
                LEFT JOIN block_embeddings e ON b.block_index = e.block_index
                WHERE e.embedding_model LIKE 'st_%'
                ORDER BY RANDOM()
                LIMIT 10
            """)
            
            sample_blocks = cursor.fetchall()
            
            if not sample_blocks:
                logger.warning("⚠️ 검증할 마이그레이션된 블록이 없습니다.")
                return True
            
            # 각 샘플 블록 검증
            for block_index, context, model_name, dim in sample_blocks:
                # 새 임베딩 생성
                expected_embedding = self.new_model.encode(context)
                
                # 데이터베이스에서 임베딩 조회
                cursor.execute("SELECT embedding FROM block_embeddings WHERE block_index = ?", (block_index,))
                result = cursor.fetchone()
                
                if not result:
                    logger.error(f"❌ 블록 {block_index}: 임베딩 데이터 없음")
                    return False
                
                stored_embedding = np.frombuffer(result[0], dtype=np.float32).tolist()
                
                # 차원 검증
                if len(stored_embedding) != len(expected_embedding):
                    logger.error(f"❌ 블록 {block_index}: 차원 불일치 ({len(stored_embedding)} vs {len(expected_embedding)})")
                    return False
                
                # 유사도 검증 (코사인 유사도)
                similarity = self.new_model.similarity(stored_embedding, expected_embedding)
                if similarity < 0.99:  # 99% 이상 유사해야 함
                    logger.error(f"❌ 블록 {block_index}: 유사도 불일치 ({similarity:.4f})")
                    return False
            
            logger.info("✅ 마이그레이션 검증 완료")
            return True
            
        except Exception as e:
            logger.error(f"❌ 마이그레이션 검증 실패: {e}")
            return False


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='임베딩 시스템 마이그레이션 v2.0')
    parser.add_argument('--db-path', default='data/memory.db', help='데이터베이스 경로')
    parser.add_argument('--backup-path', help='백업 경로')
    parser.add_argument('--batch-size', type=int, default=100, help='배치 크기')
    parser.add_argument('--dry-run', action='store_true', help='드라이런 모드')
    parser.add_argument('--verify-only', action='store_true', help='검증만 수행')
    parser.add_argument('--rollback', action='store_true', help='롤백 수행')
    parser.add_argument('--force', action='store_true', help='강제 실행')
    
    args = parser.parse_args()
    
    # 마이그레이션 관리자 초기화
    migrator = EmbeddingMigrator(args.db_path, args.backup_path)
    
    if not migrator.initialize():
        logger.error("❌ 마이그레이션 초기화 실패")
        return 1
    
    # 롤백 모드
    if args.rollback:
        if not args.force:
            response = input("정말로 롤백하시겠습니까? (y/N): ")
            if response.lower() != 'y':
                logger.info("롤백 취소됨")
                return 0
        
        if migrator.rollback():
            logger.info("✅ 롤백 완료")
            return 0
        else:
            logger.error("❌ 롤백 실패")
            return 1
    
    # 검증 모드
    if args.verify_only:
        if migrator.verify_migration():
            logger.info("✅ 검증 완료")
            return 0
        else:
            logger.error("❌ 검증 실패")
            return 1
    
    # 마이그레이션 실행
    if not args.force:
        analysis = migrator.analyze_migration_scope()
        if analysis.get('blocks_to_migrate', 0) > 0:
            response = input(f"마이그레이션을 시작하시겠습니까? ({analysis['blocks_to_migrate']:,}개 블록) (y/N): ")
            if response.lower() != 'y':
                logger.info("마이그레이션 취소됨")
                return 0
    
    if migrator.run_migration(args.batch_size, args.dry_run):
        if not args.dry_run:
            if migrator.verify_migration():
                logger.info("✅ 마이그레이션 및 검증 완료")
                return 0
            else:
                logger.error("❌ 마이그레이션 검증 실패")
                return 1
        else:
            logger.info("✅ 드라이런 완료")
            return 0
    else:
        logger.error("❌ 마이그레이션 실패")
        return 1


if __name__ == '__main__':
    sys.exit(main())
