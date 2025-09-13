#!/usr/bin/env python3
"""
GraphIndex 부트스트랩 스크립트
기존 블록들의 링크 정보를 GraphIndex에 로드하고 스냅샷 저장
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Greeum 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from greeum.core import BlockManager, DatabaseManager
from greeum.graph.index import GraphIndex
from greeum.graph.snapshot import save_graph_snapshot, load_graph_snapshot

# GraphIndex 패치 적용
from greeum.core.block_manager_graphindex import patch_block_manager_with_graphindex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def bootstrap_graph_index(db_path: str = None, output_path: str = None):
    """
    기존 블록들로부터 GraphIndex를 부트스트랩
    
    Args:
        db_path: 데이터베이스 경로 (기본: 환경변수 또는 기본값)
        output_path: 스냅샷 저장 경로 (기본: data/graph_snapshot.json)
    
    Returns:
        생성된 스냅샷 파일 경로
    """
    # 데이터베이스 설정
    if db_path:
        os.environ['GREEUM_DB_PATH'] = db_path
    
    # BlockManager 초기화 (패치 적용)
    patch_block_manager_with_graphindex(BlockManager)
    
    db_manager = DatabaseManager()
    block_manager = BlockManager(db_manager)
    
    # 기본 출력 경로
    if output_path is None:
        output_path = Path("data") / "graph_snapshot.json"
    else:
        output_path = Path(output_path)
    
    # 출력 디렉토리 생성
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("GraphIndex Bootstrap")
    logger.info("=" * 60)
    
    # 기존 블록 수 확인
    blocks = block_manager.get_blocks(limit=10000)
    logger.info(f"Found {len(blocks)} existing blocks")
    
    if not blocks:
        logger.warning("No blocks found. Creating empty GraphIndex.")
        graph_index = GraphIndex()
    else:
        # 부트스트랩 실행
        logger.info("Bootstrapping GraphIndex from block links...")
        block_manager.bootstrap_graph_index()
        graph_index = block_manager.graph_index
        
        # 통계 출력
        total_nodes = len(graph_index.adj)
        total_edges = sum(len(neighbors) for neighbors in graph_index.adj.values())
        avg_degree = total_edges / total_nodes if total_nodes > 0 else 0
        
        logger.info(f"GraphIndex Statistics:")
        logger.info(f"  Nodes: {total_nodes}")
        logger.info(f"  Edges: {total_edges}")
        logger.info(f"  Avg Degree: {avg_degree:.2f}")
        
        # 연결성 분석
        isolated_nodes = sum(1 for neighbors in graph_index.adj.values() if len(neighbors) == 0)
        logger.info(f"  Isolated Nodes: {isolated_nodes}")
    
    # 스냅샷 저장
    logger.info(f"\nSaving snapshot to {output_path}...")
    save_graph_snapshot(graph_index, output_path)
    
    # 검증을 위해 다시 로드
    logger.info("Verifying snapshot...")
    loaded_graph = load_graph_snapshot(output_path)
    
    if len(loaded_graph.adj) == len(graph_index.adj):
        logger.info("✅ Snapshot verified successfully!")
    else:
        logger.warning("⚠️ Snapshot verification failed!")
    
    logger.info("=" * 60)
    logger.info("Bootstrap completed!")
    
    return output_path


def main():
    """CLI 엔트리포인트"""
    parser = argparse.ArgumentParser(
        description="Bootstrap GraphIndex from existing blocks"
    )
    parser.add_argument(
        "--db-path",
        help="Database path (default: from environment)"
    )
    parser.add_argument(
        "--output",
        default="data/graph_snapshot.json",
        help="Output snapshot path"
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force rebuild even if snapshot exists"
    )
    
    args = parser.parse_args()
    
    # 기존 스냅샷 확인
    output_path = Path(args.output)
    if output_path.exists() and not args.rebuild:
        logger.info(f"Snapshot already exists at {output_path}")
        logger.info("Use --rebuild to force regeneration")
        
        # 기존 스냅샷 정보 출력
        try:
            graph = load_graph_snapshot(output_path)
            logger.info(f"Existing snapshot has {len(graph.adj)} nodes")
        except Exception as e:
            logger.error(f"Failed to load existing snapshot: {e}")
            logger.info("Rebuilding...")
            bootstrap_graph_index(args.db_path, args.output)
    else:
        bootstrap_graph_index(args.db_path, args.output)


if __name__ == "__main__":
    main()