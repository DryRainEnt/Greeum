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
def anchors():
    """Anchor-based memory management (STM 3-slot system)"""
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
def serve(transport: str, port: int):
    """Start MCP server for Claude Code integration"""  
    click.echo(f"Starting Greeum MCP server ({transport})...")
    
    if transport == 'stdio':
        try:
            # Native MCP Server 사용 (FastMCP 완전 배제, anyio 기반 안전한 실행)
            from ..mcp.native import run_server_sync
            run_server_sync()
        except ImportError as e:
            click.echo(f"Native MCP server import failed: {e}")
            click.echo("Please ensure anyio>=4.5 is installed: pip install anyio>=4.5")
            sys.exit(1)
        except KeyboardInterrupt:
            click.echo("\nMCP server stopped")
        except Exception as e:
            # anyio CancelledError도 여기서 캐치됨 - 조용히 처리
            error_msg = str(e)
            if "CancelledError" in error_msg or "cancelled" in error_msg.lower():
                click.echo("\nMCP server stopped")
            else:
                click.echo(f"MCP server error: {e}")
                sys.exit(1)
    elif transport == 'websocket':
        try:
            # WebSocket transport (향후 확장)
            from ..mcp.cli_entry import run_cli_server
            run_cli_server(transport='websocket', port=port)
        except ImportError as e:
            click.echo(f"MCP server import failed: {e}")
            click.echo("Please ensure all dependencies are installed")
            sys.exit(1)
        except NotImplementedError:
            click.echo(f"WebSocket transport not implemented yet")
            sys.exit(1)
        except KeyboardInterrupt:
            click.echo("\nMCP server stopped")
        except Exception as e:
            click.echo(f"MCP server error: {e}")
            sys.exit(1)
    else:
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

# Anchors 서브명령어들
@anchors.command()
def status():
    """Display current anchor status for all slots (A/B/C)"""
    click.echo("⚓ Anchor Status Report")
    click.echo("=" * 50)
    
    try:
        from ..anchors import AnchorManager
        from pathlib import Path
        from datetime import datetime
        
        anchor_path = Path("data/anchors.json")
        if not anchor_path.exists():
            click.echo("❌ Anchor system not initialized. Run bootstrap first.")
            sys.exit(1)
        
        anchor_manager = AnchorManager(anchor_path)
        
        for slot_name in ['A', 'B', 'C']:
            slot_info = anchor_manager.get_slot_info(slot_name)
            if slot_info:
                anchor_id = slot_info['anchor_block_id']
                hop_budget = slot_info['hop_budget']
                pinned = "📌 PINNED" if slot_info['pinned'] else "🔄 Active"
                last_used = datetime.fromtimestamp(slot_info['last_used_ts'])
                summary = slot_info['summary']
                
                click.echo(f"\n🔹 Slot {slot_name}: {pinned}")
                click.echo(f"   Anchor Block: #{anchor_id}")
                click.echo(f"   Hop Budget: {hop_budget}")
                click.echo(f"   Last Used: {last_used.strftime('%Y-%m-%d %H:%M:%S')}")
                click.echo(f"   Summary: {summary}")
            else:
                click.echo(f"\n🔹 Slot {slot_name}: ❌ Not initialized")
        
        click.echo("\n" + "=" * 50)
        click.echo("💡 Use 'greeum anchors set A <block_id>' to configure anchors")
                    
    except Exception as e:
        click.echo(f"❌ Error reading anchor status: {e}")
        sys.exit(1)

@anchors.command()
@click.argument('slot', type=click.Choice(['A', 'B', 'C']))
@click.argument('block_id')
def set(slot: str, block_id: str):
    """Set anchor for specified slot to given block ID"""
    click.echo(f"⚓ Setting anchor for slot {slot} to block #{block_id}...")
    
    try:
        from ..anchors import AnchorManager
        from ..core import BlockManager, DatabaseManager
        from pathlib import Path
        
        # Validate block exists
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
        
        try:
            block_data = block_manager.db_manager.get_block_by_index(int(block_id))
            if not block_data:
                click.echo(f"❌ Block #{block_id} does not exist")
                sys.exit(1)
        except ValueError:
            click.echo(f"❌ Invalid block ID: {block_id}")
            sys.exit(1)
        
        # Load anchor manager
        anchor_path = Path("data/anchors.json")
        if not anchor_path.exists():
            click.echo("❌ Anchor system not initialized. Run bootstrap first.")
            sys.exit(1)
        
        anchor_manager = AnchorManager(anchor_path)
        
        # Get block embedding for topic vector
        import numpy as np
        block_embedding = np.array(block_data.get('embedding', [0.0] * 128))
        
        # Move anchor
        anchor_manager.move_anchor(slot, block_id, block_embedding)
        
        # Display success
        content_preview = block_data.get('context', '')[:60] + '...' if len(block_data.get('context', '')) > 60 else block_data.get('context', '')
        click.echo(f"✅ Anchor {slot} set to block #{block_id}")
        click.echo(f"📝 Content: {content_preview}")
        
    except Exception as e:
        click.echo(f"❌ Failed to set anchor: {e}")
        sys.exit(1)

@anchors.command()
@click.argument('slot', type=click.Choice(['A', 'B', 'C']))
@click.argument('block_id')
def pin(slot: str, block_id: str):
    """Pin anchor for specified slot to prevent automatic movement"""
    click.echo(f"📌 Pinning anchor for slot {slot} to block #{block_id}...")
    
    try:
        from ..anchors import AnchorManager
        from ..core import BlockManager, DatabaseManager
        from pathlib import Path
        
        # Validate block exists
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
        
        try:
            block_data = block_manager.db_manager.get_block_by_index(int(block_id))
            if not block_data:
                click.echo(f"❌ Block #{block_id} does not exist")
                sys.exit(1)
        except ValueError:
            click.echo(f"❌ Invalid block ID: {block_id}")
            sys.exit(1)
        
        # Load anchor manager
        anchor_path = Path("data/anchors.json")
        if not anchor_path.exists():
            click.echo("❌ Anchor system not initialized. Run bootstrap first.")
            sys.exit(1)
        
        anchor_manager = AnchorManager(anchor_path)
        
        # Set and pin anchor
        import numpy as np
        block_embedding = np.array(block_data.get('embedding', [0.0] * 128))
        
        anchor_manager.move_anchor(slot, block_id, block_embedding)
        anchor_manager.pin_anchor(slot)
        
        # Display success
        content_preview = block_data.get('context', '')[:60] + '...' if len(block_data.get('context', '')) > 60 else block_data.get('context', '')
        click.echo(f"✅ Anchor {slot} pinned to block #{block_id}")
        click.echo(f"📝 Content: {content_preview}")
        click.echo("🔒 This anchor will not move automatically during searches")
        
    except Exception as e:
        click.echo(f"❌ Failed to pin anchor: {e}")
        sys.exit(1)

@anchors.command()
@click.argument('slot', type=click.Choice(['A', 'B', 'C']))
def unpin(slot: str):
    """Unpin anchor for specified slot to allow automatic movement"""
    click.echo(f"🔓 Unpinning anchor for slot {slot}...")
    
    try:
        from ..anchors import AnchorManager
        from pathlib import Path
        
        # Load anchor manager
        anchor_path = Path("data/anchors.json")
        if not anchor_path.exists():
            click.echo("❌ Anchor system not initialized. Run bootstrap first.")
            sys.exit(1)
        
        anchor_manager = AnchorManager(anchor_path)
        
        # Check current state
        slot_info = anchor_manager.get_slot_info(slot)
        if not slot_info:
            click.echo(f"❌ Slot {slot} not found")
            sys.exit(1)
        
        if not slot_info['pinned']:
            click.echo(f"💡 Slot {slot} is already unpinned")
            return
        
        # Unpin anchor
        anchor_manager.unpin_anchor(slot)
        
        click.echo(f"✅ Anchor {slot} unpinned")
        click.echo("🔄 This anchor will now move automatically during relevant searches")
        
    except Exception as e:
        click.echo(f"❌ Failed to unpin anchor: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()