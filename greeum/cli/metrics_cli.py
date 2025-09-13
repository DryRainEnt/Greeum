"""
메트릭 대시보드 CLI
실시간 성능 모니터링 및 메트릭 분석
"""

import click
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.progress import Progress, BarColumn, TextColumn
from typing import Optional

console = Console()


@click.group(name="metrics")
def metrics_group():
    """메트릭 및 성능 모니터링"""
    pass


@metrics_group.command("dashboard")
@click.option("--live", is_flag=True, help="실시간 업데이트 모드")
@click.option("--period", default="1h", 
              type=click.Choice(["1h", "24h", "7d"]),
              help="분석 기간")
def dashboard_command(live: bool, period: str):
    """메트릭 대시보드 표시"""
    try:
        from ..core.metrics_collector import MetricsCollector
    except ImportError:
        console.print("[red]메트릭 시스템이 설치되지 않았습니다.[/red]")
        return
    
    collector = MetricsCollector()
    
    # 기간 파싱
    period_map = {
        "1h": timedelta(hours=1),
        "24h": timedelta(days=1),
        "7d": timedelta(days=7)
    }
    start_time = datetime.now() - period_map[period]
    
    def generate_dashboard():
        """대시보드 레이아웃 생성"""
        metrics = collector.get_aggregated_metrics(start_time=start_time)
        
        # 레이아웃 생성
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # 헤더
        header_text = f"[bold cyan]Greeum 메트릭 대시보드[/bold cyan] - 기간: {period}"
        layout["header"].update(Panel(header_text, border_style="cyan"))
        
        # 바디를 2열로 분할
        layout["body"].split_row(
            Layout(name="search_metrics"),
            Layout(name="write_metrics")
        )
        
        # 검색 메트릭 테이블
        search_table = Table(title="🔍 검색 성능", show_header=True)
        search_table.add_column("메트릭", style="cyan", width=20)
        search_table.add_column("값", justify="right", width=15)
        
        search_stats = metrics.get('search', {})
        search_table.add_row("총 검색 수", f"{search_stats.get('total', 0):,}")
        search_table.add_row("로컬 검색 비율", f"{search_stats.get('local_ratio', 0):.1%}")
        search_table.add_row("폴백 발생률", f"{search_stats.get('fallback_rate', 0):.1%}")
        search_table.add_row("평균 응답시간", f"{search_stats.get('avg_latency', 0):.1f}ms")
        search_table.add_row("평균 홉 수", f"{search_stats.get('avg_hops', 0):.1f}")
        search_table.add_row("캐시 적중률", f"{search_stats.get('cache_hit_rate', 0):.1%}")
        
        # 검색 타입별 분포
        by_type = search_stats.get('by_type', {})
        if by_type:
            search_table.add_row("", "")  # 구분선
            search_table.add_row("[bold]타입별 분포[/bold]", "")
            for stype, count in by_type.items():
                search_table.add_row(f"  {stype}", str(count))
        
        layout["search_metrics"].update(Panel(search_table))
        
        # 쓰기 메트릭 테이블
        write_table = Table(title="✍️ 쓰기 성능", show_header=True)
        write_table.add_column("메트릭", style="green", width=20)
        write_table.add_column("값", justify="right", width=15)
        
        write_stats = metrics.get('write', {})
        write_table.add_row("총 블록 수", f"{write_stats.get('total_writes', 0):,}")
        write_table.add_row("앵커 근처 쓰기", f"{write_stats.get('near_anchor_ratio', 0):.1%}")
        write_table.add_row("평균 링크 수", f"{write_stats.get('avg_links', 0):.1f}")
        write_table.add_row("평균 쓰기 시간", f"{write_stats.get('avg_latency', 0):.1f}ms")
        
        layout["write_metrics"].update(Panel(write_table))
        
        # 푸터
        summary = metrics.get('summary', {})
        footer_text = (
            f"전체 작업: {summary.get('total_operations', 0):,} | "
            f"로컬 검색: {summary.get('local_search_ratio', 0):.0%} | "
            f"캐시 적중: {summary.get('cache_hit_rate', 0):.0%} | "
            f"마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}"
        )
        layout["footer"].update(Panel(footer_text, border_style="dim"))
        
        return layout
    
    try:
        if live:
            # 실시간 모드
            console.print("[yellow]실시간 대시보드 모드 (Ctrl+C로 종료)[/yellow]")
            with Live(generate_dashboard(), refresh_per_second=1, console=console) as live_display:
                while True:
                    time.sleep(5)  # 5초마다 업데이트
                    live_display.update(generate_dashboard())
        else:
            # 단일 표시
            console.print(generate_dashboard())
    except KeyboardInterrupt:
        console.print("\n[yellow]대시보드 종료[/yellow]")
    except Exception as e:
        console.print(f"[red]대시보드 오류: {e}[/red]")


@metrics_group.command("export")
@click.option("--format", type=click.Choice(["json", "csv"]), default="json",
              help="내보내기 형식")
@click.option("--output", type=click.Path(), required=True,
              help="출력 파일 경로")
@click.option("--period", default="24h",
              type=click.Choice(["1h", "24h", "7d", "30d"]),
              help="내보낼 기간")
def export_command(format: str, output: str, period: str):
    """메트릭 데이터 내보내기"""
    try:
        from ..core.metrics_collector import MetricsCollector
    except ImportError:
        console.print("[red]메트릭 시스템이 설치되지 않았습니다.[/red]")
        return
    
    collector = MetricsCollector()
    
    # 기간 파싱
    period_map = {
        "1h": timedelta(hours=1),
        "24h": timedelta(days=1),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30)
    }
    start_time = datetime.now() - period_map[period]
    
    console.print(f"[cyan]메트릭 수집 중... (기간: {period})[/cyan]")
    
    try:
        # 메트릭 수집
        metrics = collector.get_aggregated_metrics(start_time=start_time)
        
        if format == "json":
            # JSON 형식으로 저장
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)
            console.print(f"[green]✅ JSON 형식으로 저장됨: {output}[/green]")
            
        elif format == "csv":
            # CSV 형식으로 저장
            import csv
            
            with open(output, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 헤더
                writer.writerow(["Category", "Metric", "Value"])
                
                # 검색 메트릭
                search_stats = metrics.get('search', {})
                for key, value in search_stats.items():
                    if isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            writer.writerow(["Search", f"{key}.{subkey}", subvalue])
                    else:
                        writer.writerow(["Search", key, value])
                
                # 쓰기 메트릭
                write_stats = metrics.get('write', {})
                for key, value in write_stats.items():
                    writer.writerow(["Write", key, value])
                
                # 요약
                summary = metrics.get('summary', {})
                for key, value in summary.items():
                    writer.writerow(["Summary", key, value])
            
            console.print(f"[green]✅ CSV 형식으로 저장됨: {output}[/green]")
            
    except Exception as e:
        console.print(f"[red]내보내기 실패: {e}[/red]")
        return 1
    
    return 0


@metrics_group.command("reset")
@click.confirmation_option(prompt="정말로 모든 메트릭을 초기화하시겠습니까?")
def reset_command():
    """메트릭 데이터 초기화"""
    try:
        from ..core.metrics_collector import MetricsCollector
    except ImportError:
        console.print("[red]메트릭 시스템이 설치되지 않았습니다.[/red]")
        return
    
    try:
        collector = MetricsCollector()
        collector.reset()
        console.print("[green]✅ 메트릭이 초기화되었습니다.[/green]")
    except Exception as e:
        console.print(f"[red]초기화 실패: {e}[/red]")


@metrics_group.command("status")
def status_command():
    """메트릭 시스템 상태 확인"""
    try:
        from ..core.metrics_collector import MetricsCollector
    except ImportError:
        console.print("[red]❌ 메트릭 시스템이 설치되지 않았습니다.[/red]")
        return
    
    try:
        collector = MetricsCollector()
        
        # 최근 1시간 메트릭
        recent_metrics = collector.get_aggregated_metrics(
            start_time=datetime.now() - timedelta(hours=1)
        )
        
        # 상태 테이블
        table = Table(title="메트릭 시스템 상태", show_header=True)
        table.add_column("항목", style="cyan")
        table.add_column("상태", justify="right")
        
        table.add_row("시스템 상태", "[green]✅ 정상[/green]")
        table.add_row("DB 경로", str(collector.db_path))
        table.add_row("버퍼 크기", f"{len(collector.buffer)}/{collector.buffer_size}")
        table.add_row("최근 1시간 검색", str(recent_metrics['search']['total']))
        table.add_row("최근 1시간 쓰기", str(recent_metrics['write']['total_writes']))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]상태 확인 실패: {e}[/red]")


def register_metrics_commands(main_cli):
    """메인 CLI에 메트릭 명령어 등록"""
    main_cli.add_command(metrics_group)