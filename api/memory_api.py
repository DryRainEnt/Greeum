from flask import Flask, request, jsonify, render_template
import sys
from pathlib import Path
import uuid
from datetime import datetime
import os

# 상위 디렉터리 추가하여 memory_engine 패키지 임포트
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

from greeum import BlockManager, STMManager, CacheManager, PromptWrapper
from greeum.text_utils import process_user_input, extract_keywords, generate_simple_embedding

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

# 앵커 관리 API 엔드포인트
@app.route('/v1/anchors', methods=['GET'])
def get_anchors():
    """모든 앵커 상태 조회"""
    try:
        from greeum.anchors.manager import AnchorManager
        from pathlib import Path
        
        anchor_path = Path("data/anchors.json")
        if not anchor_path.exists():
            return jsonify({
                "error": "Anchors not initialized",
                "message": "Run bootstrap script to initialize anchors"
            }), 404
        
        anchor_manager = AnchorManager(anchor_path)
        
        # 모든 슬롯 정보 수집
        slots_data = []
        for slot in ['A', 'B', 'C']:
            slot_info = anchor_manager.get_slot_info(slot)
            if slot_info:
                slots_data.append({
                    "slot": slot,
                    "anchor_block_id": slot_info['anchor_block_id'],
                    "hop_budget": slot_info.get('hop_budget', 3),
                    "pinned": slot_info.get('pinned', False),
                    "last_used_ts": slot_info.get('last_used_ts', 0),
                    "summary": slot_info.get('summary', '')
                })
            else:
                slots_data.append({
                    "slot": slot,
                    "anchor_block_id": None,
                    "hop_budget": 3,
                    "pinned": False,
                    "last_used_ts": 0,
                    "summary": ""
                })
        
        # 메타데이터 추가
        try:
            import json
            with open(anchor_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                version = data.get('version', 1)
                updated_at = data.get('updated_at', int(time.time()))
        except:
            version = 1
            updated_at = int(time.time())
        
        return jsonify({
            "version": version,
            "slots": slots_data,
            "updated_at": updated_at,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "error": "Failed to get anchors",
            "message": str(e)
        }), 500

@app.route('/v1/anchors/<slot>', methods=['PATCH'])
def update_anchor(slot):
    """특정 앵커 슬롯 업데이트"""
    if slot not in ['A', 'B', 'C']:
        return jsonify({
            "error": "Invalid slot",
            "message": "Slot must be A, B, or C"
        }), 400
    
    try:
        from greeum.anchors.manager import AnchorManager
        from greeum.core.database_manager import DatabaseManager
        from pathlib import Path
        import time
        
        anchor_path = Path("data/anchors.json")
        if not anchor_path.exists():
            return jsonify({
                "error": "Anchors not initialized",
                "message": "Run bootstrap script to initialize anchors"
            }), 404
        
        # 요청 데이터 파싱
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "No data provided",
                "message": "Request body must contain JSON data"
            }), 400
        
        anchor_manager = AnchorManager(anchor_path)
        
        # 1. 앵커 블록 ID 변경
        if 'anchor_block_id' in data:
            block_id = data['anchor_block_id']
            
            # 블록 존재 여부 확인
            db_manager = DatabaseManager()
            block = db_manager.get_block_by_index(int(block_id))
            
            if not block:
                return jsonify({
                    "error": "Block not found",
                    "message": f"Block ID {block_id} does not exist"
                }), 404
            
            # 임베딩 및 요약 준비
            embedding = block.get('embedding', [0.5] * 128)
            context = block.get('context', '')
            summary = data.get('summary', context[:100] + "..." if len(context) > 100 else context)
            hop_budget = data.get('hop_budget', 3)
            
            # 앵커 이동
            success = anchor_manager.move_anchor(
                slot=slot,
                new_block_id=str(block_id),
                topic_vec=embedding,
                summary=summary,
                hop_budget=hop_budget
            )
            
            if not success:
                return jsonify({
                    "error": "Failed to move anchor",
                    "message": f"Could not set anchor for slot {slot}"
                }), 500
        
        # 2. 홉 예산 변경
        if 'hop_budget' in data:
            hop_budget = data['hop_budget']
            if not (1 <= hop_budget <= 3):
                return jsonify({
                    "error": "Invalid hop budget",
                    "message": "Hop budget must be between 1 and 3"
                }), 400
            
            # 현재 앵커 정보로 업데이트
            slot_info = anchor_manager.get_slot_info(slot)
            if slot_info:
                anchor_manager.move_anchor(
                    slot=slot,
                    new_block_id=slot_info['anchor_block_id'],
                    topic_vec=slot_info.get('topic_vec', [0.5] * 128),
                    summary=slot_info.get('summary', ''),
                    hop_budget=hop_budget
                )
        
        # 3. 핀 상태 변경
        if 'pinned' in data:
            pinned = data['pinned']
            if pinned:
                anchor_manager.pin_anchor(slot)
            else:
                anchor_manager.unpin_anchor(slot)
        
        # 업데이트된 정보 반환
        slot_info = anchor_manager.get_slot_info(slot)
        
        return jsonify({
            "success": True,
            "slot": slot,
            "anchor": {
                "anchor_block_id": slot_info['anchor_block_id'] if slot_info else None,
                "hop_budget": slot_info.get('hop_budget', 3) if slot_info else 3,
                "pinned": slot_info.get('pinned', False) if slot_info else False,
                "last_used_ts": slot_info.get('last_used_ts', 0) if slot_info else 0,
                "summary": slot_info.get('summary', '') if slot_info else ''
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except ValueError as e:
        return jsonify({
            "error": "Invalid data",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Failed to update anchor",
            "message": str(e)
        }), 500

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
    """블록 검색 (앵커 기반 검색 지원)"""
    keywords = request.args.get('keywords')
    query = request.args.get('query', keywords)  # query 파라미터도 지원
    
    if not query:
        return jsonify({"error": "query 또는 keywords 파라미터가 필요합니다."}), 400
    
    # 앵커 기반 검색 파라미터
    slot = request.args.get('slot')  # A, B, C
    radius = request.args.get('radius', 2, type=int)
    fallback = request.args.get('fallback', 'true').lower() == 'true'
    limit = request.args.get('limit', 5, type=int)
    
    try:
        # 앵커 기반 검색 시도
        if slot and slot in ['A', 'B', 'C']:
            from greeum.core.search_engine import SearchEngine
            from greeum.core.database_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            search_engine = SearchEngine(db_manager)
            
            result = search_engine.search(
                query=query,
                top_k=limit,
                slot=slot,
                radius=radius,
                fallback=fallback
            )
            
            return jsonify({
                "results": result.get('blocks', []),
                "metadata": result.get('metadata', {}),
                "search_type": "anchor_based",
                "slot": slot,
                "radius": radius,
                "fallback": fallback
            })
        else:
            # 기존 키워드 기반 검색
            if keywords:
                keywords_list = keywords.split(',')
                blocks = block_manager.search_by_keywords(keywords_list)
            else:
                # 단순한 키워드 분할 검색
                keywords_list = query.split()
                blocks = block_manager.search_by_keywords(keywords_list)
            
            return jsonify({
                "results": blocks,
                "search_type": "keyword_based",
                "keywords": keywords_list
            })
            
    except ImportError:
        # 앵커 시스템이 없는 경우 기존 검색으로 후퇴
        keywords_list = query.split()
        blocks = block_manager.search_by_keywords(keywords_list)
        
        return jsonify({
            "results": blocks,
            "search_type": "fallback_keyword",
            "note": "Anchor-based search not available"
        })
    except Exception as e:
        return jsonify({
            "error": "검색 중 오류가 발생했습니다.",
            "message": str(e)
        }), 500

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

# Anchor 엔드포인트 추가
@app.route('/api/v1/anchors', methods=['GET'])
def get_anchors():
    """Get current anchor states for all slots"""
    try:
        sys.path.insert(0, parent_dir)
        from greeum.anchors import AnchorManager
        
        anchor_path = Path(parent_dir) / "data" / "anchors.json"
        if not anchor_path.exists():
            return jsonify({
                "error": "Anchor system not initialized. Run bootstrap first."
            }), 404
        
        anchor_manager = AnchorManager(anchor_path)
        
        # Get all slot info
        slots = []
        for slot_name in ['A', 'B', 'C']:
            slot_info = anchor_manager.get_slot_info(slot_name)
            if slot_info:
                slots.append({
                    'slot': slot_info['slot'],
                    'anchor_block_id': slot_info['anchor_block_id'],
                    'hop_budget': slot_info['hop_budget'],
                    'pinned': slot_info['pinned'],
                    'last_used_ts': slot_info['last_used_ts'],
                    'summary': slot_info['summary']
                })
        
        # Get metadata
        anchor_data = anchor_manager._load_state()
        
        return jsonify({
            'version': anchor_data.get('version', 1),
            'slots': slots,
            'updated_at': anchor_data.get('updated_at', int(datetime.now().timestamp()))
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to get anchors: {str(e)}"}), 500

@app.route('/api/v1/anchors/<slot>', methods=['PATCH'])
def update_anchor(slot):
    """Update specific anchor slot configuration"""
    if slot not in ['A', 'B', 'C']:
        return jsonify({"error": f"Invalid slot: {slot}. Must be A, B, or C"}), 400
    
    try:
        sys.path.insert(0, parent_dir)
        from greeum.anchors import AnchorManager
        from greeum.core import BlockManager, DatabaseManager
        import numpy as np
        
        update_data = request.get_json() or {}
        
        # Load anchor manager
        anchor_path = Path(parent_dir) / "data" / "anchors.json"
        if not anchor_path.exists():
            return jsonify({
                "error": "Anchor system not initialized. Run bootstrap first."
            }), 404
        
        anchor_manager = AnchorManager(anchor_path)
        
        # Check if slot exists
        current_info = anchor_manager.get_slot_info(slot)
        if not current_info:
            return jsonify({"error": f"Slot {slot} not found"}), 404
        
        # Update anchor block if requested
        if 'anchor_block_id' in update_data:
            block_id = update_data['anchor_block_id']
            
            # Validate block exists
            db_manager = DatabaseManager()
            block_manager_instance = BlockManager(db_manager)
            
            try:
                block_data = block_manager_instance.db_manager.get_block_by_index(int(block_id))
                if not block_data:
                    return jsonify({
                        "error": f"Block #{block_id} does not exist"
                    }), 400
            except ValueError:
                return jsonify({"error": f"Invalid block ID: {block_id}"}), 400
            
            # Move anchor
            block_embedding = np.array(block_data.get('embedding', [0.0] * 128))
            anchor_manager.move_anchor(slot, block_id, block_embedding)
        
        # Update hop budget if requested
        if 'hop_budget' in update_data:
            hop_budget = update_data['hop_budget']
            if not isinstance(hop_budget, int) or not (1 <= hop_budget <= 3):
                return jsonify({"error": "hop_budget must be integer between 1-3"}), 400
            anchor_manager.set_hop_budget(slot, hop_budget)
        
        # Update pin status if requested
        if 'pinned' in update_data:
            pinned = update_data['pinned']
            if not isinstance(pinned, bool):
                return jsonify({"error": "pinned must be boolean"}), 400
            
            if pinned:
                anchor_manager.pin_anchor(slot)
            else:
                anchor_manager.unpin_anchor(slot)
        
        # Return updated state
        updated_info = anchor_manager.get_slot_info(slot)
        return jsonify({
            'slot': updated_info['slot'],
            'anchor_block_id': updated_info['anchor_block_id'],
            'hop_budget': updated_info['hop_budget'],
            'pinned': updated_info['pinned'],
            'last_used_ts': updated_info['last_used_ts'],
            'summary': updated_info['summary']
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to update anchor: {str(e)}"}), 500

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