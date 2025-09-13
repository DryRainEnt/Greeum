"""
Claude Code Environment Detection for Greeum v2.6.3
STM Architecture Reimagining - Phase 1

Claude Code MCP 호스트 감지 및 통합 유틸리티
"""

import os
import sys
import json
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@dataclass
class ClaudeCodeEnvironment:
    """Claude Code 환경 정보"""
    is_claude_code: bool
    host_type: str
    entrypoint: str
    claude_flag: str
    session_info: Dict[str, Any]
    detected_at: datetime
    

class ClaudeCodeDetector:
    """Claude Code MCP 호스트 감지 유틸리티"""
    
    def __init__(self):
        self._environment_info = None
        self._detection_timestamp = None
    
    def detect_environment(self) -> ClaudeCodeEnvironment:
        """환경 감지 및 정보 수집"""
        if self._environment_info is None:
            self._environment_info = self._perform_detection()
            self._detection_timestamp = datetime.now()
        
        return self._environment_info
    
    def _perform_detection(self) -> ClaudeCodeEnvironment:
        """실제 환경 감지 로직"""
        is_claude_code = False
        detection_methods = []
        
        # 방법 1: 환경 변수 확인 (가장 확실한 방법)
        claudecode_flag = os.getenv('CLAUDECODE', '')
        entrypoint = os.getenv('CLAUDE_CODE_ENTRYPOINT', '')
        
        if claudecode_flag == '1':
            is_claude_code = True
            detection_methods.append('CLAUDECODE_FLAG')
        
        if entrypoint:
            is_claude_code = True
            detection_methods.append('ENTRYPOINT_VAR')
        
        # 방법 2: 프로세스 트리 확인
        if HAS_PSUTIL:
            try:
                current_process = psutil.Process()
                parent = current_process.parent()
                
                if parent and 'claude' in parent.name().lower():
                    is_claude_code = True
                    detection_methods.append('PARENT_PROCESS')
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # 방법 3: 실행 경로 패턴 확인
        execution_path = ' '.join(sys.argv)
        if '.claude' in execution_path.lower():
            is_claude_code = True
            detection_methods.append('EXECUTION_PATH')
        
        # 방법 4: MCP 서버 설정 파일 확인
        claude_config_path = os.path.expanduser('~/.claude/mcp_servers.json')
        if os.path.exists(claude_config_path):
            try:
                with open(claude_config_path, 'r') as f:
                    config = json.load(f)
                    if 'mcpServers' in config and len(config['mcpServers']) > 0:
                        detection_methods.append('MCP_CONFIG_EXISTS')
            except json.JSONDecodeError:
                pass
        
        # 세션 정보 수집
        session_info = self._collect_session_info()
        
        return ClaudeCodeEnvironment(
            is_claude_code=is_claude_code,
            host_type='claude_code' if is_claude_code else 'unknown',
            entrypoint=entrypoint,
            claude_flag=claudecode_flag,
            session_info={
                'detection_methods': detection_methods,
                'environment_vars': self._get_claude_env_vars(),
                'mcp_servers': self._get_mcp_server_info(),
                'session_data': session_info
            },
            detected_at=datetime.now()
        )
    
    def _collect_session_info(self) -> Dict[str, Any]:
        """Claude Code 세션 정보 수집"""
        session_info = {
            'session_id': None,
            'shell_snapshots': [],
            'working_directory': os.getcwd(),
            'python_path': sys.path[0] if sys.path else None
        }
        
        # Shell snapshot 경로들 수집
        shell_snapshot_dir = os.path.expanduser('~/.claude/shell-snapshots')
        if os.path.exists(shell_snapshot_dir):
            try:
                snapshots = [f for f in os.listdir(shell_snapshot_dir) 
                           if f.startswith('snapshot-')]
                session_info['shell_snapshots'] = sorted(snapshots)[-5:]  # 최근 5개
            except OSError:
                pass
        
        # 현재 실행 중인 프로세스에서 세션 ID 추출 시도
        try:
            for env_var in os.environ:
                if 'session' in env_var.lower() or 'claude' in env_var.lower():
                    value = os.environ[env_var]
                    if len(value) > 10 and '-' in value:  # UUID 패턴 같은 것
                        session_info['session_id'] = value
                        break
        except Exception:
            pass
        
        return session_info
    
    def _get_claude_env_vars(self) -> Dict[str, str]:
        """Claude 관련 환경 변수 수집"""
        claude_vars = {}
        for key, value in os.environ.items():
            if 'claude' in key.lower():
                claude_vars[key] = value
        return claude_vars
    
    def _get_mcp_server_info(self) -> Dict[str, Any]:
        """MCP 서버 정보 수집"""
        mcp_info = {
            'config_exists': False,
            'server_count': 0,
            'greeum_mcp_configured': False
        }
        
        claude_config_path = os.path.expanduser('~/.claude/mcp_servers.json')
        if os.path.exists(claude_config_path):
            try:
                with open(claude_config_path, 'r') as f:
                    config = json.load(f)
                    
                mcp_info['config_exists'] = True
                
                if 'mcpServers' in config:
                    servers = config['mcpServers']
                    mcp_info['server_count'] = len(servers)
                    mcp_info['greeum_mcp_configured'] = 'greeum_mcp' in servers
                    mcp_info['server_names'] = list(servers.keys())
                    
            except (json.JSONDecodeError, KeyError):
                pass
        
        return mcp_info
    
    @property
    def is_claude_code_host(self) -> bool:
        """현재 MCP 서버가 Claude Code에서 실행 중인지 확인"""
        env = self.detect_environment()
        return env.is_claude_code
    
    @property
    def claude_session_id(self) -> Optional[str]:
        """Claude Code 세션 ID 반환"""
        env = self.detect_environment()
        return env.session_info.get('session_data', {}).get('session_id')
    
    def get_precompact_hook_path(self) -> Optional[str]:
        """PreCompact Hook 설정 경로 반환"""
        if not self.is_claude_code_host:
            return None
        
        return os.path.expanduser('~/.claude/settings.json')
    
    def is_precompact_hook_configured(self) -> bool:
        """PreCompact Hook이 이미 설정되어 있는지 확인"""
        hook_path = self.get_precompact_hook_path()
        if not hook_path or not os.path.exists(hook_path):
            return False
        
        try:
            with open(hook_path, 'r') as f:
                config = json.load(f)
            
            return (
                'hooks' in config and 
                'PreCompact' in config['hooks'] and 
                len(config['hooks']['PreCompact']) > 0
            )
        except (json.JSONDecodeError, KeyError):
            return False
    
    def get_environment_summary(self) -> str:
        """환경 정보 요약 문자열"""
        env = self.detect_environment()
        
        if env.is_claude_code:
            return f"🎯 Claude Code 환경 (감지: {', '.join(env.session_info['detection_methods'])})"
        else:
            return "💻 일반 MCP 환경"
    
    def print_detection_report(self):
        """감지 결과 상세 리포트 출력"""
        env = self.detect_environment()
        
        print("=" * 60)
        print("🔍 Claude Code Environment Detection Report")
        print("=" * 60)
        
        print(f"Host Type: {env.host_type}")
        print(f"Is Claude Code: {'✅ YES' if env.is_claude_code else '[ERROR] NO'}")
        print(f"Detection Time: {env.detected_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if env.is_claude_code:
            print(f"\n🎯 Claude Code Details:")
            print(f"  Entrypoint: {env.entrypoint}")
            print(f"  Claude Flag: {env.claude_flag}")
            print(f"  Detection Methods: {', '.join(env.session_info['detection_methods'])}")
            
            session_data = env.session_info.get('session_data', {})
            if session_data.get('session_id'):
                print(f"  Session ID: {session_data['session_id']}")
            
            mcp_info = env.session_info.get('mcp_servers', {})
            if mcp_info.get('config_exists'):
                print(f"  MCP Servers: {mcp_info['server_count']} configured")
                print(f"  Greeum MCP: {'✅ Configured' if mcp_info['greeum_mcp_configured'] else '[ERROR] Not configured'}")
            
            print(f"  PreCompact Hook: {'✅ Configured' if self.is_precompact_hook_configured() else '[ERROR] Not configured'}")
        
        print("=" * 60)


# 전역 인스턴스 (싱글톤 패턴)
_detector_instance = None

def get_claude_code_detector() -> ClaudeCodeDetector:
    """Claude Code Detector 싱글톤 인스턴스 반환"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = ClaudeCodeDetector()
    return _detector_instance


# 편의 함수들
def is_claude_code_host() -> bool:
    """현재 환경이 Claude Code인지 확인"""
    return get_claude_code_detector().is_claude_code_host

def get_claude_session_id() -> Optional[str]:
    """Claude Code 세션 ID 반환"""
    return get_claude_code_detector().claude_session_id

def print_environment_info():
    """환경 정보 출력"""
    get_claude_code_detector().print_detection_report()


if __name__ == "__main__":
    # 직접 실행 시 환경 감지 리포트 출력
    print_environment_info()