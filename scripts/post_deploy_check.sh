#!/bin/bash
# Greeum 배포 후 자동 검증 스크립트

set -e

echo "🚀 Greeum v2.4.0rc1 배포 후 검증 시작..."

# 1. 버전 확인
echo "📋 1. 버전 확인"
VERSION=$(python3 -c "import greeum; print(greeum.__version__)")
if [ "$VERSION" = "2.4.0rc1" ]; then
    echo "✅ Version check passed: $VERSION"
else
    echo "❌ Version mismatch: expected 2.4.0rc1, got $VERSION"
    exit 1
fi

# 2. 기본 import 테스트
echo "📋 2. 기본 Import 테스트"
python3 -c "
from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
from greeum.client import MemoryClient
print('✅ All imports successful')
"

# 3. 데이터베이스 초기화 테스트
echo "📋 3. 데이터베이스 초기화 테스트"
python3 -c "
import tempfile
from greeum.core.database_manager import DatabaseManager
with tempfile.NamedTemporaryFile() as tmp:
    db = DatabaseManager(connection_string=f'sqlite:///{tmp.name}')
    print('✅ Database initialization successful')
"

# 4. CI 상태 확인
echo "📋 4. CI 상태 확인"
if command -v gh &> /dev/null; then
    LATEST_RUN=$(gh run list --limit 1 --json conclusion --jq '.[0].conclusion')
    if [ "$LATEST_RUN" = "success" ]; then
        echo "✅ Latest CI run: SUCCESS"
    else
        echo "⚠️  Latest CI run: $LATEST_RUN"
    fi
else
    echo "⚠️  GitHub CLI not available, skipping CI check"
fi

# 5. PyPI 접근성 테스트 (모의)
echo "📋 5. PyPI 접근성 확인"
if curl -s https://pypi.org/pypi/greeum/json | grep -q "2.4.0rc1"; then
    echo "✅ PyPI version available"
else
    echo "⚠️  PyPI version not yet indexed (normal delay)"
fi

echo "🎉 배포 후 검증 완료!"
echo "🔍 모니터링 포인트:"
echo "  - GitHub Issues: https://github.com/DryRainEnt/Greeum/issues"
echo "  - PyPI Stats: https://pypi.org/project/greeum/#history"
echo "  - CI Status: https://github.com/DryRainEnt/Greeum/actions"