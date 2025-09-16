#!/usr/bin/env python3
"""
Greeum Doctor - Integrated Diagnostics and Repair Tool
Check, migration, cleanup, and optimization all in one

Usage:
    greeum doctor           # Full diagnostics and auto-repair
    greeum doctor --check   # Diagnostics only
    greeum doctor --fix     # Include auto-repair
    greeum doctor --force   # Force repair (backup recommended)
"""

import sys
import os
import time
import sqlite3
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import shutil

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from greeum.core.database_manager import DatabaseManager
from greeum.embedding_models import init_sentence_transformer, embedding_registry
import logging

logger = logging.getLogger(__name__)


class GreeumDoctor:
    """Greeum 시스템 진단 및 복구 도구"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or self._find_database()
        self.db_manager = DatabaseManager(self.db_path)
        self.issues = []
        self.fixes_applied = []

    def _find_database(self) -> str:
        """데이터베이스 위치 자동 탐색"""
        candidates = [
            'data/memory.db',
            os.path.expanduser('~/.greeum/memory.db'),
            'memory.db'
        ]

        for path in candidates:
            if os.path.exists(path):
                return path

        raise FileNotFoundError("데이터베이스를 찾을 수 없습니다. --db-path를 지정하세요.")

    def backup_database(self) -> str:
        """데이터베이스 백업"""
        backup_dir = Path(self.db_path).parent / 'backups'
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f'memory_backup_{timestamp}.db'

        shutil.copy2(self.db_path, backup_path)
        return str(backup_path)

    def check_health(self) -> Dict[str, any]:
        """시스템 건강 상태 전체 진단"""
        print("\n🔍 Greeum 시스템 진단 시작...\n")

        health = {
            'database': self._check_database(),
            'embeddings': self._check_embeddings(),
            'dependencies': self._check_dependencies(),
            'performance': self._check_performance()
        }

        # 종합 점수 계산
        total_score = sum(h['score'] for h in health.values()) / len(health)
        health['total_score'] = total_score

        return health

    def _check_database(self) -> Dict:
        """데이터베이스 정합성 검사"""
        cursor = self.db_manager.conn.cursor()
        result = {'score': 100, 'issues': [], 'stats': {}}

        try:
            # 1. 테이블 존재 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            required_tables = ['blocks', 'block_embeddings', 'branch_meta', 'short_term_memories']

            for table in required_tables:
                if table not in tables:
                    result['issues'].append(f"필수 테이블 누락: {table}")
                    result['score'] -= 25

            # 2. 데이터 정합성
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM blocks) as blocks_count,
                    (SELECT COUNT(*) FROM block_embeddings) as embeddings_count,
                    (SELECT COUNT(*) FROM block_embeddings
                     WHERE block_index NOT IN (SELECT block_index FROM blocks)) as orphaned
            """)
            stats = cursor.fetchone()

            result['stats'] = {
                'blocks': stats[0],
                'embeddings': stats[1],
                'orphaned': stats[2]
            }

            if stats[2] > 0:
                result['issues'].append(f"고아 임베딩 {stats[2]}개 발견")
                result['score'] -= 10
                self.issues.append(('orphaned_embeddings', stats[2]))

            # 3. 인덱스 확인
            cursor.execute("PRAGMA index_list('blocks')")
            indexes = cursor.fetchall()
            if len(indexes) < 2:
                result['issues'].append("인덱스 부족 (성능 저하 가능)")
                result['score'] -= 5

        except Exception as e:
            result['issues'].append(f"데이터베이스 오류: {e}")
            result['score'] = 0

        return result

    def _check_embeddings(self) -> Dict:
        """임베딩 시스템 검사"""
        cursor = self.db_manager.conn.cursor()
        result = {'score': 100, 'issues': [], 'stats': {}}

        try:
            # 임베딩 모델별 분포
            cursor.execute("""
                SELECT embedding_model, COUNT(*) as cnt
                FROM block_embeddings
                GROUP BY embedding_model
            """)

            model_stats = {}
            for row in cursor.fetchall():
                model_name = row[0] or 'NULL'
                model_stats[model_name] = row[1]

            result['stats'] = model_stats

            # 구식 모델 검사
            old_models = ['default', 'simple', 'simple_hash_768', 'simple_768', 'NULL']
            old_count = sum(model_stats.get(m, 0) for m in old_models)

            if old_count > 0:
                # 실제 컨텐츠가 있는지 확인
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM block_embeddings be
                    JOIN blocks b ON be.block_index = b.block_index
                    WHERE be.embedding_model IN ('default', 'simple', 'simple_hash_768', 'simple_768')
                       OR be.embedding_model IS NULL
                """)
                valid_old = cursor.fetchone()[0]

                if valid_old > 0:
                    result['issues'].append(f"마이그레이션 필요: {valid_old}개 블록")
                    result['score'] -= 20
                    self.issues.append(('needs_migration', valid_old))
                else:
                    result['issues'].append(f"정리 필요: {old_count}개 고아 임베딩")
                    result['score'] -= 10
                    self.issues.append(('orphaned_old_embeddings', old_count))

        except Exception as e:
            result['issues'].append(f"임베딩 검사 실패: {e}")
            result['score'] = 0

        return result

    def _check_dependencies(self) -> Dict:
        """의존성 검사"""
        result = {'score': 100, 'issues': [], 'available': {}}

        # sentence-transformers 확인
        try:
            from sentence_transformers import SentenceTransformer
            result['available']['sentence_transformers'] = True
        except ImportError:
            result['available']['sentence_transformers'] = False
            result['issues'].append("sentence-transformers not installed (reduced performance)")
            result['score'] -= 30
            self.issues.append(('missing_dependency', 'sentence-transformers'))

        # 현재 사용 중인 임베딩 모델 확인
        try:
            from greeum.embedding_models import get_embedding_model_name
            current_model = get_embedding_model_name()
            result['available']['current_model'] = current_model

            if 'simple' in current_model.lower():
                result['issues'].append(f"저성능 모델 사용 중: {current_model}")
                result['score'] -= 20
        except:
            pass

        return result

    def _check_performance(self) -> Dict:
        """성능 지표 검사"""
        cursor = self.db_manager.conn.cursor()
        result = {'score': 100, 'issues': [], 'metrics': {}}

        try:
            # 데이터베이스 크기
            cursor.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0]
            result['metrics']['db_size_mb'] = db_size / (1024 * 1024)

            # 프래그멘테이션
            cursor.execute("PRAGMA freelist_count")
            freelist = cursor.fetchone()[0]

            if freelist > 1000:
                result['issues'].append(f"데이터베이스 프래그멘테이션: {freelist} 페이지")
                result['score'] -= 10
                self.issues.append(('fragmentation', freelist))

            # 쿼리 성능 테스트
            start = time.time()
            cursor.execute("SELECT COUNT(*) FROM blocks")
            query_time = time.time() - start
            result['metrics']['query_time_ms'] = query_time * 1000

            if query_time > 0.1:
                result['issues'].append(f"느린 쿼리 응답: {query_time:.3f}초")
                result['score'] -= 15

        except Exception as e:
            result['issues'].append(f"성능 검사 실패: {e}")
            result['score'] = 50

        return result

    def fix_issues(self, force: bool = False) -> List[str]:
        """발견된 문제 자동 복구"""
        if not self.issues and not force:
            print("✅ 복구할 문제가 없습니다.")
            return []

        print("\n🔧 문제 복구 시작...\n")
        fixes = []

        for issue_type, data in self.issues:
            if issue_type == 'orphaned_embeddings':
                if self._fix_orphaned_embeddings(data):
                    fixes.append(f"고아 임베딩 {data}개 정리 완료")

            elif issue_type == 'orphaned_old_embeddings':
                if self._fix_orphaned_old_embeddings(data):
                    fixes.append(f"구식 고아 임베딩 {data}개 정리 완료")

            elif issue_type == 'needs_migration':
                if self._fix_migration(data):
                    fixes.append(f"{data}개 블록 마이그레이션 완료")

            elif issue_type == 'fragmentation':
                if self._fix_fragmentation():
                    fixes.append("데이터베이스 최적화 완료")

            elif issue_type == 'missing_dependency':
                self._suggest_dependency_fix(data)

        return fixes

    def _fix_orphaned_embeddings(self, count: int) -> bool:
        """고아 임베딩 정리"""
        try:
            cursor = self.db_manager.conn.cursor()
            cursor.execute("""
                DELETE FROM block_embeddings
                WHERE block_index NOT IN (SELECT block_index FROM blocks)
            """)
            self.db_manager.conn.commit()
            print(f"  ✓ {cursor.rowcount}개 고아 임베딩 삭제")
            return True
        except Exception as e:
            print(f"  ✗ 고아 임베딩 정리 실패: {e}")
            return False

    def _fix_orphaned_old_embeddings(self, count: int) -> bool:
        """구식 고아 임베딩 정리"""
        try:
            cursor = self.db_manager.conn.cursor()
            cursor.execute("""
                DELETE FROM block_embeddings
                WHERE (embedding_model IN ('default', 'simple', 'simple_hash_768', 'simple_768')
                       OR embedding_model IS NULL)
                  AND block_index NOT IN (SELECT block_index FROM blocks)
            """)
            self.db_manager.conn.commit()
            print(f"  ✓ {cursor.rowcount}개 구식 고아 임베딩 삭제")
            return True
        except Exception as e:
            print(f"  ✗ 구식 임베딩 정리 실패: {e}")
            return False

    def _fix_migration(self, count: int) -> bool:
        """임베딩 마이그레이션"""
        try:
            print(f"  🔄 {count}개 블록 마이그레이션 중...")

            # SentenceTransformer 초기화
            try:
                model = init_sentence_transformer()
                model_name = model.get_model_name()
            except:
                print("  ⚠️  sentence-transformers 없음. 설치 후 재실행하세요.")
                return False

            cursor = self.db_manager.conn.cursor()

            # 마이그레이션 대상 조회
            cursor.execute("""
                SELECT b.block_index, b.context
                FROM blocks b
                JOIN block_embeddings be ON b.block_index = be.block_index
                WHERE be.embedding_model IN ('default', 'simple', 'simple_hash_768', 'simple_768')
                   OR be.embedding_model IS NULL
                LIMIT 100
            """)

            blocks = cursor.fetchall()
            if not blocks:
                return True

            # 배치 처리
            from greeum.embedding_models import get_embedding
            import numpy as np

            for block_index, context in blocks:
                embedding = get_embedding(context)
                if embedding:
                    emb_array = np.array(embedding, dtype=np.float32)
                    cursor.execute("""
                        UPDATE block_embeddings
                        SET embedding = ?, embedding_model = ?, embedding_dim = ?
                        WHERE block_index = ?
                    """, (emb_array.tobytes(), model_name, len(embedding), block_index))

            self.db_manager.conn.commit()
            print(f"  ✓ {len(blocks)}개 블록 마이그레이션 완료")

            # 남은 블록이 있으면 재귀 호출
            remaining = count - len(blocks)
            if remaining > 0:
                return self._fix_migration(remaining)

            return True

        except Exception as e:
            print(f"  ✗ 마이그레이션 실패: {e}")
            return False

    def _fix_fragmentation(self) -> bool:
        """데이터베이스 최적화"""
        try:
            cursor = self.db_manager.conn.cursor()
            cursor.execute("VACUUM")
            cursor.execute("ANALYZE")
            print("  ✓ 데이터베이스 최적화 완료")
            return True
        except Exception as e:
            print(f"  ✗ 최적화 실패: {e}")
            return False

    def _suggest_dependency_fix(self, package: str):
        """의존성 설치 안내"""
        print(f"\n  ⚠️  {package} 설치 필요:")
        print(f"     pip install {package}")
        print(f"     또는")
        print(f"     pip install greeum[full]")

    def print_report(self, health: Dict):
        """진단 결과 보고서 출력"""
        print("\n" + "="*50)
        print("📋 Greeum Doctor 진단 보고서")
        print("="*50)

        # 종합 점수
        score = health['total_score']
        if score >= 90:
            status = "🟢 건강"
            emoji = "😊"
        elif score >= 70:
            status = "🟡 주의"
            emoji = "🤔"
        elif score >= 50:
            status = "🟠 경고"
            emoji = "😰"
        else:
            status = "🔴 위험"
            emoji = "😱"

        print(f"\n종합 상태: {status} (점수: {score:.0f}/100) {emoji}")

        # 각 영역별 결과
        for category, data in health.items():
            if category == 'total_score':
                continue

            print(f"\n[{category.upper()}]")
            print(f"  점수: {data['score']}/100")

            if data.get('stats'):
                print("  통계:")
                for key, value in data['stats'].items():
                    print(f"    - {key}: {value}")

            if data.get('metrics'):
                print("  성능:")
                for key, value in data['metrics'].items():
                    print(f"    - {key}: {value:.2f}")

            if data['issues']:
                print("  문제:")
                for issue in data['issues']:
                    print(f"    ⚠️  {issue}")
            else:
                print("  ✅ 정상")

        # 권장 사항
        if self.issues:
            print("\n📌 권장 조치:")
            for issue_type, _ in self.issues:
                if issue_type == 'orphaned_embeddings':
                    print("  • greeum doctor --fix 실행하여 고아 데이터 정리")
                elif issue_type == 'needs_migration':
                    print("  • greeum doctor --fix 실행하여 임베딩 마이그레이션")
                elif issue_type == 'fragmentation':
                    print("  • greeum doctor --fix 실행하여 데이터베이스 최적화")
                elif issue_type == 'missing_dependency':
                    print("  • pip install greeum[full] 실행하여 전체 의존성 설치")

        print("\n" + "="*50)


def main():
    """CLI 진입점"""
    parser = argparse.ArgumentParser(description='Greeum Doctor - 시스템 진단 및 복구')
    parser.add_argument('--db-path', help='데이터베이스 경로')
    parser.add_argument('--check', action='store_true', help='진단만 수행')
    parser.add_argument('--fix', action='store_true', help='자동 복구 포함')
    parser.add_argument('--force', action='store_true', help='강제 복구')
    parser.add_argument('--no-backup', action='store_true', help='백업 생략')

    args = parser.parse_args()

    try:
        doctor = GreeumDoctor(args.db_path)

        # 백업
        if (args.fix or args.force) and not args.no_backup:
            backup_path = doctor.backup_database()
            print(f"📦 백업 생성: {backup_path}")

        # 진단
        health = doctor.check_health()
        doctor.print_report(health)

        # 복구
        if args.fix or args.force or (not args.check and doctor.issues):
            if not args.check:
                print("\n복구를 진행하시겠습니까? (y/N): ", end='')
                if input().lower() != 'y':
                    print("복구가 취소되었습니다.")
                    return 0

            fixes = doctor.fix_issues(args.force)
            if fixes:
                print(f"\n✅ 복구 완료: {len(fixes)}개 문제 해결")
                for fix in fixes:
                    print(f"  • {fix}")

            # 재진단
            print("\n🔄 복구 후 재진단...")
            health = doctor.check_health()
            print(f"\n최종 상태: 점수 {health['total_score']:.0f}/100")

        return 0 if health['total_score'] >= 70 else 1

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())