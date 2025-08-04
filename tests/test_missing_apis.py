"""
Phase 1에서 새로 구현한 Missing API 메서드들의 전용 단위 테스트
- DatabaseManager.health_check()
- BlockManager.verify_integrity()
"""

import os
import shutil
import sqlite3

from tests.base_test_case import BaseGreeumTestCase
from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager


class TestHealthCheckAPI(BaseGreeumTestCase):
    """DatabaseManager.health_check() 전용 테스트"""
    
    def setUp(self):
        super().setUp()
        
        # health_check 전용 데이터베이스 매니저
        self.health_db_path = os.path.join(self.temp_dir, "test_health.db")
        self.health_db_manager = DatabaseManager(connection_string=self.health_db_path)
    
    def test_health_check_normal_database(self):
        """정상 데이터베이스에서 health_check 성공"""
        result = self.health_db_manager.health_check()
        self.assertTrue(result)
    
    def test_health_check_memory_database(self):
        """메모리 데이터베이스에서 health_check 성공"""
        memory_db = DatabaseManager(connection_string=":memory:")
        result = memory_db.health_check()
        self.assertTrue(result)
        memory_db.close()
    
    def test_health_check_required_tables_exist(self):
        """필수 테이블들이 모두 존재하는지 확인"""
        # health_check가 확인하는 테이블들
        required_tables = ['blocks', 'block_keywords', 'block_tags', 'block_metadata']
        
        cursor = self.health_db_manager.conn.cursor()
        for table in required_tables:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table,))
            self.assertIsNotNone(cursor.fetchone(), f"Required table '{table}' should exist")
        
        # health_check도 성공해야 함
        self.assertTrue(self.health_db_manager.health_check())
    
    def test_health_check_schema_validation(self):
        """blocks 테이블 스키마 검증"""
        cursor = self.health_db_manager.conn.cursor()
        cursor.execute("PRAGMA table_info(blocks)")
        columns = {row[1] for row in cursor.fetchall()}
        
        required_columns = {
            'block_index', 'timestamp', 'context', 
            'importance', 'hash', 'prev_hash'
        }
        
        self.assertTrue(required_columns.issubset(columns))
        self.assertTrue(self.health_db_manager.health_check())
    
    def test_health_check_database_integrity(self):
        """데이터베이스 무결성 검사"""
        # 일부 데이터 추가
        cursor = self.health_db_manager.conn.cursor()
        cursor.execute("""
            INSERT INTO blocks 
            (block_index, timestamp, context, importance, hash, prev_hash)
            VALUES (0, '2025-08-04T12:00:00', 'test', 0.5, 'hash', '')
        """)
        self.health_db_manager.conn.commit()
        
        # health_check가 무결성도 확인해야 함
        self.assertTrue(self.health_db_manager.health_check())


class TestVerifyIntegrityAPI(BaseGreeumTestCase):
    """BlockManager.verify_integrity() 전용 테스트"""
    
    def setUp(self):
        super().setUp()
        
        # verify_integrity 전용 매니저들
        self.integrity_db_path = os.path.join(self.temp_dir, "test_integrity.db")
        self.integrity_db_manager = DatabaseManager(connection_string=self.integrity_db_path)
        self.integrity_block_manager = BlockManager(self.integrity_db_manager)
    
    def test_verify_integrity_empty_blockchain(self):
        """빈 블록체인은 유효해야 함"""
        result = self.integrity_block_manager.verify_integrity()
        self.assertTrue(result)
    
    def test_verify_integrity_single_block(self):
        """단일 블록 체인 검증"""
        self.integrity_block_manager.add_block(
            context="First block",
            keywords=["first"],
            tags=["genesis"],
            embedding=[0.1] * 128,
            importance=0.8
        )
        
        result = self.integrity_block_manager.verify_integrity()
        self.assertTrue(result)
    
    def test_verify_integrity_multiple_blocks(self):
        """다중 블록 체인 검증"""
        # 5개 블록 추가
        for i in range(5):
            self.integrity_block_manager.add_block(
                context=f"Block {i}",
                keywords=[f"keyword{i}"],
                tags=[f"tag{i}"],
                embedding=[i * 0.1] * 128,
                importance=0.5 + i * 0.1
            )
        
        result = self.integrity_block_manager.verify_integrity()
        self.assertTrue(result)
    
    def test_verify_integrity_hash_chain_validation(self):
        """해시 체인 연결 검증"""
        # 3개 블록 추가
        blocks = []
        for i in range(3):
            block = self.integrity_block_manager.add_block(
                context=f"Chain block {i}",
                keywords=[f"chain{i}"],
                tags=["chain"],
                embedding=[i * 0.2] * 128,
                importance=0.7
            )
            blocks.append(block)
        
        # 체인 연결 확인
        self.assertEqual(blocks[0]['prev_hash'], "")  # Genesis block
        self.assertEqual(blocks[1]['prev_hash'], blocks[0]['hash'])
        self.assertEqual(blocks[2]['prev_hash'], blocks[1]['hash'])
        
        # 무결성 검증 성공
        result = self.integrity_block_manager.verify_integrity()
        self.assertTrue(result)
    
    def test_verify_integrity_index_continuity(self):
        """블록 인덱스 연속성 검증"""
        # 블록들이 0, 1, 2, ... 순서로 생성되는지 확인
        for i in range(4):
            block = self.integrity_block_manager.add_block(
                context=f"Index test {i}",
                keywords=["index"],
                tags=["continuity"],
                embedding=[0.3] * 128,
                importance=0.6
            )
            self.assertEqual(block['block_index'], i)
        
        result = self.integrity_block_manager.verify_integrity()
        self.assertTrue(result)
    
    def test_verify_integrity_with_special_characters(self):
        """특수 문자가 포함된 블록들의 무결성 검증"""
        special_contexts = [
            "한글 테스트 블록",
            "English with émojis 🚀",
            "SQL injection'; DROP TABLE blocks; --",
            "Unicode: αβγδε ñáéíóú"
        ]
        
        for i, context in enumerate(special_contexts):
            self.integrity_block_manager.add_block(
                context=context,
                keywords=[f"special{i}", "unicode"],
                tags=["test", "special"],
                embedding=[0.4 + i * 0.1] * 128,
                importance=0.8
            )
        
        result = self.integrity_block_manager.verify_integrity()
        self.assertTrue(result)


class TestMissingAPIIntegration(BaseGreeumTestCase):
    """두 API 메서드의 통합 테스트"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_integration.db")
        self.db_manager = DatabaseManager(connection_string=self.db_path)
        self.block_manager = BlockManager(self.db_manager)
    
    def tearDown(self):
        try:
            self.db_manager.close()
        except:
            pass
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_health_check_and_integrity_together(self):
        """health_check와 verify_integrity 동시 테스트"""
        # 초기 상태 - 둘 다 성공해야 함
        self.assertTrue(self.health_db_manager.health_check())
        self.assertTrue(self.integrity_block_manager.verify_integrity())
        
        # 블록 추가 후에도 둘 다 성공해야 함
        for i in range(3):
            self.integrity_block_manager.add_block(
                context=f"Integration test {i}",
                keywords=[f"integration{i}"],
                tags=["integration"],
                embedding=[0.5] * 128,
                importance=0.7
            )
            
            # 각 블록 추가 후마다 검증
            self.assertTrue(self.health_db_manager.health_check())
            self.assertTrue(self.integrity_block_manager.verify_integrity())
    
    def test_large_scale_validation(self):
        """대규모 데이터에서 두 API 성능 테스트"""
        # 100개 블록 추가
        for i in range(100):
            self.integrity_block_manager.add_block(
                context=f"Large scale test block {i:03d}",
                keywords=[f"large{i}", "scale", "test"],
                tags=["performance", f"batch{i//10}"],
                embedding=[i * 0.01] * 128,
                importance=0.5 + (i % 50) * 0.01
            )
        
        # 두 API 모두 성공해야 함
        self.assertTrue(self.health_db_manager.health_check())
        self.assertTrue(self.integrity_block_manager.verify_integrity())


if __name__ == '__main__':
    # 개별 테스트 클래스 실행
    unittest.main(verbosity=2)