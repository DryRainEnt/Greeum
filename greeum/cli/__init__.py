"""
Greeum v2.0 통합 CLI 시스템

사용법:
  greeum memory add "새로운 기억"
  greeum memory search "검색어"
  greeum mcp serve --transport stdio
  greeum api serve --port 5000
"""

try:
    import click
except ImportError:
    print("❌ Click not installed. Install with: pip install greeum")
    import sys
    sys.exit(1)

import sys
from typing import Optional

@click.group()
@click.version_option()
def main():
    """Greeum Universal Memory System v2.0"""
    pass

@main.group()
def memory():
    """Memory management commands (STM/LTM)"""
    pass

@main.group() 
def mcp():
    """MCP server commands"""
    pass

@main.group()
def ltm():
    """Long-term memory (LTM) specialized commands"""
    pass

@main.group()
def stm():
    """Short-term memory (STM) specialized commands"""
    pass

@main.group()
def api():
    """API server commands"""
    pass

@main.group()
def slots():
    """AI Context Slots management (v2.5.1 enhanced)"""
    pass

@main.group()
def migrate():
    """Database migration commands (v2.5.3 AI-Powered Migration)"""
    pass

@main.group()
def backup():
    """Memory backup and restore commands (v2.6.1)"""
    pass

@main.group() 
def restore():
    """Memory restore commands (v2.6.1)"""
    pass

# Memory 서브명령어들
@memory.command()
@click.argument('content')
@click.option('--importance', '-i', default=0.5, help='Importance score (0.0-1.0)')
@click.option('--tags', '-t', help='Comma-separated tags')
@click.option('--slot', '-s', type=click.Choice(['A', 'B', 'C']), help='Insert near specified anchor slot')
def add(content: str, importance: float, tags: Optional[str], slot: Optional[str]):
    """Add new memory to long-term storage"""
    try:
        if slot:
            # Use anchor-based write
            from ..api.write import write as anchor_write
            
            result = anchor_write(
                text=content,
                slot=slot,
                policy={'importance': importance, 'tags': tags}
            )
            
            click.echo(f"✅ Memory added near anchor {slot} (Block #{result})")
            
        else:
            # Use traditional write
            from ..core import BlockManager, DatabaseManager
            from ..text_utils import process_user_input
            
            db_manager = DatabaseManager()
            block_manager = BlockManager(db_manager)
            
            # 텍스트 처리
            processed = process_user_input(content)
            keywords = processed.get('keywords', [])
            tag_list = tags.split(',') if tags else processed.get('tags', [])
            embedding = processed.get('embedding', [0.0] * 384)
            
            # 블록 추가
            block = block_manager.add_block(
                context=content,
                keywords=keywords,
                tags=tag_list,
                embedding=embedding,
                importance=importance
            )
            
            if block:
                click.echo(f"✅ Memory added (Block #{block['block_index']})")
            else:
                click.echo("❌ Failed to add memory")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)

@memory.command()
@click.argument('query')
@click.option('--count', '-c', default=5, help='Number of results')
@click.option('--threshold', '-th', default=0.1, help='Similarity threshold')
@click.option('--slot', '-s', type=click.Choice(['A', 'B', 'C']), help='Use anchor-based localized search')
@click.option('--radius', '-r', type=int, help='Graph search radius (1-3)')
@click.option('--no-fallback', is_flag=True, help='Disable fallback to global search')
def search(query: str, count: int, threshold: float, slot: str, radius: int, no_fallback: bool):
    """Search memories by keywords/semantic similarity"""
    try:
        from ..core.search_engine import SearchEngine
        
        # Use enhanced search engine with anchor support
        search_engine = SearchEngine()
        
        # Perform search with anchor parameters
        result = search_engine.search(
            query=query,
            top_k=count,
            slot=slot,
            radius=radius,
            fallback=not no_fallback
        )
        
        blocks = result.get('blocks', [])
        metadata = result.get('metadata', {})
        timing = result.get('timing', {})
        
        if blocks:
            # Display search info
            if slot:
                search_type = f"🎯 Anchor-based search (slot {slot})"
                if metadata.get('fallback_used'):
                    search_type += " → 🔄 Global fallback"
                click.echo(search_type)
                click.echo(f"   Hit rate: {metadata.get('local_hit_rate', 0):.1%}")
                click.echo(f"   Avg hops: {metadata.get('avg_hops', 0)}")
            else:
                click.echo("🔍 Global semantic search")
            
            # Display timing
            total_ms = sum(timing.values())
            click.echo(f"   Search time: {total_ms:.1f}ms")
            
            click.echo(f"\n📋 Found {len(blocks)} memories:")
            for i, block in enumerate(blocks, 1):
                timestamp = block.get('timestamp', 'Unknown')
                content = block.get('context', 'No content')[:80]
                relevance = block.get('relevance_score', 0)
                final_score = block.get('final_score', relevance)
                
                click.echo(f"{i}. [{timestamp}] {content}...")
                click.echo(f"   Score: {final_score:.3f}")
        else:
            if slot and not no_fallback:
                click.echo(f"❌ No memories found in anchor slot {slot}, and fallback disabled")
            else:
                click.echo("❌ No memories found")
            
    except Exception as e:
        click.echo(f"❌ Search failed: {e}")
        sys.exit(1)

# MCP 서브명령어들
@mcp.command()
@click.option('--transport', '-t', default='stdio', help='Transport type (stdio/ws)')
@click.option('--port', '-p', default=3000, help='WebSocket port (if transport=ws)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging (INFO level)')
@click.option('--debug', '-d', is_flag=True, help='Enable debug logging (DEBUG level)')
@click.option('--quiet', '-q', is_flag=True, help='[DEPRECATED] Use default behavior instead')
def serve(transport: str, port: int, verbose: bool, debug: bool, quiet: bool):
    """Start MCP server for Claude Code integration"""  
    # 로깅 레벨 결정 (새로운 정책: 기본은 조용함)
    if debug:
        log_level = 'debug'
        click.echo(f"🔍 Starting Greeum MCP server ({transport}) - DEBUG mode...")
    elif verbose:
        log_level = 'verbose'
        click.echo(f"📝 Starting Greeum MCP server ({transport}) - VERBOSE mode...")
    else:
        log_level = 'quiet'
        # 기본은 조용함 (출력 없음)
    
    # --quiet 플래그 호환성 경고
    if quiet:
        if verbose or debug:
            click.echo("⚠️  Warning: --quiet is deprecated and conflicts with --verbose/--debug")
        else:
            click.echo("⚠️  Warning: --quiet is deprecated. Default behavior is now quiet.")
    
    if transport == 'stdio':
        try:
            # Native MCP Server 사용 (FastMCP 완전 배제, anyio 기반 안전한 실행)
            from ..mcp.native import run_server_sync
            run_server_sync(log_level=log_level)
        except ImportError as e:
            if verbose or debug:
                click.echo(f"Native MCP server import failed: {e}")
                click.echo("Please ensure anyio>=4.5 is installed: pip install anyio>=4.5")
            sys.exit(1)
        except KeyboardInterrupt:
            if verbose or debug:
                click.echo("\nMCP server stopped")
        except Exception as e:
            # anyio CancelledError도 여기서 캐치됨 - 조용히 처리
            error_msg = str(e)
            if "CancelledError" in error_msg or "cancelled" in error_msg.lower():
                if verbose or debug:
                    click.echo("\nMCP server stopped")
            else:
                if verbose or debug:
                    click.echo(f"MCP server error: {e}")
                sys.exit(1)
    elif transport == 'websocket':
        try:
            # WebSocket transport (향후 확장)
            from ..mcp.cli_entry import run_cli_server
            run_cli_server(transport='websocket', port=port)
        except ImportError as e:
            if verbose or debug:
                click.echo(f"MCP server import failed: {e}")
                click.echo("Please ensure all dependencies are installed")
            sys.exit(1)
        except NotImplementedError:
            if verbose or debug:
                click.echo(f"WebSocket transport not implemented yet")
            sys.exit(1)
        except KeyboardInterrupt:
            if verbose or debug:
                click.echo("\nMCP server stopped")
        except Exception as e:
            if verbose or debug:
                click.echo(f"MCP server error: {e}")
            sys.exit(1)
    else:
        if verbose or debug:
            click.echo(f"❌ Transport '{transport}' not supported")
        sys.exit(1)

# API 서브명령어들  
@api.command()
@click.option('--port', '-p', default=5000, help='Server port')
@click.option('--host', '-h', default='localhost', help='Server host')
def serve(port: int, host: str):
    """Start REST API server"""
    click.echo(f"🌐 Starting Greeum API server on {host}:{port}...")
    
    try:
        from ..api.memory_api import app
        import uvicorn
        uvicorn.run(app, host=host, port=port)
    except ImportError:
        click.echo("❌ API server dependencies not installed. Try: pip install greeum[api]")
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n👋 API server stopped")

# LTM 서브명령어들
@ltm.command()
@click.option('--trends', is_flag=True, help='Analyze emotional and topic trends')
@click.option('--period', '-p', default='6m', help='Analysis period (e.g., 6m, 1y)')
@click.option('--output', '-o', default='text', help='Output format (text/json)')
def analyze(trends: bool, period: str, output: str):
    """Analyze long-term memory patterns and trends"""
    click.echo(f"🔍 Analyzing LTM patterns...")
    
    if trends:
        click.echo(f"📊 Trend analysis for period: {period}")
    
    try:
        from ..core import BlockManager, DatabaseManager
        import json
        from datetime import datetime, timedelta
        
        # 기간 파싱
        period_map = {'m': 'months', 'y': 'years', 'd': 'days', 'w': 'weeks'}
        period_num = int(period[:-1])
        period_unit = period_map.get(period[-1], 'months')
        
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
        
        # 전체 블록 조회
        all_blocks = block_manager.get_blocks()
        
        analysis = {
            "total_blocks": len(all_blocks),
            "analysis_period": period,
            "analysis_date": datetime.now().isoformat(),
            "summary": f"Analyzed {len(all_blocks)} memory blocks"
        }
        
        if trends:
            # 키워드 빈도 분석
            keyword_freq = {}
            for block in all_blocks:
                keywords = block.get('keywords', [])
                for keyword in keywords:
                    keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
            
            # 상위 키워드
            top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            analysis["top_keywords"] = top_keywords
        
        if output == 'json':
            click.echo(json.dumps(analysis, indent=2, ensure_ascii=False))
        else:
            click.echo(f"📈 Analysis Results:")
            click.echo(f"  • Total memories: {analysis['total_blocks']}")
            click.echo(f"  • Period: {analysis['analysis_period']}")
            if trends and 'top_keywords' in analysis:
                click.echo(f"  • Top keywords:")
                for keyword, freq in analysis['top_keywords'][:5]:
                    click.echo(f"    - {keyword}: {freq} times")
                    
    except Exception as e:
        click.echo(f"❌ Analysis failed: {e}")
        sys.exit(1)

@ltm.command()
@click.option('--repair', is_flag=True, help='Attempt to repair integrity issues')
def verify(repair: bool):
    """Verify blockchain-like LTM integrity"""
    click.echo("🔍 Verifying LTM blockchain integrity...")
    
    try:
        from ..core import BlockManager, DatabaseManager
        import hashlib
        
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
        
        all_blocks = block_manager.get_blocks()
        
        issues = []
        verified_count = 0
        
        for i, block in enumerate(all_blocks):
            # 해시 검증
            if 'hash' in block:
                # 블록 데이터로부터 해시 재계산
                block_data = {
                    'block_index': block.get('block_index'),
                    'timestamp': block.get('timestamp'),
                    'context': block.get('context'),
                    'prev_hash': block.get('prev_hash', '')
                }
                calculated_hash = hashlib.sha256(
                    str(block_data).encode()
                ).hexdigest()[:16]
                
                if block.get('hash') != calculated_hash:
                    issues.append(f"Block #{block.get('block_index', i)}: Hash mismatch")
                else:
                    verified_count += 1
            else:
                issues.append(f"Block #{block.get('block_index', i)}: Missing hash")
        
        # 결과 출력
        total_blocks = len(all_blocks)
        click.echo(f"✅ Verified {verified_count}/{total_blocks} blocks")
        
        if issues:
            click.echo(f"⚠️  Found {len(issues)} integrity issues:")
            for issue in issues[:10]:  # 최대 10개만 표시
                click.echo(f"  • {issue}")
            
            if repair:
                click.echo("🔨 Repair functionality not implemented yet")
        else:
            click.echo("🎉 All blocks verified successfully!")
                    
    except Exception as e:
        click.echo(f"❌ Verification failed: {e}")
        sys.exit(1)

@ltm.command()
@click.option('--format', '-f', default='json', help='Export format (json/blockchain/csv)')
@click.option('--output', '-o', help='Output file path')
@click.option('--limit', '-l', type=int, help='Limit number of blocks')
def export(format: str, output: str, limit: int):
    """Export LTM data in various formats"""
    click.echo(f"📤 Exporting LTM data (format: {format})...")
    
    try:
        from ..core import BlockManager, DatabaseManager
        import json
        import csv
        from pathlib import Path
        
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
        
        all_blocks = block_manager.get_blocks()
        
        if limit:
            all_blocks = all_blocks[:limit]
        
        # 출력 파일 경로 결정
        if not output:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"greeum_ltm_export_{timestamp}.{format}"
        
        output_path = Path(output)
        
        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_blocks, f, indent=2, ensure_ascii=False)
                
        elif format == 'blockchain':
            # 블록체인 형태로 구조화
            blockchain_data = {
                "chain_info": {
                    "total_blocks": len(all_blocks),
                    "export_date": datetime.now().isoformat(),
                    "format_version": "1.0"
                },
                "blocks": all_blocks
            }
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(blockchain_data, f, indent=2, ensure_ascii=False)
                
        elif format == 'csv':
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if all_blocks:
                    writer = csv.DictWriter(f, fieldnames=all_blocks[0].keys())
                    writer.writeheader()
                    writer.writerows(all_blocks)
        
        click.echo(f"✅ Exported {len(all_blocks)} blocks to: {output_path}")
        click.echo(f"📄 File size: {output_path.stat().st_size} bytes")
                    
    except Exception as e:
        click.echo(f"❌ Export failed: {e}")
        sys.exit(1)

# STM 서브명령어들
@stm.command()
@click.argument('content')
@click.option('--ttl', default='1h', help='Time to live (e.g., 1h, 30m, 2d)')
@click.option('--importance', '-i', default=0.3, help='Importance score (0.0-1.0)')
def add(content: str, ttl: str, importance: float):
    """Add content to short-term memory with TTL"""
    click.echo(f"🧠 Adding to STM (TTL: {ttl})...")
    
    try:
        from ..core import STMManager, DatabaseManager
        import re
        from datetime import datetime, timedelta
        
        # TTL 파싱
        ttl_pattern = r'(\d+)([hmdw])'
        match = re.match(ttl_pattern, ttl.lower())
        if not match:
            click.echo("❌ Invalid TTL format. Use: 1h, 30m, 2d, 1w")
            sys.exit(1)
        
        amount, unit = match.groups()
        amount = int(amount)
        
        unit_map = {'m': 'minutes', 'h': 'hours', 'd': 'days', 'w': 'weeks'}
        unit_name = unit_map.get(unit, 'hours')
        
        # TTL 계산
        kwargs = {unit_name: amount}
        expiry_time = datetime.now() + timedelta(**kwargs)
        
        db_manager = DatabaseManager()
        stm_manager = STMManager(db_manager)
        
        # STM에 추가
        memory_data = {
            'content': content,
            'importance': importance,
            'ttl_seconds': int(timedelta(**kwargs).total_seconds()),
            'expiry_time': expiry_time.isoformat()
        }
        result = stm_manager.add_memory(memory_data)
        
        if result:
            click.echo(f"✅ Added to STM (expires: {expiry_time.strftime('%Y-%m-%d %H:%M:%S')})")
        else:
            click.echo("❌ Failed to add to STM")
            sys.exit(1)
                    
    except Exception as e:
        click.echo(f"❌ STM add failed: {e}")
        sys.exit(1)

@stm.command()
@click.option('--threshold', '-t', default=0.8, help='Importance threshold for promotion')
@click.option('--dry-run', is_flag=True, help='Show what would be promoted without doing it')
def promote(threshold: float, dry_run: bool):
    """Promote important STM entries to LTM"""
    click.echo(f"🔝 Promoting STM → LTM (threshold: {threshold})...")
    
    try:
        from ..core import STMManager, BlockManager, DatabaseManager
        from ..text_utils import process_user_input
        
        db_manager = DatabaseManager()
        stm_manager = STMManager(db_manager)
        block_manager = BlockManager(db_manager)
        
        # STM에서 모든 항목 조회 (충분히 큰 수로)
        stm_entries = stm_manager.get_recent_memories(count=1000)
        
        candidates = []
        for entry in stm_entries:
            if entry.get('importance', 0) >= threshold:
                candidates.append(entry)
        
        if not candidates:
            click.echo(f"📭 No STM entries above threshold {threshold}")
            return
        
        click.echo(f"🎯 Found {len(candidates)} candidates for promotion:")
        
        promoted_count = 0
        for entry in candidates:
            content = entry.get('content', '')
            importance = entry.get('importance', 0)
            
            click.echo(f"  • {content[:50]}... (importance: {importance:.2f})")
            
            if not dry_run:
                # LTM으로 승격
                keywords, tags = process_user_input(content)
                
                # 간단한 임베딩 (실제로는 더 정교하게)
                simple_embedding = [hash(word) % 1000 / 1000.0 for word in content.split()[:10]]
                simple_embedding.extend([0.0] * (10 - len(simple_embedding)))  # 10차원으로 패딩
                
                ltm_block = block_manager.add_block(
                    context=content,
                    keywords=keywords,
                    tags=tags,
                    embedding=simple_embedding,
                    importance=importance,
                    metadata={'promoted_from_stm': True}
                )
                
                if ltm_block:
                    # STM에서 제거
                    stm_manager.remove_memory(entry.get('id', ''))
                    promoted_count += 1
        
        if dry_run:
            click.echo(f"🔍 Dry run: {len(candidates)} entries would be promoted")
        else:
            click.echo(f"✅ Promoted {promoted_count}/{len(candidates)} entries to LTM")
                    
    except Exception as e:
        click.echo(f"❌ Promotion failed: {e}")
        sys.exit(1)

@stm.command()
@click.option('--smart', is_flag=True, help='Use intelligent cleanup based on importance')
@click.option('--expired', is_flag=True, help='Remove only expired entries')
@click.option('--threshold', '-t', default=0.2, help='Remove entries below this importance')
def cleanup(smart: bool, expired: bool, threshold: float):
    """Clean up short-term memory entries"""
    click.echo("🧹 Cleaning up STM...")
    
    try:
        from ..core import STMManager, DatabaseManager
        from datetime import datetime
        
        db_manager = DatabaseManager()
        stm_manager = STMManager(db_manager)
        stm_entries = stm_manager.get_recent_memories(count=1000)
        
        if not stm_entries:
            click.echo("📭 STM is already empty")
            return
        
        removed_count = 0
        total_count = len(stm_entries)
        
        click.echo(f"📊 Total STM entries: {total_count}")
        
        for entry in stm_entries:
            should_remove = False
            reason = ""
            
            if expired:
                # 만료된 항목만 제거
                expiry = entry.get('expiry_time')
                if expiry and datetime.now() > datetime.fromisoformat(expiry):
                    should_remove = True
                    reason = "expired"
            
            elif smart:
                # 지능형 정리
                importance = entry.get('importance', 0)
                if importance < threshold:
                    should_remove = True
                    reason = f"low importance ({importance:.2f} < {threshold})"
            
            else:
                # 기본: 낮은 중요도만
                importance = entry.get('importance', 0)
                if importance < 0.1:
                    should_remove = True
                    reason = "very low importance"
            
            if should_remove:
                entry_id = entry.get('id', '')
                content = entry.get('content', '')[:30]
                
                if stm_manager.remove_memory(entry_id):
                    click.echo(f"  🗑️  Removed: {content}... ({reason})")
                    removed_count += 1
        
        click.echo(f"✅ Cleanup complete: {removed_count}/{total_count} entries removed")
        click.echo(f"📊 Remaining STM entries: {total_count - removed_count}")
                    
    except Exception as e:
        click.echo(f"❌ Cleanup failed: {e}")
        sys.exit(1)

# AI Context Slots 서브명령어들 (v2.5.1)
@slots.command()
def status():
    """Display current AI Context Slots status (v2.5.1)"""
    click.echo("🧠 AI Context Slots Status Report (v2.5.1)")
    click.echo("=" * 50)
    
    try:
        from ..core.working_memory import AIContextualSlots
        from datetime import datetime
        
        # AI Context Slots 인스턴스 생성
        slots_instance = AIContextualSlots()
        
        # 슬롯 상태 확인
        status = slots_instance.get_status()
        
        active_count = sum(1 for s in status.values() if s is not None)
        click.echo(f"Active Slots: {active_count}/3")
        
        for slot_name, slot_info in status.items():
            if slot_info:
                slot_type = slot_info['type']
                content = slot_info['content_preview']
                timestamp = slot_info['timestamp']
                importance = slot_info['importance']
                is_anchor = slot_info['is_anchor']
                
                # 슬롯 타입별 아이콘
                type_icon = {"context": "🎯", "anchor": "⚓", "buffer": "📋"}.get(slot_type, "🔹")
                
                click.echo(f"\n{type_icon} {slot_name.upper()} Slot ({slot_type})")
                click.echo(f"   Content: {content}")
                click.echo(f"   Importance: {importance:.2f}")
                click.echo(f"   Created: {timestamp}")
                
                if is_anchor and slot_info.get('anchor_block'):
                    click.echo(f"   🔗 LTM Anchor: Block #{slot_info['anchor_block']}")
                    
            else:
                click.echo(f"\n⭕ {slot_name.upper()} Slot: Empty")
        
        click.echo("\n" + "=" * 50)
        click.echo("💡 Use 'greeum slots set <content>' to add to slots")
        click.echo("💡 Use 'greeum slots clear <slot_name>' to clear specific slot")
                    
    except Exception as e:
        click.echo(f"❌ Error reading slots status: {e}")
        sys.exit(1)

@slots.command()
@click.argument('content')
@click.option('--importance', '-i', default=0.5, help='Importance score (0.0-1.0)')
@click.option('--ltm-anchor', type=int, help='LTM block ID for anchoring')
@click.option('--radius', default=5, help='Search radius for LTM anchor')
def set(content: str, importance: float, ltm_anchor: int, radius: int):
    """Add content to AI Context Slots with smart allocation"""
    click.echo(f"🧠 Adding content to AI Context Slots...")
    
    try:
        from ..core.working_memory import AIContextualSlots
        
        # AI Context Slots 인스턴스 생성
        slots_instance = AIContextualSlots()
        
        # 컨텍스트 구성
        context = {
            'importance': importance,
            'metadata': {'cli_command': True}
        }
        
        if ltm_anchor:
            context['ltm_block_id'] = ltm_anchor
            context['search_radius'] = radius
        
        # AI가 최적 슬롯 결정
        used_slot = slots_instance.ai_decide_usage(content, context)
        
        # 결과 출력
        click.echo(f"✅ Content added to {used_slot.upper()} slot")
        click.echo(f"📝 Content: {content[:80]}{'...' if len(content) > 80 else ''}")
        click.echo(f"🎯 AI chose {used_slot} slot based on content analysis")
        
        if ltm_anchor:
            click.echo(f"🔗 LTM Anchor: Block #{ltm_anchor} (radius: {radius})")
        
    except Exception as e:
        click.echo(f"❌ Failed to add to slots: {e}")
        sys.exit(1)

@slots.command()
@click.argument('slot_name', type=click.Choice(['active', 'anchor', 'buffer', 'all']))
def clear(slot_name: str):
    """Clear specific slot or all slots"""
    click.echo(f"🗑️  Clearing {slot_name} slot(s)...")
    
    try:
        from ..core.working_memory import AIContextualSlots
        
        # AI Context Slots 인스턴스 생성
        slots_instance = AIContextualSlots()
        
        if slot_name == "all":
            # 모든 슬롯 비우기
            cleared_count = 0
            for slot in ['active', 'anchor', 'buffer']:
                if slots_instance.clear_slot(slot):
                    cleared_count += 1
            
            click.echo(f"✅ Cleared {cleared_count} slots")
            
        else:
            # 특정 슬롯 비우기
            if slots_instance.clear_slot(slot_name):
                click.echo(f"✅ Cleared {slot_name.upper()} slot")
            else:
                click.echo(f"⚠️  {slot_name.upper()} slot was already empty")
        
    except Exception as e:
        click.echo(f"❌ Failed to clear slot: {e}")
        sys.exit(1)

@slots.command()
@click.argument('query')
@click.option('--limit', '-l', default=5, help='Maximum number of results')
def search(query: str, limit: int):
    """Search using AI Context Slots integration"""
    click.echo(f"🔍 Searching with AI Context Slots: '{query}'")
    
    try:
        from ..core.database_manager import DatabaseManager
        from ..core.block_manager import BlockManager
        
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
        
        # 슬롯 통합 검색 실행
        results = block_manager.search_with_slots(
            query=query, 
            limit=limit, 
            use_slots=True
        )
        
        if results:
            click.echo(f"📋 Found {len(results)} results:")
            
            for i, result in enumerate(results, 1):
                source = result.get('source', 'unknown')
                content = result.get('context', 'No content')[:80]
                importance = result.get('importance', 0)
                
                if source == 'working_memory':
                    slot_type = result.get('slot_type', 'unknown')
                    type_icon = {"context": "🎯", "anchor": "⚓", "buffer": "📋"}.get(slot_type, "🔹")
                    click.echo(f"{i}. {type_icon} [{slot_type.upper()} SLOT] {content}...")
                else:
                    block_index = result.get('block_index', '?')
                    click.echo(f"{i}. 📚 [LTM #{block_index}] {content}...")
                
                click.echo(f"   Importance: {importance:.2f}")
        else:
            click.echo("❌ No results found")
        
    except Exception as e:
        click.echo(f"❌ Search failed: {e}")
        sys.exit(1)

# Migration 서브명령어들 (v2.5.3 AI-Powered Migration)
@migrate.command()
@click.option('--data-dir', default='data', help='Data directory path')
@click.option('--force', is_flag=True, help='Force migration even if already v2.5.3')
def check(data_dir: str, force: bool):
    """Check database schema version and trigger migration if needed"""
    click.echo("🔍 Checking Greeum database schema version...")
    
    try:
        from ..core.migration import ForcedMigrationInterface
        
        # Create migration interface
        interface = ForcedMigrationInterface(data_dir)
        
        if force:
            # Force migration regardless of version
            success = interface._force_migration_flow()
        else:
            # Normal migration check
            success = interface.check_and_force_migration()
        
        if success:
            click.echo("\n✨ Database is ready for use!")
            sys.exit(0)
        else:
            click.echo("\n❌ Migration failed or was cancelled")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Migration check failed: {e}")
        sys.exit(1)

@migrate.command()
@click.option('--data-dir', default='data', help='Data directory path')
def status(data_dir: str):
    """Check current migration status and schema version"""
    click.echo("📊 Greeum Database Migration Status")
    click.echo("=" * 40)
    
    try:
        from ..core.migration import SchemaVersionManager, AtomicBackupSystem
        from pathlib import Path
        import os
        
        db_path = Path(data_dir) / "memory.db"
        
        if not db_path.exists():
            click.echo("📂 Database Status: Not found")
            click.echo("   This appears to be a new installation")
            return
        
        # Check schema version
        version_manager = SchemaVersionManager(str(db_path))
        version_manager.connect()
        
        current_version = version_manager.detect_schema_version()
        needs_migration = version_manager.needs_migration()
        stats = version_manager.get_migration_stats() if needs_migration else None
        
        click.echo(f"📋 Schema Version: {current_version.value}")
        click.echo(f"📂 Database Size: {db_path.stat().st_size} bytes")
        
        if stats:
            click.echo(f"💾 Total Memories: {stats['total_blocks']}")
            click.echo(f"📅 Date Range: {stats['earliest_memory']} to {stats['latest_memory']}")
        
        if needs_migration:
            click.echo("\n⚠️  Migration Required:")
            click.echo("   Legacy v2.5.2 database detected")
            click.echo("   Run 'greeum migrate check' to upgrade")
        else:
            click.echo("\n✅ Migration Status: Up to date")
        
        # Check backup status
        backup_system = AtomicBackupSystem(data_dir)
        backups = backup_system.list_backups()
        
        click.echo(f"\n💾 Backup Status: {len(backups)} backups available")
        if backups:
            recent_backup = sorted(backups, key=lambda x: x['created_at'], reverse=True)[0]
            click.echo(f"   Most recent: {recent_backup['created_at']}")
        
        version_manager.close()
        
    except Exception as e:
        click.echo(f"❌ Status check failed: {e}")
        sys.exit(1)

@migrate.command()
@click.option('--data-dir', default='data', help='Data directory path')
@click.option('--backup-id', help='Specific backup ID to rollback to')
@click.option('--reason', default='Manual rollback', help='Reason for rollback')
def rollback(data_dir: str, backup_id: str, reason: str):
    """Rollback to previous database state using backups"""
    click.echo("↩️  Initiating Emergency Rollback")
    
    try:
        from ..core.migration import EmergencyRollbackManager, AtomicBackupSystem
        from pathlib import Path
        
        db_path = Path(data_dir) / "memory.db"
        backup_system = AtomicBackupSystem(data_dir)
        rollback_manager = EmergencyRollbackManager(str(db_path), backup_system)
        
        if not backup_id:
            # List available rollback options
            options = rollback_manager.list_rollback_options()
            
            if not options:
                click.echo("❌ No rollback options available")
                return
            
            click.echo("📋 Available rollback options:")
            for i, option in enumerate(options[:10], 1):
                created = option['created_at'][:19]  # Remove milliseconds
                size_kb = option['backup_size'] / 1024
                status = "✅ Verified" if option['backup_verified'] else "⚠️  Unverified"
                
                click.echo(f"{i}. {option['backup_id']}")
                click.echo(f"   Created: {created}")
                click.echo(f"   Size: {size_kb:.1f} KB")
                click.echo(f"   Status: {status}")
                click.echo()
            
            # Get user choice
            choice = click.prompt("Select backup number (1-{}) or 'q' to quit".format(len(options)), type=str)
            
            if choice.lower() == 'q':
                click.echo("Rollback cancelled")
                return
            
            try:
                backup_index = int(choice) - 1
                if 0 <= backup_index < len(options):
                    backup_id = options[backup_index]['backup_id']
                else:
                    click.echo("❌ Invalid selection")
                    return
            except ValueError:
                click.echo("❌ Invalid selection")
                return
        
        # Confirm rollback
        click.echo(f"\n⚠️  WARNING: This will restore database to backup '{backup_id}'")
        click.echo("   All changes since that backup will be lost!")
        
        if not click.confirm("Proceed with rollback?"):
            click.echo("Rollback cancelled")
            return
        
        # Perform rollback
        result = rollback_manager.perform_emergency_rollback(backup_id, reason)
        
        # Show results
        if result['status'] == 'SUCCESS':
            click.echo(f"\n✅ Rollback completed successfully!")
            click.echo(f"⏱️  Duration: {result['rollback_duration']:.1f} seconds")
            click.echo(f"💾 Current state backed up as: {result.get('current_state_backup', 'N/A')}")
        elif result['status'] == 'PARTIAL_SUCCESS':
            click.echo(f"\n⚠️  Rollback completed with warnings")
            click.echo(f"⏱️  Duration: {result['rollback_duration']:.1f} seconds")
            for error in result['errors']:
                click.echo(f"   ⚠️  {error}")
        else:
            click.echo(f"\n❌ Rollback failed!")
            for error in result['errors']:
                click.echo(f"   ❌ {error}")
        
    except Exception as e:
        click.echo(f"❌ Rollback failed: {e}")
        sys.exit(1)

@migrate.command()
@click.option('--data-dir', default='data', help='Data directory path')
def validate(data_dir: str):
    """Validate migration results and database health"""
    click.echo("🔍 Validating Database Migration Health")
    click.echo("=" * 40)
    
    try:
        from ..core.migration import MigrationValidator, AtomicBackupSystem
        from pathlib import Path
        
        db_path = Path(data_dir) / "memory.db"
        
        if not db_path.exists():
            click.echo("❌ Database not found")
            return
        
        # Create validator
        backup_system = AtomicBackupSystem(data_dir)
        validator = MigrationValidator(str(db_path), backup_system)
        
        # Find most recent backup for validation
        backups = backup_system.list_backups()
        recent_backup_id = None
        
        if backups:
            recent_backup = sorted(backups, key=lambda x: x['created_at'], reverse=True)[0]
            recent_backup_id = recent_backup['backup_id']
        
        if not recent_backup_id:
            click.echo("⚠️  No recent backup found for validation")
            return
        
        # Run validation
        click.echo("🔄 Running comprehensive validation...")
        results = validator.validate_full_migration(recent_backup_id)
        
        # Display results
        status_colors = {
            "VALIDATION_PASSED": "✅",
            "MINOR_WARNINGS": "⚠️ ", 
            "WARNINGS": "⚠️ ",
            "MINOR_ISSUES": "🔶",
            "MAJOR_ISSUES": "🔴",
            "CRITICAL_FAILURE": "❌"
        }
        
        status_icon = status_colors.get(results['overall_status'], "❓")
        click.echo(f"\n{status_icon} Overall Status: {results['overall_status']}")
        
        # Show individual check results
        for check_name, check_result in results['checks'].items():
            check_status = check_result.get('status', 'UNKNOWN')
            check_icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌", "ERROR": "💥"}.get(check_status, "❓")
            
            click.echo(f"\n{check_icon} {check_name.replace('_', ' ').title()}: {check_status}")
            
            # Show additional details for failed/warning checks
            if check_status in ["FAIL", "ERROR"]:
                error = check_result.get('error')
                if error:
                    click.echo(f"   Error: {error}")
                
                errors = check_result.get('errors', [])
                for error in errors[:3]:  # Show first 3 errors
                    click.echo(f"   • {error}")
            
            elif check_status == "WARN":
                warnings = check_result.get('warnings', [])
                for warning in warnings[:3]:  # Show first 3 warnings
                    click.echo(f"   • {warning}")
        
        # Migration recommendations
        if results['overall_status'] == "CRITICAL_FAILURE":
            click.echo(f"\n🚨 CRITICAL: Consider emergency rollback")
            click.echo(f"   Run: greeum migrate rollback --backup-id {recent_backup_id}")
        elif results['overall_status'] in ["MAJOR_ISSUES", "MINOR_ISSUES"]:
            click.echo(f"\n💡 Recommendation: Monitor system closely")
            click.echo(f"   Consider rollback if issues persist")
        else:
            click.echo(f"\n🎉 Migration validation completed successfully!")
        
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}")
        sys.exit(1)

@migrate.command()
@click.option('--data-dir', default='data', help='Data directory path')
@click.option('--keep-backups', default=5, help='Number of backups to keep')
def cleanup(data_dir: str, keep_backups: int):
    """Clean up old migration backups"""
    click.echo(f"🧹 Cleaning up migration backups (keeping {keep_backups} most recent)")
    
    try:
        from ..core.migration import AtomicBackupSystem
        
        backup_system = AtomicBackupSystem(data_dir)
        
        # Show current backup status
        backups = backup_system.list_backups()
        click.echo(f"📊 Current backups: {len(backups)}")
        
        if len(backups) <= keep_backups:
            click.echo("✅ No cleanup needed")
            return
        
        # Perform cleanup
        backup_system.cleanup_old_backups(keep_backups)
        
        # Show results
        remaining_backups = backup_system.list_backups()
        removed_count = len(backups) - len(remaining_backups)
        
        click.echo(f"✅ Cleanup completed:")
        click.echo(f"   Removed: {removed_count} old backups")
        click.echo(f"   Remaining: {len(remaining_backups)} backups")
        
        # Calculate space saved (approximate)
        if backups:
            avg_size = sum(b.get('backup_size', 0) for b in backups) / len(backups)
            space_saved = avg_size * removed_count
            click.echo(f"   Space saved: ~{space_saved/1024:.1f} KB")
        
    except Exception as e:
        click.echo(f"❌ Cleanup failed: {e}")
        sys.exit(1)

# v2.6.1 Backup 서브명령어들
@backup.command()
@click.option('--output', '-o', required=True, help='백업 파일 저장 경로')
@click.option('--include-metadata/--no-metadata', default=True, help='시스템 메타데이터 포함 여부')
def export(output: str, include_metadata: bool):
    """전체 메모리를 백업 파일로 내보내기"""
    try:
        from ..core.backup_restore import MemoryBackupEngine
        from ..core.hierarchical_memory import HierarchicalMemorySystem
        from ..core.database_manager import DatabaseManager
        from pathlib import Path
        
        click.echo("🔄 메모리 백업을 시작합니다...")
        
        # 계층적 메모리 시스템 초기화
        db_manager = DatabaseManager()
        system = HierarchicalMemorySystem(db_manager)
        system.initialize()
        
        backup_engine = MemoryBackupEngine(system)
        success = backup_engine.create_backup(output, include_metadata)
        
        if success:
            click.echo(f"✅ 백업 완료: {output}")
            backup_path = Path(output)
            if backup_path.exists():
                size_mb = backup_path.stat().st_size / (1024 * 1024)
                click.echo(f"📁 파일 크기: {size_mb:.2f} MB")
        else:
            click.echo("❌ 백업 생성에 실패했습니다")
            
    except Exception as e:
        click.echo(f"💥 백업 중 오류: {e}")

# v2.6.1 Restore 서브명령어들
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
    """백업 파일로부터 메모리 복원"""
    try:
        from ..core.backup_restore import MemoryRestoreEngine, RestoreFilter
        from ..core.hierarchical_memory import HierarchicalMemorySystem
        from ..core.database_manager import DatabaseManager
        from ..core.memory_layer import MemoryLayerType
        from datetime import datetime
        
        # 복원 필터 생성
        date_from = None
        if from_date:
            try:
                date_from = datetime.strptime(from_date, '%Y-%m-%d')
            except ValueError:
                click.echo(f"⚠️ 잘못된 시작 날짜 형식: {from_date}")
        
        date_to = None
        if to_date:
            try:
                date_to = datetime.strptime(to_date, '%Y-%m-%d') 
            except ValueError:
                click.echo(f"⚠️ 잘못된 끝 날짜 형식: {to_date}")
        
        keyword_list = None
        if keywords:
            keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
        
        layer_list = None
        if layers:
            layer_map = {
                'working': MemoryLayerType.WORKING,
                'stm': MemoryLayerType.STM,
                'ltm': MemoryLayerType.LTM
            }
            layer_names = [layer.strip().lower() for layer in layers.split(',')]
            layer_list = [layer_map[name] for name in layer_names if name in layer_map]
        
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        filter_config = RestoreFilter(
            date_from=date_from,
            date_to=date_to,
            keywords=keyword_list,
            layers=layer_list,
            importance_min=importance_min,
            importance_max=importance_max,
            tags=tag_list
        )
        
        # 계층적 메모리 시스템 초기화
        db_manager = DatabaseManager()
        system = HierarchicalMemorySystem(db_manager)
        system.initialize()
        
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
            click.echo("🔄 메모리 복원을 시작합니다...")
            
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
                click.echo(f"   🧠 Working Memory: {result.working_count}개")
                click.echo(f"   ⚡ STM: {result.stm_count}개") 
                click.echo(f"   🏛️  LTM: {result.ltm_count}개")
                click.echo(f"   📈 총 처리: {result.total_processed}개")
                click.echo(f"   ⏱️  소요 시간: {result.execution_time:.2f}초")
                
                if result.error_count > 0:
                    click.echo(f"   ⚠️  오류: {result.error_count}개")
                    for error in result.errors[:5]:  # 최대 5개 오류만 표시
                        click.echo(f"      - {error}")
            else:
                click.echo("❌ 복원에 실패했습니다")
                for error in result.errors:
                    click.echo(f"   💥 {error}")
                    
    except Exception as e:
        click.echo(f"💥 복원 중 오류: {e}")

if __name__ == '__main__':
    main()