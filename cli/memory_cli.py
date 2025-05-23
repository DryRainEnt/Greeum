#!/usr/bin/env python
import sys
import argparse
from pathlib import Path
import time
from datetime import datetime
import uuid
import json
import os

# 상위 디렉터리 추가하여 memory_engine 패키지 임포트
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

from greeum import BlockManager, STMManager, CacheManager, PromptWrapper
from greeum.text_utils import process_user_input, extract_keywords
from greeum.embedding_models import get_embedding

def print_colored(text, color="white"):
    """색상 있는 텍스트 출력"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")

def add_memory(args):
    """기억 추가하기"""
    block_manager = BlockManager()
    
    if args.file:
        # 파일에서 컨텍스트 읽기
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                context = f.read()
        except Exception as e:
            print_colored(f"파일 읽기 오류: {e}", "red")
            return
    else:
        context = args.context
    
    if not context:
        print_colored("컨텍스트를 입력해주세요.", "red")
        return
    
    # 처리할 데이터 준비
    processed = process_user_input(context)
    
    # 키워드 & 태그 오버라이드 (지정된 경우)
    if args.keywords:
        processed["keywords"] = args.keywords.split(',')
    
    if args.tags:
        processed["tags"] = args.tags.split(',')
    
    # 중요도 오버라이드 (지정된 경우)
    if args.importance is not None:
        processed["importance"] = args.importance
    
    # 블록 추가
    block = block_manager.add_block(
        context=processed["context"],
        keywords=processed["keywords"],
        tags=processed["tags"],
        embedding=processed["embedding"],
        importance=processed["importance"]
    )
    
    print_colored("기억이 성공적으로 추가되었습니다!", "green")
    print_colored(f"블록 인덱스: {block['block_index']}", "cyan")
    print_colored(f"키워드: {', '.join(block['keywords'])}", "yellow")
    print_colored(f"태그: {', '.join(block['tags'])}", "purple")
    print_colored(f"중요도: {block['importance']:.2f}", "blue")

def add_stm(args):
    """단기 기억 추가하기"""
    stm_manager = STMManager()
    
    if not args.content:
        print_colored("내용을 입력해주세요.", "red")
        return
    
    memory_data = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "content": args.content,
        "speaker": args.speaker or "user"
    }
    
    stm_manager.add_memory(memory_data)
    print_colored("단기 기억이 추가되었습니다!", "green")

def search_memory(args):
    """기억 검색하기"""
    block_manager = BlockManager()
    
    if args.keywords:
        keywords = args.keywords.split(',')
        results = block_manager.search_by_keywords(keywords)
        
        print_colored(f"키워드 '{', '.join(keywords)}'로 검색한 결과:", "cyan")
        if not results:
            print_colored("검색 결과가 없습니다.", "yellow")
            return
    else:
        # 가장 최근 5개 블록 표시
        results = block_manager.get_blocks()[-5:]
        print_colored(f"최근 기억 {len(results)}개:", "cyan")
    
    for block in results:
        print_colored(f"--------- 블록 #{block['block_index']} ---------", "purple")
        print_colored(f"시간: {block['timestamp']}", "blue")
        print_colored(f"키워드: {', '.join(block['keywords'])}", "yellow")
        print_colored(f"태그: {', '.join(block['tags'])}", "green")
        print_colored(f"중요도: {block['importance']:.2f}", "blue")
        print_colored(f"내용: {block['context']}", "white")
        print()

def get_stm(args):
    """단기 기억 조회하기"""
    stm_manager = STMManager()
    
    count = args.count or 5
    memories = stm_manager.get_recent_memories(count=count)
    
    print_colored(f"최근 단기 기억 {len(memories)}개:", "cyan")
    if not memories:
        print_colored("단기 기억이 없습니다.", "yellow")
        return
    
    for memory in memories:
        timestamp = memory.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(timestamp)
            timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            pass
            
        print_colored(f"--------- ID: {memory.get('id', 'unknown')} ---------", "purple")
        print_colored(f"시간: {timestamp}", "blue")
        print_colored(f"화자: {memory.get('speaker', 'unknown')}", "yellow")
        print_colored(f"내용: {memory.get('content', '')}", "white")
        print()

def generate_prompt(args):
    """프롬프트 생성하기"""
    db_path = args.db_path or os.path.join(parent_dir, "data", "memory.db")
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    from greeum import DatabaseManager
    db_m = DatabaseManager(db_path)
    bm = BlockManager(db_m)
    sm = STMManager(db_m)
    cache_m = CacheManager(block_manager=bm, stm_manager=sm)
    prompt_wrapper = PromptWrapper(cache_manager=cache_m, stm_manager=sm)
    
    if not args.input:
        print_colored("입력 텍스트를 지정해주세요.", "red")
        return
    
    user_input = args.input
    
    embedding = get_embedding(user_input)
    
    keywords = extract_keywords(user_input)
    
    cache_m.update_cache(query_text=user_input, query_embedding=embedding, query_keywords=keywords)
    
    prompt = prompt_wrapper.compose_prompt(user_input)
    
    if args.output:
        # 파일에 저장
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(prompt)
            print_colored(f"프롬프트가 {args.output} 파일에 저장되었습니다.", "green")
        except Exception as e:
            print_colored(f"파일 저장 오류: {e}", "red")
    else:
        # 화면에 출력
        print_colored("생성된 프롬프트:", "cyan")
        print()
        print(prompt)

def clear_memories(args):
    """기억 초기화하기"""
    if args.type == "stm" or args.type == "all":
        stm_manager = STMManager()
        stm_manager.clear_all()
        print_colored("단기 기억이 초기화되었습니다.", "green")
    
    if args.type == "cache" or args.type == "all":
        cache_manager = CacheManager()
        cache_manager.clear_cache()
        print_colored("웨이포인트 캐시가 초기화되었습니다.", "green")
    
    if args.type == "blocks" or args.type == "all":
        data_path = "data/block_memory.jsonl"
        if os.path.exists(data_path):
            # 백업 생성
            backup_path = f"data/block_memory_backup_{int(time.time())}.jsonl"
            try:
                os.rename(data_path, backup_path)
                print_colored(f"기존 블록 데이터가 {backup_path}에 백업되었습니다.", "yellow")
                # 새 파일 생성
                with open(data_path, 'w', encoding='utf-8') as f:
                    pass  # 빈 파일 생성
                print_colored("블록 메모리가 초기화되었습니다.", "green")
            except Exception as e:
                print_colored(f"블록 메모리 초기화 오류: {e}", "red")
        else:
            print_colored("블록 메모리 파일이 존재하지 않습니다.", "yellow")

def verify_blocks(args):
    """블록 체인 무결성 검증"""
    block_manager = BlockManager()
    is_valid = block_manager.verify_blocks()
    
    if is_valid:
        print_colored("블록체인 무결성 검증 성공: 모든 블록이 유효합니다.", "green")
    else:
        print_colored("블록체인 무결성 검증 실패: 손상된 블록이 있습니다.", "red")

def main():
    parser = argparse.ArgumentParser(description="Memory Block Engine CLI")
    subparsers = parser.add_subparsers(dest="command", help="실행할 명령")
    
    # 블록 추가 커맨드
    add_parser = subparsers.add_parser("add", help="장기 기억 블록 추가")
    add_parser.add_argument("-c", "--context", help="기억할 내용")
    add_parser.add_argument("-f", "--file", help="내용이 담긴 파일")
    add_parser.add_argument("-k", "--keywords", help="키워드 (쉼표로 구분)")
    add_parser.add_argument("-t", "--tags", help="태그 (쉼표로 구분)")
    add_parser.add_argument("-i", "--importance", type=float, help="중요도 (0~1)")
    
    # 단기기억 추가 커맨드
    stm_parser = subparsers.add_parser("stm", help="단기 기억 추가")
    stm_parser.add_argument("content", help="기억할 내용")
    stm_parser.add_argument("-s", "--speaker", help="화자 (기본값: user)")
    
    # 기억 검색 커맨드
    search_parser = subparsers.add_parser("search", help="기억 검색")
    search_parser.add_argument("-k", "--keywords", help="검색할 키워드 (쉼표로 구분)")
    
    # 단기기억 조회 커맨드
    get_stm_parser = subparsers.add_parser("get-stm", help="단기 기억 조회")
    get_stm_parser.add_argument("-c", "--count", type=int, help="조회할 기억 수 (기본값: 5)")
    
    # 프롬프트 생성 커맨드
    prompt_parser = subparsers.add_parser("prompt", help="현재 컨텍스트에 맞는 프롬프트 생성")
    prompt_parser.add_argument("-i", "--input", help="사용자 입력 텍스트")
    prompt_parser.add_argument("-o", "--output", help="출력 파일 경로 (지정하지 않으면 화면에 출력)")
    prompt_parser.add_argument("--db-path", default=None, help="데이터베이스 경로 (기본: data/memory.db)")
    
    # 메모리 초기화 커맨드
    clear_parser = subparsers.add_parser("clear", help="메모리 초기화")
    clear_parser.add_argument("type", choices=["stm", "cache", "blocks", "all"], 
                             help="초기화할 메모리 유형")
    
    # 블록 체인 검증 커맨드
    verify_parser = subparsers.add_parser("verify", help="블록체인 무결성 검증")
    
    args = parser.parse_args()
    
    # 명령어 실행
    if args.command == "add":
        add_memory(args)
    elif args.command == "stm":
        add_stm(args)
    elif args.command == "search":
        search_memory(args)
    elif args.command == "get-stm":
        get_stm(args)
    elif args.command == "prompt":
        generate_prompt(args)
    elif args.command == "clear":
        clear_memories(args)
    elif args.command == "verify":
        verify_blocks(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 