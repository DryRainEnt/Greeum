#!/bin/bash
# Greeum 로컬 개발 버전 설치 스크립트 - WSL 테스트용

echo "🔧 Greeum 로컬 개발 버전 설치 (WSL 테스트용)"
echo "================================================"

# 현재 디렉토리가 Greeum 프로젝트인지 확인
if [ ! -f "pyproject.toml" ] || [ ! -d "greeum" ]; then
    echo "❌ Greeum 프로젝트 디렉토리에서 실행해주세요"
    exit 1
fi

echo "📦 현재 개발 버전으로 pip 설치..."
pip install -e . --force-reinstall

echo "🔍 설치 확인..."
python3 -c "
try:
    import greeum
    print(f'✅ Greeum {greeum.__version__} 설치 성공')
    
    from greeum.mcp.adapters.base_adapter import BaseAdapter
    print('✅ BaseAdapter 임포트 성공')
    
    from greeum.mcp.native_mcp_server import NativeMCPServer
    print('✅ NativeMCPServer 임포트 성공')
    
except Exception as e:
    print(f'❌ 설치 실패: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 설치 완료! 이제 어디서든 사용 가능:"
    echo ""
    echo "# 직접 실행"
    echo "python -m greeum.mcp.native_mcp_server"
    echo ""
    echo "# 또는 절대 경로 없이"  
    echo "python -c \"from greeum.mcp.native_mcp_server import main; main()\""
    echo ""
    echo "🔧 Claude Desktop 설정에서 다음과 같이 사용 가능:"
    echo "\"command\": \"python\","
    echo "\"args\": [\"-m\", \"greeum.mcp.native_mcp_server\"]"
else
    echo "❌ 설치 실패"
    exit 1
fi