import sys
import platform
import importlib
import logging
from typing import Optional

# from . import __version__ as greeum_version # 패키지 루트의 __init__.py에서 버전을 가져오도록 수정 필요
# 임시로 greeum.__version__ 접근 시도. 실제로는 패키지 구조에 따라 달라짐.
try:
    from greeum import __version__ as greeum_current_version
except ImportError:
    # greeum 패키지가 아직 sys.path에 없거나, __init__.py에 __version__이 없을 수 있음
    # 이 경우, setup.py나 다른 방식에서 버전을 가져와야 함.
    # 여기서는 임시로 None 처리하거나, 호출하는 측에서 greeum 패키지를 먼저 임포트했다고 가정.
    try:
        # 현재 파일이 greeum 패키지 내부에 있으므로 상대경로 시도
        from . import __version__ as greeum_current_version
    except ImportError:
        greeum_current_version = "unknown"

logger = logging.getLogger(__name__)

MIN_PYTHON_VERSION = (3, 8) # 최소 Python 버전 (예시)

# requirements.txt를 기반으로 하거나 주요 의존성 명시
REQUIRED_DEPENDENCIES = {
    "numpy": "1.20.0",
    "requests": "2.25.0",
    "sqlalchemy": "1.4.0",
    # "sentence-transformers": "2.2.0", # 선택적 의존성은 제외하거나 별도 확인
    # "openai": "0.27.0", # 선택적 의존성
}

def get_package_version(package_name: str) -> Optional[str]:
    """설치된 패키지의 버전을 가져옵니다."""
    try:
        module = importlib.import_module(package_name)
        return getattr(module, '__version__', None) or getattr(module, 'VERSION', None)
    except ImportError:
        return None
    except Exception as e:
        logger.debug(f"Error checking {package_name} version: {e}")
        return None

def check_python_version() -> dict:
    """Python 버전 확인"""
    current_version_str = platform.python_version()
    current_version_tuple = platform.python_version_tuple()
    min_version_str = '.'.join(map(str, MIN_PYTHON_VERSION))
    
    status = "ok"
    message = f"Current Python version: {current_version_str}"
    
    if tuple(map(int, current_version_tuple[:2])) < MIN_PYTHON_VERSION:
        status = "error"
        message = f"Current Python version ({current_version_str}) is lower than minimum required version ({min_version_str})."
        
    return {
        "status": status,
        "version": current_version_str,
        "min_required": min_version_str,
        "message": message
    }

def check_greeum_version() -> dict:
    """Greeum 패키지 버전 확인"""
    # from . import __version__ as greeum_version # __init__.py에 정의되어 있어야 함
    # 이 함수가 greeum 패키지 외부에서 호출될 수도 있으므로, import greeum 시도
    # try:
    #     import greeum
    #     current_greeum_version = greeum.__version__
    # except (ImportError, AttributeError):
    #     current_greeum_version = "unknown"
    
    # 위에서 이미 greeum_current_version 을 가져오도록 시도했음.
    status = "ok" if greeum_current_version != "unknown" else "error"
    message = f"Greeum version: {greeum_current_version}"
    if status == "error":
        message = "Greeum 패키지 버전을 확인할 수 없습니다."
        
    return {
        "status": status,
        "version": greeum_current_version,
        "message": message
    }

def check_dependencies() -> dict:
    """필수 의존성 패키지 확인"""
    results = {}
    all_ok = True
    for pkg_name, min_version_str in REQUIRED_DEPENDENCIES.items():
        installed_version_str = get_package_version(pkg_name)
        if installed_version_str:
            # 버전 비교 로직 (간단화된 버전, 실제로는 packaging.version 사용 권장)
            # from packaging.version import parse as parse_version
            # if parse_version(installed_version_str) >= parse_version(min_version_str):
            # status = "ok"
            # else:
            # status = "warning" # 또는 "error"
            # message = f"{pkg_name} version ({installed_version_str}) differs from/lower than recommended version ({min_version_str})"
            
            # 간단 비교: 최소 버전 이상인지 확인 (정확하지 않을 수 있음)
            try:
                # 간단하게 첫번째 숫자만 비교하거나, 전체 문자열 비교
                # 여기서는 존재 유무와 버전 문자열만 기록
                status = "ok"
                message = f"{pkg_name} installed (version: {installed_version_str})"
            except Exception:
                 status = "warning"
                 message = f"{pkg_name} 버전 ({installed_version_str}) 비교 중 오류, 권장: {min_version_str}"
                 all_ok = False # 버전 비교 실패 시 경고로 처리
        else:
            status = "error"
            message = f"{pkg_name} (권장 버전: {min_version_str})이(가) 설치되지 않았습니다."
            all_ok = False
        results[pkg_name] = {"status": status, "installed_version": installed_version_str, "required_version": min_version_str, "message": message}
    
    overall_status = "ok" if all_ok else ("warning" if any(r['status'] == 'warning' for r in results.values()) else "error")
    return {"overall_status": overall_status, "details": results}

def check_database_connectivity() -> dict:
    """데이터베이스 연결성 확인 (인메모리 SQLite 사용)"""
    try:
        from greeum.database_manager import DatabaseManager
        # 인메모리 DB로 테스트
        db_manager = DatabaseManager(connection_string=":memory:")
        # 간단한 쿼리 실행 (예: 테이블 목록 조회 또는 테이블 생성 확인)
        cursor = db_manager.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blocks';")
        if cursor.fetchone():
            db_manager.close()
            return {"status": "ok", "message": "SQLite 데이터베이스 연결 및 기본 테이블 확인 완료."}
        else:
            db_manager.close()
            return {"status": "error", "message": "SQLite 연결은 성공했으나 'blocks' 테이블을 찾을 수 없습니다."}
    except ImportError:
        return {"status": "error", "message": "DatabaseManager를 import할 수 없습니다."}
    except Exception as e:
        logger.error(f"Error during DB connection test: {e}", exc_info=True)
        return {"status": "error", "message": f"데이터베이스 연결 테스트 실패: {e}"}

def check_default_embedding_model() -> dict:
    """기본 임베딩 모델 로드 가능 여부 확인"""
    try:
        from greeum.embedding_models import get_embedding, EmbeddingRegistry
        # 기본 모델 가져오기 시도 (기본 모델이 설정되어 있어야 함)
        # registry = EmbeddingRegistry() # 전역 인스턴스를 사용한다고 가정
        # default_model_name = registry.get_default_model_name()
        # if not default_model_name:
        # return {"status": "warning", "message": "기본 임베딩 모델이 설정되지 않았습니다."}
        
        # get_embedding 함수가 기본 모델을 사용하거나, 특정 모델을 로드할 수 있어야 함
        # 여기서는 "default" 라는 이름의 모델이 등록되어 있다고 가정하고 테스트
        # 혹은 SimpleEmbeddingModel 직접 로드 테스트
        from greeum.embedding_models import SimpleEmbeddingModel
        model = SimpleEmbeddingModel(dimension=768) # 초기화 성공 여부
        embedding = model.encode("테스트 문장")
        if isinstance(embedding, list) and len(embedding) > 0:
             return {"status": "ok", "message": "기본 임베딩 모델(SimpleEmbeddingModel) 로드 및 테스트 인코딩 성공."}
        else:
            return {"status": "error", "message": "기본 임베딩 모델(SimpleEmbeddingModel) 테스트 인코딩 실패."}

    except ImportError:
        return {"status": "error", "message": "embedding_models 모듈을 import할 수 없습니다."}
    except Exception as e:
        logger.error(f"Error during default embedding model test: {e}", exc_info=True)
        return {"status": "error", "message": f"기본 임베딩 모델 테스트 실패: {e}"}

def check_environment(verbose: bool = False) -> dict:
    """Greeum 실행 환경 진단"""
    results = {
        "python_version": check_python_version(),
        "greeum_version": check_greeum_version(),
        "dependencies": check_dependencies(),
        "database_connectivity": check_database_connectivity(),
        "default_embedding_model": check_default_embedding_model()
    }
    
    overall_ok = True
    summary_messages = []

    for key, result in results.items():
        if isinstance(result, dict) and result.get("status") != "ok":
            overall_ok = False
            summary_messages.append(f"- {key.replace('_', ' ').title()}: {result.get('status', 'unknown')} ({result.get('message', '')})")
        elif isinstance(result, dict) and result.get("overall_status") and result.get("overall_status") != "ok": # for dependencies
            overall_ok = False
            summary_messages.append(f"- {key.replace('_', ' ').title()}: {result.get('overall_status', 'unknown')}")
            if verbose:
                 for dep_key, dep_result in result.get("details", {}).items():
                    if dep_result.get("status") != "ok":
                        summary_messages.append(f"  - {dep_key}: {dep_result.get('status')}, {dep_result.get('message')}")
    
    final_status = {"overall_status": "ok" if overall_ok else "error", "details": results}
    if not overall_ok:
        logger.warning("Greeum environment diagnosis: Issues found in some areas.")
        for msg in summary_messages:
            logger.warning(msg)
    else:
        logger.info("Greeum environment diagnosis: All systems operational.")
        
    return final_status

if __name__ == '__main__':
    # CLI로 실행 시 간략한 결과 출력
    print("Greeum 환경 진단 도구")
    print("="*30)
    results = check_environment(verbose=True)
    
    print(f"\nPython 버전: {results['details']['python_version']['status']} ({results['details']['python_version']['version']}) - 최소: {results['details']['python_version']['min_required']}")
    print(f"Greeum 버전: {results['details']['greeum_version']['status']} ({results['details']['greeum_version']['version']})")
    print(f"데이터베이스 연결성: {results['details']['database_connectivity']['status']} - {results['details']['database_connectivity']['message']}")
    print(f"기본 임베딩 모델: {results['details']['default_embedding_model']['status']} - {results['details']['default_embedding_model']['message']}")
    
    print("\n의존성 패키지:")
    dep_details = results['details']['dependencies']['details']
    all_deps_ok = True
    for pkg_name, info in dep_details.items():
        print(f"  - {pkg_name}: {info['status']} (설치: {info['installed_version'] or '미설치'}, 필요: {info['required_version']}) - {info['message']}")
        if info['status'] == 'error':
            all_deps_ok = False
    
    print("\n종합 상태:")
    if results['overall_status'] == 'ok':
        print("\033[92m모든 환경 점검 항목이 정상입니다.\033[0m")
    else:
        print("\033[91m일부 환경 점검 항목에서 문제가 발견되었습니다. 상세 내용을 확인하세요.\033[0m") 