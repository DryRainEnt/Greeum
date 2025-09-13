"""
Greeum v3.0 Configuration Management
중앙집중식 설정 관리
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class MemoryConfig:
    """메모리 시스템 설정"""
    
    # Database
    database_path: str = "data/greeum.db"
    database_type: str = "sqlite"  # sqlite, postgresql
    
    # Context Management
    context_timeout: int = 300  # seconds (5 minutes)
    max_active_nodes: int = 10
    activation_decay_rate: float = 0.9
    
    # Spreading Activation
    activation_threshold: float = 0.1
    activation_decay: float = 0.5
    max_propagation_depth: int = 3
    
    # Semantic Tagging
    enable_auto_tagging: bool = True
    max_domain_tags: int = 50
    tag_consolidation_interval: int = 86400  # 24 hours in seconds
    min_tag_usage: int = 3
    
    # Performance
    search_limit: int = 10
    connection_limit: int = 100
    memory_cache_size: int = 1000
    
    # Logging
    log_level: str = "INFO"
    enable_debug_logs: bool = False
    log_file: Optional[str] = None
    
    # Features
    enable_causal_reasoning: bool = False  # Disabled for v3.0
    enable_neural_memory: bool = True
    enable_migration_bridge: bool = True


@dataclass 
class APIConfig:
    """API 및 외부 서비스 설정"""
    
    # MCP Integration
    enable_mcp: bool = False
    mcp_server_path: Optional[str] = None
    
    # AI Services
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # External Services
    embedding_service: str = "local"  # local, openai, huggingface
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"


@dataclass
class SystemConfig:
    """시스템 전체 설정"""
    
    # Core
    version: str = "3.0.0-dev"
    data_directory: str = "data"
    config_directory: str = "config"
    
    # Environment
    environment: str = "development"  # development, testing, production
    debug_mode: bool = True
    
    # Security
    enable_encryption: bool = False
    encryption_key: Optional[str] = None


class ConfigManager:
    """설정 관리 클래스"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        
        # Default configurations
        self.memory = MemoryConfig()
        self.api = APIConfig()
        self.system = SystemConfig()
        
        # Load from file and environment
        self.load_config()
        self.load_from_environment()
    
    def _get_default_config_path(self) -> str:
        """기본 설정 파일 경로 결정"""
        
        # 1. Environment variable
        if os.getenv("GREEUM_CONFIG"):
            return os.getenv("GREEUM_CONFIG")
        
        # 2. Current directory
        if os.path.exists("greeum.config.json"):
            return "greeum.config.json"
        
        # 3. User home directory
        home_config = Path.home() / ".greeum" / "config.json"
        if home_config.exists():
            return str(home_config)
        
        # 4. Default location
        return "config/greeum.config.json"
    
    def load_config(self):
        """설정 파일에서 로드"""
        
        if not os.path.exists(self.config_path):
            logger.info(f"Config file not found: {self.config_path}, using defaults")
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Update configurations
            if 'memory' in config_data:
                self._update_config(self.memory, config_data['memory'])
            
            if 'api' in config_data:
                self._update_config(self.api, config_data['api'])
            
            if 'system' in config_data:
                self._update_config(self.system, config_data['system'])
            
            logger.info(f"Configuration loaded from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
    
    def load_from_environment(self):
        """환경 변수에서 설정 로드"""
        
        # Memory settings
        if os.getenv("GREEUM_DB_PATH"):
            self.memory.database_path = os.getenv("GREEUM_DB_PATH")
        
        if os.getenv("GREEUM_LOG_LEVEL"):
            self.memory.log_level = os.getenv("GREEUM_LOG_LEVEL")
        
        if os.getenv("GREEUM_DEBUG"):
            self.memory.enable_debug_logs = os.getenv("GREEUM_DEBUG").lower() == "true"
        
        # API settings
        if os.getenv("OPENAI_API_KEY"):
            self.api.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if os.getenv("ANTHROPIC_API_KEY"):
            self.api.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        # System settings
        if os.getenv("GREEUM_ENV"):
            self.system.environment = os.getenv("GREEUM_ENV")
        
        if os.getenv("GREEUM_DATA_DIR"):
            self.system.data_directory = os.getenv("GREEUM_DATA_DIR")
    
    def _update_config(self, config_obj, config_data: Dict[str, Any]):
        """설정 객체 업데이트"""
        for key, value in config_data.items():
            if hasattr(config_obj, key):
                setattr(config_obj, key, value)
            else:
                logger.warning(f"Unknown config key: {key}")
    
    def save_config(self):
        """설정을 파일에 저장"""
        
        config_data = {
            'memory': asdict(self.memory),
            'api': asdict(self.api),
            'system': asdict(self.system)
        }
        
        # Create directory if needed
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save config to {self.config_path}: {e}")
    
    def get_database_path(self) -> str:
        """데이터베이스 경로 반환"""
        if os.path.isabs(self.memory.database_path):
            return self.memory.database_path
        else:
            return os.path.join(self.system.data_directory, self.memory.database_path)
    
    def setup_logging(self):
        """로깅 설정"""
        
        level = getattr(logging, self.memory.log_level.upper(), logging.INFO)
        
        # Basic configuration
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File logging if specified
        if self.memory.log_file:
            file_handler = logging.FileHandler(self.memory.log_file)
            file_handler.setLevel(level)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            logging.getLogger().addHandler(file_handler)
        
        # Debug mode adjustments
        if self.memory.enable_debug_logs:
            logging.getLogger('greeum').setLevel(logging.DEBUG)
        else:
            # Suppress noise from other modules
            logging.getLogger('greeum.core.causal_reasoning').setLevel(logging.ERROR)
    
    def is_production(self) -> bool:
        """프로덕션 환경인지 확인"""
        return self.system.environment == "production"
    
    def is_development(self) -> bool:
        """개발 환경인지 확인"""
        return self.system.environment == "development"


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """전역 설정 매니저 반환"""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager()
        _config_manager.setup_logging()
    
    return _config_manager


def set_config_path(path: str):
    """설정 파일 경로 지정"""
    global _config_manager
    _config_manager = ConfigManager(path)
    _config_manager.setup_logging()


# Convenience functions
def get_memory_config() -> MemoryConfig:
    """메모리 설정 반환"""
    return get_config().memory


def get_api_config() -> APIConfig:
    """API 설정 반환"""
    return get_config().api


def get_system_config() -> SystemConfig:
    """시스템 설정 반환"""
    return get_config().system