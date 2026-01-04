"""
Greeum Server Configuration

Environment-based configuration for the API server.
v5.0.0: Added authentication settings.
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """Server configuration settings."""

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8400, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")

    # CORS
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Log level")

    # Data
    data_dir: Path = Field(
        default_factory=lambda: Path.home() / ".greeum",
        description="Data directory path"
    )

    # Authentication (v5.0.0)
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication (None = disabled)"
    )
    auth_enabled: bool = Field(
        default=False,
        description="Enable API key authentication"
    )
    public_endpoints: List[str] = Field(
        default=["/", "/health", "/docs", "/redoc", "/openapi.json"],
        description="Endpoints that bypass authentication"
    )

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Load configuration from environment variables."""
        api_key = os.getenv("GREEUM_API_KEY")
        public_endpoints_str = os.getenv(
            "GREEUM_PUBLIC_ENDPOINTS",
            "/,/health,/docs,/redoc,/openapi.json"
        )

        return cls(
            host=os.getenv("GREEUM_HOST", "0.0.0.0"),
            port=int(os.getenv("GREEUM_PORT", "8400")),
            debug=os.getenv("GREEUM_DEBUG", "").lower() in ("true", "1", "yes"),
            cors_origins=os.getenv("GREEUM_CORS_ORIGINS", "*").split(","),
            log_level=os.getenv("GREEUM_LOG_LEVEL", "INFO"),
            data_dir=Path(os.getenv("GREEUM_DATA_DIR", str(Path.home() / ".greeum"))),
            # Authentication (v5.0.0)
            api_key=api_key,
            auth_enabled=bool(api_key),  # Auto-enable if API key is set
            public_endpoints=[ep.strip() for ep in public_endpoints_str.split(",")],
        )


# Global config instance
config = ServerConfig.from_env()
