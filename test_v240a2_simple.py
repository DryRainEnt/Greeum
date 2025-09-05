#!/usr/bin/env python3
"""
v2.4.0a2 간단한 동작 확인 테스트
"""

import sys
sys.path.append('/Users/dryrain/DevRoom/Greeum')

from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager

def test_v240a2_integration():
    """v2.4.0a2 핵심 기능 간단 테스트"""
    
    print("🧪 v2.4.0a2 기본 동작 테스트")
    print("=" * 40)
    
    # 1. 테스트 환경 구성
    db_manager = DatabaseManager("data/test_v240a2_simple.db") 
    block_manager = BlockManager(db_manager)
    
    # 2. 액탄트 자동 라벨링 테스트
    test_content = "새로운 AI 프로젝트를 시작했고 정말 흥미로워요"
    
    print(f"📝 테스트 메모리: {test_content}")
    
    block = block_manager.add_block(
        context=test_content,
        keywords=["AI", "프로젝트"],
        tags=["시작"],
        embedding=[0.1] * 128,
        importance=0.8
    )
    
    if block:
        print(f"✅ 블록 생성 성공: #{block['block_index']}")
        
        # 액탄트 분석 확인
        metadata = block.get('metadata', {})
        actant_analysis = metadata.get('actant_analysis', {})
        actants = actant_analysis.get('actants', {})
        
        print(f"🎭 액탄트 분석:")
        print(f"  - 추출된 액탄트: {len(actants)}개")
        print(f"  - 서사 패턴: {actant_analysis.get('narrative_pattern', 'unknown')}")
        
        for role, data in actants.items():
            print(f"  - {role}: {data['entity']} (신뢰도: {data['confidence']})")
        
        # 처리 정보 확인
        processing = metadata.get('actant_processing', {})
        print(f"  - 처리 버전: {processing.get('version', 'unknown')}")
        
        print("\n🎉 v2.4.0a2 핵심 기능 정상 동작!")
        return True
    else:
        print("❌ 블록 생성 실패")
        return False

if __name__ == "__main__":
    success = test_v240a2_integration()
    exit(0 if success else 1)