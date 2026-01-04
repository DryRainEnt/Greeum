"""Lightweight configuration storage for Greeum CLI helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

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
class RemoteConfig:
    """원격 서버 연결 설정."""
    enabled: bool = False
    server_url: str = ""
    api_key: str = ""
    default_project: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RemoteConfig":
        return cls(
            enabled=bool(payload.get("enabled", False)),
            server_url=str(payload.get("server_url", "")),
            api_key=str(payload.get("api_key", "")),
            default_project=str(payload.get("default_project", "")),
        )


@dataclass
class GreeumConfig:
    data_dir: str
    semantic_ready: bool = False
    mode: str = "local"  # "local" | "remote"
    remote: Optional[RemoteConfig] = None
    created_at: str = datetime.utcnow().isoformat()
    updated_at: str = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "data_dir": self.data_dir,
            "semantic_ready": self.semantic_ready,
            "mode": self.mode,
            "created_at": self.created_at,
            "updated_at": datetime.utcnow().isoformat(),
        }
        if self.remote:
            data["remote"] = self.remote.to_dict()
        return data

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "GreeumConfig":
        remote_data = payload.get("remote")
        remote = RemoteConfig.from_dict(remote_data) if remote_data else None

        return cls(
            data_dir=payload.get("data_dir", str(DEFAULT_DATA_DIR)),
            semantic_ready=bool(payload.get("semantic_ready", False)),
            mode=payload.get("mode", "local"),
            remote=remote,
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


# Remote config helpers
def is_remote_mode() -> bool:
    """Check if remote mode is enabled."""
    config = load_config()
    return config.mode == "remote" and config.remote is not None and config.remote.enabled


def get_remote_config() -> Optional[RemoteConfig]:
    """Get remote configuration if available."""
    config = load_config()
    return config.remote


def set_remote_config(
    server_url: str,
    api_key: str,
    default_project: str = "",
    enabled: bool = True,
) -> None:
    """Set remote server configuration."""
    config = load_config()
    config.remote = RemoteConfig(
        enabled=enabled,
        server_url=server_url,
        api_key=api_key,
        default_project=default_project,
    )
    config.mode = "remote" if enabled else "local"
    save_config(config)


def set_mode(mode: str) -> None:
    """Set connection mode (local/remote)."""
    if mode not in ("local", "remote"):
        raise ValueError(f"Invalid mode: {mode}. Must be 'local' or 'remote'.")
    config = load_config()
    config.mode = mode
    save_config(config)


def clear_remote_config() -> None:
    """Clear remote configuration and switch to local mode."""
    config = load_config()
    config.remote = None
    config.mode = "local"
    save_config(config)
