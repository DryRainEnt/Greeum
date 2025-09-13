#!/usr/bin/env python3
"""
CLI commands for Greeum anchor management.

Provides commands to view, configure, and control the 3-slot STM anchor system
for localized graph exploration.
"""

import click
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Optional, Dict, Any
from datetime import datetime

console = Console()

# 기본 설정
DEFAULT_ANCHOR_PATH = "data/anchors.json"
DEFAULT_GRAPH_PATH = "data/graph_snapshot.jsonl"


@click.group(name="anchors")
def anchors_group():
    """앵커 시스템 관리 명령어"""
    pass


@anchors_group.command("status")
@click.option("--anchor-path", default=DEFAULT_ANCHOR_PATH, help="앵커 파일 경로")
@click.option("--verbose", "-v", is_flag=True, help="상세 정보 표시")
def status_command(anchor_path: str, verbose: bool):
    """현재 앵커 상태 조회"""
    try:
        from ..anchors.manager import AnchorManager
        
        anchor_path_obj = Path(anchor_path)
        if not anchor_path_obj.exists():
            console.print(f"[yellow]앵커 파일이 존재하지 않습니다: {anchor_path}[/yellow]")
            console.print("[yellow]'greeum init' 또는 bootstrap을 실행하여 앵커를 초기화하세요.[/yellow]")
            return
        
        anchor_manager = AnchorManager(anchor_path_obj)
        
        # 상태 테이블 생성
        table = Table(title="[LINK] Greeum 앵커 상태", show_header=True, header_style="bold magenta")
        table.add_column("슬롯", style="dim", width=6)
        table.add_column("앵커 블록 ID", min_width=12)
        table.add_column("요약", min_width=30)
        table.add_column("최근 사용", min_width=16)
        table.add_column("홉 예산", justify="center", width=8)
        table.add_column("상태", justify="center", width=8)
        
        # 각 슬롯 정보 표시
        slots = ['A', 'B', 'C']
        for slot in slots:
            slot_info = anchor_manager.get_slot_info(slot)
            
            if slot_info:
                # 시간 포맷팅
                try:
                    last_used = datetime.fromtimestamp(slot_info['last_used_ts']).strftime('%Y-%m-%d %H:%M')
                except:
                    last_used = "알 수 없음"
                
                # 상태 표시
                status = "📌 고정" if slot_info.get('pinned', False) else "[PROCESS] 활성"
                
                # 요약 텍스트 길이 제한
                summary = slot_info.get('summary', '요약 없음')
                if isinstance(summary, str) and len(summary) > 40:
                    summary = summary[:37] + "..."
                
                table.add_row(
                    f"[bold]{slot}[/bold]",
                    str(slot_info['anchor_block_id']),
                    summary,
                    last_used,
                    str(slot_info.get('hop_budget', 3)),
                    status
                )
            else:
                table.add_row(
                    f"[dim]{slot}[/dim]",
                    "[dim]미설정[/dim]",
                    "[dim]앵커 없음[/dim]",
                    "[dim]-[/dim]",
                    "[dim]-[/dim]",
                    "[dim]비활성[/dim]"
                )
        
        console.print(table)
        
        # 상세 정보 표시
        if verbose:
            console.print("\n[bold cyan]📊 상세 정보:[/bold cyan]")
            
            # 앵커 파일 정보
            try:
                with open(anchor_path_obj, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    console.print(f"• 앵커 버전: {data.get('version', 'N/A')}")
                    console.print(f"• 마지막 업데이트: {datetime.fromtimestamp(data.get('updated_at', 0)).strftime('%Y-%m-%d %H:%M:%S')}")
                    console.print(f"• 파일 경로: {anchor_path_obj.absolute()}")
            except Exception as e:
                console.print(f"[red]상세 정보 로드 실패: {e}[/red]")
        
    except Exception as e:
        console.print(f"[bold red]앵커 상태 조회 실패: {str(e)}[/bold red]")


@anchors_group.command("set")
@click.argument("slot", type=click.Choice(['A', 'B', 'C']))
@click.argument("block_id", type=int)
@click.option("--anchor-path", default=DEFAULT_ANCHOR_PATH, help="앵커 파일 경로")
@click.option("--summary", default=None, help="앵커 요약 설명")
@click.option("--hop-budget", default=3, type=int, help="홉 예산 (기본: 3)")
def set_command(slot: str, block_id: int, anchor_path: str, summary: Optional[str], hop_budget: int):
    """지정된 슬롯에 앵커 설정"""
    try:
        from ..anchors.manager import AnchorManager
        from ..core.database_manager import DatabaseManager
        
        # 블록 존재 여부 확인
        db_manager = DatabaseManager()
        block = db_manager.get_block_by_index(block_id)
        
        if not block:
            console.print(f"[red]블록 ID {block_id}가 존재하지 않습니다.[/red]")
            return
        
        # 앵커 매니저 초기화
        anchor_path_obj = Path(anchor_path)
        anchor_manager = AnchorManager(anchor_path_obj)
        
        # 요약이 제공되지 않은 경우 블록 컨텍스트에서 생성
        if not summary:
            context = block.get('context', '')
            summary = context[:100] + "..." if len(context) > 100 else context
        
        # 블록 임베딩 가져오기 또는 생성
        embedding = block.get('embedding')
        if not embedding:
            console.print("[yellow]블록에 임베딩이 없습니다. 간단한 임베딩을 생성합니다.[/yellow]")
            # 간단한 임베딩 생성 (실제로는 더 정교해야 함)
            import hashlib
            import numpy as np
            hash_val = int(hashlib.md5(str(block_id).encode()).hexdigest()[:8], 16)
            embedding = np.array([(hash_val % 1000) / 1000.0] * 768)
        else:
            # embedding이 bytes면 numpy array로 변환
            import numpy as np
            if isinstance(embedding, bytes):
                embedding = np.frombuffer(embedding, dtype=np.float32)
            elif isinstance(embedding, list):
                embedding = np.array(embedding)
        
        # 앵커 이동 수행
        anchor_manager.move_anchor(
            slot=slot,
            new_block_id=str(block_id),
            topic_vec=embedding
        )
        
        # 요약과 홉 예산 업데이트
        if summary:
            anchor_manager.update_summary(slot, summary)
        if hop_budget != 3:
            anchor_manager.set_hop_budget(slot, hop_budget)
        
        success = True
        
        if success:
            console.print(f"[green]✅ 슬롯 {slot}에 블록 {block_id} 앵커 설정 완료[/green]")
            console.print(f"[dim]요약: {summary}[/dim]")
        else:
            console.print(f"[red][ERROR] 앵커 설정 실패[/red]")
            
    except Exception as e:
        console.print(f"[bold red]앵커 설정 실패: {str(e)}[/bold red]")


@anchors_group.command("pin")
@click.argument("slot", type=click.Choice(['A', 'B', 'C']))
@click.option("--anchor-path", default=DEFAULT_ANCHOR_PATH, help="앵커 파일 경로")
def pin_command(slot: str, anchor_path: str):
    """앵커 고정 (자동 이동 방지)"""
    try:
        from ..anchors.manager import AnchorManager
        
        anchor_path_obj = Path(anchor_path)
        anchor_manager = AnchorManager(anchor_path_obj)
        
        # 앵커 고정
        success = anchor_manager.pin_anchor(slot)
        
        if success:
            slot_info = anchor_manager.get_slot_info(slot)
            if slot_info:
                console.print(f"[green]📌 슬롯 {slot} (블록 {slot_info['anchor_block_id']}) 고정됨[/green]")
            else:
                console.print(f"[yellow]슬롯 {slot}에 앵커가 없지만 고정 상태로 설정됨[/yellow]")
        else:
            console.print(f"[red][ERROR] 슬롯 {slot} 고정 실패[/red]")
            
    except Exception as e:
        console.print(f"[bold red]앵커 고정 실패: {str(e)}[/bold red]")


@anchors_group.command("unpin")
@click.argument("slot", type=click.Choice(['A', 'B', 'C']))
@click.option("--anchor-path", default=DEFAULT_ANCHOR_PATH, help="앵커 파일 경로")
def unpin_command(slot: str, anchor_path: str):
    """앵커 고정 해제 (자동 이동 허용)"""
    try:
        from ..anchors.manager import AnchorManager
        
        anchor_path_obj = Path(anchor_path)
        anchor_manager = AnchorManager(anchor_path_obj)
        
        # 앵커 고정 해제
        success = anchor_manager.unpin_anchor(slot)
        
        if success:
            slot_info = anchor_manager.get_slot_info(slot)
            if slot_info:
                console.print(f"[green][PROCESS] 슬롯 {slot} (블록 {slot_info['anchor_block_id']}) 고정 해제됨[/green]")
            else:
                console.print(f"[yellow]슬롯 {slot}에 앵커가 없지만 고정 해제됨[/yellow]")
        else:
            console.print(f"[red][ERROR] 슬롯 {slot} 고정 해제 실패[/red]")
            
    except Exception as e:
        console.print(f"[bold red]앵커 고정 해제 실패: {str(e)}[/bold red]")


@anchors_group.command("clear")
@click.argument("slot", type=click.Choice(['A', 'B', 'C']))
@click.option("--anchor-path", default=DEFAULT_ANCHOR_PATH, help="앵커 파일 경로")
@click.confirmation_option(prompt="정말로 앵커를 삭제하시겠습니까?")
def clear_command(slot: str, anchor_path: str):
    """앵커 삭제"""
    try:
        from ..anchors.manager import AnchorManager
        
        anchor_path_obj = Path(anchor_path)
        anchor_manager = AnchorManager(anchor_path_obj)
        
        # 앵커 삭제
        success = anchor_manager.clear_anchor(slot)
        
        if success:
            console.print(f"[green]🗑️ 슬롯 {slot} 앵커 삭제 완료[/green]")
        else:
            console.print(f"[red][ERROR] 슬롯 {slot} 앵커 삭제 실패[/red]")
            
    except Exception as e:
        console.print(f"[bold red]앵커 삭제 실패: {str(e)}[/bold red]")


# datetime import 추가
from datetime import datetime

# 메인 CLI에 등록하기 위한 함수
def register_anchors_commands(main_cli):
    """메인 CLI에 앵커 명령어들을 등록"""
    main_cli.add_command(anchors_group)


if __name__ == "__main__":
    anchors_group()