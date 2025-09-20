#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for MCP system_doctor tool
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from greeum.mcp.native.tools import GreeumMCPTools
from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
from greeum.core.stm_manager import STMManager
from greeum.core.usage_analytics import UsageAnalytics
from greeum.core.quality_validator import QualityValidator
from greeum.core.duplicate_detector import DuplicateDetector


async def _run_system_doctor_checks():
    """Test the system_doctor MCP tool"""

    # Initialize components
    db_manager = DatabaseManager()
    block_manager = BlockManager(db_manager)
    stm_manager = STMManager(db_manager)
    usage_analytics = UsageAnalytics(db_manager)
    quality_validator = QualityValidator()
    duplicate_detector = DuplicateDetector(db_manager)

    # Create components dictionary
    components = {
        'db_manager': db_manager,
        'block_manager': block_manager,
        'stm_manager': stm_manager,
        'duplicate_detector': duplicate_detector,
        'quality_validator': quality_validator,
        'usage_analytics': usage_analytics
    }

    # Initialize MCP tools handler
    tools_handler = GreeumMCPTools(components)

    print("="*60)
    print("Testing MCP system_doctor tool")
    print("="*60)

    # Test 1: Check only (no fixes)
    print("\n📋 Test 1: Diagnostics Only")
    print("-"*40)
    result = await tools_handler.execute_tool(
        "system_doctor",
        {"check_only": True}
    )
    print(result)

    # Test 2: Auto-fix without backup
    print("\n\n🔧 Test 2: Auto-Fix (no backup)")
    print("-"*40)
    result = await tools_handler.execute_tool(
        "system_doctor",
        {"auto_fix": True, "include_backup": False}
    )
    print(result)

    # Test 3: Default behavior (auto-fix with backup)
    print("\n\n✨ Test 3: Default Behavior")
    print("-"*40)
    result = await tools_handler.execute_tool(
        "system_doctor",
        {}
    )
    print(result)

    print("\n" + "="*60)
    print("✅ MCP system_doctor tool test completed!")


def test_system_doctor():
    asyncio.run(_run_system_doctor_checks())


if __name__ == "__main__":
    asyncio.run(_run_system_doctor_checks())
