from flask import Flask, request, jsonify, render_template
import sys
from pathlib import Path
import uuid
from datetime import datetime
import os

# 상위 디렉터리 추가하여 memory_engine 패키지 임포트
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

from memory_engine import BlockManager, STMManager, CacheManager, PromptWrapper
from memory_engine.text_utils import process_user_input, extract_keywords, generate_simple_embedding

app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')

# 매니저 인스턴스
block_manager = BlockManager()
stm_manager = STMManager()
cache_manager = CacheManager(block_manager=block_manager, stm_manager=stm_manager)
prompt_wrapper = PromptWrapper(cache_manager=cache_manager, stm_manager=stm_manager)

# 웹 인터페이스 라우트
@app.route('/')
def index():
    """웹 인터페이스 메인 페이지"""
    return render_template('index.html')

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """상태 확인"""
    return jsonify({
        "status": "ok",
        "version": "0.2.0",
        "name": "MemoryBlockEngine"
    })

@app.route('/api/v1/blocks', methods=['GET'])
def get_blocks():
    """블록 목록 조회"""
    start_idx = request.args.get('start', type=int)
    end_idx = request.args.get('end', type=int)
    
    blocks = block_manager.get_blocks(start_idx, end_idx)
    return jsonify({"blocks": blocks})

@app.route('/api/v1/blocks/<int:block_id>', methods=['GET'])
def get_block(block_id):
    """특정 블록 조회"""
    block = block_manager.get_block_by_index(block_id)
    if block:
        return jsonify(block)
    return jsonify({"error": "블록을 찾을 수 없습니다."}), 404

@app.route('/api/v1/blocks', methods=['POST'])
def add_block():
    """블록 추가"""
    data = request.json
    
    if not data or 'context' not in data:
        return jsonify({"error": "컨텍스트가 필요합니다."}), 400
    
    context = data.get('context')
    keywords = data.get('keywords')
    tags = data.get('tags')
    embedding = data.get('embedding')
    importance = data.get('importance')
    
    # 처리된 데이터 얻기
    processed = process_user_input(context)
    
    # 클라이언트 데이터 우선 사용
    if keywords:
        processed["keywords"] = keywords
    if tags:
        processed["tags"] = tags
    if embedding:
        processed["embedding"] = embedding
    if importance is not None:
        processed["importance"] = importance
    
    # 블록 추가
    block = block_manager.add_block(
        context=processed["context"],
        keywords=processed["keywords"],
        tags=processed["tags"],
        embedding=processed["embedding"],
        importance=processed["importance"]
    )
    
    return jsonify(block), 201

@app.route('/api/v1/search', methods=['GET'])
def search_blocks():
    """블록 검색"""
    keywords = request.args.get('keywords')
    if not keywords:
        return jsonify({"error": "키워드가 필요합니다."}), 400
    
    keywords_list = keywords.split(',')
    blocks = block_manager.search_by_keywords(keywords_list)
    
    return jsonify({"results": blocks})

@app.route('/api/v1/stm', methods=['GET'])
def get_memories():
    """단기 기억 조회"""
    count = request.args.get('count', 10, type=int)
    memories = stm_manager.get_recent_memories(count=count)
    
    return jsonify({"memories": memories})

@app.route('/api/v1/stm', methods=['POST'])
def add_memory():
    """단기 기억 추가"""
    data = request.json
    
    if not data or 'content' not in data:
        return jsonify({"error": "내용이 필요합니다."}), 400
    
    memory_data = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "content": data.get('content'),
        "speaker": data.get('speaker', 'user')
    }
    
    stm_manager.add_memory(memory_data)
    return jsonify(memory_data), 201

@app.route('/api/v1/stm', methods=['DELETE'])
def clear_memories():
    """단기 기억 초기화"""
    stm_manager.clear_all()
    return jsonify({"message": "단기 기억이 초기화되었습니다."})

@app.route('/api/v1/cache', methods=['GET'])
def get_cache():
    """웨이포인트 캐시 조회"""
    return jsonify({
        "current_context": cache_manager.get_current_context(),
        "waypoints": cache_manager.get_waypoints()
    })

@app.route('/api/v1/cache', methods=['DELETE'])
def clear_cache():
    """웨이포인트 캐시 초기화"""
    cache_manager.clear_cache()
    return jsonify({"message": "웨이포인트 캐시가 초기화되었습니다."})

@app.route('/api/v1/prompt', methods=['POST'])
def generate_prompt():
    """프롬프트 생성"""
    data = request.json
    
    if not data or 'input' not in data:
        return jsonify({"error": "입력 텍스트가 필요합니다."}), 400
    
    user_input = data.get('input')
    system_prompt = data.get('system_prompt', '')
    
    # 입력 텍스트 처리
    embedding = generate_simple_embedding(user_input)
    keywords = extract_keywords(user_input)
    
    # 캐시 업데이트
    blocks = cache_manager.update_cache(user_input, embedding, keywords)
    
    # 프롬프트 생성
    prompt = prompt_wrapper.compose_prompt(user_input, system_prompt)
    
    return jsonify({
        "prompt": prompt,
        "relevant_blocks": blocks
    })

@app.route('/api/v1/verify', methods=['GET'])
def verify_blocks():
    """블록체인 무결성 검증"""
    is_valid = block_manager.verify_blocks()
    
    return jsonify({
        "valid": is_valid,
        "message": "블록체인 무결성 검증 성공" if is_valid else "블록체인 무결성 검증 실패"
    })

@app.route('/api/v1/process', methods=['POST'])
def process_text():
    """텍스트 처리 (키워드, 태그, 임베딩 추출)"""
    data = request.json
    
    if not data or 'text' not in data:
        return jsonify({"error": "텍스트가 필요합니다."}), 400
    
    text = data.get('text')
    result = process_user_input(text)
    
    return jsonify(result)

@app.route('/api/info')
def api_info():
    """API 정보 조회"""
    return jsonify({
        "status": "success",
        "api_version": "0.1.0",
        "name": "Greeum"
    })

if __name__ == '__main__':
    # templates 디렉토리 확인 및 생성
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
        
    # static 디렉토리 확인 및 생성
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    app.run(debug=True, host='0.0.0.0', port=5000) 