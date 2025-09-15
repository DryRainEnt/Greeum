#!/usr/bin/env python3
"""
Greeum v2.6.1 - CLI Commands for Backup and Restore
백업/복원 기능을 위한 CLI 명령어들
"""

import click
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..core.database_manager import DatabaseManager
from ..core.context_memory import ContextMemorySystem
from ..core.backup_restore import (
    MemoryBackupEngine, 
    MemoryRestoreEngine, 
    RestoreFilter
)
from ..core.memory_layer import MemoryLayerType


def get_context_system() -> ContextMemorySystem:
    """컨텍스트 메모리 시스템 인스턴스 생성"""
    db_manager = DatabaseManager()
    system = ContextMemorySystem(db_manager)
    return system


@click.group()
def backup():
    """메모리 백업 관련 명령어들"""
    pass


@backup.command()
@click.option('--output', '-o', required=True, help='백업 파일 저장 경로')
@click.option('--include-metadata/--no-metadata', default=True, help='시스템 메타데이터 포함 여부')
def export(output: str, include_metadata: bool):
    """전체 메모리를 백업 파일로 내보내기
    
    Examples:
        greeum backup export -o my_memories.json
        greeum backup export --output backups/daily_backup.json --no-metadata
    """
    try:
        click.echo("[PROCESS] 메모리 백업을 시작합니다...")
        
        system = get_context_system()
        backup_engine = MemoryBackupEngine(system)
        
        success = backup_engine.create_backup(output, include_metadata)
        
        if success:
            click.echo(f"✅ 백업 완료: {output}")
            
            # 백업 파일 정보 표시
            backup_path = Path(output)
            if backup_path.exists():
                size_mb = backup_path.stat().st_size / (1024 * 1024)
                click.echo(f"📁 파일 크기: {size_mb:.2f} MB")
        else:
            click.echo("[ERROR] 백업 생성에 실패했습니다")
            
    except Exception as e:
        click.echo(f"💥 백업 중 오류: {e}")


@backup.command()
@click.option('--schedule', type=click.Choice(['daily', 'weekly', 'monthly']), help='자동 백업 스케줄')
@click.option('--output-dir', '-d', help='백업 저장 디렉토리')
def auto(schedule: str, output_dir: str):
    """자동 백업 스케줄 설정 (향후 구현 예정)
    
    Examples:
        greeum backup auto --schedule daily --output-dir ~/greeum-backups
    """
    click.echo("⏰ 자동 백업 기능은 v2.6.2에서 구현될 예정입니다")


@click.group() 
def restore():
    """메모리 복원 관련 명령어들"""
    pass


@restore.command()
@click.argument('backup_file', type=click.Path(exists=True))
@click.option('--from-date', help='시작 날짜 (YYYY-MM-DD)')
@click.option('--to-date', help='끝 날짜 (YYYY-MM-DD)')  
@click.option('--keywords', help='키워드 필터 (쉼표로 구분)')
@click.option('--layers', help='계층 필터 (working,stm,ltm 중 선택)')
@click.option('--importance-min', type=float, help='최소 중요도 (0.0-1.0)')
@click.option('--importance-max', type=float, help='최대 중요도 (0.0-1.0)')
@click.option('--tags', help='태그 필터 (쉼표로 구분)')
@click.option('--merge/--replace', default=False, help='병합 모드 (기본: 교체)')
@click.option('--preview/--execute', default=True, help='미리보기만 표시 (기본: 미리보기)')
def from_file(
    backup_file: str,
    from_date: str,
    to_date: str, 
    keywords: str,
    layers: str,
    importance_min: float,
    importance_max: float,
    tags: str,
    merge: bool,
    preview: bool
):
    """백업 파일로부터 메모리 복원
    
    Examples:
        # 전체 복원 미리보기
        greeum restore from-file backup.json
        
        # 선택적 복원 미리보기  
        greeum restore from-file backup.json --from-date 2025-01-01 --keywords "AI,개발"
        
        # 실제 복원 실행
        greeum restore from-file backup.json --execute
        
        # 병합 복원
        greeum restore from-file backup.json --merge --execute
    """
    try:
        # 복원 필터 생성
        filter_config = _create_restore_filter(
            from_date, to_date, keywords, layers, 
            importance_min, importance_max, tags
        )
        
        system = get_context_system()
        restore_engine = MemoryRestoreEngine(system)
        
        if preview:
            # 미리보기 표시
            click.echo("🔍 복원 미리보기를 생성합니다...")
            preview_text = restore_engine.preview_restore(backup_file, filter_config)
            click.echo(preview_text)
            
            if click.confirm('복원을 진행하시겠습니까?'):
                preview = False  # 실제 복원으로 전환
            else:
                click.echo("복원이 취소되었습니다")
                return
        
        if not preview:
            # 실제 복원 실행
            click.echo("[PROCESS] 메모리 복원을 시작합니다...")
            
            result = restore_engine.restore_from_backup(
                backup_file=backup_file,
                filter_config=filter_config,
                merge_mode=merge,
                dry_run=False
            )
            
            # 결과 표시
            if result.success:
                click.echo("✅ 복원 완료!")
                click.echo(f"📊 복원 결과:")
                click.echo(f"   [MEMORY] Working Memory: {result.working_count}개")
                click.echo(f"   [FAST] STM: {result.stm_count}개") 
                click.echo(f"   🏛️  LTM: {result.ltm_count}개")
                click.echo(f"   [IMPROVE] 총 처리: {result.total_processed}개")
                click.echo(f"   ⏱️  소요 시간: {result.execution_time:.2f}초")
                
                if result.error_count > 0:
                    click.echo(f"   ⚠️  오류: {result.error_count}개")
                    for error in result.errors[:5]:  # 최대 5개 오류만 표시
                        click.echo(f"      - {error}")
            else:
                click.echo("[ERROR] 복원에 실패했습니다")
                for error in result.errors:
                    click.echo(f"   💥 {error}")
                    
    except Exception as e:
        click.echo(f"💥 복원 중 오류: {e}")


def _create_restore_filter(
    from_date: str,
    to_date: str,
    keywords: str,
    layers: str,
    importance_min: float,
    importance_max: float,
    tags: str
) -> RestoreFilter:
    """CLI 옵션으로부터 RestoreFilter 생성"""
    
    # 날짜 파싱
    date_from = None
    if from_date:
        try:
            date_from = datetime.strptime(from_date, '%Y-%m-%d')
        except ValueError:
            click.echo(f"⚠️  잘못된 시작 날짜 형식: {from_date}")
    
    date_to = None
    if to_date:
        try:
            date_to = datetime.strptime(to_date, '%Y-%m-%d') 
        except ValueError:
            click.echo(f"⚠️  잘못된 끝 날짜 형식: {to_date}")
    
    # 키워드 파싱
    keyword_list = None
    if keywords:
        keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
    
    # 계층 파싱
    layer_list = None
    if layers:
        layer_map = {
            'working': MemoryLayerType.WORKING,
            'stm': MemoryLayerType.STM,
            'ltm': MemoryLayerType.LTM
        }
        layer_names = [layer.strip().lower() for layer in layers.split(',')]
        layer_list = [layer_map[name] for name in layer_names if name in layer_map]
    
    # 태그 파싱
    tag_list = None
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
    
    return RestoreFilter(
        date_from=date_from,
        date_to=date_to,
        keywords=keyword_list,
        layers=layer_list,
        importance_min=importance_min,
        importance_max=importance_max,
        tags=tag_list
    )


# 메인 CLI에 명령어 그룹 등록을 위한 함수들
def register_backup_commands(cli_group):
    """백업 명령어들을 메인 CLI에 등록"""
    cli_group.add_command(backup)
    cli_group.add_command(restore)


if __name__ == "__main__":
    # 개별 테스트용
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'backup':
        backup()
    elif len(sys.argv) > 1 and sys.argv[1] == 'restore':
        restore()
    else:
        print("🔧 Greeum v2.6.1 Backup/Restore CLI")
        print("Usage: python backup_restore_cli.py [backup|restore] ...")