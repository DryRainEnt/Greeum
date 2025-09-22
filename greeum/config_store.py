"""Lightweight configuration storage for Greeum CLI helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

DEFAULT_DATA_DIR = Path.home() / ".greeum"
DEFAULT_ST_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def _default_config_path() -> Path:
    base = os.getenv("GREEUM_CONFIG_DIR")
    if base:
        return Path(base).expanduser() / "config.json"

    config_home = os.getenv("XDG_CONFIG_HOME")
    if config_home:
        return Path(config_home).expanduser() / "greeum" / "config.json"

    return Path.home() / ".config" / "greeum" / "config.json"


CONFIG_PATH = _default_config_path()


@dataclass
class GreeumConfig:
    data_dir: str
    semantic_ready: bool = False
    created_at: str = datetime.utcnow().isoformat()
    updated_at: str = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["updated_at"] = datetime.utcnow().isoformat()
        return data

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "GreeumConfig":
        return cls(
            data_dir=payload.get("data_dir", str(DEFAULT_DATA_DIR)),
            semantic_ready=bool(payload.get("semantic_ready", False)),
            created_at=payload.get("created_at", datetime.utcnow().isoformat()),
            updated_at=payload.get("updated_at", datetime.utcnow().isoformat()),
        )


def load_config() -> GreeumConfig:
    if not CONFIG_PATH.exists():
        return GreeumConfig(data_dir=str(Path.home() / ".greeum"))

    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return GreeumConfig(data_dir=str(Path.home() / ".greeum"))

    return GreeumConfig.from_dict(payload)


def save_config(config: GreeumConfig) -> None:
    config_dir = CONFIG_PATH.parent
    config_dir.mkdir(parents=True, exist_ok=True)

    with CONFIG_PATH.open("w", encoding="utf-8") as handle:
        json.dump(config.to_dict(), handle, indent=2, ensure_ascii=False)


def mark_semantic_ready(enabled: bool) -> None:
    config = load_config()
    config.semantic_ready = enabled
    save_config(config)


def ensure_data_dir(path_str: str) -> Path:
    data_path = Path(path_str).expanduser()
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path
