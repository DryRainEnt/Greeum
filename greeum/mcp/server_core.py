#!/usr/bin/env python3
"""
Greeum MCP Server Core
순수한 서버 로직만 담당하는 코어 모듈

🎯 설계 원칙:
- 순수한 서버 로직만 포함
- CLI 호출과 완전 분리
- FastMCP 프레임워크 기반
- 재사용 가능한 서버 컴포넌트

🔧 책임:
- Greeum 컴포넌트 초기화
- MCP 도구 정의 및 등록
- 서버 실행 로직

🌐 v4.0 API 모드:
- GREEUM_USE_API=true 환경변수로 API 모드 활성화
- GREEUM_API_URL로 API 서버 주소 지정 (기본: http://localhost:8400)
- API 실패 시 자동 폴백 (직접 모드)
"""

import logging
import os
import sys
from typing import Dict, Any, List, Optional

# FastMCP import
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("ERROR: FastMCP not found. Please install: pip install mcp>=1.0.0", file=sys.stderr)
    sys.exit(1)

# Greeum core imports
try:
    from greeum.core.block_manager import BlockManager
    from greeum.core import DatabaseManager  # Use factory pattern from __init__.py
    from greeum.core.stm_manager import STMManager
    from greeum.core.duplicate_detector import DuplicateDetector
    from greeum.core.quality_validator import QualityValidator
    from greeum.core.usage_analytics import UsageAnalytics
    from greeum.core.storage_admin import (
        create_backup,
        discover_storage_candidates,
        merge_storage,
        resolve_active_storage,
    )
    GREEUM_AVAILABLE = True
except ImportError:
    GREEUM_AVAILABLE = False

# Greeum client imports (v4.0 API mode)
try:
    from greeum.client import GreeumClient
    CLIENT_AVAILABLE = True
except ImportError:
    CLIENT_AVAILABLE = False

# 로깅 설정
logger = logging.getLogger("greeum_server_core")

class GreeumMCPServer:
    """Greeum MCP 서버 코어 클래스"""

    def __init__(self):
        self.app = FastMCP("Greeum Memory System")
        self._components = None
        self._client: Optional[GreeumClient] = None
        self._initialized = False
        self._use_api = False
        self._api_mode_active = False  # 실제 API 모드 동작 여부

    def _get_version(self) -> str:
        """중앙화된 버전 참조"""
        try:
            from greeum import __version__
            return __version__
        except ImportError:
            return "unknown"

    def _check_api_mode(self) -> bool:
        """환경변수 또는 Config 파일에서 API 모드 설정 확인"""
        # 환경변수 우선 (명시적 설정)
        use_api_env = os.environ.get("GREEUM_USE_API", "").lower()
        if use_api_env in ("true", "1", "yes"):
            return True
        if use_api_env in ("false", "0", "no"):
            return False

        # Config 파일 확인
        try:
            from greeum.config_store import load_config
            config = load_config()
            return config.mode == "remote" and config.remote is not None and config.remote.enabled
        except Exception:
            return False

    def _get_api_config(self) -> tuple:
        """API URL과 Key를 환경변수 또는 Config 파일에서 가져옴. Returns (url, api_key)."""
        api_url = os.environ.get("GREEUM_API_URL")
        api_key = os.environ.get("GREEUM_API_KEY")

        # 환경변수에 없으면 Config 파일 확인
        if not api_url:
            try:
                from greeum.config_store import load_config
                config = load_config()
                if config.remote:
                    api_url = config.remote.server_url or api_url
                    api_key = config.remote.api_key or api_key
            except Exception:
                pass

        return api_url or "http://localhost:8400", api_key

    async def initialize(self) -> None:
        """서버 컴포넌트 초기화"""
        if self._initialized:
            return

        self._use_api = self._check_api_mode()

        # API 모드 시도
        if self._use_api and CLIENT_AVAILABLE:
            api_url, api_key = self._get_api_config()
            self._client = GreeumClient(
                api_url=api_url,
                api_key=api_key,
                use_api=True,
                fallback_to_direct=False,  # 폴백 비활성화 - 명시적 실패
            )

            # API 서버 연결 확인
            if self._client._check_api_available():
                self._api_mode_active = True
                logger.info(f"Greeum MCP server initialized in API mode: {api_url}")
            else:
                # API 모드가 설정되었지만 서버 연결 불가 - 에러 발생
                raise RuntimeError(
                    f"API 모드가 설정되었지만 API 서버에 연결할 수 없습니다: {api_url}\n"
                    f"API 서버를 시작하거나 GREEUM_USE_API=false로 직접 모드를 사용하세요."
                )

        # 직접 모드 초기화 (API 모드가 비활성화된 경우에만)
        if not self._use_api:
            if not GREEUM_AVAILABLE:
                raise RuntimeError("Greeum components not available")

            try:
                # Greeum 컴포넌트 초기화
                db_manager = DatabaseManager()
                block_manager = BlockManager(db_manager)
                stm_manager = STMManager(db_manager)
                duplicate_detector = DuplicateDetector(db_manager)
                quality_validator = QualityValidator()
                usage_analytics = UsageAnalytics(db_manager)

                self._components = {
                    'db_manager': db_manager,
                    'block_manager': block_manager,
                    'stm_manager': stm_manager,
                    'duplicate_detector': duplicate_detector,
                    'quality_validator': quality_validator,
                    'usage_analytics': usage_analytics
                }

                logger.info("Greeum MCP server initialized in direct mode")

            except Exception as e:
                logger.error(f"Failed to initialize server components: {e}")
                raise

        # MCP 도구 등록
        self._register_tools()

        self._initialized = True
        mode = "API" if self._api_mode_active else "Direct"
        logger.info(f"Greeum MCP server components initialized ({mode} mode)")
    
    def _register_tools(self) -> None:
        """MCP 도구들을 서버에 등록"""
        
        @self.app.tool()
        def add_memory(content: str, importance: float = 0.5) -> str:
            """[MEMORY] Add important permanent memories to long-term storage."""
            return self._handle_add_memory(content, importance)
            
        @self.app.tool()
        def search_memory(query: str, limit: int = 5) -> str:
            """🔍 Search existing memories using keywords or semantic similarity."""
            return self._handle_search_memory(query, limit)
            
        @self.app.tool()
        def get_memory_stats() -> str:
            """📊 Get current memory system statistics and health status."""
            return self._handle_get_stats()
            
        @self.app.tool()
        def usage_analytics(days: int = 7, report_type: str = "usage") -> str:
            """📊 Get comprehensive usage analytics and insights."""
            return self._handle_usage_analytics(days, report_type)

        @self.app.tool()
        def analyze(days: int = 7) -> str:
            """🧭 Summarize slots, branches, and recent activity for quick situational awareness."""
            return self._handle_analyze_memory(days)

        @self.app.tool()
        def storage_backup(data_dir: str = "", label: str = "manual") -> str:
            """💾 Create a backup of the configured storage directory."""
            return self._handle_storage_backup(data_dir or None, label)

        @self.app.tool()
        def storage_merge(source: str = "", target: str = "", label: str = "merge") -> str:
            """🔄 Merge blocks from one storage directory into another."""
            return self._handle_storage_merge(source or None, target or None, label)

        logger.info(
            "MCP tools registered: add_memory, search_memory, get_memory_stats, usage_analytics, analyze,"
            " storage_backup, storage_merge"
        )
    
    def _handle_add_memory(self, content: str, importance: float) -> str:
        """add_memory 도구 핸들러"""
        try:
            # API 모드
            if self._api_mode_active and self._client:
                result = self._client.add_memory(content=content, importance=importance)

                if not result.get("success"):
                    return f"""WARNING: Memory Addition Failed

**Reason**: {result.get('duplicate_check', 'unknown')}
**Suggestions**: {', '.join(result.get('suggestions', []))}

Please search existing memories first or provide more specific content."""

                quality_score = result.get("quality_score", 0.0)
                suggestions = result.get("suggestions", [])
                suggestions_text = ""
                if suggestions:
                    suggestions_text = f"\n\n**Quality Suggestions**:\n" + "\n".join(f"• {s}" for s in suggestions[:2])

                return f"""SUCCESS: Memory Successfully Added!

**Block Index**: #{result.get('block_index', -1)}
**Storage**: {result.get('storage', 'LTM')} (via API)
**Duplicate Check**: {result.get('duplicate_check', 'passed').upper()}
**Quality Score**: {quality_score:.1%}
**Mode**: API{suggestions_text}"""

            # 직접 모드
            if not self._components:
                return "ERROR: Server not properly initialized"

            # 중복 검사
            duplicate_check = self._components['duplicate_detector'].check_duplicate(content)
            if duplicate_check["is_duplicate"]:
                similarity = duplicate_check["similarity_score"]

                # Get block index from similar_memories (safe access)
                block_index = 'unknown'
                if duplicate_check.get('similar_memories'):
                    first_similar = duplicate_check['similar_memories'][0]
                    block_index = first_similar.get('block_index', 'unknown')

                return f"""WARNING: Potential Duplicate Memory Detected

**Similarity**: {similarity:.1%} with existing memory
**Similar Memory**: Block #{block_index}

Please search existing memories first or provide more specific content."""

            # 품질 검증
            quality_result = self._components['quality_validator'].validate_memory_quality(content, importance)

            # 메모리 추가
            block_data = self._add_memory_direct(content, importance)

            # 사용 통계 로깅
            self._components['usage_analytics'].log_quality_metrics(
                len(content), quality_result['quality_score'], quality_result['quality_level'],
                importance, importance, False, duplicate_check["similarity_score"],
                len(quality_result['suggestions'])
            )

            # 성공 응답
            quality_feedback = f"""
**Quality Score**: {quality_result['quality_score']:.1%} ({quality_result['quality_level']})
**Adjusted Importance**: {importance:.2f} (original: {importance:.2f})"""

            suggestions_text = ""
            if quality_result['suggestions']:
                suggestions_text = f"\n\n**Quality Suggestions**:\n" + "\n".join(f"• {s}" for s in quality_result['suggestions'][:2])

            return f"""SUCCESS: Memory Successfully Added!

**Block Index**: #{block_data['block_index']}
**Storage**: Permanent (Long-term Memory)
**Duplicate Check**: PASSED{quality_feedback}{suggestions_text}"""

        except Exception as e:
            logger.error(f"add_memory failed: {e}")
            return f"ERROR: Failed to add memory: {str(e)}"
    
    def _handle_search_memory(self, query: str, limit: int) -> str:
        """search_memory 도구 핸들러"""
        try:
            # API 모드
            if self._api_mode_active and self._client:
                result = self._client.search(query=query, limit=limit)
                results = result.get("results", [])
                stats = result.get("search_stats", {})

                if results:
                    result_text = f"Found {len(results)} memories (via API, {stats.get('elapsed_ms', 0):.1f}ms):\n"
                    for i, memory in enumerate(results, 1):
                        timestamp = memory.get('timestamp', 'Unknown')
                        if hasattr(timestamp, 'isoformat'):
                            timestamp = timestamp.isoformat()
                        content = memory.get('content', '')[:100]
                        if len(memory.get('content', '')) > 100:
                            content += '...'
                        result_text += f"{i}. [{timestamp}] {content}\n"
                    return result_text
                else:
                    return f"No memories found for query: '{query}'"

            # 직접 모드
            if not self._components:
                return "ERROR: Server not properly initialized"

            results = self._search_memory_direct(query, limit)

            # 사용 통계 로깅
            self._components['usage_analytics'].log_event(
                "tool_usage", "search_memory",
                {"query_length": len(query), "results_found": len(results), "limit_requested": limit},
                0, True
            )

            if results:
                result_text = f"Found {len(results)} memories:\n"
                for i, memory in enumerate(results, 1):
                    timestamp = memory.get('timestamp', 'Unknown')
                    content = memory.get('context', '')[:100] + ('...' if len(memory.get('context', '')) > 100 else '')
                    result_text += f"{i}. [{timestamp}] {content}\n"
                return result_text
            else:
                return f"No memories found for query: '{query}'"

        except Exception as e:
            logger.error(f"search_memory failed: {e}")
            return f"ERROR: Search failed: {str(e)}"
    
    def _handle_get_stats(self) -> str:
        """get_memory_stats 도구 핸들러"""
        try:
            # API 모드
            if self._api_mode_active and self._client:
                stats = self._client.get_stats()

                return f"""**Greeum Memory Statistics** (via API)

**Long-term Memory**:
• Total Blocks: {stats.get('total_blocks', 0)}

**Short-term Memory**:
• Active Slots: {stats.get('active_branches', 0)}

**Database**:
• Size: {stats.get('database_size_mb', 0):.2f} MB
• Embedding Model: {stats.get('embedding_model', 'unknown')}

**System Status**: Operational (API Mode)
**Version**: {self._get_version()}"""

            # 직접 모드
            if not self._components:
                return "ERROR: Server not properly initialized"

            db_manager = self._components['db_manager']

            # 기본 통계
            total_blocks = db_manager.count_blocks()
            recent_blocks = db_manager.get_recent_blocks(limit=10)

            # STM 통계
            stm_stats = self._components['stm_manager'].get_stats()

            return f"""**Greeum Memory Statistics**

**Long-term Memory**:
• Total Blocks: {total_blocks}
• Recent Entries: {len(recent_blocks)}

**Short-term Memory**:
• Active Slots: {stm_stats.get('active_count', 0)}
• Available Slots: {stm_stats.get('available_slots', 0)}

**System Status**: Operational
**Version**: {self._get_version()} (Separated Architecture)"""

        except Exception as e:
            logger.error(f"get_memory_stats failed: {e}")
            return f"ERROR: Stats retrieval failed: {str(e)}"
    
    def _handle_usage_analytics(self, days: int, report_type: str) -> str:
        """usage_analytics 도구 핸들러"""
        try:
            if not self._components:
                return "ERROR: Server not properly initialized"
            
            analytics = self._components['usage_analytics'].get_usage_report(days=days, report_type=report_type)

            return f"""**Usage Analytics Report** ({days} days)

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
**Generated**: Separated Architecture v{self._get_version()}"""
        
        except Exception as e:
            logger.error(f"usage_analytics failed: {e}")
            return f"ERROR: Analytics failed: {str(e)}"

    def _handle_analyze_memory(self, days: int) -> str:
        """analyze 도구 핸들러"""
        try:
            if not self._components:
                return "ERROR: Server not properly initialized"

            analytics_component = self._components.get('usage_analytics')
            if not analytics_component:
                return "Analytics component unavailable."

            summary = analytics_component.generate_system_report(days=days)
            return summary or "No activity recorded yet."
        except Exception as e:
            logger.error(f"analyze failed: {e}")
            return f"ERROR: Analyze failed: {str(e)}"

    def _handle_storage_backup(self, data_dir: Optional[str], label: str) -> str:
        try:
            active = resolve_active_storage(data_dir)
        except FileNotFoundError as exc:
            return f"ERROR: {exc}"

        backup_info = create_backup(active.data_dir, label=label)
        candidates = discover_storage_candidates()

        lines = [
            "📦 **Storage Backup Completed**",
            "",
            f"- Active directory: {active.data_dir}",
            f"- Backup file: {backup_info['backup']}",
        ]

        sidecars = backup_info.get("sidecars") or []
        if sidecars:
            lines.append(f"- Sidecar files: {', '.join(sidecars)}")

        others = [c for c in candidates if c.data_dir != active.data_dir]
        if others:
            lines.append("")
            lines.append("Other detected storages:")
            for candidate in others:
                lines.append(
                    f"• {candidate.data_dir} — {candidate.total_blocks} blocks"
                    f" (latest: {candidate.latest_timestamp or 'n/a'})"
                )

        return "\n".join(lines)

    def _handle_storage_merge(self, source_dir: Optional[str], target_dir: Optional[str], label: str) -> str:
        if not source_dir:
            candidates = discover_storage_candidates()
            if not candidates:
                return "ERROR: No storage directories detected."

            lines = ["Detected storage locations (provide `source` to merge):"]
            for candidate in candidates:
                lines.append(
                    f"- {candidate.data_dir} — {candidate.total_blocks} blocks"
                    f" (latest: {candidate.latest_timestamp or 'n/a'})"
                )
            return "\n".join(lines)

        try:
            source = resolve_active_storage(source_dir)
            target = resolve_active_storage(target_dir)
        except FileNotFoundError as exc:
            return f"ERROR: {exc}"

        if source.db_path == target.db_path:
            return "ERROR: Source and target storage must be different."

        backup_info = create_backup(target.data_dir, label=f"pre_{label}")
        merge_result = merge_storage(source.db_path, target.db_path)

        lines = [
            "🔄 **Storage Merge Completed**",
            "",
            f"- Source: {source.db_path}",
            f"- Target: {target.db_path}",
            f"- Pre-merge backup: {backup_info['backup']}",
            f"- Blocks inserted: {merge_result.get('blocks_inserted', 0)}",
            f"- Tables updated: {merge_result.get('tables_updated', 0)}",
        ]

        if merge_result.get("blocks_inserted", 0) == 0:
            lines.append("\nNo new blocks were inserted (all hashes already present).")

        return "\n".join(lines)
    
    def _add_memory_direct(self, content: str, importance: float) -> Dict[str, Any]:
        """
        직접 메모리 추가 (BlockManager 사용)

        v4.0: BlockManager.add_block()을 사용하여 branch_aware_storage와
        LLM 분류기가 적용되도록 수정.
        """
        block_manager = self._components['block_manager']

        # BlockManager.add_block()은 다음을 자동으로 처리:
        # 1. 유사 메모리 조회
        # 2. LLM 기반 슬롯 분류 (기존 메모리 참조)
        # 3. 최적 브랜치/블록 선택
        # 4. before/after 링크 설정
        result = block_manager.add_block(
            context=content,
            keywords=[],  # BlockManager가 자동 추출
            tags=[],      # BlockManager가 자동 추출
            importance=importance,
        )

        # BlockManager가 반환하는 결과를 MCP 응답 형식으로 변환
        if isinstance(result, dict):
            return result
        else:
            # 블록 인덱스만 반환된 경우
            return {
                "block_index": result,
                "context": content,
                "importance": importance,
            }
    
    def _search_memory_direct(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """직접 메모리 검색 (기존 로직 재사용)"""
        from greeum.embedding_models import get_embedding
        
        db_manager = self._components['db_manager']
        
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
    
    async def run_stdio(self) -> None:
        """STDIO transport로 서버 실행"""
        if not self._initialized:
            raise RuntimeError("Server not initialized. Call initialize() first.")
        
        logger.info("Running MCP server with STDIO transport")
        await self.app.run()
    
    async def run_websocket(self, port: int = 3000) -> None:
        """WebSocket transport로 서버 실행 (향후 구현)"""
        if not self._initialized:
            raise RuntimeError("Server not initialized. Call initialize() first.")
        
        # WebSocket 구현은 향후 확장
        raise NotImplementedError("WebSocket transport not implemented yet")
