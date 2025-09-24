import os
import sqlite3
import time
from pathlib import Path

from click.testing import CliRunner

from greeum.cli import main
from greeum import config_store


def _create_legacy_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE blocks (
            block_index INTEGER PRIMARY KEY,
            timestamp TEXT,
            context TEXT,
            importance REAL,
            hash TEXT,
            prev_hash TEXT
        )
        """
    )
    cursor.execute(
        "INSERT INTO blocks(block_index, timestamp, context, importance, hash, prev_hash) VALUES (0, '2024', 'legacy entry', 0.5, 'h', 'p')"
    )
    conn.commit()
    conn.close()


def _run_cli(cmd, data_dir: Path):
    runner = CliRunner()
    env_cfg = data_dir / "config"
    env = {
        "GREEUM_CONFIG_DIR": str(env_cfg),
        "GREEUM_DISABLE_ST": "1",
        "GREEUM_STM_DB": str(data_dir / "stm_anchors.db"),
    }
    original_config_path = config_store.CONFIG_PATH
    config_store.CONFIG_PATH = Path(env_cfg).expanduser() / "config.json"
    os.environ["GREEUM_CONFIG_DIR"] = str(env_cfg)
    try:
        result = runner.invoke(main, cmd, env=env)
    finally:
        config_store.CONFIG_PATH = original_config_path
        os.environ.pop("GREEUM_CONFIG_DIR", None)
    return result


def test_migrate_doctor_auto(tmp_path):
    data_dir = tmp_path / "store"
    data_dir.mkdir()
    legacy_db = data_dir / "memory.db"
    _create_legacy_db(legacy_db)

    result = _run_cli(["migrate", "doctor", "--data-dir", str(data_dir), "--yes"], data_dir)
    assert result.exit_code == 0, result.output

    conn = sqlite3.connect(str(legacy_db))
    columns = {row[1] for row in conn.execute("PRAGMA table_info(blocks)")}
    conn.close()
    assert "slot" in columns


def test_migrate_validate_ok(tmp_path):
    data_dir = tmp_path / "store"
    data_dir.mkdir()
    db_path = data_dir / "memory.db"
    _create_legacy_db(db_path)
    _run_cli(["migrate", "doctor", "--data-dir", str(data_dir), "--yes"], data_dir)

    result = _run_cli(["migrate", "validate", "--data-dir", str(data_dir)], data_dir)
    assert result.exit_code == 0, result.output
    assert "Integrity check OK" in result.output


def test_migrate_cleanup_prunes(tmp_path):
    data_dir = tmp_path / "store"
    data_dir.mkdir()
    backup_dir = data_dir / "backups"
    backup_dir.mkdir()

    # create seven dummy backups with increasing timestamps
    for index in range(7):
        path = backup_dir / f"memory_schema_{index}.db"
        path.write_text("dummy")
        ts = time.time() - index
        os.utime(path, (ts, ts))

    result = _run_cli(["migrate", "cleanup", "--data-dir", str(data_dir), "--keep-backups", "2"], data_dir)
    assert result.exit_code == 0, result.output
    remaining = sorted(p.name for p in backup_dir.iterdir())
    assert len(remaining) == 2
    assert remaining == ["memory_schema_0.db", "memory_schema_1.db"]
