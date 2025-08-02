#!/usr/bin/env python3
"""
Claude Code 호환 MCP 서버
- Claude Code의 MCP 프로토콜 규격에 정확히 맞춤
- 도구 인식 문제 해결을 위한 완전 호환 버전

🔧 TOOL USAGE WORKFLOW:
1. NEW INFO: add_memory (permanent) vs stm_add (temporary)
2. FIND INFO: search_memory (searches both permanent & temporary)
3. CHECK SYSTEM: get_memory_stats (before bulk operations)
4. MANAGE TEMPORARY: stm_promote (temp→permanent) + stm_cleanup (maintenance)
5. ANALYZE DATA: ltm_analyze (patterns) → ltm_verify (integrity) → ltm_export (backup)

⚠️  BEST PRACTICES:
- Use add_memory for insights you want to keep across conversations
- Use stm_add for current session context that expires
- Always dry_run stm_promote first to preview
- Check get_memory_stats before ltm_analyze (need 10+ memories)
- Don't set importance > 0.8 unless truly critical
"""

import asyncio
import json
import sys
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import subprocess
import os
from pathlib import Path

# Import enhanced tool schemas, duplicate detection, quality validation, and usage analytics
from .enhanced_tool_schema import EnhancedToolSchema
from greeum.core.duplicate_detector import DuplicateDetector
from greeum.core.quality_validator import QualityValidator
from greeum.core.usage_analytics import UsageAnalytics

# Greeum 모듈 직접 import
try:
    from greeum.core.block_manager import BlockManager
    from greeum.core.database_manager import DatabaseManager  
    from greeum.core.stm_manager import STMManager
    GREEUM_AVAILABLE = True
except ImportError:
    GREEUM_AVAILABLE = False

# 로깅 설정 (stderr로만)
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger("claude_code_mcp")

class ClaudeCodeMCPServer:
    """Claude Code 완전 호환 MCP 서버"""
    
    def __init__(self):
        """초기화"""
        self.server_info = {
            "name": "greeum",
            "version": "2.0.5"
        }
        self.protocol_version = "2024-11-05"
        self.capabilities = {
            "tools": {},
            "resources": {},
            "prompts": {},
            "logging": {}
        }
        
        # Greeum 컴포넌트 직접 초기화
        if GREEUM_AVAILABLE:
            try:
                self.db_manager = DatabaseManager()
                self.block_manager = BlockManager(self.db_manager)
                self.stm_manager = STMManager(self.db_manager)
                # v2.0.5: 중복 검사기, 품질 검증기, 사용 분석기 초기화
                self.duplicate_detector = DuplicateDetector(self.db_manager)
                self.quality_validator = QualityValidator()
                self.usage_analytics = UsageAnalytics(self.db_manager)
                self.direct_mode = True
                # 서버 세션 시작
                self.server_session_id = f"mcp_server_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.usage_analytics.start_session(self.server_session_id, "Claude Code MCP", "mcp_server")
                logger.info("Claude Code MCP Server v2.0.5 initialized with full analytics suite (duplicate detection + quality validation + usage analytics)")
            except Exception as e:
                logger.warning(f"Failed to initialize Greeum modules: {e}")
                self.direct_mode = False
        else:
            self.direct_mode = False
    
    def __del__(self):
        """Ensure proper cleanup of analytics session"""
        if hasattr(self, 'usage_analytics') and hasattr(self, 'server_session_id'):
            try:
                self.usage_analytics.end_session(self.server_session_id)
                logger.info(f"Analytics session {self.server_session_id} properly closed")
            except Exception:
                pass  # Cleanup should never raise
            
        # CLI 경로 설정 (일부 명령어는 CLI 필요)
        try:
            self.greeum_cli = self._find_greeum_cli()
        except Exception as e:
            logger.warning(f"Failed to find Greeum CLI: {e}")
            self.greeum_cli = "python3 -m greeum.cli"  # 안전한 기본값
            
        if not self.direct_mode:
            logger.info(f"Claude Code MCP Server initialized with CLI fallback: {self.greeum_cli}")
        else:
            logger.info(f"Claude Code MCP Server initialized with direct mode, CLI available: {self.greeum_cli}")
        
    def _find_greeum_cli(self) -> str:
        """Greeum CLI 경로 자동 감지"""
        current_dir = Path(__file__).parent.parent.parent
        
        # 방법 1: Python 모듈 실행
        if (current_dir / "greeum" / "cli" / "__init__.py").exists():
            return f"python3 -m greeum.cli"
            
        # 방법 2: 설치된 명령어
        try:
            subprocess.run(["greeum", "--version"], capture_output=True, check=True)
            return "greeum"
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
            
        # 기본값
        return f"python3 -m greeum.cli"
    
    def _run_cli_command(self, command: List[str]) -> Dict[str, Any]:
        """CLI 명령어 실행"""
        try:
            # 안전한 CLI 경로 가져오기
            greeum_cli = getattr(self, 'greeum_cli', None)
            if not greeum_cli:
                return {"success": False, "error": "CLI path not configured"}
                
            full_command = greeum_cli.split() + command
            logger.info(f"Running: {' '.join(full_command)}")
            
            # 보안: 허용된 명령어만 실행
            allowed_commands = [
                "memory", "add", "search", "stats", "--version", "--help",
                "ltm", "analyze", "verify", "export", "stm", "promote", "cleanup",
                "--period", "--output", "--trends", "--repair", "--format", "--limit",
                "--threshold", "--dry-run", "--ttl", "--importance", "--smart", "--expired"
            ]
            for cmd_part in command:
                if cmd_part not in allowed_commands and not cmd_part.startswith(('-', '=')):
                    # 명령어 인젝션 방지: 안전한 텍스트만 허용
                    if not all(c.isalnum() or c in ' .-_가-힣ㄱ-ㅎㅏ-ㅣ' for c in cmd_part):
                        raise ValueError(f"Unsafe command detected: {cmd_part}")
            
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                check=True,
                timeout=30  # 보안: 타임아웃 설정
            )
            
            return {"success": True, "output": result.stdout.strip()}
                
        except subprocess.CalledProcessError as e:
            logger.error(f"CLI command failed: {e}")
            return {"success": False, "error": f"Command failed: {e.stderr or str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"success": False, "error": str(e)}
    
    def _add_memory_direct(self, content: str, importance: float = 0.5) -> Dict[str, Any]:
        """CLI와 동일한 패턴으로 메모리 추가"""
        from greeum.text_utils import process_user_input
        from datetime import datetime
        import json
        import hashlib
        
        # 텍스트 처리
        result = process_user_input(content)
        result["importance"] = importance
        
        # 타임스탬프 추가
        timestamp = datetime.now().isoformat()
        result["timestamp"] = timestamp
        
        # 블록 인덱스 생성 (마지막 블록 + 1)
        last_block_info = self.db_manager.get_last_block_info()
        if last_block_info is None:
            last_block_info = {"block_index": -1}
        block_index = last_block_info.get("block_index", -1) + 1
        
        # 이전 해시 가져오기
        prev_hash = ""
        if block_index > 0:
            prev_block = self.db_manager.get_block(block_index - 1)
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
        self.db_manager.add_block(block_data)
        
        return block_data
    
    def _search_memory_direct(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """CLI와 동일한 패턴으로 메모리 검색"""
        from greeum.embedding_models import get_embedding
        
        try:
            # 임베딩 검색 시도
            embedding = get_embedding(query)
            blocks = self.db_manager.search_blocks_by_embedding(embedding, top_k=limit)
        except Exception:
            # 임베딩 실패시 키워드 검색
            keywords = query.split()
            blocks = self.db_manager.search_blocks_by_keyword(keywords, limit=limit)
        
        return blocks

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 요청 처리 (Claude Code 규격 준수)"""
        try:
            method = request.get('method', '')
            params = request.get('params', {})
            request_id = request.get('id', 1)
            
            logger.info(f"Handling method: {method}")
            
            # 1. Initialize
            if method == 'initialize':
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": self.protocol_version,
                        "capabilities": self.capabilities,
                        "serverInfo": self.server_info
                    }
                }
            
            # 2. Tools list - Using Enhanced Tool Schemas v2.0.5
            elif method == 'tools/list':
                # Get all enhanced tool schemas with improved guidance
                enhanced_tools = EnhancedToolSchema.get_all_enhanced_schemas()
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": enhanced_tools
                    }
                }
                
            # 3. Tools call
            elif method == 'tools/call':
                tool_name = params.get('name', '')
                arguments = params.get('arguments', {})
                
                logger.info(f"Calling tool: {tool_name} with args: {arguments}")
                
                # add_memory 도구 - v2.0.5 Enhanced with Analytics, Duplicate Detection & Quality Validation
                if tool_name == 'add_memory':
                    content = arguments.get('content', '')
                    importance = arguments.get('importance', 0.5)
                    start_time = time.time()
                    
                    if self.direct_mode:
                        try:
                            # v2.0.5: 품질 검증 수행
                            quality_result = self.quality_validator.validate_memory_quality(content, importance)
                            
                            # 품질이 너무 낮으면 저장 중단
                            if not quality_result["should_store"]:
                                duration_ms = int((time.time() - start_time) * 1000)
                                
                                # Analytics: 품질 검증 실패 로깅
                                self.usage_analytics.log_event(
                                    "tool_usage", tool_name, 
                                    {"quality_score": quality_result['quality_score'], "quality_level": quality_result['quality_level']},
                                    duration_ms, False, "Quality validation failed", session_id=self.server_session_id
                                )
                                self.usage_analytics.log_quality_metrics(
                                    len(content), quality_result['quality_score'], quality_result['quality_level'],
                                    importance, quality_result['adjusted_importance'], False, 0.0, len(quality_result['suggestions'])
                                )
                                
                                quality_warning = f"""❌ **Low Quality Content Detected!**

**Quality Score**: {quality_result['quality_score']:.1%} ({quality_result['quality_level']})
**Issues Found**: Quality below acceptable threshold

**Suggestions for Improvement**:
{chr(10).join('• ' + suggestion for suggestion in quality_result['suggestions'])}

**Warnings**:
{chr(10).join('• ' + warning for warning in quality_result['warnings'])}

⚠️ **Memory NOT stored** due to low quality. Please improve content and try again."""
                                
                                return {
                                    "jsonrpc": "2.0",
                                    "id": request_id,
                                    "result": {
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": quality_warning
                                            }
                                        ]
                                    }
                                }
                            
                            # v2.0.5: 중복 검사 수행
                            duplicate_check = self.duplicate_detector.check_duplicate(content, importance)
                            
                            # 중복 발견시 사용자에게 알림
                            if duplicate_check["is_duplicate"]:
                                duration_ms = int((time.time() - start_time) * 1000)
                                similar_memory = duplicate_check["similar_memories"][0] if duplicate_check["similar_memories"] else {}
                                block_index = similar_memory.get("block_index", "unknown")
                                similarity = duplicate_check["similarity_score"]
                                
                                # Analytics: 중복 검사 실패 로깅
                                self.usage_analytics.log_event(
                                    "tool_usage", tool_name,
                                    {"duplicate_similarity": similarity, "existing_block": block_index},
                                    duration_ms, False, "Duplicate content detected", session_id=self.server_session_id
                                )
                                self.usage_analytics.log_quality_metrics(
                                    len(content), quality_result['quality_score'], quality_result['quality_level'],
                                    importance, quality_result['adjusted_importance'], True, similarity, len(quality_result['suggestions'])
                                )
                                
                                warning_text = f"""🚫 **Duplicate Content Detected!**

**Similarity**: {similarity:.1%} match found
**Existing Memory**: Block #{block_index}
**Content Preview**: {similar_memory.get('context', '')[:100]}...

**Recommendation**: {duplicate_check['recommendation']}

💡 **Suggested Actions**:
• Use `search_memory` to review existing content
• Update existing memory if needed  
• Add only truly new information

⚠️ **Memory NOT stored** to prevent duplication."""
                                
                                return {
                                    "jsonrpc": "2.0",
                                    "id": request_id,
                                    "result": {
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": warning_text
                                            }
                                        ]
                                    }
                                }
                            
                            # 품질 검증 및 중복 검사 통과 - 실제 저장
                            # 품질 점수에 따라 중요도 조정
                            adjusted_importance = quality_result["adjusted_importance"]
                            block_data = self._add_memory_direct(content, adjusted_importance)
                            duration_ms = int((time.time() - start_time) * 1000)
                            
                            # Analytics: 성공적인 메모리 저장 로깅
                            self.usage_analytics.log_event(
                                "tool_usage", tool_name,
                                {
                                    "block_index": block_data['block_index'],
                                    "quality_score": quality_result['quality_score'],
                                    "quality_level": quality_result['quality_level'],
                                    "importance_adjusted": adjusted_importance != importance
                                },
                                duration_ms, True, session_id=self.server_session_id
                            )
                            self.usage_analytics.log_quality_metrics(
                                len(content), quality_result['quality_score'], quality_result['quality_level'],
                                importance, adjusted_importance, False, duplicate_check["similarity_score"], 
                                len(quality_result['suggestions'])
                            )
                            
                            # v2.0.5: 품질 및 중복 피드백 포함한 성공 메시지
                            quality_feedback = f"""
**Quality Score**: {quality_result['quality_score']:.1%} ({quality_result['quality_level']})
**Adjusted Importance**: {adjusted_importance:.2f} (original: {importance:.2f})"""
                            
                            # 추가 제안사항이 있으면 포함
                            suggestions_text = ""
                            if quality_result['suggestions']:
                                suggestions_text = f"\n\n💡 **Quality Suggestions**:\n" + "\n".join(f"• {s}" for s in quality_result['suggestions'][:2])
                            
                            result_text = f"""✅ **Memory Successfully Added!**

**Block Index**: #{block_data['block_index']}
**Storage**: Permanent (Long-term Memory)
**Duplicate Check**: ✅ Passed{quality_feedback}{suggestions_text}"""
                            
                            return {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "result": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": result_text
                                        }
                                    ]
                                }
                            }
                        except Exception as e:
                            logger.error(f"Enhanced memory add failed: {e}")
                            return {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "error": {
                                    "code": -32603,
                                    "message": f"Failed to add memory: {str(e)}"
                                }
                            }
                    else:
                        # CLI fallback
                        command = ["memory", "add", content, "--importance", str(importance)]
                        result = self._run_cli_command(command)
                        
                        if result["success"]:
                            return {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "result": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": f"✅ Memory added to PERMANENT storage: {result['output']}"
                                        }
                                    ]
                                }
                            }
                        else:
                            return {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "error": {
                                    "code": -32603,
                                    "message": f"Failed to add memory: {result['error']}"
                                }
                            }
                
                # search_memory 도구
                elif tool_name == 'search_memory':
                    query = arguments.get('query', '')
                    limit = arguments.get('limit', 5)
                    start_time = time.time()
                    
                    if self.direct_mode:
                        try:
                            # 직접 모듈 사용 - CLI와 동일한 패턴
                            results = self._search_memory_direct(query, limit)
                            duration_ms = int((time.time() - start_time) * 1000)
                            
                            # Analytics: 검색 이벤트 로깅
                            self.usage_analytics.log_event(
                                "tool_usage", tool_name,
                                {
                                    "query_length": len(query),
                                    "results_found": len(results),
                                    "limit_requested": limit
                                },
                                duration_ms, True, session_id=self.server_session_id
                            )
                            
                            if results:
                                result_text = f"🔍 Found {len(results)} memories:\n"
                                for i, memory in enumerate(results, 1):
                                    timestamp = memory.get('timestamp', 'Unknown')
                                    content = memory.get('context', '')[:100] + ('...' if len(memory.get('context', '')) > 100 else '')
                                    result_text += f"{i}. [{timestamp}] {content}\n"
                            else:
                                result_text = "❌ No memories found"
                            
                            return {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "result": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": result_text
                                        }
                                    ]
                                }
                            }
                        except Exception as e:
                            logger.error(f"Direct memory search failed: {e}")
                            return {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "error": {
                                    "code": -32603,
                                    "message": f"Failed to search memory: {str(e)}"
                                }
                            }
                    else:
                        # CLI fallback
                        command = ["memory", "search", query, "--count", str(limit)]
                        result = self._run_cli_command(command)
                        
                        if result["success"]:
                            return {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "result": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": f"🔍 Search results:\n{result['output']}"
                                        }
                                    ]
                                }
                            }
                        else:
                            return {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "error": {
                                    "code": -32603,
                                    "message": f"Failed to search memory: {result['error']}"
                                }
                            }
                
                # get_memory_stats 도구
                elif tool_name == 'get_memory_stats':
                    try:
                        # 메모리 통계 직접 수집
                        data_dir = Path.home() / ".greeum"
                        
                        stats = {
                            "data_directory": str(data_dir),
                            "exists": data_dir.exists(),
                            "files": []
                        }
                        
                        if data_dir.exists():
                            for file in data_dir.glob("*"):
                                if file.is_file():
                                    stats["files"].append({
                                        "name": file.name,
                                        "size": file.stat().st_size
                                    })
                        
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"📊 Memory Statistics:\n{json.dumps(stats, indent=2)}"
                                    }
                                ]
                            }
                        }
                        
                    except Exception as e:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32603,
                                "message": f"Failed to get stats: {str(e)}"
                            }
                        }
                
                # usage_analytics 도구 - v2.0.5 New Analytics Tool
                elif tool_name == 'usage_analytics':
                    days = arguments.get('days', 7)
                    report_type = arguments.get('report_type', 'usage')
                    start_time = time.time()
                    
                    if self.direct_mode and hasattr(self, 'usage_analytics'):
                        try:
                            if report_type == 'usage' or report_type == 'all':
                                usage_stats = self.usage_analytics.get_usage_statistics(days)
                            
                            if report_type == 'quality' or report_type == 'all':
                                quality_trends = self.usage_analytics.get_quality_trends(days)
                            
                            if report_type == 'performance' or report_type == 'all':
                                performance_insights = self.usage_analytics.get_performance_insights(days)
                            
                            duration_ms = int((time.time() - start_time) * 1000)
                            
                            # Analytics: analytics 요청 자체도 로깅
                            self.usage_analytics.log_event(
                                "tool_usage", tool_name,
                                {"report_type": report_type, "days": days},
                                duration_ms, True, session_id=self.server_session_id
                            )
                            
                            # 보고서 생성
                            if report_type == 'usage':
                                report_text = f"""📊 **Usage Analytics Report** ({days} days)

**Basic Statistics**:
• Total Events: {usage_stats['basic_stats']['total_events']}
• Unique Sessions: {usage_stats['basic_stats']['unique_sessions']}
• Success Rate: {usage_stats['basic_stats']['success_rate']:.1%}
• Avg Response Time: {usage_stats['basic_stats']['avg_duration_ms']:.0f}ms

**Top Tools Used**:
{chr(10).join(f"• {tool}: {count} times" for tool, count in list(usage_stats['tool_usage'].items())[:5])}

**Quality Statistics**:
• Average Quality Score: {usage_stats['quality_stats']['avg_quality_score']:.2f}
• Duplicate Rate: {usage_stats['quality_stats']['duplicate_rate']:.1%}
• Quality Checks: {usage_stats['quality_stats']['total_quality_checks']}"""
                            
                            elif report_type == 'quality':
                                report_text = f"""📈 **Quality Trends Report** ({days} days)

**Quality Distribution**:
{chr(10).join(f"• {level}: {count}" for level, count in quality_trends['quality_distribution'].items())}

**Recent Trends**:
{chr(10).join(f"• {trend['date']}: {trend['avg_quality']:.2f} avg quality ({trend['count']} memories)" for trend in quality_trends['daily_trends'][-5:])}

**Duplicate Analysis**:
{chr(10).join(f"• {trend['date']}: {trend['duplicate_rate']:.1%} duplicate rate" for trend in quality_trends['duplicate_trends'][-3:])}"""
                            
                            elif report_type == 'performance':
                                report_text = f"""⚡ **Performance Insights Report** ({days} days)

**Performance by Tool**:
{chr(10).join(f"• {perf['tool_name']}: {perf['avg_duration_ms']:.0f}ms avg ({perf['operation_count']} ops)" for perf in performance_insights['performance_by_tool'][:5])}

**Error Patterns**:
{chr(10).join(f"• {error['tool_name']}: {error['error_count']} errors" for error in performance_insights['error_patterns'][:3])}

**Recommendations**:
{chr(10).join(f"• {rec}" for rec in performance_insights['recommendations'])}"""
                            
                            else:  # 'all'
                                report_text = f"""📊 **Complete Analytics Report** ({days} days)

**Usage Summary**:
• Total Events: {usage_stats['basic_stats']['total_events']}
• Success Rate: {usage_stats['basic_stats']['success_rate']:.1%}
• Avg Quality: {usage_stats['quality_stats']['avg_quality_score']:.2f}

**Top Issues**:
{chr(10).join(f"• {rec}" for rec in performance_insights['recommendations'][:3])}

💡 Use specific report types for detailed analysis: 'usage', 'quality', or 'performance'"""
                            
                            return {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "result": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": report_text
                                        }
                                    ]
                                }
                            }
                            
                        except Exception as e:
                            logger.error(f"Analytics report generation failed: {e}")
                            return {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "error": {
                                    "code": -32603,
                                    "message": f"Failed to generate analytics report: {str(e)}"
                                }
                            }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32603,
                                "message": "Analytics not available in CLI mode"
                            }
                        }
                
                # LTM 도구들
                elif tool_name == 'ltm_analyze':
                    trends = arguments.get('trends', True)
                    period = arguments.get('period', '6m')
                    output = arguments.get('output', 'text')
                    
                    command = ["ltm", "analyze", "--period", period, "--output", output]
                    if trends:
                        command.append("--trends")
                    
                    result = self._run_cli_command(command)
                    
                    if result["success"]:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": f"📊 LTM Analysis:\n{result['output']}"}]
                            }
                        }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {"code": -32603, "message": f"LTM analysis failed: {result['error']}"}
                        }
                
                elif tool_name == 'ltm_verify':
                    repair = arguments.get('repair', False)
                    
                    command = ["ltm", "verify"]
                    if repair:
                        command.append("--repair")
                    
                    result = self._run_cli_command(command)
                    
                    if result["success"]:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": f"🔍 LTM Verification:\n{result['output']}"}]
                            }
                        }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {"code": -32603, "message": f"LTM verification failed: {result['error']}"}
                        }
                
                elif tool_name == 'ltm_export':
                    format_type = arguments.get('format', 'json')
                    limit = arguments.get('limit')
                    
                    command = ["ltm", "export", "--format", format_type]
                    if limit:
                        command.extend(["--limit", str(limit)])
                    
                    result = self._run_cli_command(command)
                    
                    if result["success"]:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": f"📤 LTM Export:\n{result['output']}"}]
                            }
                        }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {"code": -32603, "message": f"LTM export failed: {result['error']}"}
                        }
                
                # STM 도구들
                elif tool_name == 'stm_add':
                    content = arguments.get('content', '')
                    ttl = arguments.get('ttl', '1h')
                    importance = arguments.get('importance', 0.3)
                    
                    command = ["stm", "add", content, "--ttl", ttl, "--importance", str(importance)]
                    result = self._run_cli_command(command)
                    
                    if result["success"]:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": f"🧠 Added to TEMPORARY memory (expires in {ttl}):\n{result['output']}"}]
                            }
                        }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {"code": -32603, "message": f"STM add failed: {result['error']}"}
                        }
                
                elif tool_name == 'stm_promote':
                    threshold = arguments.get('threshold', 0.8)
                    dry_run = arguments.get('dry_run', False)
                    
                    command = ["stm", "promote", "--threshold", str(threshold)]
                    if dry_run:
                        command.append("--dry-run")
                    
                    result = self._run_cli_command(command)
                    
                    if result["success"]:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": f"⬆️ Promoted from temporary to PERMANENT storage:\n{result['output']}"}]
                            }
                        }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {"code": -32603, "message": f"STM promote failed: {result['error']}"}
                        }
                
                elif tool_name == 'stm_cleanup':
                    smart = arguments.get('smart', False)
                    expired = arguments.get('expired', False)
                    threshold = arguments.get('threshold', 0.2)
                    
                    command = ["stm", "cleanup", "--threshold", str(threshold)]
                    if smart:
                        command.append("--smart")
                    if expired:
                        command.append("--expired")
                    
                    result = self._run_cli_command(command)
                    
                    if result["success"]:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": f"🧹 Cleaned up temporary memories:\n{result['output']}"}]
                            }
                        }
                    else:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {"code": -32603, "message": f"STM cleanup failed: {result['error']}"}
                        }
                
                # 알 수 없는 도구
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    }
            
            # 4. Notifications (처리하지 않음)
            elif method == 'notifications/initialized':
                # 알림은 응답하지 않음
                return None
                
            # 5. 지원하지 않는 메서드
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
        except Exception as e:
            logger.error(f"Request handling failed: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get('id', 1),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

async def main():
    """메인 서버 루프"""
    try:
        server = ClaudeCodeMCPServer()
        logger.info("Claude Code compatible MCP server started")
        
        # STDIO로 JSON-RPC 메시지 처리
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                    
                line = line.strip()
                if not line:
                    continue
                    
                # JSON 파싱
                request = json.loads(line)
                response = await server.handle_request(request)
                
                # 응답 전송 (None이 아닌 경우에만)
                if response is not None:
                    print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"}
                }
                print(json.dumps(error_response), flush=True)
                
            except KeyboardInterrupt:
                logger.info("Server interrupted")
                break
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)
    finally:
        logger.info("Claude Code MCP server stopped")

if __name__ == "__main__":
    # Python 버전 확인
    if sys.version_info < (3, 6):
        print("Error: Python 3.6+ required", file=sys.stderr)
        sys.exit(1)
        
    # 비동기 실행
    try:
        asyncio.run(main())
    except AttributeError:
        # Python 3.6 호환성
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())