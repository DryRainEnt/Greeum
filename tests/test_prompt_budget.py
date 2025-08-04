from greeum.core.prompt_wrapper import PromptWrapper
from greeum.core.working_memory import STMWorkingSet
from greeum.core.cache_manager import CacheManager
from greeum.core.block_manager import BlockManager


def test_token_budget():
    bm = BlockManager(use_faiss=False)
    cm = CacheManager(block_manager=bm)
    pw = PromptWrapper(cache_manager=cm)

    # add fake block
    bm.add_block(
        context="이것은 매우 중요하고 긴 장기 기억 블록입니다.",
        keywords=["중요"],
        tags=["테스트"],
        embedding=[0.1]*128,
        importance=0.9,
    )
    cm.update_waypoints([{"block_index":0, "relevance":0.95}])
    prompt = pw.compose_prompt("안녕", token_budget=30)
    assert len(prompt.split()) <= 30 