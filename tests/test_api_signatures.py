import inspect
from greeum.core.block_manager import BlockManager
from greeum.core.stm_manager import STMManager


def test_blockmanager_add_block_signature():
    sig = inspect.signature(BlockManager.add_block)
    params = list(sig.parameters)
    expected = [
        'self', 'context', 'keywords', 'tags', 'embedding', 'importance',
        'metadata', 'embedding_model'
    ]
    assert params[:len(expected)] == expected


def test_stm_add_memory_signature():
    sig = inspect.signature(STMManager.add_memory)
    params = list(sig.parameters)
    assert params[:2] == ['self', 'memory_data'] 