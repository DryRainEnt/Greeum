#!/usr/bin/env python
import os
import sys
import json
import argparse
from datetime import datetime
import logging
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import click

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('memory_cli')

# 모듈 디렉토리 추가
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

# 콘솔 설정
console = Console()

# 동적 버전 로드
try:
    from . import __version__
except ImportError:
    try:
        import greeum
        __version__ = greeum.__version__
    except (ImportError, AttributeError):
        __version__ = "2.1.0"

@click.group()
@click.version_option(version=__version__)
def main():
    """Greeum - LLM 독립적 기억 시스템 CLI"""
    pass

@main.command("init")
@click.option("--db-path", default=None, help="데이터베이스 경로 (기본: data/memory.db)")
@click.option("--use-embedding", default="simple", help="사용할 임베딩 모델 (simple, sentence-transformer, openai)")
@click.option("--openai-key", default=None, help="OpenAI API 키 (OpenAI 임베딩 모델 사용시 필요)")
def init_command(db_path, use_embedding, openai_key):
    """메모리 엔진 초기화"""
    try:
        # 데이터 디렉토리 확인
        data_dir = os.path.dirname(db_path or "data/memory.db")
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir)
            console.print(f"[green]데이터 디렉토리 생성: {data_dir}[/green]")
        
        # 데이터베이스 초기화
        from greeum import DatabaseManager
        db_path = db_path or os.path.join("data", "memory.db")
        db_manager = DatabaseManager(db_path)
        console.print(f"[green]데이터베이스 초기화 완료: {db_path}[/green]")
        
        # 임베딩 모델 초기화
        if use_embedding == "simple":
            from greeum.embedding_models import SimpleEmbeddingModel, register_embedding_model
            model = SimpleEmbeddingModel()
            register_embedding_model("default", model, set_as_default=True)
            console.print("[green]간단한 임베딩 모델 초기화 완료[/green]")
        elif use_embedding == "sentence-transformer":
            from greeum.embedding_models import init_sentence_transformer
            init_sentence_transformer()
            console.print("[green]SentenceTransformer 임베딩 모델 초기화 완료[/green]")
        elif use_embedding == "openai":
            if not openai_key:
                console.print("[yellow]OpenAI API 키가 필요합니다. --openai-key 옵션을 사용하세요.[/yellow]")
                return
            from greeum.embedding_models import init_openai
            init_openai(api_key=openai_key)
            console.print("[green]OpenAI 임베딩 모델 초기화 완료[/green]")
        else:
            console.print(f"[red]지원하지 않는 임베딩 모델: {use_embedding}[/red]")
            return
        
        console.print("[bold green]메모리 엔진 초기화 완료![/bold green]")
    except Exception as e:
        console.print(f"[bold red]초기화 오류: {str(e)}[/bold red]")

@main.command("add-memory")
@click.argument("text")
@click.option("--db-path", default=None, help="데이터베이스 경로 (기본: data/memory.db)")
@click.option("--keywords", default=None, help="키워드 (쉼표로 구분)")
@click.option("--tags", default=None, help="태그 (쉼표로 구분)")
@click.option("--importance", default=None, type=float, help="중요도 (0~1)")
def add_memory_command(text, db_path, keywords, tags, importance):
    """새 기억 추가"""
    try:
        # 데이터베이스 연결
        from greeum import DatabaseManager
        db_path = db_path or os.path.join("data", "memory.db")
        db_manager = DatabaseManager(db_path)
        
        # 텍스트 처리
        from greeum.text_utils import process_user_input
        
        # 사용자가 제공한 키워드와 태그 처리
        user_keywords = keywords.split(",") if keywords else None
        user_tags = tags.split(",") if tags else None
        
        # 텍스트 처리
        result = process_user_input(text)
        
        # 사용자 제공 값 우선 적용
        if user_keywords:
            result["keywords"] = user_keywords
        if user_tags:
            result["tags"] = user_tags
        if importance is not None:
            result["importance"] = importance
        
        # 타임스탬프 및 해시 추가
        from hashlib import sha256
        timestamp = datetime.now().isoformat()
        result["timestamp"] = timestamp
        
        # 블록 인덱스 생성 (마지막 블록 + 1)
        last_block = db_manager.get_blocks(limit=1)
        block_index = 0
        if last_block:
            block_index = last_block[0].get("block_index", -1) + 1
        
        # 이전 해시 가져오기
        prev_hash = ""
        if block_index > 0:
            prev_block = db_manager.get_block(block_index - 1)
            if prev_block:
                prev_hash = prev_block.get("hash", "")
        
        # 해시 계산
        hash_data = {
            "block_index": block_index,
            "timestamp": timestamp,
            "context": text,
            "prev_hash": prev_hash
        }
        hash_str = json.dumps(hash_data, sort_keys=True)
        hash_value = sha256(hash_str.encode()).hexdigest()
        
        # 최종 블록 데이터
        block_data = {
            "block_index": block_index,
            "timestamp": timestamp,
            "context": text,
            "keywords": result.get("keywords", []),
            "tags": result.get("tags", []),
            "embedding": result.get("embedding", []),
            "importance": result.get("importance", 0.5),
            "hash": hash_value,
            "prev_hash": prev_hash
        }
        
        # 데이터베이스에 추가
        db_manager.add_block(block_data)
        
        # 출력
        console.print(f"[green]기억 블록 추가 완료: #{block_index}[/green]")
        console.print(Panel.fit(
            f"[bold]컨텍스트:[/bold] {text}\n"
            f"[bold]키워드:[/bold] {', '.join(block_data['keywords'])}\n"
            f"[bold]태그:[/bold] {', '.join(block_data['tags'])}\n"
            f"[bold]중요도:[/bold] {block_data['importance']:.2f}"
        ))
    except Exception as e:
        console.print(f"[bold red]기억 추가 오류: {str(e)}[/bold red]")

@main.command("search")
@click.argument("query")
@click.option("--db-path", default=None, help="데이터베이스 경로 (기본: data/memory.db)")
@click.option("--limit", default=5, help="결과 개수 제한")
@click.option("--mode", default="hybrid", help="검색 모드 (embedding, keyword, temporal, hybrid)")
@click.option("--slot", type=click.Choice(['A', 'B', 'C']), help="앵커 슬롯 기반 국소 검색")
@click.option("--radius", default=2, type=int, help="국소 검색 반경 (홉 수)")
@click.option("--fallback", is_flag=True, default=True, help="국소 검색 실패시 전역 검색")
def search_command(query, db_path, limit, mode, slot, radius, fallback):
    """기억 검색"""
    try:
        # 데이터베이스 연결
        from greeum import DatabaseManager
        db_path = db_path or os.path.join("data", "memory.db")
        db_manager = DatabaseManager(db_path)
        
        blocks = []
        
        # 앵커 기반 검색이 요청된 경우
        if slot:
            try:
                from greeum.core.search_engine import SearchEngine
                search_engine = SearchEngine(db_manager)
                
                # 앵커 기반 국소 검색 수행
                result = search_engine.search(
                    query=query,
                    top_k=limit,
                    slot=slot,
                    radius=radius,
                    fallback=fallback
                )
                
                blocks = result.get('blocks', [])
                metadata = result.get('metadata', {})
                
                # 검색 정보 출력
                console.print(f"[blue]앵커 슬롯 {slot} 기반 검색 (반경: {radius}홉)[/blue]")
                if metadata.get('local_search_used'):
                    console.print(f"[green]✓ 국소 검색 성공 ({metadata.get('local_results', 0)}개 결과)[/green]")
                if metadata.get('fallback_used'):
                    console.print(f"[yellow]⚠ 전역 검색으로 후퇴 ({metadata.get('fallback_results', 0)}개 추가)[/yellow]")
                    
            except ImportError:
                console.print("[red]앵커 기반 검색을 사용할 수 없습니다. 기본 검색을 사용합니다.[/red]")
                slot = None  # 기본 검색으로 후퇴
            except Exception as e:
                console.print(f"[red]앵커 검색 오류: {e}. 기본 검색을 사용합니다.[/red]")
                slot = None  # 기본 검색으로 후퇴
        
        # 기본 검색 모드 (앵커 기반이 아닌 경우)
        if not slot:
            # 검색 모드에 따라 다른 방법 사용
            if mode == "embedding":
                # 임베딩 검색
                from greeum.embedding_models import get_embedding
                embedding = get_embedding(query)
                blocks = db_manager.search_blocks_by_embedding(embedding, top_k=limit)
                console.print("[blue]임베딩 검색 결과:[/blue]")
            elif mode == "keyword":
                # 키워드 검색
                keywords = query.split()
                blocks = db_manager.search_blocks_by_keyword(keywords, limit=limit)
                console.print("[blue]키워드 검색 결과:[/blue]")
            elif mode == "temporal":
                # 시간적 검색
                from greeum.temporal_reasoner import TemporalReasoner
                reasoner = TemporalReasoner(db_manager)
                result = reasoner.search_by_time_reference(query)
                blocks = result.get("blocks", [])
                
                # 시간 참조 정보 출력
                time_ref = result.get("time_ref")
                if time_ref:
                    console.print(f"[blue]시간 표현 감지: {time_ref.get('term')}[/blue]")
                    from_date = time_ref.get("from_date")
                    to_date = time_ref.get("to_date")
                    if from_date and to_date:
                        console.print(f"[blue]검색 범위: {from_date} ~ {to_date}[/blue]")
                console.print("[blue]시간적 검색 결과:[/blue]")
            elif mode == "hybrid":
                # 하이브리드 검색 (기본값)
                from greeum.temporal_reasoner import TemporalReasoner, get_embedding
                reasoner = TemporalReasoner(db_manager)
                embedding = get_embedding(query)
                keywords = query.split()
                result = reasoner.hybrid_search(query, embedding, keywords, top_k=limit)
                blocks = result.get("blocks", [])
                console.print("[blue]하이브리드 검색 결과:[/blue]")
            else:
                console.print(f"[red]지원하지 않는 검색 모드: {mode}[/red]")
                return
        
        # 결과 출력
        if not blocks:
            console.print("[yellow]검색 결과가 없습니다.[/yellow]")
            return
        
        table = Table(title=f"'{query}' 검색 결과")
        table.add_column("블록 #", justify="right", style="cyan")
        table.add_column("날짜", style="blue")
        table.add_column("컨텍스트", style="green")
        table.add_column("키워드", style="yellow")
        table.add_column("관련도", justify="right", style="magenta")
        
        for block in blocks:
            # 날짜 형식 변환
            try:
                timestamp = datetime.fromisoformat(block.get("timestamp", ""))
                date_str = timestamp.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = block.get("timestamp", "")[:16]
            
            # 컨텍스트 요약 (너무 길면 자름)
            context = block.get("context", "")
            if len(context) > 50:
                context = context[:47] + "..."
            
            # 키워드 출력
            keywords = ", ".join(block.get("keywords", [])[:3])
            
            # 관련도 점수
            score = ""
            if "similarity" in block:
                score = f"{block['similarity']:.2f}"
            elif "relevance_score" in block:
                score = f"{block['relevance_score']:.2f}"
            
            table.add_row(
                str(block.get("block_index", "")),
                date_str,
                context,
                keywords,
                score
            )
        
        console.print(table)
        
        # 블록 상세 보기 안내
        console.print("\n[bold]블록 상세 정보를 보려면:[/bold]")
        console.print("memory-engine get-block <블록 번호>")
        
    except Exception as e:
        console.print(f"[bold red]검색 오류: {str(e)}[/bold red]")

@main.command("get-block")
@click.argument("block_index", type=int)
@click.option("--db-path", default=None, help="데이터베이스 경로 (기본: data/memory.db)")
def get_block_command(block_index, db_path):
    """특정 블록 상세 정보 조회"""
    try:
        # 데이터베이스 연결
        from greeum import DatabaseManager
        db_path = db_path or os.path.join("data", "memory.db")
        db_manager = DatabaseManager(db_path)
        
        # 블록 조회
        block = db_manager.get_block(block_index)
        
        if not block:
            console.print(f"[yellow]블록 #{block_index}를 찾을 수 없습니다.[/yellow]")
            return
        
        # 시간 형식 변환
        try:
            timestamp = datetime.fromisoformat(block.get("timestamp", ""))
            date_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        except:
            date_str = block.get("timestamp", "")
        
        # 블록 정보 출력
        console.print(Panel.fit(
            f"[bold cyan]블록 #{block_index}[/bold cyan] [blue]({date_str})[/blue]\n\n"
            f"[bold]컨텍스트:[/bold]\n{block.get('context', '')}\n\n"
            f"[bold]키워드:[/bold] {', '.join(block.get('keywords', []))}\n"
            f"[bold]태그:[/bold] {', '.join(block.get('tags', []))}\n"
            f"[bold]중요도:[/bold] {block.get('importance', 0):.2f}\n\n"
            f"[bold]해시:[/bold] {block.get('hash', '')[:16]}...\n"
            f"[bold]이전 해시:[/bold] {block.get('prev_hash', '')[:16]}..."
        ))
        
        # 수정 이력 확인
        try:
            from greeum.memory_evolution import MemoryEvolutionManager
            evolution_manager = MemoryEvolutionManager(db_manager)
            revisions = evolution_manager.get_revision_chain(block_index)
            
            if len(revisions) > 1:
                console.print(f"\n[blue]이 블록은 {len(revisions)} 개의 수정 이력이 있습니다.[/blue]")
                for i, rev in enumerate(revisions):
                    if rev.get("block_index") == block_index:
                        continue
                    console.print(f"  - 수정 #{i+1}: 블록 #{rev.get('block_index')} ({rev.get('timestamp', '')[:16]})")
        except ImportError:
            pass
            
    except Exception as e:
        console.print(f"[bold red]블록 조회 오류: {str(e)}[/bold red]")

@main.command("update-memory")
@click.argument("block_index", type=int)
@click.argument("new_text")
@click.option("--db-path", default=None, help="데이터베이스 경로 (기본: data/memory.db)")
@click.option("--reason", default="내용 업데이트", help="변경 이유")
def update_memory_command(block_index, new_text, db_path, reason):
    """기존 기억 업데이트"""
    try:
        # 데이터베이스 연결
        from greeum import DatabaseManager, MemoryEvolutionManager
        db_path = db_path or os.path.join("data", "memory.db")
        db_manager = DatabaseManager(db_path)
        
        # 진화 관리자 초기화
        evolution_manager = MemoryEvolutionManager(db_manager)
        
        # 수정본 생성
        revision = evolution_manager.create_memory_revision(
            original_block_index=block_index,
            new_context=new_text,
            reason=reason
        )
        
        if revision:
            console.print(f"[green]기억 블록 업데이트 완료: #{revision['block_index']}[/green]")
            console.print(Panel.fit(
                f"[bold]원본 블록:[/bold] #{block_index}\n"
                f"[bold]수정 이유:[/bold] {reason}\n"
                f"[bold]새 내용:[/bold] {new_text}\n"
            ))
        else:
            console.print("[red]기억 업데이트 실패[/red]")
            
    except Exception as e:
        console.print(f"[bold red]업데이트 오류: {str(e)}[/bold red]")

@main.command("recent-memories")
@click.option("--limit", default=10, help="표시할 기억 개수")
@click.option("--db-path", default=None, help="데이터베이스 경로 (기본: data/memory.db)")
def recent_memories_command(limit, db_path):
    """최근 기억 목록 조회"""
    try:
        # 데이터베이스 연결
        from greeum import DatabaseManager
        db_path = db_path or os.path.join("data", "memory.db")
        db_manager = DatabaseManager(db_path)
        
        # 최근 블록 조회
        blocks = db_manager.get_blocks(limit=limit)
        
        if not blocks:
            console.print("[yellow]저장된 기억이 없습니다.[/yellow]")
            return
        
        # 테이블 생성
        table = Table(title=f"최근 {limit}개 기억")
        table.add_column("블록 #", justify="right", style="cyan")
        table.add_column("날짜", style="blue")
        table.add_column("컨텍스트", style="green")
        table.add_column("중요도", style="magenta")
        
        for block in blocks:
            # 날짜 형식 변환
            try:
                timestamp = datetime.fromisoformat(block.get("timestamp", ""))
                date_str = timestamp.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = block.get("timestamp", "")[:16]
            
            # 컨텍스트 요약
            context = block.get("context", "")
            if len(context) > 50:
                context = context[:47] + "..."
            
            table.add_row(
                str(block.get("block_index", "")),
                date_str,
                context,
                f"{block.get('importance', 0):.2f}"
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]기억 조회 오류: {str(e)}[/bold red]")

# 앵커 명령어 등록
from .cli.anchors import register_anchors_commands
register_anchors_commands(main)

if __name__ == "__main__":
    main() 