"""
문서 검증 CLI
마크다운 문서의 코드 예시가 실제로 작동하는지 검증
"""

import click
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
import logging

console = Console()
logger = logging.getLogger(__name__)


@click.group(name="validate")
def validate_group():
    """문서 및 코드 검증"""
    pass


@validate_group.command("docs")
@click.option("--docs-dir", type=click.Path(), default="docs",
              help="문서 디렉토리 경로")
@click.option("--output", type=click.Path(), 
              help="검증 결과를 저장할 JSON 파일 경로")
@click.option("--verbose", is_flag=True,
              help="상세 출력 모드")
def validate_docs_command(docs_dir: str, output: str, verbose: bool):
    """마크다운 문서의 코드 예시 검증"""
    try:
        from ..core.doc_validator import DocumentValidator
    except ImportError:
        console.print("[red]문서 검증 시스템이 설치되지 않았습니다.[/red]")
        return 1
    
    docs_path = Path(docs_dir)
    if not docs_path.exists():
        console.print(f"[red]❌ 문서 디렉토리를 찾을 수 없습니다: {docs_path}[/red]")
        return 1
    
    console.print(f"[cyan]📚 문서 검증 시작: {docs_path}[/cyan]")
    
    validator = DocumentValidator(docs_path)
    
    # Progress bar for extraction
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        # 예시 추출
        extract_task = progress.add_task("[cyan]코드 예시 추출 중...", total=None)
        examples = validator.extract_examples()
        progress.update(extract_task, completed=True, description=f"[green]✅ {len(examples)}개 예시 추출 완료")
    
    if not examples:
        console.print("[yellow]⚠️ 검증할 코드 예시가 없습니다.[/yellow]")
        return 0
    
    # 예시 통계 표시
    type_counts = {}
    for example in examples:
        type_counts[example.example_type] = type_counts.get(example.example_type, 0) + 1
    
    stats_table = Table(title="추출된 예시 통계", show_header=True)
    stats_table.add_column("타입", style="cyan")
    stats_table.add_column("개수", justify="right")
    
    for ex_type, count in sorted(type_counts.items()):
        stats_table.add_row(ex_type, str(count))
    
    console.print(stats_table)
    console.print()
    
    # 검증 실행
    console.print("[cyan]🔍 예시 검증 시작...[/cyan]")
    
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        validate_task = progress.add_task("[cyan]검증 중...", total=len(examples))
        
        passed, failed = validator.validate_all()
        
        progress.update(validate_task, completed=len(examples))
    
    # 결과 표시
    console.print()
    
    # 요약 패널
    if failed == 0:
        summary_style = "green"
        summary_icon = "✅"
        summary_text = f"모든 테스트 통과! ({passed}개)"
    else:
        summary_style = "red" if failed > passed else "yellow"
        summary_icon = "❌" if failed > passed else "⚠️"
        summary_text = f"통과: {passed}개, 실패: {failed}개"
    
    summary_panel = Panel(
        f"[bold {summary_style}]{summary_icon} {summary_text}[/bold {summary_style}]",
        title="검증 결과",
        border_style=summary_style
    )
    console.print(summary_panel)
    
    # 실패한 예시 상세 표시
    if failed > 0 and verbose:
        console.print("\n[red]실패한 예시:[/red]")
        
        failed_table = Table(show_header=True)
        failed_table.add_column("파일", style="cyan")
        failed_table.add_column("줄", justify="right")
        failed_table.add_column("타입")
        failed_table.add_column("오류", style="red")
        
        for result in validator.results:
            if result['status'] == 'fail':
                file_path = Path(result['file']).name
                failed_table.add_row(
                    file_path,
                    str(result['line']),
                    result['type'],
                    result['message'][:50] + "..." if len(result['message']) > 50 else result['message']
                )
        
        console.print(failed_table)
    
    # 결과 저장
    if output:
        output_path = Path(output)
        validator.save_results(output_path)
        console.print(f"\n[green]💾 결과가 저장되었습니다: {output_path}[/green]")
    
    # 리포트 생성
    if verbose:
        console.print("\n[bold]📊 상세 리포트:[/bold]")
        report = validator.generate_report()
        console.print(report)
    
    return 0 if failed == 0 else 1


@validate_group.command("cli")
@click.argument("command")
@click.option("--dry-run", is_flag=True,
              help="실제 실행하지 않고 검증만 수행")
def validate_cli_command(command: str, dry_run: bool):
    """단일 CLI 명령어 검증"""
    console.print(f"[cyan]🔍 명령어 검증: {command}[/cyan]")
    
    if not command.startswith("greeum"):
        console.print("[yellow]⚠️ greeum 명령어가 아닙니다.[/yellow]")
        return 1
    
    try:
        from ..core.doc_validator import DocumentValidator, DocExample
    except ImportError:
        console.print("[red]문서 검증 시스템이 설치되지 않았습니다.[/red]")
        return 1
    
    # 임시 예시 생성
    example = DocExample(
        file_path=Path("<cli>"),
        line_number=1,
        example_type='cli',
        content=command
    )
    
    validator = DocumentValidator()
    result = validator.validate_cli_example(example)
    
    if result['status'] == 'pass':
        console.print(f"[green]✅ 명령어 검증 성공: {result['message']}[/green]")
        return 0
    elif result['status'] == 'skip':
        console.print(f"[yellow]⏭️ 건너뜀: {result['message']}[/yellow]")
        return 0
    else:
        console.print(f"[red]❌ 명령어 검증 실패: {result['message']}[/red]")
        return 1


@validate_group.command("status")
def status_command():
    """문서 검증 시스템 상태 확인"""
    try:
        from ..core.doc_validator import DocumentValidator
        console.print("[green]✅ 문서 검증 시스템이 정상적으로 설치되어 있습니다.[/green]")
        
        # 문서 디렉토리 확인
        docs_dir = Path("docs")
        if docs_dir.exists():
            md_files = list(docs_dir.rglob("*.md"))
            console.print(f"[cyan]📚 문서 디렉토리: {docs_dir}[/cyan]")
            console.print(f"[cyan]📄 마크다운 파일: {len(md_files)}개[/cyan]")
        else:
            console.print("[yellow]⚠️ docs 디렉토리를 찾을 수 없습니다.[/yellow]")
        
    except ImportError:
        console.print("[red]❌ 문서 검증 시스템이 설치되지 않았습니다.[/red]")
        return 1
    
    return 0


def register_validate_commands(main_cli):
    """메인 CLI에 검증 명령어 등록"""
    main_cli.add_command(validate_group)