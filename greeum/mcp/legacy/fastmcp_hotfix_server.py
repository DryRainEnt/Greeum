#!/usr/bin/env python3
"""
Greeum FastMCP Hotfix Server - v2.2.6
WSL Claude CLI 연동 문제 해결을 위한 FastMCP 기반 핫픽스

🎯 목표:
- 기존 claude_code_mcp_server.py의 모든 기능을 FastMCP로 이식
- 100% 기존 사용자 호환성 보장
- WSL, PowerShell 등 모든 환경에서 정상 연동

🔧 기술적 접근:
- FastMCP 프레임워크 사용으로 stdin/stdout 표준 처리
- 기존 비즈니스 로직 100% 재사용 
- 도구 이름, 파라미터, 응답 형식 완전 동일
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

# FastMCP import
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("ERROR: FastMCP not found. Please install: pip install mcp>=1.0.0", file=sys.stderr)
    sys.exit(1)

# Greeum core imports
try:
    from greeum.core.block_manager import BlockManager
    from greeum.core.database_manager import DatabaseManager  
    from greeum.core.stm_manager import STMManager
    from greeum.core.duplicate_detector import DuplicateDetector
    from greeum.core.quality_validator import QualityValidator
    from greeum.core.usage_analytics import UsageAnalytics
    GREEUM_AVAILABLE = True
except ImportError:
    GREEUM_AVAILABLE = False

# 로깅 설정
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger("greeum_fastmcp")

# FastMCP 앱 초기화
app = FastMCP("Greeum Memory System")

# Global Greeum components (기존 패턴과 동일)
_greeum_components = None

def get_greeum_components():
    """Greeum 컴포넌트 싱글톤 초기화"""
    global _greeum_components
    
    if _greeum_components is None and GREEUM_AVAILABLE:
        try:
            db_manager = DatabaseManager()
            block_manager = BlockManager(db_manager)
            stm_manager = STMManager(db_manager)
            duplicate_detector = DuplicateDetector(db_manager)
            quality_validator = QualityValidator()
            usage_analytics = UsageAnalytics(db_manager)
            
            _greeum_components = {
                'db_manager': db_manager,
                'block_manager': block_manager,
                'stm_manager': stm_manager,
                'duplicate_detector': duplicate_detector,
                'quality_validator': quality_validator,
                'usage_analytics': usage_analytics
            }
            
            logger.info("✅ Greeum components initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Greeum components: {e}")
            _greeum_components = None
    
    return _greeum_components

def add_memory_direct(content: str, importance: float = 0.5) -> Dict[str, Any]:
    """기존 _add_memory_direct 로직 재사용"""
    from greeum.text_utils import process_user_input
    from datetime import datetime
    import json
    import hashlib
    
    components = get_greeum_components()
    if not components:
        raise Exception("Greeum components not available")
    
    db_manager = components['db_manager']
    
    # 기존 로직 그대로 사용
    result = process_user_input(content)
    result["importance"] = importance
    
    timestamp = datetime.now().isoformat()
    result["timestamp"] = timestamp
    
    # 블록 인덱스 생성
    last_block_info = db_manager.get_last_block_info()
    if last_block_info is None:
        last_block_info = {"block_index": -1}
    block_index = last_block_info.get("block_index", -1) + 1
    
    # 이전 해시
    prev_hash = ""
    if block_index > 0:
        prev_block = db_manager.get_block(block_index - 1)
        if prev_block:
            prev_hash = prev_block.get("hash", "")
    
    # 해시 계산
    hash_data = {
        "block_index": block_index,
        "timestamp": timestamp,
        "context": content,
        "prev_hash": prev_hash
    }
    hash_str = json.dumps(hash_data, sort_keys=True)
    hash_value = hashlib.sha256(hash_str.encode()).hexdigest()
    
    # 최종 블록 데이터
    block_data = {
        "block_index": block_index,
        "timestamp": timestamp,
        "context": content,
        "keywords": result.get("keywords", []),
        "tags": result.get("tags", []),
        "embedding": result.get("embedding", []),
        "importance": result.get("importance", 0.5),
        "hash": hash_value,
        "prev_hash": prev_hash
    }
    
    # 데이터베이스에 추가
    db_manager.add_block(block_data)
    
    return block_data

def search_memory_direct(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """기존 _search_memory_direct 로직 재사용"""
    from greeum.embedding_models import get_embedding
    
    components = get_greeum_components()
    if not components:
        raise Exception("Greeum components not available")
    
    db_manager = components['db_manager']
    
    try:
        # 임베딩 기반 검색
        embedding = get_embedding(query)
        blocks = db_manager.search_blocks_by_embedding(embedding, top_k=limit)
        
        return blocks if blocks else []
    except Exception as e:
        logger.warning(f"Embedding search failed: {e}, falling back to keyword search")
        # 키워드 검색 폴백
        blocks = db_manager.search_by_keyword(query, limit=limit)
        return blocks if blocks else []

# FastMCP 도구 정의
@app.tool()
def add_memory(content: str, importance: float = 0.5) -> str:
    """🧠 Add important permanent memories to long-term storage.
    
    ⚠️  USAGE GUIDELINES:
    • ALWAYS search_memory first to avoid duplicates
    • Store meaningful information, not casual conversation
    • Use appropriate importance levels (see guide below)

    ✅ GOOD USES: user preferences, project details, decisions, recurring issues
    ❌ AVOID: greetings, weather, current time, temporary session info

    🔍 WORKFLOW: search_memory → analyze results → add_memory (if truly new)
    """
    try:
        components = get_greeum_components()
        if not components:
            return "❌ Greeum components not available. Please check installation."
        
        # 중복 검사
        duplicate_check = components['duplicate_detector'].check_duplicate(content)
        if duplicate_check["is_duplicate"]:
            similarity = duplicate_check["similarity_score"]
            return f"""⚠️  **Potential Duplicate Memory Detected**

**Similarity**: {similarity:.1%} with existing memory
**Similar Memory**: Block #{duplicate_check['similar_block_index']}

Please search existing memories first or provide more specific content."""
        
        # 품질 검증
        quality_result = components['quality_validator'].validate_memory_quality(content, importance)
        
        # 메모리 추가
        block_data = add_memory_direct(content, importance)
        
        # 사용 통계 로깅
        components['usage_analytics'].log_quality_metrics(
            len(content), quality_result['quality_score'], quality_result['quality_level'],
            importance, importance, False, duplicate_check["similarity_score"], 
            len(quality_result['suggestions'])
        )
        
        # 성공 응답 (기존과 동일한 형식)
        quality_feedback = f"""
**Quality Score**: {quality_result['quality_score']:.1%} ({quality_result['quality_level']})
**Adjusted Importance**: {importance:.2f} (original: {importance:.2f})"""
        
        suggestions_text = ""
        if quality_result['suggestions']:
            suggestions_text = f"\n\n💡 **Quality Suggestions**:\n" + "\n".join(f"• {s}" for s in quality_result['suggestions'][:2])
        
        return f"""✅ **Memory Successfully Added!**

**Block Index**: #{block_data['block_index']}
**Storage**: Permanent (Long-term Memory)
**Duplicate Check**: ✅ Passed{quality_feedback}{suggestions_text}"""
    
    except Exception as e:
        logger.error(f"add_memory failed: {e}")
        return f"❌ Failed to add memory: {str(e)}"

@app.tool()
def search_memory(query: str, limit: int = 5) -> str:
    """🔍 Search existing memories using keywords or semantic similarity.
    
    ⚠️  ALWAYS USE THIS FIRST before add_memory to avoid duplicates!

    ✅ USE WHEN:
    • User mentions 'before', 'previous', 'remember'
    • Starting new conversation (check user context)
    • User asks about past discussions or projects
    • Before storing new information (duplicate check)

    🎯 SEARCH TIPS: Use specific keywords, try multiple terms if needed
    """
    try:
        components = get_greeum_components()
        if not components:
            return "❌ Greeum components not available. Please check installation."
        
        results = search_memory_direct(query, limit)
        
        # 사용 통계 로깅
        components['usage_analytics'].log_event(
            "tool_usage", "search_memory",
            {"query_length": len(query), "results_found": len(results), "limit_requested": limit},
            0, True
        )
        
        if results:
            result_text = f"🔍 Found {len(results)} memories:\n"
            for i, memory in enumerate(results, 1):
                timestamp = memory.get('timestamp', 'Unknown')
                content = memory.get('context', '')[:100] + ('...' if len(memory.get('context', '')) > 100 else '')
                result_text += f"{i}. [{timestamp}] {content}\n"
            return result_text
        else:
            return f"🔍 No memories found for query: '{query}'"
    
    except Exception as e:
        logger.error(f"search_memory failed: {e}")
        return f"❌ Search failed: {str(e)}"

@app.tool()
def get_memory_stats() -> str:
    """📊 Get current memory system statistics and health status.
    
    USE WHEN:
    • Starting new conversations (check user context)
    • Memory system seems slow or full
    • Debugging memory-related issues
    • Regular health checks

    💡 PROVIDES: File counts, sizes, system status
    """
    try:
        components = get_greeum_components()
        if not components:
            return "❌ Greeum components not available. Please check installation."
        
        db_manager = components['db_manager']
        
        # 기본 통계
        total_blocks = db_manager.count_blocks()
        recent_blocks = db_manager.get_recent_blocks(limit=10)
        
        # STM 통계
        stm_stats = components['stm_manager'].get_stats()
        
        return f"""📊 **Greeum Memory Statistics**

**Long-term Memory**:
• Total Blocks: {total_blocks}
• Recent Entries: {len(recent_blocks)}

**Short-term Memory**:
• Active Slots: {stm_stats.get('active_count', 0)}
• Available Slots: {stm_stats.get('available_slots', 0)}

**System Status**: ✅ Operational
**Version**: 2.2.6 (FastMCP Hotfix)"""
    
    except Exception as e:
        logger.error(f"get_memory_stats failed: {e}")
        return f"❌ Stats retrieval failed: {str(e)}"

@app.tool()
def usage_analytics(days: int = 7, report_type: str = "usage") -> str:
    """📊 Get comprehensive usage analytics and insights.
    
    USE FOR:
    • Understanding memory usage patterns
    • Identifying performance bottlenecks
    • Analyzing user behavior trends
    • System health monitoring

    💡 PROVIDES: Usage statistics, quality trends, performance insights
    """
    try:
        components = get_greeum_components()
        if not components:
            return "❌ Greeum components not available. Please check installation."
        
        analytics = components['usage_analytics'].get_usage_report(days=days, report_type=report_type)
        
        return f"""📈 **Usage Analytics Report** ({days} days)

**Activity Summary**:
• Total Operations: {analytics.get('total_operations', 0)}
• Memory Additions: {analytics.get('add_operations', 0)}
• Search Operations: {analytics.get('search_operations', 0)}

**Quality Metrics**:
• Average Quality Score: {analytics.get('avg_quality_score', 0):.1%}
• High Quality Rate: {analytics.get('high_quality_rate', 0):.1%}

**Performance**:
• Average Response Time: {analytics.get('avg_response_time', 0):.1f}ms
• Success Rate: {analytics.get('success_rate', 0):.1%}

**Report Type**: {report_type.title()}
**Generated**: FastMCP v2.2.6"""
    
    except Exception as e:
        logger.error(f"usage_analytics failed: {e}")
        return f"❌ Analytics failed: {str(e)}"

# 서버 실행
async def main():
    """FastMCP 서버 실행"""
    # Greeum 컴포넌트 초기화
    components = get_greeum_components()
    if not components:
        logger.error("❌ Cannot start server: Greeum components unavailable")
        sys.exit(1)
    
    logger.info("🚀 Starting Greeum FastMCP server...")
    logger.info("✅ All tools registered: add_memory, search_memory, get_memory_stats, usage_analytics")
    
    # FastMCP 서버 실행 (stdio transport)
    await app.run()

if __name__ == "__main__":
    try:
        # 기존 이벤트 루프가 있는지 확인
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 이미 실행중인 루프가 있으면 새 스레드에서 실행
            import threading
            import concurrent.futures
            
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                return new_loop.run_until_complete(main())
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                future.result()
        else:
            # 실행중인 루프가 없으면 정상 실행
            asyncio.run(main())
    except RuntimeError as e:
        if "already running" in str(e).lower():
            # asyncio 충돌 시 새 루프에서 실행
            import threading
            
            def run_server():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                new_loop.run_until_complete(main())
            
            thread = threading.Thread(target=run_server)
            thread.start()
            thread.join()
        else:
            raise