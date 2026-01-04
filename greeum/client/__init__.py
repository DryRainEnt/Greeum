"""
Greeum Client Package

HTTP 클라이언트와 로컬 STM 캐시를 제공합니다.
MCP 서버가 API 모드로 동작할 때 사용됩니다.
"""

from greeum.client.client import GreeumClient
from greeum.client.http_client import GreeumHTTPClient
from greeum.client.stm_cache import STMCache

# Legacy client imports (from greeum/client.py via parent package)
# These are re-exported for backwards compatibility
import sys
import os
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# Import legacy client module directly
import importlib.util
_legacy_client_path = os.path.join(_parent_dir, "client.py")
if os.path.exists(_legacy_client_path):
    _spec = importlib.util.spec_from_file_location("_legacy_client", _legacy_client_path)
    _legacy_client = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_legacy_client)

    # Re-export legacy classes
    MemoryClient = _legacy_client.MemoryClient
    SimplifiedMemoryClient = _legacy_client.SimplifiedMemoryClient
    ClientError = _legacy_client.ClientError
    ConnectionFailedError = _legacy_client.ConnectionFailedError
    AuthenticationError = _legacy_client.AuthenticationError
    APIError = _legacy_client.APIError
    RequestTimeoutError = _legacy_client.RequestTimeoutError

__all__ = [
    # New client classes
    "GreeumClient", "GreeumHTTPClient", "STMCache",
    # Legacy client classes (backwards compatibility)
    "MemoryClient", "SimplifiedMemoryClient",
    "ClientError", "ConnectionFailedError", "AuthenticationError",
    "APIError", "RequestTimeoutError",
]
