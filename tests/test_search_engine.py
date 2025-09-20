from greeum.core.search_engine import SearchEngine
from greeum.core.block_manager import BlockManager
from greeum.core.database_manager import DatabaseManager


def test_search_engine():
    db_manager = DatabaseManager(connection_string=":memory:")
    bm = BlockManager(db_manager)
    # add two blocks
    bm.add_block(
        context="나는 오늘 커피를 마셨다.",
        keywords=["커피"],
        tags=[],
        embedding=[0.05]*768,
        importance=0.5,
    )
    bm.add_block(
        context="내일 프로젝트 미팅이 있다.",
        keywords=["프로젝트"],
        tags=[],
        embedding=[0.07]*768,
        importance=0.8,
    )
    se = SearchEngine(block_manager=bm)
    result = se.search("프로젝트", top_k=2)
    assert result["blocks"]
    assert "timing" in result 
