#!/usr/bin/env python3
"""
Greeum v2.6.2 - CLI Commands for Dashboard
대시보드 기능을 위한 CLI 명령어들
"""

import click
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..core.dashboard import MemoryDashboard, get_dashboard_system
from ..core.memory_layer import MemoryLayerType


@click.group()
def dashboard():
    """메모리 대시보드 관련 명령어들"""
    pass


@dashboard.command()
@click.option('--output', '-o', help='결과를 파일로 저장할 경로')
@click.option('--json-format', is_flag=True, help='JSON 형태로 출력')
def overview(output: Optional[str], json_format: bool):
    """메모리 시스템 전체 개요 표시
    
    Examples:
        greeum dashboard overview
        greeum dashboard overview --output dashboard_report.json
        greeum dashboard overview --json-format
    """
    try:
        dashboard_system = get_dashboard_system()
        overview_data = dashboard_system.get_overview()
        
        if json_format or output:
            # JSON 형태로 출력
            json_output = json.dumps(overview_data, indent=2, ensure_ascii=False)
            
            if output:
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(json_output)
                click.echo(f"✅ 대시보드 리포트 저장됨: {output}")
            else:
                click.echo(json_output)
        else:
            # 사용자 친화적 형태로 출력
            _display_overview_friendly(overview_data)
            
    except Exception as e:
        click.echo(f"💥 대시보드 개요 생성 실패: {e}")


@dashboard.command()
@click.argument('layer', type=click.Choice(['working', 'stm', 'ltm']))
@click.option('--output', '-o', help='결과를 파일로 저장할 경로')
def analyze(layer: str, output: Optional[str]):
    """특정 메모리 계층 상세 분석
    
    Examples:
        greeum dashboard analyze working
        greeum dashboard analyze stm --output stm_analysis.json
        greeum dashboard analyze ltm
    """
    try:
        dashboard_system = get_dashboard_system()
        
        # 계층 타입 변환
        layer_map = {
            'working': MemoryLayerType.WORKING,
            'stm': MemoryLayerType.STM,
            'ltm': MemoryLayerType.LTM
        }
        
        layer_type = layer_map[layer]
        analytics = dashboard_system.get_layer_analytics(layer_type)
        
        if output:
            # JSON 파일로 저장
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(analytics.__dict__, f, indent=2, ensure_ascii=False, default=str)
            click.echo(f"✅ {layer.upper()} 분석 결과 저장됨: {output}")
        else:
            # 콘솔에 친화적 형태로 출력
            _display_layer_analytics_friendly(analytics)
            
    except Exception as e:
        click.echo(f"💥 계층 분석 실패: {e}")


@dashboard.command()
@click.option('--format', 'output_format', type=click.Choice(['simple', 'detailed', 'json']), 
              default='simple', help='출력 형태')
def health(output_format: str):
    """시스템 건강도 확인
    
    Examples:
        greeum dashboard health
        greeum dashboard health --format detailed
        greeum dashboard health --format json
    """
    try:
        dashboard_system = get_dashboard_system()
        health_data = dashboard_system.get_system_health()
        
        if output_format == 'json':
            click.echo(json.dumps(health_data.__dict__, indent=2, ensure_ascii=False, default=str))
        elif output_format == 'detailed':
            _display_health_detailed(health_data)
        else:
            _display_health_simple(health_data)
            
    except Exception as e:
        click.echo(f"💥 시스템 건강도 확인 실패: {e}")


@dashboard.command()
@click.option('--output', '-o', required=True, help='리포트 파일 저장 경로')
@click.option('--include-details/--no-details', default=True, 
              help='상세 계층 분석 포함 여부')
def export(output: str, include_details: bool):
    """완전한 대시보드 리포트 내보내기
    
    Examples:
        greeum dashboard export --output full_report.json
        greeum dashboard export --output simple_report.json --no-details
    """
    try:
        dashboard_system = get_dashboard_system()
        
        success = dashboard_system.export_dashboard_report(
            output_path=output,
            include_details=include_details
        )
        
        if success:
            file_size = Path(output).stat().st_size / 1024  # KB
            click.echo(f"✅ 대시보드 리포트 생성 완료: {output} ({file_size:.1f} KB)")
            
            if include_details:
                click.echo("📊 상세 계층 분석 포함")
            else:
                click.echo("📋 기본 개요만 포함")
        else:
            click.echo("[ERROR] 리포트 생성에 실패했습니다")
            
    except Exception as e:
        click.echo(f"💥 리포트 내보내기 실패: {e}")


@dashboard.command()
def watch():
    """실시간 대시보드 모니터링 (개발 중)
    
    미래 구현 예정: 터미널에서 실시간으로 시스템 상태를 모니터링
    """
    click.echo("⏰ 실시간 대시보드 기능은 v2.6.3에서 구현될 예정입니다")
    click.echo("현재는 'greeum dashboard overview'를 주기적으로 실행해주세요")


# 출력 헬퍼 함수들

def _display_overview_friendly(data: dict):
    """사용자 친화적 개요 출력"""
    stats = data['memory_stats']
    health = data['system_health']
    
    click.echo("[MEMORY] Greeum Memory Dashboard")
    click.echo("=" * 50)
    
    # 기본 통계
    click.echo(f"📊 전체 메모리: {stats['total_memories']}개")
    click.echo(f"   [MEMORY] Working Memory: {stats['working_memory_count']}개")
    click.echo(f"   [FAST] STM: {stats['stm_count']}개")
    click.echo(f"   🏛️  LTM: {stats['ltm_count']}개")
    
    click.echo()
    
    # 시스템 건강도
    health_percent = health['overall_health'] * 100
    health_emoji = "🟢" if health_percent >= 80 else "🟡" if health_percent >= 60 else "🔴"
    click.echo(f"{health_emoji} 시스템 건강도: {health_percent:.1f}%")
    
    # 용량 정보
    click.echo(f"💾 총 용량: {stats['total_size_mb']:.1f} MB")
    click.echo(f"[FAST] 평균 검색 시간: {health['avg_search_time_ms']:.1f}ms")
    
    # 경고사항
    if health['warnings']:
        click.echo("\n⚠️  주의사항:")
        for warning in health['warnings']:
            click.echo(f"   • {warning}")
    
    # 권장사항
    if health['recommendations']:
        click.echo("\n💡 권장사항:")
        for rec in health['recommendations']:
            click.echo(f"   • {rec}")
    
    # 인기 키워드
    click.echo("\n🔥 인기 키워드:")
    for keyword, count in stats['popular_keywords'][:5]:
        click.echo(f"   #{keyword} ({count}회)")


def _display_layer_analytics_friendly(analytics):
    """계층 분석 친화적 출력"""
    layer_name = {
        MemoryLayerType.WORKING: "Working Memory",
        MemoryLayerType.STM: "Short-term Memory", 
        MemoryLayerType.LTM: "Long-term Memory"
    }[analytics.layer_type]
    
    layer_emoji = {
        MemoryLayerType.WORKING: "[MEMORY]",
        MemoryLayerType.STM: "[FAST]",
        MemoryLayerType.LTM: "🏛️"
    }[analytics.layer_type]
    
    click.echo(f"{layer_emoji} {layer_name} 상세 분석")
    click.echo("=" * 40)
    
    click.echo(f"📊 총 메모리 수: {analytics.count}개")
    click.echo(f"⭐ 평균 중요도: {analytics.avg_importance:.2f}")
    click.echo(f"📏 평균 내용 길이: {analytics.avg_content_length}자")
    click.echo(f"🔑 키워드 다양성: {analytics.keyword_diversity}개 고유 키워드")
    
    click.echo(f"\n⏰ 시간 분석:")
    click.echo(f"   평균 보존 기간: {analytics.avg_age_days:.1f}일")
    click.echo(f"   가장 오래된 메모리: {analytics.oldest_memory_days:.1f}일")
    click.echo(f"   가장 최근 메모리: {analytics.newest_memory_hours:.1f}시간 전")
    
    if analytics.retention_rate > 0:
        click.echo(f"[IMPROVE] LTM 승급률: {analytics.retention_rate * 100:.1f}%")
    
    # 인기 태그
    if analytics.tag_usage:
        click.echo(f"\n🏷️  인기 태그:")
        sorted_tags = sorted(analytics.tag_usage.items(), key=lambda x: x[1], reverse=True)
        for tag, count in sorted_tags[:5]:
            click.echo(f"   #{tag} ({count}회)")


def _display_health_simple(health):
    """간단한 건강도 출력"""
    health_percent = health.overall_health * 100
    health_emoji = "🟢" if health_percent >= 80 else "🟡" if health_percent >= 60 else "🔴"
    
    click.echo(f"{health_emoji} 시스템 건강도: {health_percent:.1f}%")
    
    if health_percent >= 80:
        click.echo("✅ 시스템이 정상적으로 작동하고 있습니다")
    elif health_percent >= 60:
        click.echo("⚠️  시스템에 약간의 주의가 필요합니다")
    else:
        click.echo("🔴 시스템 점검이 필요합니다")


def _display_health_detailed(health):
    """상세한 건강도 출력"""
    _display_health_simple(health)
    
    click.echo(f"\n[IMPROVE] 성능 지표:")
    click.echo(f"   검색 속도: {health.avg_search_time_ms:.1f}ms")
    click.echo(f"   메모리 사용량: {health.memory_usage_mb:.1f}MB")
    click.echo(f"   데이터베이스 크기: {health.database_size_mb:.1f}MB")
    
    click.echo(f"\n🎯 품질 지표:")
    click.echo(f"   평균 품질 점수: {health.avg_quality_score:.2f}")
    click.echo(f"   중복률: {health.duplicate_rate * 100:.1f}%")
    click.echo(f"   승급 성공률: {health.promotion_success_rate * 100:.1f}%")
    
    if health.warnings:
        click.echo(f"\n⚠️  경고:")
        for warning in health.warnings:
            click.echo(f"   • {warning}")
    
    if health.recommendations:
        click.echo(f"\n💡 권장사항:")
        for rec in health.recommendations:
            click.echo(f"   • {rec}")


# 메인 CLI에 대시보드 명령어 그룹 등록을 위한 함수
def register_dashboard_commands(cli_group):
    """대시보드 명령어들을 메인 CLI에 등록"""
    cli_group.add_command(dashboard)


if __name__ == "__main__":
    # 개별 테스트용
    dashboard()