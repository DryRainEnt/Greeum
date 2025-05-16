from flask import Flask, request, jsonify
import logging
from typing import Dict, Any, List, Optional, Union
import os

# MemoryEngine 관련 모듈 임포트
from memory_engine.block_manager import BlockManager
from memory_engine.stm_manager import STMManager
from memory_engine.cache_manager import CacheManager
from memory_engine.prompt_wrapper import PromptWrapper

class MCPService:
    """
    Cursor MCP(Model Control Protocol) 서비스
    MemoryEngine과 MCP 프로토콜을 연결하는 서비스 구현
    """
    
    def __init__(self, data_dir: str = "./data", port: int = 8000):
        """
        MCP 서비스 초기화
        
        Args:
            data_dir: 데이터 디렉토리 경로
            port: 서비스 포트
        """
        self.app = Flask("MemoryEngineMCP")
        self.port = port
        self.data_dir = data_dir
        self.api_keys = {}
        
        # 로깅 설정
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("MCPService")
        
        # MemoryEngine 컴포넌트 초기화
        os.makedirs(data_dir, exist_ok=True)
        self.block_manager = BlockManager(data_dir=data_dir)
        self.stm_manager = STMManager(data_dir=data_dir)
        self.cache_manager = CacheManager(data_dir=data_dir)
        self.prompt_wrapper = PromptWrapper()
        
        # API 라우트 설정
        self._setup_routes()
        
    def _setup_routes(self):
        """
        API 라우트 설정
        """
        # API 키 검증 데코레이터
        def require_api_key(f):
            def wrapper(*args, **kwargs):
                auth_header = request.headers.get("Authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    return jsonify({"error": "API 키가 필요합니다."}), 401
                
                api_key = auth_header.split("Bearer ")[1]
                if api_key not in self.api_keys:
                    return jsonify({"error": "유효하지 않은 API 키입니다."}), 401
                
                return f(*args, **kwargs)
            wrapper.__name__ = f.__name__
            return wrapper
        
        # 메모리 관리 API
        @self.app.route("/api/mcp/memory", methods=["POST"])
        @require_api_key
        def memory_api():
            data = request.json
            action = data.get("action")
            
            if action == "add":
                memory_content = data.get("memory_content")
                if not memory_content:
                    return jsonify({"error": "메모리 내용이 필요합니다."}), 400
                
                # 장기 기억에 추가
                memory_id = self.block_manager.add_memory(memory_content)
                # 단기 기억에도 추가
                self.stm_manager.add_memory(memory_content, ttl=3600)  # 1시간 TTL
                # 캐시 업데이트
                self.cache_manager.update_cache()
                
                return jsonify({"success": True, "memory_id": memory_id})
            
            elif action == "get":
                memory_id = data.get("memory_id")
                if not memory_id:
                    return jsonify({"error": "메모리 ID가 필요합니다."}), 400
                
                memory = self.block_manager.get_memory(memory_id)
                if not memory:
                    return jsonify({"error": "메모리를 찾을 수 없습니다."}), 404
                
                return jsonify({"success": True, "memory": memory})
            
            elif action == "query":
                query = data.get("query")
                limit = data.get("limit", 10)
                if not query:
                    return jsonify({"error": "쿼리가 필요합니다."}), 400
                
                # 관련 기억 검색
                results = self.cache_manager.search(query, limit=limit)
                # 단기 기억에서도 검색
                stm_results = self.stm_manager.search(query, limit=limit)
                
                # 중복 제거 및 결합
                all_results = results + [r for r in stm_results if r["id"] not in [x["id"] for x in results]]
                all_results = all_results[:limit]  # 제한 개수만큼 반환
                
                return jsonify({"success": True, "results": all_results})
            
            elif action == "update":
                memory_id = data.get("memory_id")
                memory_content = data.get("memory_content")
                if not memory_id or not memory_content:
                    return jsonify({"error": "메모리 ID와 내용이 필요합니다."}), 400
                
                success = self.block_manager.update_memory(memory_id, memory_content)
                if not success:
                    return jsonify({"error": "메모리 업데이트에 실패했습니다."}), 500
                
                # 캐시 업데이트
                self.cache_manager.update_cache()
                
                return jsonify({"success": True})
            
            elif action == "delete":
                memory_id = data.get("memory_id")
                if not memory_id:
                    return jsonify({"error": "메모리 ID가 필요합니다."}), 400
                
                success = self.block_manager.delete_memory(memory_id)
                if not success:
                    return jsonify({"error": "메모리 삭제에 실패했습니다."}), 500
                
                # 캐시 업데이트
                self.cache_manager.update_cache()
                
                return jsonify({"success": True})
            
            else:
                return jsonify({"error": f"알 수 없는 액션: {action}"}), 400
        
        # API 키 관리 API
        @self.app.route("/api/mcp/admin/api_key", methods=["POST"])
        def manage_api_key():
            data = request.json
            action = data.get("action")
            admin_key = data.get("admin_key")
            
            # 관리자 키 검증 (실제 구현에서는 환경 변수 등으로 보안 강화)
            if not admin_key or admin_key != os.environ.get("ADMIN_KEY", "admin_secret"):
                return jsonify({"error": "관리자 권한이 필요합니다."}), 401
            
            if action == "create":
                # 새 API 키 생성
                import uuid
                new_key = str(uuid.uuid4())
                self.api_keys[new_key] = {
                    "created_at": str(__import__("datetime").datetime.now()),
                    "name": data.get("name", "API Key")
                }
                return jsonify({"success": True, "api_key": new_key})
            
            elif action == "revoke":
                # API 키 폐기
                api_key = data.get("api_key")
                if not api_key or api_key not in self.api_keys:
                    return jsonify({"error": "유효하지 않은 API 키입니다."}), 400
                
                del self.api_keys[api_key]
                return jsonify({"success": True})
            
            elif action == "list":
                # API 키 목록
                keys_info = {k: v for k, v in self.api_keys.items()}
                return jsonify({"success": True, "keys": keys_info})
            
            else:
                return jsonify({"error": f"알 수 없는 액션: {action}"}), 400
    
    def start(self):
        """
        MCP 서비스 시작
        """
        self.logger.info(f"MCP 서비스 시작: http://localhost:{self.port}")
        self.app.run(host="0.0.0.0", port=self.port, debug=False)

# CLI 실행용
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="MemoryEngine MCP 서비스")
    parser.add_argument("--data-dir", default="./data", help="데이터 디렉토리 경로")
    parser.add_argument("--port", type=int, default=8000, help="서비스 포트")
    
    args = parser.parse_args()
    
    service = MCPService(data_dir=args.data_dir, port=args.port)
    service.start()

if __name__ == "__main__":
    main() 