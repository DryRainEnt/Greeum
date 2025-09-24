import os
import sqlite3
from click.testing import CliRunner
from pathlib import Path

from greeum.cli import main
from greeum import config_store


def _create_legacy_db(db_path):
    conn = sqlite3.connect(str(db_path))
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
        "INSERT INTO blocks(block_index, timestamp, context, importance, hash, prev_hash) VALUES (0, '2024', 'legacy', 0.5, 'h', 'p')"
    )
    conn.commit()
    conn.close()


def test_setup_migrates_legacy_schema(tmp_path):
    data_dir = tmp_path / "store"
    data_dir.mkdir()
    db_path = data_dir / "memory.db"
    _create_legacy_db(db_path)

    runner = CliRunner()
    env_cfg = str(tmp_path / "config")
    env = {
        "GREEUM_CONFIG_DIR": env_cfg,
        "GREEUM_DISABLE_ST": "1",
        "GREEUM_STM_DB": str(data_dir / "stm_anchors.db"),
    }
    original_config_path = config_store.CONFIG_PATH
    config_store.CONFIG_PATH = Path(env_cfg).expanduser() / "config.json"
    os.environ["GREEUM_CONFIG_DIR"] = env_cfg
    result = runner.invoke(
        main,
        ["setup", "--data-dir", str(data_dir), "--skip-warmup", "--skip-worker"],
        env=env,
        input="\n",
    )
    config_store.CONFIG_PATH = original_config_path
    os.environ.pop("GREEUM_CONFIG_DIR", None)
    assert result.exit_code == 0, result.output

    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute("PRAGMA table_info(blocks)")
    columns = {row[1] for row in cursor.fetchall()}
    conn.close()
    assert "slot" in columns


def test_setup_resets_malformed_db(tmp_path):
    data_dir = tmp_path / "store"
    data_dir.mkdir()
    db_path = data_dir / "memory.db"
    db_path.write_text("not-a-sqlite-database")

    runner = CliRunner()
    env_cfg = str(tmp_path / "config")
    env = {
        "GREEUM_CONFIG_DIR": env_cfg,
        "GREEUM_DISABLE_ST": "1",
        "GREEUM_STM_DB": str(data_dir / "stm_anchors.db"),
    }
    original_config_path = config_store.CONFIG_PATH
    config_store.CONFIG_PATH = Path(env_cfg).expanduser() / "config.json"
    os.environ["GREEUM_CONFIG_DIR"] = env_cfg
    result = runner.invoke(
        main,
        ["setup", "--data-dir", str(data_dir), "--skip-warmup", "--skip-worker"],
        env=env,
        input="y\n",
    )
    config_store.CONFIG_PATH = original_config_path
    os.environ.pop("GREEUM_CONFIG_DIR", None)
    assert result.exit_code == 0, result.output

    conn = sqlite3.connect(str(db_path))
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    conn.close()
    assert integrity == "ok"

    backups = list((data_dir / "backups").glob("memory_malformed_*.db"))
    assert backups, "Expected backup of malformed database"
