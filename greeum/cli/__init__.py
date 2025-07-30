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
def api():
    """API server commands"""
    pass

# Memory 서브명령어들
@memory.command()
@click.argument('content')
@click.option('--importance', '-i', default=0.5, help='Importance score (0.0-1.0)')
@click.option('--tags', '-t', help='Comma-separated tags')
def add(content: str, importance: float, tags: Optional[str]):
    """Add new memory to long-term storage"""
    from ..core import BlockManager, DatabaseManager
    from ..text_utils import process_user_input
    
    try:
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
def search(query: str, count: int, threshold: float):
    """Search memories by keywords/semantic similarity"""
    from ..core import BlockManager, DatabaseManager
    
    try:
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
        
        results = block_manager.search_by_keywords([query], limit=count)
        
        if results:
            click.echo(f"🔍 Found {len(results)} memories:")
            for i, block in enumerate(results, 1):
                click.echo(f"{i}. [{block.get('timestamp', 'Unknown')}] {block.get('context', 'No content')[:100]}...")
        else:
            click.echo("❌ No memories found")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)

# MCP 서브명령어들
@mcp.command()
@click.option('--transport', '-t', default='stdio', help='Transport type (stdio/ws)')
@click.option('--port', '-p', default=3000, help='WebSocket port (if transport=ws)')
def serve(transport: str, port: int):
    """Start MCP server for Claude Code integration"""  
    click.echo(f"🚀 Starting Greeum MCP server ({transport})...")
    
    if transport == 'stdio':
        from ..mcp.claude_code_mcp_server import main as mcp_main
        import asyncio
        try:
            asyncio.run(mcp_main())
        except KeyboardInterrupt:
            click.echo("\n👋 MCP server stopped")
    else:
        click.echo(f"❌ Transport '{transport}' not supported yet")
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

if __name__ == '__main__':
    main()