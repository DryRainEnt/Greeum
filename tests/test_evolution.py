from greeum.memory_evolution import MemoryEvolutionManager
from greeum.core.block_manager import BlockManager


def test_summarize_blocks():
    bm = BlockManager(use_faiss=False)
    me = MemoryEvolutionManager(bm.db_manager)

    # add two blocks
    id1 = bm.add_block("오늘 날씨가 좋고 프로젝트를 시작했다.", ["날씨"], [], [0.1]*128, 0.6)
    id2 = bm.add_block("프로젝트 초기 설정과 문서화를 완료했다.", ["문서화"], [], [0.1]*128, 0.7)
    summary = me.summarize_blocks([0,1])
    assert summary is not None
    assert "summary" in summary.get("tags", []) 