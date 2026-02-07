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
@backup.command()
@click.option('--merge/--replace', default=True, help='병합 모드 (기본: 병합, 중복 건너뜀)')
def push(merge: bool):
    """로컬 메모리를 원격 서버에 백업

    Examples:
        greeum backup push
        greeum backup push --replace
    """
    from ..config_store import is_remote_mode, get_remote_config

    if is_remote_mode():
        click.echo("[WARN] 현재 원격 모드입니다. 로컬 → 원격 백업은 로컬 모드에서 실행하세요.")
        click.echo("       또는 다른 원격 서버로 백업하려면 --remote 옵션을 사용하세요.")
        return

    # 1. 로컬 메모리 내보내기
    click.echo("[1/3] 로컬 메모리 내보내기 중...")
    import tempfile
    import json

    try:
        system = get_context_system()
        backup_engine = MemoryBackupEngine(system)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            tmp_path = f.name

        success = backup_engine.create_backup(tmp_path, include_metadata=True)
        if not success:
            click.echo("[ERROR] 로컬 백업 생성 실패")
            return

        backup_data = json.loads(Path(tmp_path).read_text(encoding='utf-8'))
        total = backup_data.get('metadata', {}).get('total_memories', 0)
        click.echo(f"      {total}개 메모리 준비 완료")

        Path(tmp_path).unlink(missing_ok=True)
    except Exception as e:
        click.echo(f"[ERROR] 내보내기 실패: {e}")
        return

    # 2. 원격 서버 정보 확인
    click.echo("[2/3] 원격 서버 연결 중...")
    server_env = Path.home() / ".greeum" / ".server.env"
    remote_url = None
    api_key = None

    if server_env.exists():
        for line in server_env.read_text().strip().split('\n'):
            if line.startswith('GREEUM_SERVER_URL='):
                remote_url = line.split('=', 1)[1]
            elif line.startswith('GREEUM_API_KEY='):
                api_key = line.split('=', 1)[1]

    if not remote_url:
        remote_url = click.prompt("원격 서버 URL", default="http://localhost:8400")
    if not api_key:
        api_key = click.prompt("API Key", hide_input=True)

    click.echo(f"      서버: {remote_url}")

    # 3. 업로드
    click.echo("[3/3] 업로드 중...")
    try:
        from ..client.http_client import GreeumHTTPClient
        client = GreeumHTTPClient(base_url=remote_url, api_key=api_key)
        result = client.backup_push(backup_data, merge=merge)

        if result.get('success'):
            click.echo(f"\n  백업 완료!")
            click.echo(f"  전체: {result.get('total', 0)}개")
            click.echo(f"  복원: {result.get('restored', 0)}개")
            click.echo(f"  건너뜀: {result.get('skipped', 0)}개 (중복)")
            click.echo(f"  오류: {result.get('errors', 0)}개")
        else:
            click.echo(f"[ERROR] 업로드 실패: {result}")
    except Exception as e:
        click.echo(f"[ERROR] 업로드 실패: {e}")


@backup.command()
@click.option('--output', '-o', help='다운로드한 백업을 파일로 저장 (미지정 시 바로 복원)')
@click.option('--merge/--replace', default=True, help='병합 모드 (기본: 병합)')
def pull(output: Optional[str], merge: bool):
    """원격 서버에서 메모리를 로컬로 가져오기

    Examples:
        greeum backup pull                    # 바로 로컬에 복원
        greeum backup pull -o remote.json     # 파일로만 저장
    """
    from ..config_store import is_remote_mode, get_remote_config

    # 1. 원격 서버 정보
    click.echo("[1/3] 원격 서버 연결 중...")

    remote_conf = get_remote_config()
    if remote_conf and remote_conf.enabled:
        remote_url = remote_conf.server_url
        api_key = remote_conf.api_key
    else:
        server_env = Path.home() / ".greeum" / ".server.env"
        remote_url = None
        api_key = None
        if server_env.exists():
            for line in server_env.read_text().strip().split('\n'):
                if line.startswith('GREEUM_SERVER_URL='):
                    remote_url = line.split('=', 1)[1]
                elif line.startswith('GREEUM_API_KEY='):
                    api_key = line.split('=', 1)[1]

    if not remote_url:
        remote_url = click.prompt("원격 서버 URL", default="http://localhost:8400")
    if not api_key:
        api_key = click.prompt("API Key", hide_input=True)

    click.echo(f"      서버: {remote_url}")

    # 2. 다운로드
    click.echo("[2/3] 다운로드 중...")
    try:
        from ..client.http_client import GreeumHTTPClient
        client = GreeumHTTPClient(base_url=remote_url, api_key=api_key)
        backup_data = client.backup_pull()
        total = backup_data.get('metadata', {}).get('total_memories', 0)
        click.echo(f"      {total}개 메모리 수신 완료")
    except Exception as e:
        click.echo(f"[ERROR] 다운로드 실패: {e}")
        return

    # 파일로 저장만 하는 경우
    if output:
        import json
        Path(output).write_text(
            json.dumps(backup_data, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        click.echo(f"\n  저장 완료: {output}")
        size_mb = Path(output).stat().st_size / (1024 * 1024)
        click.echo(f"  파일 크기: {size_mb:.2f} MB")
        return

    # 3. 로컬에 복원
    click.echo("[3/3] 로컬에 복원 중...")
    try:
        import tempfile
        import json

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, encoding='utf-8'
        ) as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
            tmp_path = f.name

        system = get_context_system()
        restore_engine = MemoryRestoreEngine(system)

        result = restore_engine.restore_from_backup(
            backup_path=tmp_path,
            merge=merge,
        )

        Path(tmp_path).unlink(missing_ok=True)

        if result.get('success'):
            click.echo(f"\n  복원 완료!")
            click.echo(f"  복원: {result.get('restored_count', 0)}개")
            click.echo(f"  건너뜀: {result.get('skipped_count', 0)}개")
        else:
            click.echo(f"[ERROR] 복원 실패: {result.get('error', 'unknown')}")

    except Exception as e:
        click.echo(f"[ERROR] 복원 실패: {e}")


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