"""
CI 테스트 수정 확인
CI에서 실패한 Phase 2 테스트를 로컬에서 재현
"""

import os
import tempfile
from pathlib import Path

# 환경 설정
data_dir = Path(os.environ.get('GREEUM_DATA_DIR', tempfile.gettempdir()))
data_dir.mkdir(exist_ok=True)
print(f'[DATA] Using data directory: {data_dir}')

# 기본 메모리 시스템 테스트
from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
from greeum.text_utils import process_user_input

try:
    # 1. 데이터베이스 초기화
    db_path = data_dir / 'test_user.db'
    db = DatabaseManager(str(db_path))
    print('✅ Database initialization OK')
    
    # 2. 블록 매니저 초기화
    block_mgr = BlockManager(db)
    print('✅ Block manager initialization OK')
    
    # 3. 텍스트 처리 테스트
    test_content = 'This is a test memory for cross-platform validation'
    processed = process_user_input(test_content)
    print(f'✅ Text processing OK - Keywords: {len(processed.get("keywords", []))}')
    
    # 4. 메모리 블록 추가 테스트 (핵심 테스트!)
    block = block_mgr.add_block(
        context=test_content,
        keywords=processed.get('keywords', []),
        tags=['test', 'cross-platform'],
        embedding=processed.get('embedding', [0.1] * 128),
        importance=0.8
    )
    
    # 이전 코드는 block이 int였을 때 실패했음
    # 수정 후 block은 dict이어야 함
    if isinstance(block, dict):
        print(f'✅ Memory block creation OK - Index: {block.get("block_index", "unknown")}')
        print(f'   Block type: {type(block)}')
        print(f'   Block keys: {list(block.keys())}')
    elif isinstance(block, int):
        print(f'❌ FAIL: Block is int (old behavior) - value: {block}')
        exit(1)
    else:
        print(f'❌ FAIL: Unexpected block type: {type(block)}')
        exit(1)
    
    # 5. 검색 테스트
    results = block_mgr.search_by_keywords(['test', 'memory'], limit=5)
    print(f'✅ Memory search OK - Found: {len(results)} results')
    
    print('\n🎉 SUCCESS: All basic functionality tests PASSED')
    print('✅ add_block() now correctly returns a dictionary')
    
except Exception as e:
    print(f'❌ FAIL: Basic functionality test FAILED: {e}')
    import traceback
    traceback.print_exc()
    exit(1)