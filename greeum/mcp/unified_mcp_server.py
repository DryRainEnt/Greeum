#!/usr/bin/env python3
"""
Greeum 통합 MCP 서버 v2.2.7
- 모든 환경(WSL/PowerShell/macOS/Linux)에서 안정적 작동
- 환경 자동 감지 및 최적 어댑터 선택
- AsyncIO 충돌 완전 방지
- 기존 API 100% 호환성 보장
"""

import os
import sys
import platform
import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger("unified_mcp")

class EnvironmentDetector:
    """실행 환경 자동 감지"""
    
    @staticmethod
    def detect_environment() -> str:
        """
        실행 환경을 감지하여 최적 어댑터 결정
        
        Returns:
            'wsl': Windows WSL 환경
            'powershell': Windows PowerShell 환경  
            'macos': macOS 환경
            'linux': Linux 환경
            'unknown': 알 수 없는 환경
        """
        system = platform.system().lower()
        
        # WSL 감지
        if system == 'linux' and 'microsoft' in platform.release().lower():
            return 'wsl'
            
        # PowerShell 감지 (Windows에서 실행 중이고 TERM 환경변수 확인)
        if system == 'windows' or os.environ.get('OS', '').lower() == 'windows_nt':
            return 'powershell'
            
        # macOS 감지
        if system == 'darwin':
            return 'macos'
            
        # Linux 감지
        if system == 'linux':
            return 'linux'
            
        return 'unknown'

class AdapterManager:
    """어댑터 관리 및 로딩"""
    
    def __init__(self):
        self.environment = EnvironmentDetector.detect_environment()
        self.adapter = None
        
    async def load_adapter(self):
        """환경에 맞는 어댑터 로딩"""
        try:
            if self.environment in ['wsl', 'powershell']:
                # WSL/PowerShell: FastMCP 어댑터 사용
                from .adapters.fastmcp_adapter import FastMCPAdapter
                self.adapter = FastMCPAdapter()
                logger.info(f"✅ FastMCP adapter loaded for {self.environment}")
                
            else:
                # macOS/Linux: JSON-RPC 어댑터 사용
                from .adapters.jsonrpc_adapter import JSONRPCAdapter
                self.adapter = JSONRPCAdapter()
                logger.info(f"✅ JSON-RPC adapter loaded for {self.environment}")
                
        except ImportError as e:
            logger.error(f"❌ Failed to load adapter for {self.environment}: {e}")
            # 폴백: 기본 어댑터 시도
            try:
                from .adapters.base_adapter import BaseAdapter
                self.adapter = BaseAdapter()
                logger.warning("⚠️  Using fallback base adapter")
            except ImportError:
                logger.critical("❌ No adapters available")
                sys.exit(1)
                
    async def run_server(self):
        """통합 서버 실행"""
        if not self.adapter:
            await self.load_adapter()
            
        try:
            logger.info(f"🚀 Starting Greeum unified MCP server ({self.environment})")
            await self.adapter.run()
        except Exception as e:
            logger.error(f"❌ Server failed: {e}")
            sys.exit(1)

# 메인 실행 함수
async def main():
    """통합 MCP 서버 메인 실행 함수"""
    try:
        # 환경 감지 및 어댑터 매니저 초기화
        manager = AdapterManager()
        logger.info(f"🔍 Environment detected: {manager.environment}")
        
        # 서버 실행
        await manager.run_server()
        
    except KeyboardInterrupt:
        logger.info("👋 Unified MCP server stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # AsyncIO 런타임 안전장치
    try:
        # 기존 이벤트 루프가 있는지 확인
        loop = asyncio.get_running_loop()
        logger.warning("⚠️  Event loop already running, using existing loop")
        # 기존 루프에서 실행
        asyncio.create_task(main())
    except RuntimeError:
        # 새 이벤트 루프에서 실행
        asyncio.run(main())