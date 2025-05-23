import time, tracemalloc, argparse
from greeum.block_manager import BlockManager
from greeum.embedding_models import get_embedding

def generate_dummy_blocks(bm: BlockManager, n: int = 10000):
    for i in range(n):
        ctx = f"더미 블록 {i}번 – 프로젝트 테스트"
        bm.add_block(ctx, ["더미"], [], [0.01]*128, 0.5)

def bench_search(bm: BlockManager, query: str = "프로젝트", runs: int = 10):
    emb = get_embedding(query)
    t0 = time.perf_counter()
    for _ in range(runs):
        bm.search_by_embedding(emb, top_k=5)
    return (time.perf_counter() - t0) * 1000 / runs  # ms

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="skip heavy generation")
    args = parser.parse_args()

    bm = BlockManager(use_faiss=False)
    if not args.quick:
        print("Generating dummy blocks…")
        generate_dummy_blocks(bm)
    tracemalloc.start()
    latency = bench_search(bm)
    current, peak = tracemalloc.get_traced_memory()
    print(f"Average vector search latency: {latency:.2f} ms")
    print(f"RSS current/peak: {current/1e6:.1f} MB / {peak/1e6:.1f} MB")
    tracemalloc.stop()

if __name__ == "__main__":
    main() 