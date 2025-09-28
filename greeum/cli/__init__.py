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
    print("[ERROR] Click not installed. Install with: pip install greeum")
    import sys
    sys.exit(1)

import os
import sys
import sqlite3
import subprocess
import shutil
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict

from ..config_store import (
    DEFAULT_DATA_DIR,
    DEFAULT_ST_MODEL,
    GreeumConfig,
    ensure_data_dir,
    load_config,
    mark_semantic_ready,
    save_config,
)
from ..core.database_manager import DatabaseManager
from ..core.stm_anchor_store import get_anchor_store
from ..core.branch_schema import BranchSchemaSQL
from ..embedding_models import (
    init_sentence_transformer,
    force_simple_fallback,
)
from ..worker.client import WriteServiceClient, resolve_endpoint, WorkerUnavailableError
from ..worker import ensure_http_worker, get_worker_state


def _backup_database_files(db_path: Path, label: str = "auto") -> Path:
    """Create timestamped backups of the primary database and auxiliary files."""

    data_dir = db_path.parent
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_dir = data_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_path = backup_dir / f"memory_{label}_{timestamp}.db"
    if db_path.exists():
        shutil.copy(db_path, backup_path)

    for suffix in ("-wal", "-shm"):
        sidecar = Path(f"{db_path}{suffix}")
        if sidecar.exists():
            shutil.copy(sidecar, backup_dir / f"{sidecar.name}_{timestamp}")

    anchor_path = Path(os.environ.get("GREEUM_STM_DB", str(data_dir / "stm_anchors.db")))
    if anchor_path.exists():
        shutil.copy(anchor_path, backup_dir / f"stm_anchors_{label}_{timestamp}.db")

    return backup_path


def _reset_anchor_singleton() -> None:
    try:
        from ..core import stm_anchor_store

        with stm_anchor_store._singleton_lock:  # type: ignore[attr-defined]
            if stm_anchor_store._singleton is not None:  # type: ignore[attr-defined]
                try:
                    stm_anchor_store._singleton.close()  # type: ignore[attr-defined]
                except Exception:
                    pass
                stm_anchor_store._singleton = None  # type: ignore[attr-defined]
    except Exception:
        pass


def _remove_corrupt_database(db_path: Path) -> None:
    for suffix in ("", "-wal", "-shm"):
        target = Path(f"{db_path}{suffix}")
        if target.exists():
            target.unlink()

    anchor_path = Path(os.environ.get("GREEUM_STM_DB", str(db_path.parent / "stm_anchors.db")))
    if anchor_path.exists():
        try:
            anchor_path.unlink()
        except OSError:
            pass

    _reset_anchor_singleton()


def _ensure_database_ready(data_dir: Path, *, auto_accept: bool = False) -> None:
    db_path = data_dir / "memory.db"
    if not db_path.exists():
        return

    try:
        manager = DatabaseManager(connection_string=str(db_path))
        cursor = manager.conn.cursor()
    except sqlite3.DatabaseError as exc:
        message = str(exc).lower()
        if any(keyword in message for keyword in ("malformed", "not a database")):
            click.echo("[WARNING]  Existing database appears to be corrupted or uses an unsupported schema.")
            if auto_accept or click.confirm("Automatically back up the old files and rebuild a fresh database?", default=True):
                backup_path = _backup_database_files(db_path, label="malformed")
                click.echo(f"   - Backup saved to {backup_path}")
                _remove_corrupt_database(db_path)
                click.echo("   - Removed corrupt database. A new one will be created on next run.")
                return
            raise click.ClickException("Setup aborted: database schema is malformed.")
        raise click.ClickException(f"Database initialization failed: {exc}")

    try:
        needs_migration = BranchSchemaSQL.check_migration_needed(cursor)
    except Exception as exc:
        manager.conn.close()
        raise click.ClickException(f"Migration check failed: {exc}")

    if not needs_migration:
        manager.conn.close()
        return

    click.echo("[WARNING]  Existing database schema is older than the current release.")
    if not (auto_accept or click.confirm("Back up and upgrade the schema now?", default=True)):
        manager.conn.close()
        raise click.ClickException("Setup aborted: schema migration declined by user.")

    backup_path = _backup_database_files(db_path, label="schema")
    click.echo(f"   - Backup saved to {backup_path}")

    try:
        manager._apply_branch_migration(cursor)
        manager._initialize_branch_structures(cursor)
        manager.conn.commit()
    except Exception as exc:
        manager.conn.close()
        raise click.ClickException(f"Schema migration failed: {exc}")

    manager.conn.close()
    click.echo("   - Schema migration completed successfully.")



def _download_sentence_transformer(model: str) -> Path:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise ImportError(
            "sentence-transformers not installed. Install with 'pip install greeum[full]' "
            "or 'pip install sentence-transformers'."
        ) from exc

    cache_dir = Path.home() / ".cache" / "sentence_transformers"
    if os.getenv("GREEUM_DISABLE_ST"):
        raise RuntimeError("Semantic warmup skipped because GREEUM_DISABLE_ST is set.")
    SentenceTransformer(
        model,
        cache_folder=str(cache_dir),
        device=os.getenv("GREEUM_ST_DEVICE", None),
    )
    return cache_dir

@click.group()
@click.version_option()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--debug', is_flag=True, help='Enable debug logging (most verbose)')
@click.option('--quiet', '-q', is_flag=True, help='Suppress all non-essential output')
@click.pass_context
def main(ctx: click.Context, verbose: bool, debug: bool, quiet: bool):
    """Greeum Universal Memory System"""
    
    # Context에 로그 설정 저장
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['debug'] = debug
    ctx.obj['quiet'] = quiet
    
    # Console output 설정을 위한 환경변수 설정
    if verbose or debug:
        os.environ['GREEUM_CLI_VERBOSE'] = '1'
    else:
        os.environ.pop('GREEUM_CLI_VERBOSE', None)
    
    # 로그 레벨 설정
    import logging
    
    if debug:
        log_level = logging.DEBUG
    elif verbose:
        log_level = logging.INFO
    elif quiet:
        log_level = logging.ERROR
    else:
        log_level = logging.WARNING  # 기본값: 경고 이상만 표시
    
    # 로그 포맷 설정
    if debug:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    elif verbose:
        log_format = '%(levelname)s: %(message)s'
    else:
        log_format = '%(message)s'
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 특정 로거들의 레벨 조정 (너무 시끄러운 외부 라이브러리들)
    if not debug:
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

    # Ensure data directory from config is available if user hasn't set env vars
    config = load_config()
    data_dir = config.data_dir or str(DEFAULT_DATA_DIR)
    ensure_data_dir(data_dir)
    os.environ.setdefault('GREEUM_DATA_DIR', data_dir)


@main.command()
@click.option('--data-dir', type=click.Path(file_okay=False, dir_okay=True, writable=True), help='Custom data directory')
@click.option('--skip-warmup', is_flag=True, help='Skip SentenceTransformer warm-up step')
@click.option('--start-worker/--skip-worker', default=True, show_default=True, help='Launch background worker after setup completes')
def setup(data_dir: Optional[str], skip_warmup: bool, start_worker: bool):
    """Interactive first-time setup (data dir + optional warm-up)."""

    click.echo("[TOOLS]  Greeum setup wizard")
    config = load_config()

    default_dir = data_dir or config.data_dir or str(DEFAULT_DATA_DIR)
    if data_dir:
        chosen_dir = str(Path(data_dir).expanduser())
        click.echo(f"Using data directory: {chosen_dir}")
    else:
        chosen_dir = click.prompt(
            "Data directory (used for memories, cache, logs)",
            default=str(Path(default_dir).expanduser()),
        )

    target_dir = ensure_data_dir(chosen_dir)
    os.environ['GREEUM_DATA_DIR'] = str(target_dir)
    try:
        _ensure_database_ready(Path(target_dir))
    except click.ClickException as exc:
        click.echo(f"[ERROR] {exc}")
        sys.exit(1)

    semantic_ready = config.semantic_ready
    warmup_performed = False

    if skip_warmup:
        click.echo("Skipping embedding warm-up (hash fallback will be used by default).")
    else:
        default_confirm = not config.semantic_ready
        if click.confirm("Run SentenceTransformer warm-up now?", default=default_confirm):
            click.echo(f"[PACKAGE] Downloading {DEFAULT_ST_MODEL} ...")
            try:
                cache_dir = _download_sentence_transformer(DEFAULT_ST_MODEL)
            except ImportError as exc:
                click.echo(f"[ERROR] {exc}", err=True)
                semantic_ready = False
            except Exception as exc:  # noqa: BLE001
                click.echo(f"[ERROR] Warm-up failed: {exc}", err=True)
                semantic_ready = False
            else:
                click.echo(f"[OK] Warm-up complete. Model cached at {cache_dir}.")
                semantic_ready = True
                warmup_performed = True
        else:
            click.echo("Warm-up skipped. You can run 'greeum mcp warmup' later.")

    config.data_dir = str(target_dir)
    config.semantic_ready = semantic_ready
    save_config(config)

    if warmup_performed:
        mark_semantic_ready(True)
    elif not semantic_ready:
        mark_semantic_ready(False)

    worker_endpoint = None
    worker_log = None
    if start_worker:
        click.echo("\n[ROCKET] Launching background worker...")
        try:
            endpoint = ensure_http_worker(
                data_dir=Path(target_dir),
                semantic=semantic_ready,
                allow_spawn=True,
            )
            worker_endpoint = endpoint
            os.environ['GREEUM_MCP_HTTP'] = endpoint
            state = get_worker_state(Path(target_dir)) or {}
            worker_log = state.get('log')
        except Exception as exc:  # noqa: BLE001 - show warning only
            click.echo(f"[WARN] Failed to launch worker automatically: {exc}")
        else:
            click.echo(f"   - Worker endpoint: {worker_endpoint}")
            if worker_log:
                click.echo(f"   - Worker log: {worker_log}")
            else:
                click.echo("   - Worker log: <not recorded>")

    click.echo("\nSetup summary:")
    click.echo(f"   - Data directory: {target_dir}")
    click.echo(
        "   - Semantic embeddings: "
        + ("ready" if semantic_ready else "hash fallback (run warmup to enable)")
    )
    if start_worker and worker_endpoint:
        click.echo("   - Worker: running (auto-start)")
    elif start_worker:
        click.echo("   - Worker: failed to start (use 'greeum worker serve' later)")
    else:
        click.echo("   - Worker: skipped (use 'greeum worker serve' when needed)")
    click.echo("   - Next step: run 'greeum memory add ""Your first note""' to test the connection")
@main.group()
def memory():
    """Memory management commands (STM/LTM)"""
    pass

@main.group() 
def mcp():
    """MCP server commands"""
    pass

@main.group()
def worker():
    """Worker daemon utilities"""
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

@main.group()
def dashboard():
    """Memory dashboard and analytics (v2.6.2)"""
    pass

@main.group()
def graph():
    """Graph network management (v3.0.0)"""
    pass

@main.group()
def metrics():
    """Metrics and performance monitoring"""
    pass

@main.group()
def validate():
    """Documentation and code validation"""
    pass

@main.command()
@click.option('--check', is_flag=True, help='진단만 수행')
@click.option('--fix', is_flag=True, help='자동 복구 포함')
@click.option('--force', is_flag=True, help='강제 복구')
@click.option('--no-backup', is_flag=True, help='백업 생략')
@click.option('--db-path', help='데이터베이스 경로')
def doctor(check: bool, fix: bool, force: bool, no_backup: bool, db_path: str):
    """System diagnostics and repair tool (체크, 마이그레이션, 정리, 최적화)"""
    try:
        from .doctor import GreeumDoctor

        doctor_instance = GreeumDoctor(db_path)

        # 백업
        if (fix or force) and not no_backup:
            backup_path = doctor_instance.backup_database()
            click.echo(f"[PACKAGE] 백업 생성: {backup_path}")

        # 진단
        health = doctor_instance.check_health()
        doctor_instance.print_report(health)

        # 복구
        if fix or force or (not check and doctor_instance.issues):
            if not check and not fix and not force:
                response = click.confirm("\n복구를 진행하시겠습니까?", default=False)
                if not response:
                    click.echo("복구가 취소되었습니다.")
                    return

            fixes = doctor_instance.fix_issues(force)
            if fixes:
                click.echo(f"\n[OK] 복구 완료: {len(fixes)}개 문제 해결")
                for fix_msg in fixes:
                    click.echo(f"  - {fix_msg}")

            # 재진단
            click.echo("\n[LOOP] 복구 후 재진단...")
            health = doctor_instance.check_health()
            click.echo(f"\n최종 상태: 점수 {health['total_score']:.0f}/100")

        sys.exit(0 if health['total_score'] >= 70 else 1)

    except Exception as e:
        click.echo(f"[ERROR] 오류 발생: {e}")
        sys.exit(1)


# Memory 서브명령어들
def _maybe_call_http_tool(tool: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    endpoint = os.getenv('GREEUM_MCP_HTTP')
    if not endpoint:
        return None

    import json
    import urllib.request
    import urllib.error
    import uuid

    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/call",
        "params": {
            "name": tool,
            "arguments": arguments,
        },
    }

    timeout = float(os.getenv('GREEUM_HTTP_TIMEOUT', '30'))
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 204:
                return {}
            body = resp.read().decode('utf-8')
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode('utf-8')
        raise RuntimeError(f"HTTP call failed: {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"HTTP call failed: {exc}") from exc

    try:
        message = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid MCP HTTP response: {body}") from exc

    if 'error' in message:
        raise RuntimeError(f"MCP error: {message['error']}")

    return message.get('result')


def _decide_worker(use_worker_flag: bool, no_worker_flag: bool) -> Optional[bool]:
    if no_worker_flag:
        return False
    if use_worker_flag:
        return True
    env = os.getenv("GREEUM_USE_WORKER")
    if env:
        return env.lower() not in {"0", "false", "no", "off"}
    return None


def _try_worker_call(tool: str, arguments: Dict[str, Any], use_worker_flag: bool, no_worker_flag: bool, quiet: bool = False, config: Optional[GreeumConfig] = None) -> Optional[Dict[str, Any]]:
    decision = _decide_worker(use_worker_flag, no_worker_flag)
    endpoint = resolve_endpoint()

    if decision is False:
        return None

    if not endpoint:
        base_dir = os.environ.get("GREEUM_DATA_DIR")
        data_root = base_dir or (config.data_dir if config else str(DEFAULT_DATA_DIR))
        data_dir = Path(data_root).expanduser()
        semantic_ready = bool(config.semantic_ready) if config else False
        try:
            endpoint = ensure_http_worker(
                data_dir=data_dir,
                semantic=semantic_ready,
                allow_spawn=True,
            )
            if endpoint:
                os.environ["GREEUM_MCP_HTTP"] = endpoint
        except Exception as exc:  # noqa: BLE001 - surface fallback warning
            if not quiet:
                click.echo(f"[WARN] Auto worker unavailable ({exc}); using local execution.")
            endpoint = None

    try:
        if not endpoint:
            return None
        client = WriteServiceClient(endpoint)
        payload = client.call(tool, arguments)
        if isinstance(payload, dict):
            text_blocks = [
                block.get("text", "")
                for block in payload.get("content", [])
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            if text_blocks:
                payload["text"] = "\n".join(block.strip() for block in text_blocks if block)
        return payload
    except WorkerUnavailableError as exc:
        if not quiet:
            click.echo(f"[WARN] Worker unavailable ({exc}); falling back to local execution.")
        return None


@memory.command()
@click.argument('content')
@click.option('--importance', '-i', default=0.5, help='Importance score (0.0-1.0)')
@click.option('--tags', '-t', help='Comma-separated tags')
@click.option('--slot', '-s', type=click.Choice(['A', 'B', 'C']), help='Insert near specified anchor slot')
@click.option('--use-worker', is_flag=True, help='Force using the worker endpoint when available')
@click.option('--no-worker', is_flag=True, help='Force local execution without contacting the worker')
def add(content: str, importance: float, tags: Optional[str], slot: Optional[str], use_worker: bool, no_worker: bool):
    """Add new memory to long-term storage"""
    try:
        config = load_config()
        worker_args = {
            "content": content,
            "importance": importance,
        }
        if tags:
            worker_args["metadata"] = {"tags": tags.split(',')}
        if slot:
            worker_args["slot"] = slot
        worker_response = _try_worker_call("add_memory", worker_args, use_worker, no_worker, config=config)
        if worker_response is not None:
            text = worker_response.get("text")
            if text:
                click.echo(text)
                return
            data = worker_response.get("data") or {}
            block_id = data.get("block_index", data.get("id", "unknown"))
            click.echo(f"[OK] Memory added via worker (Block #{block_id})")
            return

        if slot:
            # Use anchor-based write
            from ..api.write import write as anchor_write
            
            result = anchor_write(
                text=content,
                slot=slot,
                policy={'importance': importance, 'tags': tags}
            )
            
            click.echo(f"[OK] Memory added near anchor {slot} (Block #{result})")
            
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
                # block is now just the block_index (int) instead of a dict
                click.echo(f"[OK] Memory added (Block #{block})")
            else:
                click.echo("[ERROR] Failed to add memory")
            
    except Exception as e:
        click.echo(f"[ERROR] Error: {e}")
        sys.exit(1)

@memory.command()
@click.argument('query')
@click.option('--count', '-c', default=5, help='Number of results')
@click.option('--threshold', '-th', default=0.1, help='Similarity threshold')
@click.option('--slot', '-s', type=click.Choice(['A', 'B', 'C']), help='Use anchor-based localized search')
@click.option('--radius', '-r', type=int, help='Graph search radius (1-3)')
@click.option('--no-fallback', is_flag=True, help='Disable fallback to global search')
@click.option('--use-worker', is_flag=True, help='Force using the worker endpoint when available')
@click.option('--no-worker', is_flag=True, help='Force local execution without contacting the worker')
def search(query: str, count: int, threshold: float, slot: str, radius: int, no_fallback: bool, use_worker: bool, no_worker: bool):
    """Search memories by keywords/semantic similarity"""
    try:
        config = load_config()
        worker_args = {
            "query": query,
            "limit": count,
            "threshold": threshold,
            "fallback": not no_fallback,
        }
        if slot:
            worker_args["slot"] = slot
        worker_response = _try_worker_call("search_memory", worker_args, use_worker, no_worker, quiet=True, config=config)
        if worker_response is not None:
            text = worker_response.get("text")
            if text:
                click.echo(text)
                return
            items = worker_response.get('data', {}).get('items', [])
            if items:
                for idx, item in enumerate(items, 1):
                    snippet = (item.get('context') or '')[:80]
                    score = item.get('relevance_score', item.get('score'))
                    click.echo(f"{idx}. {snippet} (score={score})")
            else:
                click.echo("No results found (worker)")
            return

        from ..core.block_manager import BlockManager
        from ..core.database_manager import DatabaseManager

        # Use BlockManager for DFS-based search instead of SearchEngine
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)

        # Perform search with v3 DFS system
        result = block_manager.search_with_slots(
            query=query,
            limit=count,
            use_slots=True,
            entry="cursor",
            depth=3 if slot else 0,
            fallback=not no_fallback
        )

        # Extract blocks from result
        if isinstance(result, dict):
            blocks = result.get('items', [])
            metadata = result.get('meta', {})
        else:
            blocks = result
        metadata = result.get('metadata', {})
        timing = result.get('timing', {})
        
        if blocks:
            # Display search info
            if slot:
                search_type = f"[TARGET] Anchor-based search (slot {slot})"
                if metadata.get('fallback_used'):
                    search_type += " -> [PROCESS] Global fallback"
                click.echo(search_type)
                click.echo(f"   Hit rate: {metadata.get('local_hit_rate', 0):.1%}")
                click.echo(f"   Avg hops: {metadata.get('avg_hops', 0)}")
            else:
                click.echo("[SEARCH] Global semantic search")
            
            # Display timing
            total_ms = sum(timing.values())
            click.echo(f"   Search time: {total_ms:.1f}ms")
            
            click.echo(f"\n[CLIPBOARD] Found {len(blocks)} memories:")
            for i, block in enumerate(blocks, 1):
                timestamp = block.get('timestamp', 'Unknown')
                content = block.get('context', 'No content')[:80]
                relevance = block.get('relevance_score', 0)
                final_score = block.get('final_score', relevance)
                
                click.echo(f"{i}. [{timestamp}] {content}...")
                click.echo(f"   Score: {final_score:.3f}")
        else:
            if slot and not no_fallback:
                click.echo(f"[ERROR] No memories found in anchor slot {slot}, and fallback disabled")
            else:
                click.echo("[ERROR] No memories found")

    except Exception as e:
        click.echo(f"[ERROR] Search failed: {e}")
        sys.exit(1)


@memory.command('reindex')
@click.option(
    '--data-dir',
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
    help='Target data directory (defaults to configured data store)',
)
@click.option('--disable-faiss', is_flag=True, help='Skip FAISS vector index rebuild')
def memory_reindex(data_dir: Optional[str], disable_faiss: bool) -> None:
    """Rebuild branch-aware indices for the selected database."""
    from ..core.branch_index import BranchIndexManager

    if disable_faiss:
        os.environ['GREEUM_DISABLE_FAISS'] = 'true'

    if data_dir:
        target_dir = Path(data_dir).expanduser()
        db_path = target_dir if target_dir.suffix == '.db' else target_dir / 'memory.db'
        manager = DatabaseManager(connection_string=str(db_path))
    else:
        manager = DatabaseManager()

    click.echo('[LOOP] Rebuilding branch indices...')
    try:
        branch_manager = BranchIndexManager(manager)
        stats = branch_manager.get_stats()
        click.echo(
            "[OK] Rebuilt {count} branches ({mode}, vectorized={vectorized}).".format(
                count=stats['branch_count'],
                mode=stats['mode'],
                vectorized=stats['vectorized_branches'],
            )
        )
    except Exception as exc:  # noqa: BLE001 - surface to CLI
        click.echo(f"[ERROR] Branch reindex failed: {exc}")
        sys.exit(1)
    finally:
        try:
            manager.conn.close()
        except Exception:
            pass
        except Exception:
            pass

# MCP 서브명령어들
@mcp.command()
@click.option('--transport', '-t', default='stdio', help='Transport type (stdio/http/ws)')
@click.option('--port', '-p', default=3000, help='Port for HTTP or WebSocket transports')
@click.option('--host', default='127.0.0.1', show_default=True, help='Host for HTTP transport')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging (INFO level)')
@click.option('--debug', '-d', is_flag=True, help='Enable debug logging (DEBUG level)')
@click.option('--quiet', '-q', is_flag=True, help='[DEPRECATED] Use default behavior instead')
@click.option('--semantic/--no-semantic', default=False, show_default=True,
              help='Enable semantic embeddings (requires cached SentenceTransformer)')
def serve(transport: str, port: int, host: str, verbose: bool, debug: bool, quiet: bool, semantic: bool):
    """Start MCP server for Claude Code integration"""  
    config = load_config()
    # 로깅 레벨 결정 (새로운 정책: 기본은 조용함)
    if debug:
        log_level = 'debug'
        click.echo(f"[DEBUG] Starting Greeum MCP server ({transport})...")
    elif verbose:
        log_level = 'verbose'
        click.echo(f"[NOTE] Starting Greeum MCP server ({transport}) - VERBOSE mode...")
    else:
        log_level = 'quiet'
        # 기본은 조용함 (출력 없음)
    
    # --quiet 플래그 호환성 경고
    if quiet:
        if verbose or debug:
            click.echo("Warning: --quiet is deprecated and conflicts with --verbose/--debug")
        else:
            click.echo("Warning: --quiet is deprecated. Default behavior is now quiet.")
    
    if transport == 'stdio':
        ensure_data_dir(config.data_dir)
        os.environ.setdefault('GREEUM_DATA_DIR', config.data_dir)
        if semantic:
            # Allow explicit opt-in by clearing the fallback flag
            if os.getenv('GREEUM_DISABLE_ST'):
                os.environ.pop('GREEUM_DISABLE_ST')
            if verbose or debug and not config.semantic_ready:
                click.echo('[WARN] Semantic mode requested but warm-up is not recorded; first startup may take longer.')
            try:
                init_sentence_transformer(set_as_default=True)
            except RuntimeError as err:
                if verbose or debug:
                    click.echo(f'[WARN] {err}')
            except ImportError as err:
                if verbose or debug:
                    click.echo(f'[WARN] {err}')
                force_simple_fallback(set_as_default=True)
        else:
            os.environ.setdefault('GREEUM_DISABLE_ST', '1')
            if verbose or debug:
                if config.semantic_ready:
                    click.echo('[NOTE] Semantic embeddings available. Use --semantic to enable them for this session.')
                else:
                    click.echo('[NOTE] SentenceTransformer disabled (hash fallback). Use --semantic after warm-up to re-enable.')
            force_simple_fallback(set_as_default=True)
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
    elif transport == 'http':
        try:
            from ..mcp.native.http_server import run_http_server
            run_http_server(host=host, port=port, log_level=log_level)
        except RuntimeError as e:
            if verbose or debug:
                click.echo(str(e))
            sys.exit(1)
        except KeyboardInterrupt:
            if verbose or debug:
                click.echo("\nMCP HTTP server stopped")
        except Exception as e:
            if verbose or debug:
                click.echo(f"MCP HTTP server error: {e}")
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
            click.echo(f"[ERROR] Transport '{transport}' not supported")
        sys.exit(1)


@worker.command('serve')
@click.option('--host', default='127.0.0.1', show_default=True)
@click.option('--port', default=8800, show_default=True, type=int)
@click.option('--semantic', is_flag=True, help='Enable semantic embeddings for the worker')
@click.option('--stdio', is_flag=True, help='Use STDIO transport instead of HTTP')
def worker_serve(host: str, port: int, semantic: bool, stdio: bool) -> None:
    """Start the long-running worker daemon."""
    transport = 'stdio' if stdio else 'http'
    cmd = [
        sys.executable,
        '-m',
        'greeum.cli',
        'mcp',
        'serve',
        '-t',
        transport,
    ]
    if not stdio:
        cmd += ['--host', host, '--port', str(port)]
    if semantic:
        cmd.append('--semantic')
    click.echo(f"Starting worker daemon ({'STDIO' if stdio else 'HTTP'})...")
    click.echo('Command: ' + ' '.join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        click.echo(f"Worker exited with status {exc.returncode}")

@mcp.command('warmup')
@click.option('--model', default='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
              show_default=True, help='SentenceTransformer model to pre-download')
def warmup_embeddings(model: str):
    """Download the semantic embedding model so --semantic starts instantly."""

    click.echo(f"[PACKAGE] Downloading {model} ...")

    try:
        cache_dir = _download_sentence_transformer(model)
    except ImportError as exc:
        click.echo(f"[ERROR] {exc}", err=True)
        mark_semantic_ready(False)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001 - surface full error to user
        click.echo(f"[ERROR] Warm-up failed: {exc}", err=True)
        mark_semantic_ready(False)
        sys.exit(1)

    mark_semantic_ready(True)
    click.echo(f"[OK] Warm-up complete. Model cached at {cache_dir}.")
    click.echo("   Use 'greeum mcp serve --semantic' to enable semantic embeddings.")


# API 서브명령어들  
@api.command()
@click.option('--port', '-p', default=5000, help='Server port')
@click.option('--host', '-h', default='localhost', help='Server host')
def serve(port: int, host: str):
    """Start REST API server"""
    click.echo(f"[GLOBE] Starting Greeum API server on {host}:{port}...")
    
    try:
        from ..api.memory_api import app
        import uvicorn
        uvicorn.run(app, host=host, port=port)
    except ImportError:
        click.echo("[ERROR] API server dependencies not installed. Try: pip install greeum[api]")
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n[HELLO] API server stopped")

# LTM 서브명령어들
@ltm.command()
@click.option('--trends', is_flag=True, help='(Reserved for compatibility)')
@click.option('--period', '-p', default='7d', help='(Reserved for compatibility)')
@click.option('--output', '-o', default='text', help='Output format (text/json)')
def analyze(trends: bool, period: str, output: str):
    """Summarize branch-based long-term memory activity."""

    from ..core import BlockManager, DatabaseManager

    click.echo("== STM Slot Overview ==")

    try:
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
    except Exception as exc:
        click.echo(f"[ERROR] Failed to initialize database: {exc}")
        sys.exit(1)

    cursor = db_manager.conn.cursor()

    # Discover available block columns once for conditional queries.
    cursor.execute("PRAGMA table_info(blocks)")
    block_columns = {row[1] for row in cursor.fetchall()}
    has_branch_created = 'branch_created_at' in block_columns

    anchor_store = get_anchor_store()
    slots = anchor_store.get_slots()

    branch_slot_map: Dict[str, List[str]] = defaultdict(list)
    slot_rows: List[str] = []

    def _shorten(text: Optional[str], limit: int = 80) -> str:
        if not text:
            return ''
        text = text.strip().replace('\n', ' ')
        return text if len(text) <= limit else text[: limit - 3] + '...'

    slot_order = ["A", "B", "C"]
    for slot_name in slot_order:
        slot_info = slots.get(slot_name)
        if not slot_info or not slot_info.anchor_block:
            slot_rows.append(f"[{slot_name}] empty")
            continue

        block_data = block_manager._get_block_by_hash(slot_info.anchor_block)
        if not block_data:
            slot_rows.append(f"[{slot_name}] head missing (hash {slot_info.anchor_block[:8]})")
            continue

        branch_root = block_data.get('root') or '(unassigned)'
        branch_slot_map[branch_root].append(slot_name)

        timestamp = block_data.get('timestamp') or 'unknown'
        context_preview = _shorten(block_data.get('context'))
        block_index = block_data.get('block_index', 'n/a')
        slot_rows.append(
            f"[{slot_name}] root={branch_root[:8]} block={block_index} time={timestamp}"
        )
        if context_preview:
            slot_rows.append(f"    {context_preview}")

    for line in slot_rows:
        click.echo(line)

    # ------------------------------------------------------------------
    # Branch statistics
    # ------------------------------------------------------------------
    click.echo("\n== Branch Structure ==")

    try:
        cursor.execute(
            """
            SELECT root,
                   MIN(timestamp) AS first_ts,
                   MAX(timestamp) AS last_ts,
                   COUNT(*) AS node_count
            FROM blocks
            WHERE root IS NOT NULL AND root <> ''
            GROUP BY root
            ORDER BY last_ts DESC
            """
        )
    except sqlite3.OperationalError as exc:
        click.echo(f"[ERROR] Branch columns unavailable: {exc}")
        sys.exit(1)

    branch_stats: Dict[str, Dict[str, Any]] = {}
    branches = cursor.fetchall()

    # Pre-compute keyword label, parent branch, and representative snippets.
    keyword_stmt = (
        "SELECT bk.keyword, COUNT(*) AS cnt "
        "FROM block_keywords bk JOIN blocks b ON bk.block_index = b.block_index "
        "WHERE b.root = ? GROUP BY bk.keyword ORDER BY cnt DESC LIMIT 3"
    )

    first_block_stmt = (
        "SELECT block_index, context, timestamp, before, hash "
        "FROM blocks WHERE root = ? "
        + ("ORDER BY branch_created_at ASC, block_index ASC " if has_branch_created else "ORDER BY timestamp ASC, block_index ASC ")
        + "LIMIT 1"
    )

    recent_block_stmt = (
        "SELECT context FROM blocks WHERE root = ? ORDER BY timestamp DESC, block_index DESC LIMIT 1"
    )

    for root, first_ts, last_ts, node_count in branches:
        stats: Dict[str, Any] = {
            'root': root,
            'count': node_count,
            'first_ts': first_ts,
            'last_ts': last_ts,
            'slots': branch_slot_map.get(root, []),
        }

        # Keywords
        cursor.execute(keyword_stmt, (root,))
        keywords = [row[0] for row in cursor.fetchall()]
        stats['keywords'] = keywords

        # First block / parent branch inference
        cursor.execute(first_block_stmt, (root,))
        first_row = cursor.fetchone()
        parent_root = None
        first_context = ''
        if first_row:
            _, first_context, _, before_hash, first_hash = first_row
            if before_hash:
                parent_block = block_manager._get_block_by_hash(before_hash)
                if parent_block and parent_block.get('root') and parent_block.get('root') != root:
                    parent_root = parent_block.get('root')
        stats['parent_root'] = parent_root
        stats['first_context'] = first_context

        cursor.execute(recent_block_stmt, (root,))
        latest_row = cursor.fetchone()
        stats['recent_context'] = latest_row[0] if latest_row else ''

        # Derive human-readable label
        if keywords:
            stats['label'] = '/'.join(keywords)
        elif first_context:
            stats['label'] = _shorten(first_context, limit=40)
        else:
            stats['label'] = root[:12]

        branch_stats[root] = stats

    if not branch_stats:
        click.echo("No branch data available yet.")
    else:
        # Build parent->children mapping
        children: Dict[Optional[str], List[str]] = defaultdict(list)
        for root, stats in branch_stats.items():
            children[stats.get('parent_root')].append(root)

        def parse_ts(ts: Optional[str]) -> datetime:
            if not ts:
                return datetime.min
            try:
                return datetime.fromisoformat(ts)
            except ValueError:
                try:
                    return datetime.strptime(ts.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                except Exception:
                    return datetime.min

        def fmt_date(ts: Optional[str]) -> str:
            if not ts:
                return 'unknown'
            dt = parse_ts(ts)
            if dt == datetime.min:
                return 'unknown'
            return dt.strftime('%Y-%m-%d')

        def slot_tag(slots: List[str]) -> str:
            return '[' + ','.join(sorted(slots)) + ']' if slots else '[-]'

        printed: set[str] = set()

        def branch_line(root_id: str, depth: int = 0) -> None:
            stats = branch_stats[root_id]
            indent = '  ' * depth
            tag = slot_tag(stats['slots'])
            span = f"{fmt_date(stats['first_ts'])} -> {fmt_date(stats['last_ts'])}"
            parent_root = stats.get('parent_root')
            parent_label = branch_stats[parent_root]['label'] if parent_root in branch_stats else '-'
            click.echo(f"{indent}{tag} {stats['label']} (nodes={stats['count']}, span={span})")
            click.echo(f"{indent}  root={root_id[:12]} parent={parent_label}")
            recent_preview = _shorten(stats['recent_context'])
            if recent_preview:
                click.echo(f"{indent}  latest: {recent_preview}")
            printed.add(root_id)
            for child_root in sorted(children.get(root_id, []), key=lambda r: parse_ts(branch_stats[r]['last_ts']), reverse=True):
                branch_line(child_root, depth + 1)

        top_level = sorted(children.get(None, []), key=lambda r: parse_ts(branch_stats[r]['last_ts']), reverse=True)
        for root in top_level:
            branch_line(root, 0)

        # Output any orphan branches that reference missing parents
        for root_id in sorted(branch_stats.keys(), key=lambda r: parse_ts(branch_stats[r]['last_ts']), reverse=True):
            if root_id not in printed:
                click.echo("-- detached branch --")
                branch_line(root_id, 0)

    # ------------------------------------------------------------------
    # Recent usage statistics
    # ------------------------------------------------------------------
    click.echo("\n== Activity (Last 7 Days) ==")

    today = datetime.utcnow().date()
    days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    cutoff = (today - timedelta(days=6)).strftime('%Y-%m-%d')

    cursor.execute(
        """
        SELECT substr(timestamp, 1, 10) AS day, COUNT(*)
        FROM blocks
        WHERE timestamp >= ?
        GROUP BY day
        """,
        (cutoff,),
    )
    rows = cursor.fetchall()
    day_counts = {row[0]: row[1] for row in rows}

    total = 0
    for day in days:
        key = day.strftime('%Y-%m-%d')
        count = day_counts.get(key, 0)
        total += count
        bar = '#' * min(40, count) if count else ''
        click.echo(f"{key} | {count:3d} {bar}")

    avg = total / 7 if days else 0
    click.echo(f"Average per day: {avg:.2f}")
    click.echo(f"Total nodes added (7d): {total}")

    if output == 'json':
        summary = {
            'slots': slot_rows,
            'branches': branch_stats,
            'recent_activity': {day.strftime('%Y-%m-%d'): day_counts.get(day.strftime('%Y-%m-%d'), 0) for day in days},
            'average_per_day': avg,
            'total_7d': total,
        }
        import json

        click.echo(json.dumps(summary, indent=2, ensure_ascii=True))

@ltm.command()
@click.option('--repair', is_flag=True, help='Attempt to repair integrity issues')
def verify(repair: bool):
    """Verify blockchain-like LTM integrity"""
    click.echo("[SEARCH] Verifying LTM blockchain integrity...")
    
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
        click.echo(f"[OK] Verified {verified_count}/{total_blocks} blocks")
        
        if issues:
            click.echo(f"[WARNING]  Found {len(issues)} integrity issues:")
            for issue in issues[:10]:  # 최대 10개만 표시
                click.echo(f"  - {issue}")
            
            if repair:
                click.echo("[HAMMER] Repair functionality not implemented yet")
        else:
            click.echo("[SUCCESS] All blocks verified successfully!")
                    
    except Exception as e:
        click.echo(f"[ERROR] Verification failed: {e}")
        sys.exit(1)

@ltm.command()
@click.option('--format', '-f', default='json', help='Export format (json/blockchain/csv)')
@click.option('--output', '-o', help='Output file path')
@click.option('--limit', '-l', type=int, help='Limit number of blocks')
def export(format: str, output: str, limit: int):
    """Export LTM data in various formats"""
    click.echo(f"[OUTBOX] Exporting LTM data (format: {format})...")
    
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
        
        click.echo(f"[OK] Exported {len(all_blocks)} blocks to: {output_path}")
        click.echo(f"[PAGE] File size: {output_path.stat().st_size} bytes")
                    
    except Exception as e:
        click.echo(f"[ERROR] Export failed: {e}")
        sys.exit(1)

# STM 서브명령어들
@stm.command()
@click.argument('content')
@click.option('--ttl', default='1h', help='Time to live (e.g., 1h, 30m, 2d)')
@click.option('--importance', '-i', default=0.3, help='Importance score (0.0-1.0)')
def add(content: str, ttl: str, importance: float):
    """Add content to short-term memory with TTL"""
    click.echo(f"[MEMORY] Adding to STM (TTL: {ttl})...")
    
    try:
        from ..core import STMManager, DatabaseManager
        import re
        from datetime import datetime, timedelta
        
        # TTL 파싱
        ttl_pattern = r'(\d+)([hmdw])'
        match = re.match(ttl_pattern, ttl.lower())
        if not match:
            click.echo("[ERROR] Invalid TTL format. Use: 1h, 30m, 2d, 1w")
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
            click.echo(f"[OK] Added to STM (expires: {expiry_time.strftime('%Y-%m-%d %H:%M:%S')})")
        else:
            click.echo("[ERROR] Failed to add to STM")
            sys.exit(1)
                    
    except Exception as e:
        click.echo(f"[ERROR] STM add failed: {e}")
        sys.exit(1)

@stm.command()
@click.option('--threshold', '-t', default=0.8, help='Importance threshold for promotion')
@click.option('--dry-run', is_flag=True, help='Show what would be promoted without doing it')
def promote(threshold: float, dry_run: bool):
    """Promote important STM entries to LTM"""
    click.echo(f"[TOP] Promoting STM -> LTM (threshold: {threshold})...")
    
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
            click.echo(f"[MAILBOX] No STM entries above threshold {threshold}")
            return
        
        click.echo(f"[TARGET] Found {len(candidates)} candidates for promotion:")
        
        promoted_count = 0
        for entry in candidates:
            content = entry.get('content', '')
            importance = entry.get('importance', 0)
            
            click.echo(f"  - {content[:50]}... (importance: {importance:.2f})")
            
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
            click.echo(f"[SEARCH] Dry run: {len(candidates)} entries would be promoted")
        else:
            click.echo(f"[OK] Promoted {promoted_count}/{len(candidates)} entries to LTM")
                    
    except Exception as e:
        click.echo(f"[ERROR] Promotion failed: {e}")
        sys.exit(1)

@stm.command()
@click.option('--smart', is_flag=True, help='Use intelligent cleanup based on importance')
@click.option('--expired', is_flag=True, help='Remove only expired entries')
@click.option('--threshold', '-t', default=0.2, help='Remove entries below this importance')
def cleanup(smart: bool, expired: bool, threshold: float):
    """Clean up short-term memory entries"""
    click.echo("[BROOM] Cleaning up STM...")
    
    try:
        from ..core import STMManager, DatabaseManager
        from datetime import datetime
        
        db_manager = DatabaseManager()
        stm_manager = STMManager(db_manager)
        stm_entries = stm_manager.get_recent_memories(count=1000)
        
        if not stm_entries:
            click.echo("[MAILBOX] STM is already empty")
            return
        
        removed_count = 0
        total_count = len(stm_entries)
        
        click.echo(f"[CHART] Total STM entries: {total_count}")
        
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
                    click.echo(f"  [TRASH]  Removed: {content}... ({reason})")
                    removed_count += 1
        
        click.echo(f"[OK] Cleanup complete: {removed_count}/{total_count} entries removed")
        click.echo(f"[CHART] Remaining STM entries: {total_count - removed_count}")
                    
    except Exception as e:
        click.echo(f"[ERROR] Cleanup failed: {e}")
        sys.exit(1)

# AI Context Slots 서브명령어들 (v3.0.0.post5)
@slots.command()
def status():
    """Display current AI Context Slots status (v3.0.0.post5)"""
    click.echo("[MEMORY] AI Context Slots Status Report (v3.0.0.post5)")
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
                type_icon = {"context": "[TARGET]", "anchor": "[ANCHOR]", "buffer": "[CLIPBOARD]"}.get(slot_type, "[BLUE_DIAMOND]")
                
                click.echo(f"\n{type_icon} {slot_name.upper()} Slot ({slot_type})")
                click.echo(f"   Content: {content}")
                click.echo(f"   Importance: {importance:.2f}")
                click.echo(f"   Created: {timestamp}")
                
                if is_anchor and slot_info.get('anchor_block'):
                    click.echo(f"   [LINK] LTM Anchor: Block #{slot_info['anchor_block']}")
                    
            else:
                click.echo(f"\n[CIRCLE] {slot_name.upper()} Slot: Empty")
        
        click.echo("\n" + "=" * 50)
        click.echo("[IDEA] Use 'greeum slots set <content>' to add to slots")
        click.echo("[IDEA] Use 'greeum slots clear <slot_name>' to clear specific slot")
                    
    except Exception as e:
        click.echo(f"[ERROR] Error reading slots status: {e}")
        sys.exit(1)

@slots.command(name='set')
@click.argument('content')
@click.option('--importance', '-i', default=0.5, help='Importance score (0.0-1.0)')
@click.option('--ltm-anchor', type=int, help='LTM block ID for anchoring')
@click.option('--radius', default=5, help='Search radius for LTM anchor')
def set_slot(content: str, importance: float, ltm_anchor: int, radius: int):
    """Add content to AI Context Slots with smart allocation"""
    click.echo(f"[MEMORY] Adding content to AI Context Slots...")
    
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
        click.echo(f"[OK] Content added to {used_slot.upper()} slot")
        click.echo(f"[NOTE] Content: {content[:80]}{'...' if len(content) > 80 else ''}")
        click.echo(f"[TARGET] AI chose {used_slot} slot based on content analysis")
        
        if ltm_anchor:
            click.echo(f"[LINK] LTM Anchor: Block #{ltm_anchor} (radius: {radius})")
        
    except Exception as e:
        click.echo(f"[ERROR] Failed to add to slots: {e}")
        sys.exit(1)

@slots.command()
@click.argument('slot_name', type=click.Choice(['active', 'anchor', 'buffer', 'all']))
def clear(slot_name: str):
    """Clear specific slot or all slots"""
    click.echo(f"[TRASH]  Clearing {slot_name} slot(s)...")
    
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
            
            click.echo(f"[OK] Cleared {cleared_count} slots")
            
        else:
            # 특정 슬롯 비우기
            if slots_instance.clear_slot(slot_name):
                click.echo(f"[OK] Cleared {slot_name.upper()} slot")
            else:
                click.echo(f"[WARNING]  {slot_name.upper()} slot was already empty")
        
    except Exception as e:
        click.echo(f"[ERROR] Failed to clear slot: {e}")
        sys.exit(1)

@slots.command()
@click.argument('query')
@click.option('--limit', '-l', default=5, help='Maximum number of results')
def search(query: str, limit: int):
    """Search using AI Context Slots integration"""
    click.echo(f"[SEARCH] Searching with AI Context Slots: '{query}'")
    
    try:
        from greeum.core import DatabaseManager
        from greeum.core.block_manager import BlockManager
        
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
        
        # 슬롯 통합 검색 실행
        results = block_manager.search_with_slots(
            query=query, 
            limit=limit, 
            use_slots=True
        )
        
        if results:
            click.echo(f"[CLIPBOARD] Found {len(results)} results:")
            
            for i, result in enumerate(results, 1):
                source = result.get('source', 'unknown')
                content = result.get('context', 'No content')[:80]
                importance = result.get('importance', 0)
                
                if source == 'working_memory':
                    slot_type = result.get('slot_type', 'unknown')
                    type_icon = {"context": "[TARGET]", "anchor": "[ANCHOR]", "buffer": "[CLIPBOARD]"}.get(slot_type, "[BLUE_DIAMOND]")
                    click.echo(f"{i}. {type_icon} [{slot_type.upper()} SLOT] {content}...")
                else:
                    block_index = result.get('block_index', '?')
                    click.echo(f"{i}. [BOOKS] [LTM #{block_index}] {content}...")
                
                click.echo(f"   Importance: {importance:.2f}")
        else:
            click.echo("[ERROR] No results found")
        
    except Exception as e:
        click.echo(f"[ERROR] Search failed: {e}")
        sys.exit(1)

# Migration 서브명령어들 (v2.5.3 AI-Powered Migration)
@migrate.command()
@click.option('--data-dir', default='data', help='Data directory path')
@click.option('--force', is_flag=True, help='Force migration even if already v2.5.3')
def check(data_dir: str, force: bool):
    """Check database schema version and trigger migration if needed"""
    click.echo("[SEARCH] Checking Greeum database schema version...")
    
    try:
        from pathlib import Path

        db_path = Path(data_dir).expanduser() / "memory.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)

        manager = DatabaseManager(str(db_path))
        cursor = manager.conn.cursor()

        needs_migration = BranchSchemaSQL.check_migration_needed(cursor)

        if force or needs_migration:
            manager._apply_branch_migration(cursor)
            manager._initialize_branch_structures(cursor)
            manager.conn.commit()
            click.echo("\n[OK] Branch schema migration applied.")
        else:
            click.echo("\n[OK] Branch schema already up to date.")

        manager.conn.close()
        sys.exit(0)

    except Exception as e:
        click.echo(f"[ERROR] Migration check failed: {e}")
        sys.exit(1)

@migrate.command()
@click.option('--data-dir', default='data', help='Data directory path')
def status(data_dir: str):
    """Check current migration status and schema version"""
    click.echo("[CHART] Greeum Database Migration Status")
    click.echo("=" * 40)
    
    try:
        from pathlib import Path

        db_path = Path(data_dir).expanduser() / "memory.db"

        if not db_path.exists():
            click.echo("[OPEN_FOLDER] Database Status: Not found")
            click.echo("   This appears to be a new installation")
            return

        manager = DatabaseManager(str(db_path))
        cursor = manager.conn.cursor()

        cursor.execute("PRAGMA table_info(blocks)")
        columns = {row[1] for row in cursor.fetchall()}
        branch_columns = {
            'root', 'before', 'after', 'xref',
            'slot', 'branch_similarity', 'branch_created_at'
        }

        branch_ready = branch_columns.issubset(columns)
        anchor_store = get_anchor_store()
        slot_rows = [
            (slot_name, slot_data.anchor_block)
            for slot_name, slot_data in anchor_store.get_slots().items()
        ]

        click.echo(f"[OPEN_FOLDER] Database Size: {db_path.stat().st_size} bytes")
        click.echo(f"[CLIPBOARD] Branch Columns Present: {'yes' if branch_ready else 'no'}")

        if slot_rows:
            click.echo("\n[TARGET] STM Slots:")
            for slot_name, block_hash in slot_rows:
                head = block_hash[:8] + '...' if block_hash else 'None'
                click.echo(f"   - {slot_name}: head={head}")
        else:
            click.echo("\n[WARNING]  STM anchor entries not initialized yet.")

        pending = BranchSchemaSQL.check_migration_needed(cursor)
        click.echo("\n[OK] Migration Status: {}".format("Ready" if not pending else "Additional migration required"))

        manager.conn.close()

    except Exception as e:
        click.echo(f"[ERROR] Status check failed: {e}")
        sys.exit(1)

@migrate.command()
@click.option('--data-dir', default='data', help='Data directory path')
@click.option('--yes', '-y', is_flag=True, help='Run without interactive prompts')
def doctor(data_dir: str, yes: bool):
    """Repair legacy or malformed databases."""

    data_path = Path(data_dir).expanduser()
    if data_path.is_file():
        db_path = data_path
        data_path = db_path.parent
    else:
        db_path = data_path / 'memory.db'

    if not db_path.exists():
        click.echo(f"[OPEN_FOLDER] No database found at {db_path}. Nothing to repair.")
        return

    try:
        _ensure_database_ready(data_path, auto_accept=yes)
        click.echo("[OK] Schema check completed. Database is ready.")
    except click.ClickException as exc:
        click.echo(f"[ERROR] Repair aborted: {exc}")


@migrate.command()
@click.option('--data-dir', default='data', help='Data directory path')
def validate(data_dir: str):
    """Run PRAGMA integrity_check on the active database."""

    data_path = Path(data_dir).expanduser()
    if data_path.is_file():
        db_path = data_path
    else:
        db_path = data_path / 'memory.db'

    if not db_path.exists():
        click.echo(f"[OPEN_FOLDER] Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(str(db_path))
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        conn.close()
    except sqlite3.DatabaseError as exc:
        click.echo(f"[ERROR] Integrity check failed to run: {exc}")
        return

    if result.lower() == 'ok':
        click.echo("[OK] Integrity check OK")
    else:
        click.echo(f"[ERROR] Integrity issues detected: {result}")


@migrate.command()
@click.option('--data-dir', default='data', help='Data directory path')
@click.option('--keep-backups', default=5, help='Number of backups to keep')
def cleanup(data_dir: str, keep_backups: int):
    """Remove old backup files, keeping the most recent N entries."""

    data_path = Path(data_dir).expanduser()
    backup_dir = data_path / 'backups'
    if not backup_dir.exists():
        click.echo("[OPEN_FOLDER] No backups directory found.")
        return

    backup_files = sorted(
        [p for p in backup_dir.iterdir() if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if len(backup_files) <= keep_backups:
        click.echo(f"[OK] {len(backup_files)} backups found. Nothing to remove.")
        return

    to_remove = backup_files[keep_backups:]
    for path in to_remove:
        path.unlink(missing_ok=True)

    click.echo(f"[BROOM] Removed {len(to_remove)} old backups. Kept {keep_backups} recent copies.")

# v2.6.1 Backup 서브명령어들
@backup.command()
@click.option('--output', '-o', required=True, help='백업 파일 저장 경로')
@click.option('--include-metadata/--no-metadata', default=True, help='시스템 메타데이터 포함 여부')
def export(output: str, include_metadata: bool):
    """전체 메모리를 백업 파일로 내보내기"""
    try:
        from ..core.backup_restore import MemoryBackupEngine
        # from ..core.hierarchical_memory import HierarchicalMemorySystem  # REMOVED: File deleted
        from ..core.database_manager import DatabaseManager
        from pathlib import Path
        
        click.echo("[PROCESS] 메모리 백업을 시작합니다...")
        
        # 계층적 메모리 시스템 초기화 - SIMPLIFIED
        db_manager = DatabaseManager()
        # HierarchicalMemorySystem removed - using DatabaseManager directly
        
        backup_engine = MemoryBackupEngine(db_manager)
        success = backup_engine.create_backup(output, include_metadata)
        
        if success:
            click.echo(f"[OK] 백업 완료: {output}")
            backup_path = Path(output)
            if backup_path.exists():
                size_mb = backup_path.stat().st_size / (1024 * 1024)
                click.echo(f"[FOLDER] 파일 크기: {size_mb:.2f} MB")
        else:
            click.echo("[ERROR] 백업 생성에 실패했습니다")
            
    except Exception as e:
        click.echo(f"[BURST] 백업 중 오류: {e}")


@backup.command()
@click.option('--schedule', type=click.Choice(['hourly', 'daily', 'weekly', 'monthly']), 
              required=True, help='백업 주기 설정')
@click.option('--output-dir', '-d', help='백업 저장 디렉토리 (기본: ~/greeum-backups)')
@click.option('--max-backups', type=int, default=10, help='보존할 최대 백업 수 (기본: 10개)')
@click.option('--enable/--disable', default=True, help='자동 백업 활성화/비활성화')
def auto(schedule: str, output_dir: str, max_backups: int, enable: bool):
    """자동 백업 스케줄 설정 및 관리
    
    Examples:
        greeum backup auto --schedule daily --output-dir ~/backups
        greeum backup auto --schedule weekly --max-backups 5
        greeum backup auto --schedule daily --disable
    """
    try:
        from pathlib import Path
        import json
        import os
        
        if not output_dir:
            output_dir = str(Path.home() / "greeum-backups")
        
        # 백업 디렉토리 생성
        backup_path = Path(output_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # 자동 백업 설정 파일 경로
        config_file = backup_path / "auto_backup_config.json"
        
        if enable:
            # 자동 백업 활성화
            from datetime import datetime
            
            config = {
                "enabled": True,
                "schedule": schedule,
                "output_dir": str(backup_path),
                "max_backups": max_backups,
                "last_backup": None,
                "created_at": datetime.now().isoformat()
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            click.echo(f"[OK] 자동 백업 활성화됨")
            click.echo(f"   [DATE] 주기: {schedule}")
            click.echo(f"   [FOLDER] 디렉토리: {output_dir}")
            click.echo(f"   [123] 최대 백업 수: {max_backups}개")
            click.echo()
            click.echo("[IDEA] 자동 백업 실행 방법:")
            
            if schedule == 'hourly':
                cron_expr = "0 * * * *"
            elif schedule == 'daily':
                cron_expr = "0 2 * * *"  # 새벽 2시
            elif schedule == 'weekly':
                cron_expr = "0 2 * * 0"  # 일요일 새벽 2시
            else:  # monthly
                cron_expr = "0 2 1 * *"  # 매월 1일 새벽 2시
            
            click.echo(f"   crontab에 추가: {cron_expr} greeum backup run-auto")
            click.echo("   또는 시스템 스케줄러를 사용하여 'greeum backup run-auto' 실행")
            
        else:
            # 자동 백업 비활성화
            if config_file.exists():
                config_file.unlink()
                click.echo("[OK] 자동 백업이 비활성화되었습니다")
            else:
                click.echo("[INFO]  자동 백업이 이미 비활성화 상태입니다")
                
    except Exception as e:
        click.echo(f"[BURST] 자동 백업 설정 실패: {e}")


@backup.command()
def run_auto():
    """자동 백업 실행 (스케줄러에서 호출)
    
    이 명령어는 cron이나 시스템 스케줄러에서 호출됩니다.
    """
    try:
        from pathlib import Path
        from datetime import datetime, timedelta
        import json
        import glob
        
        # 기본 백업 디렉토리
        backup_dir = Path.home() / "greeum-backups"
        config_file = backup_dir / "auto_backup_config.json"
        
        if not config_file.exists():
            click.echo("[WARNING]  자동 백업이 설정되지 않았습니다. 'greeum backup auto' 명령어를 먼저 실행하세요")
            return
        
        # 설정 로드
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if not config.get('enabled', False):
            click.echo("[INFO]  자동 백업이 비활성화되어 있습니다")
            return
        
        schedule = config['schedule']
        max_backups = config.get('max_backups', 10)
        last_backup = config.get('last_backup')
        
        # 마지막 백업 이후 충분한 시간이 지났는지 확인
        now = datetime.now()
        should_backup = True
        
        if last_backup:
            last_backup_time = datetime.fromisoformat(last_backup)
            
            if schedule == 'hourly' and now - last_backup_time < timedelta(hours=1):
                should_backup = False
            elif schedule == 'daily' and now - last_backup_time < timedelta(days=1):
                should_backup = False
            elif schedule == 'weekly' and now - last_backup_time < timedelta(weeks=1):
                should_backup = False
            elif schedule == 'monthly' and now - last_backup_time < timedelta(days=30):
                should_backup = False
        
        if not should_backup:
            click.echo("[INFO]  아직 백업 시간이 아닙니다")
            return
        
        # 백업 실행
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"auto_backup_{timestamp}.json"
        backup_path = backup_dir / backup_filename
        
        click.echo(f"[PROCESS] 자동 백업 실행: {backup_filename}")
        
        # 백업 엔진 초기화 및 백업 실행
        from ..core.backup_restore import MemoryBackupEngine
        # from ..core.hierarchical_memory import HierarchicalMemorySystem  # REMOVED: File deleted
        from ..core.database_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        
        backup_engine = MemoryBackupEngine(db_manager)
        success = backup_engine.create_backup(str(backup_path), include_metadata=True)
        
        if success:
            # 백업 설정 업데이트
            config['last_backup'] = now.isoformat()
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # 오래된 백업 파일 정리
            backup_pattern = str(backup_dir / "auto_backup_*.json")
            backup_files = sorted(glob.glob(backup_pattern), reverse=True)  # 최신부터
            
            if len(backup_files) > max_backups:
                old_backups = backup_files[max_backups:]
                for old_backup in old_backups:
                    Path(old_backup).unlink()
                    click.echo(f"[TRASH]  오래된 백업 삭제: {Path(old_backup).name}")
            
            file_size = backup_path.stat().st_size / (1024 * 1024)
            click.echo(f"[OK] 자동 백업 완료: {backup_filename} ({file_size:.2f} MB)")
            click.echo(f"[CHART] 보존된 백업 수: {min(len(backup_files), max_backups)}개")
            
        else:
            click.echo("[ERROR] 자동 백업 실패")
            
    except Exception as e:
        click.echo(f"[BURST] 자동 백업 실행 실패: {e}")


@backup.command()
def status():
    """자동 백업 상태 확인"""
    try:
        from pathlib import Path
        from datetime import datetime
        import json
        import glob
        
        backup_dir = Path.home() / "greeum-backups"
        config_file = backup_dir / "auto_backup_config.json"
        
        if not config_file.exists():
            click.echo("[WHITE_CIRCLE] 자동 백업: 미설정")
            click.echo("[IDEA] 'greeum backup auto --schedule daily' 로 설정하세요")
            return
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        status_emoji = "[GREEN]" if config.get('enabled', False) else "[RED]"
        status_text = "활성화" if config.get('enabled', False) else "비활성화"
        
        click.echo(f"{status_emoji} 자동 백업: {status_text}")
        
        if config.get('enabled', False):
            click.echo(f"   [DATE] 주기: {config.get('schedule', 'unknown')}")
            click.echo(f"   [FOLDER] 디렉토리: {config.get('output_dir', 'unknown')}")
            click.echo(f"   [123] 최대 보존: {config.get('max_backups', 10)}개")
            
            last_backup = config.get('last_backup')
            if last_backup:
                click.echo(f"   [CLOCK] 마지막 백업: {last_backup}")
            else:
                click.echo(f"   [CLOCK] 마지막 백업: 없음")
        
        # 백업 파일 목록
        backup_pattern = str(backup_dir / "auto_backup_*.json")
        backup_files = sorted(glob.glob(backup_pattern), reverse=True)
        
        if backup_files:
            click.echo(f"\n[CLIPBOARD] 백업 파일 ({len(backup_files)}개):")
            for backup_file in backup_files[:5]:  # 최대 5개만 표시
                backup_path = Path(backup_file)
                size_mb = backup_path.stat().st_size / (1024 * 1024)
                mtime = datetime.fromtimestamp(backup_path.stat().st_mtime)
                click.echo(f"   - {backup_path.name} ({size_mb:.2f} MB, {mtime.strftime('%Y-%m-%d %H:%M')})")
            
            if len(backup_files) > 5:
                click.echo(f"   ... 및 {len(backup_files) - 5}개 더")
        else:
            click.echo("\n[CLIPBOARD] 백업 파일: 없음")
            
    except Exception as e:
        click.echo(f"[BURST] 자동 백업 상태 확인 실패: {e}")


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
        # from ..core.hierarchical_memory import HierarchicalMemorySystem  # REMOVED
        from ..core.database_manager import DatabaseManager
        # from ..core.memory_layer import MemoryLayerType  # REMOVED
        from datetime import datetime
        
        # 복원 필터 생성
        date_from = None
        if from_date:
            try:
                date_from = datetime.strptime(from_date, '%Y-%m-%d')
            except ValueError:
                click.echo(f"[WARNING] 잘못된 시작 날짜 형식: {from_date}")
        
        date_to = None
        if to_date:
            try:
                date_to = datetime.strptime(to_date, '%Y-%m-%d') 
            except ValueError:
                click.echo(f"[WARNING] 잘못된 끝 날짜 형식: {to_date}")
        
        keyword_list = None
        if keywords:
            keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
        
        layer_list = None
        if layers:
            # Simplified layer mapping without MemoryLayerType enum
            layer_names = [layer.strip().lower() for layer in layers.split(',')]
            layer_list = layer_names  # Just pass as strings
        
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
        
        # 계층적 메모리 시스템 초기화 - SIMPLIFIED
        db_manager = DatabaseManager()
        # HierarchicalMemorySystem removed - using DatabaseManager directly
        
        restore_engine = MemoryRestoreEngine(system)
        
        if preview:
            # 미리보기 표시
            click.echo("[SEARCH] 복원 미리보기를 생성합니다...")
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
                click.echo("[OK] 복원 완료!")
                click.echo(f"[CHART] 복원 결과:")
                click.echo(f"   [MEMORY] Working Memory: {result.working_count}개")
                click.echo(f"   [FAST] STM: {result.stm_count}개") 
                click.echo(f"   [HALL]  LTM: {result.ltm_count}개")
                click.echo(f"   [IMPROVE] 총 처리: {result.total_processed}개")
                click.echo(f"   [TIMER]  소요 시간: {result.execution_time:.2f}초")
                
                if result.error_count > 0:
                    click.echo(f"   [WARNING]  오류: {result.error_count}개")
                    for error in result.errors[:5]:  # 최대 5개 오류만 표시
                        click.echo(f"      - {error}")
            else:
                click.echo("[ERROR] 복원에 실패했습니다")
                for error in result.errors:
                    click.echo(f"   [BURST] {error}")
                    
    except Exception as e:
        click.echo(f"[BURST] 복원 중 오류: {e}")


# v2.6.2 Dashboard 서브명령어들
@dashboard.command()
@click.option('--output', '-o', help='결과를 파일로 저장할 경로')
@click.option('--json-format', is_flag=True, help='JSON 형태로 출력')
def overview(output: str, json_format: bool):
    """메모리 시스템 전체 개요 표시"""
    try:
        from ..core.dashboard import get_dashboard_system
        import json
        
        dashboard_system = get_dashboard_system()
        overview_data = dashboard_system.get_overview()
        
        if json_format or output:
            # JSON 형태로 출력
            json_output = json.dumps(overview_data, indent=2, ensure_ascii=False)
            
            if output:
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(json_output)
                click.echo(f"[OK] 대시보드 리포트 저장됨: {output}")
            else:
                click.echo(json_output)
        else:
            # 사용자 친화적 형태로 출력
            _display_dashboard_overview(overview_data)
            
    except Exception as e:
        click.echo(f"[BURST] 대시보드 개요 생성 실패: {e}")


@dashboard.command()
@click.option('--format', 'output_format', type=click.Choice(['simple', 'detailed', 'json']), 
              default='simple', help='출력 형태')
def health(output_format: str):
    """시스템 건강도 확인"""
    try:
        from ..core.dashboard import get_dashboard_system
        import json
        
        dashboard_system = get_dashboard_system()
        health_data = dashboard_system.get_system_health()
        
        if output_format == 'json':
            click.echo(json.dumps(health_data.__dict__, indent=2, ensure_ascii=False, default=str))
        elif output_format == 'detailed':
            _display_health_detailed(health_data)
        else:
            _display_health_simple(health_data)
            
    except Exception as e:
        click.echo(f"[BURST] 시스템 건강도 확인 실패: {e}")


@dashboard.command()
@click.option('--output', '-o', required=True, help='리포트 파일 저장 경로')
@click.option('--include-details/--no-details', default=True, 
              help='상세 계층 분석 포함 여부')
def export(output: str, include_details: bool):
    """완전한 대시보드 리포트 내보내기"""
    try:
        from ..core.dashboard import get_dashboard_system
        from pathlib import Path
        
        dashboard_system = get_dashboard_system()
        
        success = dashboard_system.export_dashboard_report(
            output_path=output,
            include_details=include_details
        )
        
        if success:
            file_size = Path(output).stat().st_size / 1024  # KB
            click.echo(f"[OK] 대시보드 리포트 생성 완료: {output} ({file_size:.1f} KB)")
            
            if include_details:
                click.echo("[CHART] 상세 계층 분석 포함")
            else:
                click.echo("[CLIPBOARD] 기본 개요만 포함")
        else:
            click.echo("[ERROR] 리포트 생성에 실패했습니다")
            
    except Exception as e:
        click.echo(f"[BURST] 리포트 내보내기 실패: {e}")


# 대시보드 출력 헬퍼 함수들
def _display_dashboard_overview(data: dict):
    """사용자 친화적 대시보드 개요 출력"""
    stats = data['memory_stats']
    health = data['system_health']
    
    click.echo("[MEMORY] Greeum Memory Dashboard")
    click.echo("=" * 50)
    
    # 기본 통계
    click.echo(f"[CHART] 전체 메모리: {stats['total_memories']}개")
    click.echo(f"   [MEMORY] Working Memory: {stats['working_memory_count']}개")
    click.echo(f"   [FAST] STM: {stats['stm_count']}개")
    click.echo(f"   [HALL]  LTM: {stats['ltm_count']}개")
    
    click.echo()
    
    # 시스템 건강도
    health_percent = health['overall_health'] * 100
    health_emoji = "[GREEN]" if health_percent >= 80 else "[YELLOW]" if health_percent >= 60 else "[RED]"
    click.echo(f"{health_emoji} 시스템 건강도: {health_percent:.1f}%")
    
    # 용량 정보
    click.echo(f"[DISK] 총 용량: {stats['total_size_mb']:.1f} MB")
    click.echo(f"[FAST] 평균 검색 시간: {health['avg_search_time_ms']:.1f}ms")
    
    # 경고사항
    if health['warnings']:
        click.echo("\n[WARNING]  주의사항:")
        for warning in health['warnings']:
            click.echo(f"   - {warning}")
    
    # 권장사항
    if health['recommendations']:
        click.echo("\n[IDEA] 권장사항:")
        for rec in health['recommendations']:
            click.echo(f"   - {rec}")
    
    # 인기 키워드
    if 'popular_keywords' in stats:
        click.echo("\n[FIRE] 인기 키워드:")
        for keyword, count in stats['popular_keywords'][:5]:
            click.echo(f"   #{keyword} ({count}회)")


def _display_health_simple(health):
    """간단한 건강도 출력"""
    health_percent = health.overall_health * 100
    health_emoji = "[GREEN]" if health_percent >= 80 else "[YELLOW]" if health_percent >= 60 else "[RED]"
    
    click.echo(f"{health_emoji} 시스템 건강도: {health_percent:.1f}%")
    
    if health_percent >= 80:
        click.echo("[OK] 시스템이 정상적으로 작동하고 있습니다")
    elif health_percent >= 60:
        click.echo("[WARNING]  시스템에 약간의 주의가 필요합니다")
    else:
        click.echo("[RED] 시스템 점검이 필요합니다")


def _display_health_detailed(health):
    """상세한 건강도 출력"""
    _display_health_simple(health)
    
    click.echo(f"\n[IMPROVE] 성능 지표:")
    click.echo(f"   검색 속도: {health.avg_search_time_ms:.1f}ms")
    click.echo(f"   메모리 사용량: {health.memory_usage_mb:.1f}MB")
    click.echo(f"   데이터베이스 크기: {health.database_size_mb:.1f}MB")
    
    click.echo(f"\n[TARGET] 품질 지표:")
    click.echo(f"   평균 품질 점수: {health.avg_quality_score:.2f}")
    click.echo(f"   중복률: {health.duplicate_rate * 100:.1f}%")
    click.echo(f"   승급 성공률: {health.promotion_success_rate * 100:.1f}%")
    
    if health.warnings:
        click.echo(f"\n[WARNING]  경고:")
        for warning in health.warnings:
            click.echo(f"   - {warning}")
    
    if health.recommendations:
        click.echo(f"\n[IDEA] 권장사항:")
        for rec in health.recommendations:
            click.echo(f"   - {rec}")


# v2.7.0: Causal Reasoning Commands
@main.group()
def causal():
    """Causal reasoning and relationship analysis commands"""
    pass


@causal.command()
@click.argument('block_id', type=int)
@click.option('--format', 'output_format', type=click.Choice(['simple', 'detailed', 'json']), 
              default='simple', help='Output format')
def relationships(block_id: int, output_format: str):
    """Show causal relationships for a specific memory block"""
    try:
        from greeum.core import DatabaseManager
        from greeum.core.block_manager import BlockManager
        
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
        
        # Get the block info
        block = db_manager.get_block(block_id)
        if not block:
            click.echo(f"[ERROR] Block #{block_id} not found", err=True)
            return
        
        # Get causal relationships
        relationships = block_manager.get_causal_relationships(block_id)
        
        if output_format == 'json':
            import json
            click.echo(json.dumps({
                'block_id': block_id,
                'relationships': relationships
            }, indent=2, ensure_ascii=False))
            return
        
        if not relationships:
            click.echo(f"[SEARCH] No causal relationships found for block #{block_id}")
            return
        
        click.echo(f"[LINK] Causal relationships for block #{block_id}:")
        click.echo(f"   Context: {block['context'][:60]}...")
        click.echo()
        
        for i, rel in enumerate(relationships, 1):
            source_id = rel['source_block_id']
            target_id = rel['target_block_id']
            relation_type = rel['relation_type']
            confidence = rel['confidence']
            
            # Determine direction
            if source_id == block_id:
                direction = "->"
                other_id = target_id
                role = "Causes"
            else:
                direction = "<-"
                other_id = source_id
                role = "Caused by"
            
            # Get other block context
            other_block = db_manager.get_block(other_id)
            other_context = other_block['context'][:50] + "..." if other_block else "Unknown"
            
            confidence_emoji = "[FIRE]" if confidence >= 0.8 else "[POWER]" if confidence >= 0.6 else "[IDEA]"
            
            click.echo(f"{i}. {confidence_emoji} {role} Block #{other_id} ({confidence:.2f})")
            click.echo(f"   {direction} {other_context}")
            click.echo(f"   Type: {relation_type}")
            
            if output_format == 'detailed':
                import json
                keywords = json.loads(rel.get('keywords_matched', '[]'))
                if keywords:
                    click.echo(f"   Keywords: {', '.join(keywords)}")
                
                temporal_gap = rel.get('temporal_gap_hours')
                if temporal_gap is not None:
                    if temporal_gap < 1:
                        gap_str = f"{temporal_gap * 60:.0f} minutes"
                    elif temporal_gap < 24:
                        gap_str = f"{temporal_gap:.1f} hours"
                    else:
                        gap_str = f"{temporal_gap / 24:.1f} days"
                    click.echo(f"   Time gap: {gap_str}")
            
            click.echo()
        
    except Exception as e:
        click.echo(f"[ERROR] Error analyzing relationships: {e}", err=True)


@causal.command()
@click.argument('start_block_id', type=int)
@click.option('--depth', default=3, help='Maximum chain depth to explore')
@click.option('--format', 'output_format', type=click.Choice(['simple', 'detailed', 'json']), 
              default='simple', help='Output format')
def chain(start_block_id: int, depth: int, output_format: str):
    """Find causal relationship chains starting from a block"""
    try:
        from greeum.core import DatabaseManager
        from greeum.core.block_manager import BlockManager
        
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
        
        # Get the starting block
        start_block = db_manager.get_block(start_block_id)
        if not start_block:
            click.echo(f"[ERROR] Start block #{start_block_id} not found", err=True)
            return
        
        # Find causal chain
        chain_results = block_manager.find_causal_chain(start_block_id, depth)
        
        if output_format == 'json':
            import json
            click.echo(json.dumps({
                'start_block_id': start_block_id,
                'chain': chain_results
            }, indent=2, ensure_ascii=False))
            return
        
        if not chain_results:
            click.echo(f"[SEARCH] No causal chains found starting from block #{start_block_id}")
            return
        
        click.echo(f"[LINK] Causal chain starting from block #{start_block_id}:")
        click.echo(f"   Start: {start_block['context'][:60]}...")
        click.echo()
        
        # Group by depth for better visualization
        by_depth = {}
        for item in chain_results:
            d = item['depth']
            if d not in by_depth:
                by_depth[d] = []
            by_depth[d].append(item)
        
        for depth_level in sorted(by_depth.keys()):
            items = by_depth[depth_level]
            indent = "  " * (depth_level + 1)
            
            for item in items:
                confidence = item['confidence']
                target_block = item['target_block']
                target_context = target_block['context'][:50] + "..."
                
                confidence_emoji = "[FIRE]" if confidence >= 0.8 else "[POWER]" if confidence >= 0.6 else "[IDEA]"
                
                click.echo(f"{indent}down {confidence_emoji} Block #{item['target_id']} ({confidence:.2f})")
                click.echo(f"{indent}   {target_context}")
                
                if output_format == 'detailed':
                    click.echo(f"{indent}   Type: {item['relation_type']}")
        
    except Exception as e:
        click.echo(f"[ERROR] Error finding causal chain: {e}", err=True)


@causal.command()
@click.option('--format', 'output_format', type=click.Choice(['simple', 'detailed', 'json']), 
              default='simple', help='Output format')
def stats(output_format: str):
    """Show causal reasoning detection statistics"""
    try:
        from greeum.core import DatabaseManager
        from greeum.core.block_manager import BlockManager
        
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
        
        # Get statistics
        statistics = block_manager.get_causal_statistics()
        
        if 'error' in statistics:
            click.echo(f"[ERROR] {statistics['error']}", err=True)
            return
        
        if output_format == 'json':
            import json
            click.echo(json.dumps(statistics, indent=2, ensure_ascii=False))
            return
        
        click.echo("[CHART] Causal Reasoning Statistics")
        click.echo("=" * 35)
        
        # Detection summary
        total_analyzed = statistics.get('total_analyzed', 0)
        relationships_found = statistics.get('relationships_found', 0)
        accuracy_estimate = statistics.get('accuracy_estimate', 0.0)
        
        click.echo(f"\n[SEARCH] Detection Summary:")
        click.echo(f"   Total blocks analyzed: {total_analyzed}")
        click.echo(f"   Relationships found: {relationships_found}")
        if total_analyzed > 0:
            detection_rate = (relationships_found / total_analyzed) * 100
            click.echo(f"   Detection rate: {detection_rate:.1f}%")
        click.echo(f"   Estimated accuracy: {accuracy_estimate:.1f}%")
        
        # Confidence distribution
        high_conf = statistics.get('high_confidence', 0)
        medium_conf = statistics.get('medium_confidence', 0)
        low_conf = statistics.get('low_confidence', 0)
        
        click.echo(f"\n[UP] Confidence Distribution:")
        click.echo(f"   [FIRE] High (>=0.8): {high_conf}")
        click.echo(f"   [POWER] Medium (0.5-0.8): {medium_conf}")
        click.echo(f"   [IDEA] Low (<0.5): {low_conf}")
        
        # Relationship types
        by_type = statistics.get('by_type', {})
        if by_type:
            click.echo(f"\n[LABEL]  Relationship Types:")
            for rel_type, count in by_type.items():
                if count > 0:
                    click.echo(f"   {rel_type}: {count}")
        
        # Database statistics
        total_stored = statistics.get('total_stored', 0)
        stored_dist = statistics.get('stored_confidence_distribution', {})
        
        if output_format == 'detailed':
            click.echo(f"\n[DISK] Storage Statistics:")
            click.echo(f"   Total stored relationships: {total_stored}")
            
            if stored_dist:
                click.echo(f"   Stored confidence distribution:")
                for level, count in stored_dist.items():
                    click.echo(f"     {level}: {count}")
        
    except Exception as e:
        click.echo(f"[ERROR] Error getting causal statistics: {e}", err=True)


# Import and register graph commands
try:
    from .graph import graph_group
    main.commands.pop('graph', None)
    main.add_command(graph_group, name='graph')
except ImportError:
    pass  # Graph CLI not available

# Import and register metrics commands
try:
    from .metrics_cli import metrics_group
    # Replace the empty metrics group with the real one
    main.commands.pop('metrics', None)
    main.add_command(metrics_group, name='metrics')
except ImportError:
    pass  # Metrics CLI not available

# Import and register validate commands  
try:
    from .validate_cli import validate_group
    # Replace the empty validate group with the real one
    main.commands.pop('validate', None)
    main.add_command(validate_group, name='validate')
except ImportError:
    pass  # Validate CLI not available


if __name__ == '__main__':
    main()
