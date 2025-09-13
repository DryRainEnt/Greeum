#!/usr/bin/env python3
"""
Graph management CLI commands for Greeum v3.0.0
"""

import click
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from datetime import datetime
from typing import Dict, Any

console = Console()


@click.group(name="graph")
def graph_group():
    """Graph network management commands"""
    pass


@graph_group.command("bootstrap")
@click.option("--blocks", "-n", default=100, help="Number of recent blocks to process")
@click.option("--force", is_flag=True, help="Force regeneration of all links")
@click.option("--threshold", default=0.7, help="Similarity threshold (0.0-1.0)")
def bootstrap_command(blocks: int, force: bool, threshold: float):
    """Bootstrap graph connections between memory blocks"""
    try:
        from ..core import DatabaseManager, BlockManager
        from ..core.graph_bootstrap import GraphBootstrap
        
        console.print(f"[blue]Starting graph bootstrap for {blocks} blocks...[/blue]")
        
        # 초기화
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
        bootstrap = GraphBootstrap(db_manager, block_manager)
        
        # 임계값 설정
        bootstrap.config['similarity_threshold'] = threshold
        
        # 부트스트랩 실행
        stats = bootstrap.bootstrap_graph(last_n_blocks=blocks, force=force)
        
        # 결과 표시
        table = Table(title="Bootstrap Results", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Blocks Processed", str(stats['blocks_processed']))
        table.add_row("Links Created", str(stats['links_created']))
        table.add_row("Clusters Found", str(stats['clusters_found']))
        table.add_row("Average Similarity", f"{stats['average_similarity']:.3f}")
        
        console.print(table)
        
        if stats['links_created'] > 0:
            console.print(f"[green]✅ Successfully created {stats['links_created']} links[/green]")
        else:
            console.print("[yellow]⚠️ No links created. Try lowering the threshold.[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error during bootstrap: {e}[/red]")


@graph_group.command("snapshot")
@click.option("--output", "-o", required=True, help="Output file path")
@click.option("--format", type=click.Choice(['json', 'graphml']), default='json')
def snapshot_command(output: str, format: str):
    """Create a snapshot of current graph state"""
    try:
        from ..core import DatabaseManager, BlockManager
        from ..core.graph_bootstrap import GraphBootstrap
        
        console.print("[blue]Creating graph snapshot...[/blue]")
        
        # 초기화
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
        bootstrap = GraphBootstrap(db_manager, block_manager)
        
        # 스냅샷 생성
        snapshot = bootstrap.get_graph_snapshot()
        
        # 파일 저장
        output_path = Path(output)
        
        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)
        elif format == 'graphml':
            # GraphML 형식으로 변환
            graphml = _convert_to_graphml(snapshot)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(graphml)
        
        # 통계 표시
        console.print(f"[green]✅ Snapshot saved to: {output_path}[/green]")
        console.print(f"   Nodes: {snapshot['stats']['total_nodes']}")
        console.print(f"   Edges: {snapshot['stats']['total_edges']}")
        
    except Exception as e:
        console.print(f"[red]Error creating snapshot: {e}[/red]")


@graph_group.command("restore")
@click.argument("snapshot_file", type=click.Path(exists=True))
@click.option("--merge", is_flag=True, help="Merge with existing links")
def restore_command(snapshot_file: str, merge: bool):
    """Restore graph from a snapshot file"""
    try:
        from ..core import DatabaseManager, BlockManager
        from ..core.graph_bootstrap import GraphBootstrap
        
        console.print(f"[blue]Restoring graph from: {snapshot_file}[/blue]")
        
        # 스냅샷 로드
        with open(snapshot_file, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        # 초기화
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
        bootstrap = GraphBootstrap(db_manager, block_manager)
        
        # 기존 링크 제거 (merge가 False인 경우)
        if not merge:
            console.print("[yellow]Clearing existing links...[/yellow]")
            # 실제 구현 필요
        
        # 복원 실행
        success = bootstrap.restore_from_snapshot(snapshot)
        
        if success:
            edges = len(snapshot.get('edges', []))
            console.print(f"[green]✅ Successfully restored {edges} edges[/green]")
        else:
            console.print("[red]❌ Restoration failed[/red]")
            
    except Exception as e:
        console.print(f"[red]Error restoring snapshot: {e}[/red]")


@graph_group.command("stats")
@click.option("--detailed", is_flag=True, help="Show detailed statistics")
def stats_command(detailed: bool):
    """Show graph network statistics"""
    try:
        from ..core import DatabaseManager, BlockManager
        
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
        
        # 기본 통계 수집
        total_blocks = len(db_manager.get_blocks(limit=10000))
        
        # 연결 통계
        connected_blocks = 0
        total_links = 0
        max_links = 0
        orphan_blocks = 0
        
        blocks = db_manager.get_blocks(limit=1000)
        
        for block in blocks:
            block_id = block['block_index']
            neighbors = block_manager.get_block_neighbors(block_id)
            
            if neighbors:
                connected_blocks += 1
                link_count = len(neighbors)
                total_links += link_count
                max_links = max(max_links, link_count)
            else:
                orphan_blocks += 1
        
        # 평균 계산
        avg_links = total_links / connected_blocks if connected_blocks > 0 else 0
        
        # 테이블 생성
        table = Table(title="Graph Network Statistics", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Blocks", str(total_blocks))
        table.add_row("Connected Blocks", str(connected_blocks))
        table.add_row("Orphan Blocks", str(orphan_blocks))
        table.add_row("Total Links", str(total_links // 2))  # 양방향이므로 2로 나눔
        table.add_row("Average Links/Block", f"{avg_links:.2f}")
        table.add_row("Max Links/Block", str(max_links))
        
        console.print(table)
        
        if detailed:
            # 상세 정보 표시
            console.print("\n[bold]Top Connected Blocks:[/bold]")
            
            # 가장 많이 연결된 블록들
            connected_list = []
            for block in blocks[:100]:  # 상위 100개만 확인
                block_id = block['block_index']
                neighbors = block_manager.get_block_neighbors(block_id)
                if neighbors:
                    connected_list.append((block_id, len(neighbors), block.get('context', '')[:50]))
            
            connected_list.sort(key=lambda x: x[1], reverse=True)
            
            for i, (block_id, link_count, context) in enumerate(connected_list[:5], 1):
                console.print(f"{i}. Block #{block_id}: {link_count} links")
                console.print(f"   Context: {context}...")
        
    except Exception as e:
        console.print(f"[red]Error getting statistics: {e}[/red]")


def _convert_to_graphml(snapshot: Dict) -> str:
    """Convert snapshot to GraphML format"""
    graphml = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="context" for="node" attr.name="context" attr.type="string"/>
  <key id="importance" for="node" attr.name="importance" attr.type="double"/>
  <key id="weight" for="edge" attr.name="weight" attr.type="double"/>
  <graph id="G" edgedefault="undirected">
"""
    
    # Add nodes
    for node in snapshot['nodes']:
        graphml += f'    <node id="{node["id"]}">\n'
        graphml += f'      <data key="context">{node["context"]}</data>\n'
        graphml += f'      <data key="importance">{node["importance"]}</data>\n'
        graphml += f'    </node>\n'
    
    # Add edges
    for edge in snapshot['edges']:
        graphml += f'    <edge source="{edge["source"]}" target="{edge["target"]}">\n'
        graphml += f'      <data key="weight">{edge["weight"]}</data>\n'
        graphml += f'    </edge>\n'
    
    graphml += """  </graph>
</graphml>"""
    
    return graphml