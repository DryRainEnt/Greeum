#!/usr/bin/env python3
"""
MemoryBlockEngine REST API 서버
"""

import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_restx import Api, Resource, fields, reqparse
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("memory_api")

# 앱 초기화
app = Flask(__name__)
CORS(app)  # 크로스 오리진 요청 허용
api = Api(app, version='0.1.0', title='MemoryBlockEngine API',
         description='LLM 독립적 메모리 시스템 API')

# 네임스페이스 정의
ns_memory = api.namespace('memory', description='기억 관리 작업')
ns_search = api.namespace('search', description='기억 검색 작업')
ns_evolution = api.namespace('evolution', description='기억 진화 작업')
ns_knowledge = api.namespace('knowledge', description='지식 그래프 작업')

# 전역 데이터베이스 관리자
db_manager = None

def get_db():
    """데이터베이스 매니저 초기화 및 반환"""
    global db_manager
    if db_manager is None:
        try:
            # 환경 변수에서 DB 경로 가져오기 (없으면 기본값 사용)
            db_path = os.environ.get("MEMORY_DB_PATH", "data/memory.db")
            data_dir = os.path.dirname(db_path)
            if data_dir and not os.path.exists(data_dir):
                os.makedirs(data_dir)
                
            # 데이터베이스 매니저 초기화
            from memory_engine import DatabaseManager
            db_manager = DatabaseManager(db_path)
            
            # 임베딩 모델 초기화
            try:
                from memory_engine.embedding_models import SimpleEmbeddingModel, register_embedding_model
                model = SimpleEmbeddingModel()
                register_embedding_model("default", model, set_as_default=True)
                logger.info("임베딩 모델 초기화 완료")
            except ImportError:
                logger.warning("임베딩 모델 초기화 실패")
            
            logger.info(f"데이터베이스 매니저 초기화 완료 ({db_path})")
        except Exception as e:
            logger.error(f"데이터베이스 초기화 오류: {e}")
            raise
    
    return db_manager

# API 모델 정의
memory_model = api.model('Memory', {
    'context': fields.String(required=True, description='기억 내용'),
    'keywords': fields.List(fields.String, description='키워드 목록'),
    'tags': fields.List(fields.String, description='태그 목록'),
    'importance': fields.Float(description='중요도 (0~1)'),
})

search_model = api.model('Search', {
    'query': fields.String(required=True, description='검색 쿼리'),
    'mode': fields.String(description='검색 모드 (embedding, keyword, temporal, hybrid)'),
    'limit': fields.Integer(description='결과 제한 개수')
})

revision_model = api.model('Revision', {
    'original_block_index': fields.Integer(required=True, description='원본 블록 인덱스'),
    'new_context': fields.String(required=True, description='새 내용'),
    'reason': fields.String(description='변경 이유')
})

entity_model = api.model('Entity', {
    'name': fields.String(required=True, description='엔티티 이름'),
    'type': fields.String(required=True, description='엔티티 유형'),
    'confidence': fields.Float(description='신뢰도')
})

# 기억 관리 API 엔드포인트
@ns_memory.route('/')
class MemoryList(Resource):
    @ns_memory.doc('list_memories')
    def get(self):
        """최근 기억 목록 조회"""
        try:
            # 쿼리 매개변수
            parser = reqparse.RequestParser()
            parser.add_argument('limit', type=int, default=10, help='반환할 최대 기억 수')
            parser.add_argument('offset', type=int, default=0, help='시작 오프셋')
            args = parser.parse_args()
            
            db = get_db()
            blocks = db.get_blocks(limit=args['limit'], offset=args['offset'])
            
            return jsonify({
                'status': 'success',
                'count': len(blocks),
                'data': blocks
            })
        except Exception as e:
            logger.error(f"기억 목록 조회 오류: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @ns_memory.doc('create_memory')
    @ns_memory.expect(memory_model)
    def post(self):
        """새 기억 생성"""
        try:
            data = request.json
            
            # 필수 필드 확인
            if 'context' not in data:
                return jsonify({
                    'status': 'error',
                    'message': '필수 필드 누락: context'
                }), 400
            
            # 텍스트 처리
            from memory_engine.text_utils import process_user_input
            
            # 사용자 입력 처리
            result = process_user_input(data['context'])
            
            # 사용자 제공 값 우선 적용
            if 'keywords' in data:
                result['keywords'] = data['keywords']
            if 'tags' in data:
                result['tags'] = data['tags']
            if 'importance' in data:
                result['importance'] = data['importance']
            
            # 타임스탬프 및 해시 추가
            from hashlib import sha256
            timestamp = datetime.now().isoformat()
            result['timestamp'] = timestamp
            
            # 데이터베이스 연결
            db = get_db()
            
            # 블록 인덱스 생성 (마지막 블록 + 1)
            last_block = db.get_blocks(limit=1)
            block_index = 0
            if last_block:
                block_index = last_block[0].get('block_index', -1) + 1
            
            # 이전 해시 가져오기
            prev_hash = ""
            if block_index > 0:
                prev_block = db.get_block(block_index - 1)
                if prev_block:
                    prev_hash = prev_block.get('hash', '')
            
            # 해시 계산
            hash_data = {
                'block_index': block_index,
                'timestamp': timestamp,
                'context': data['context'],
                'prev_hash': prev_hash
            }
            hash_str = json.dumps(hash_data, sort_keys=True)
            hash_value = sha256(hash_str.encode()).hexdigest()
            
            # 최종 블록 데이터
            block_data = {
                'block_index': block_index,
                'timestamp': timestamp,
                'context': data['context'],
                'keywords': result.get('keywords', []),
                'tags': result.get('tags', []),
                'embedding': result.get('embedding', []),
                'importance': result.get('importance', 0.5),
                'hash': hash_value,
                'prev_hash': prev_hash
            }
            
            # 데이터베이스에 추가
            added_index = db.add_block(block_data)
            
            return jsonify({
                'status': 'success',
                'block_index': added_index,
                'data': block_data
            })
        except Exception as e:
            logger.error(f"기억 생성 오류: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

@ns_memory.route('/<int:block_index>')
@ns_memory.param('block_index', '블록 인덱스')
class Memory(Resource):
    @ns_memory.doc('get_memory')
    def get(self, block_index):
        """특정 기억 조회"""
        try:
            db = get_db()
            block = db.get_block(block_index)
            
            if not block:
                return jsonify({
                    'status': 'error',
                    'message': f'블록 {block_index}를 찾을 수 없습니다.'
                }), 404
            
            return jsonify({
                'status': 'success',
                'data': block
            })
        except Exception as e:
            logger.error(f"기억 조회 오류: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

# 검색 API 엔드포인트
@ns_search.route('/')
class SearchMemory(Resource):
    @ns_search.doc('search_memories')
    @ns_search.expect(search_model)
    def post(self):
        """기억 검색"""
        try:
            data = request.json
            
            # 필수 필드 확인
            if 'query' not in data:
                return jsonify({
                    'status': 'error',
                    'message': '필수 필드 누락: query'
                }), 400
                
            query = data['query']
            mode = data.get('mode', 'hybrid')
            limit = data.get('limit', 5)
            
            db = get_db()
            
            if mode == 'embedding':
                # 임베딩 검색
                try:
                    from memory_engine import get_embedding
                    embedding = get_embedding(query)
                    blocks = db.search_blocks_by_embedding(embedding, top_k=limit)
                    search_info = {'type': 'embedding'}
                except ImportError:
                    return jsonify({
                        'status': 'error',
                        'message': '임베딩 모듈을 사용할 수 없습니다.'
                    }), 500
            elif mode == 'keyword':
                # 키워드 검색
                keywords = query.split()
                blocks = db.search_blocks_by_keyword(keywords, limit=limit)
                search_info = {'type': 'keyword', 'keywords': keywords}
            elif mode == 'temporal':
                # 시간적 검색
                try:
                    from memory_engine import TemporalReasoner
                    reasoner = TemporalReasoner(db)
                    result = reasoner.search_by_time_reference(query)
                    blocks = result.get('blocks', [])
                    search_info = {
                        'type': 'temporal',
                        'time_ref': result.get('time_ref'),
                        'time_range': result.get('search_range')
                    }
                except ImportError:
                    return jsonify({
                        'status': 'error',
                        'message': '시간적 추론 모듈을 사용할 수 없습니다.'
                    }), 500
            elif mode == 'hybrid':
                # 하이브리드 검색
                try:
                    from memory_engine import TemporalReasoner, get_embedding
                    reasoner = TemporalReasoner(db)
                    embedding = get_embedding(query)
                    keywords = query.split()
                    result = reasoner.hybrid_search(query, embedding, keywords, top_k=limit)
                    blocks = result.get('blocks', [])
                    search_info = {
                        'type': 'hybrid',
                        'weights': result.get('weights'),
                        'time_info': result.get('time_info')
                    }
                except ImportError:
                    return jsonify({
                        'status': 'error',
                        'message': '하이브리드 검색 모듈을 사용할 수 없습니다.'
                    }), 500
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'지원하지 않는 검색 모드: {mode}'
                }), 400
            
            return jsonify({
                'status': 'success',
                'query': query,
                'search_info': search_info,
                'count': len(blocks),
                'data': blocks
            })
        except Exception as e:
            logger.error(f"검색 오류: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

# 기억 진화 API 엔드포인트
@ns_evolution.route('/revisions')
class MemoryRevision(Resource):
    @ns_evolution.doc('create_revision')
    @ns_evolution.expect(revision_model)
    def post(self):
        """기억 수정본 생성"""
        try:
            data = request.json
            
            # 필수 필드 확인
            if 'original_block_index' not in data:
                return jsonify({
                    'status': 'error',
                    'message': '필수 필드 누락: original_block_index'
                }), 400
            if 'new_context' not in data:
                return jsonify({
                    'status': 'error',
                    'message': '필수 필드 누락: new_context'
                }), 400
                
            db = get_db()
            
            try:
                from memory_engine import MemoryEvolutionManager
                evolution_manager = MemoryEvolutionManager(db)
                
                revision = evolution_manager.create_memory_revision(
                    original_block_index=data['original_block_index'],
                    new_context=data['new_context'],
                    reason=data.get('reason', '내용 업데이트')
                )
                
                if not revision:
                    return jsonify({
                        'status': 'error',
                        'message': '수정본 생성 실패'
                    }), 500
                
                return jsonify({
                    'status': 'success',
                    'block_index': revision.get('block_index'),
                    'data': revision
                })
            except ImportError:
                return jsonify({
                    'status': 'error',
                    'message': '기억 진화 모듈을 사용할 수 없습니다.'
                }), 500
        except Exception as e:
            logger.error(f"수정본 생성 오류: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

@ns_evolution.route('/revisions/<int:block_index>')
@ns_evolution.param('block_index', '블록 인덱스')
class RevisionChain(Resource):
    @ns_evolution.doc('get_revision_chain')
    def get(self, block_index):
        """수정 이력 조회"""
        try:
            db = get_db()
            
            try:
                from memory_engine import MemoryEvolutionManager
                evolution_manager = MemoryEvolutionManager(db)
                
                revisions = evolution_manager.get_revision_chain(block_index)
                
                if not revisions:
                    return jsonify({
                        'status': 'error',
                        'message': f'블록 {block_index}의 수정 이력을 찾을 수 없습니다.'
                    }), 404
                
                return jsonify({
                    'status': 'success',
                    'count': len(revisions),
                    'data': revisions
                })
            except ImportError:
                return jsonify({
                    'status': 'error',
                    'message': '기억 진화 모듈을 사용할 수 없습니다.'
                }), 500
        except Exception as e:
            logger.error(f"수정 이력 조회 오류: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

# 지식 그래프 API 엔드포인트
@ns_knowledge.route('/entities')
class Entities(Resource):
    @ns_knowledge.doc('search_entities')
    def get(self):
        """엔티티 검색"""
        try:
            # 쿼리 매개변수
            parser = reqparse.RequestParser()
            parser.add_argument('query', required=True, help='검색할 엔티티 이름')
            parser.add_argument('type', help='엔티티 유형 필터')
            parser.add_argument('limit', type=int, default=10, help='반환할 최대 엔티티 수')
            args = parser.parse_args()
            
            db = get_db()
            
            try:
                from memory_engine import KnowledgeGraphManager
                kg_manager = KnowledgeGraphManager(db)
                
                entities = kg_manager.search_entities(
                    query=args['query'],
                    entity_type=args['type'],
                    limit=args['limit']
                )
                
                return jsonify({
                    'status': 'success',
                    'count': len(entities),
                    'data': entities
                })
            except ImportError:
                return jsonify({
                    'status': 'error',
                    'message': '지식 그래프 모듈을 사용할 수 없습니다.'
                }), 500
        except Exception as e:
            logger.error(f"엔티티 검색 오류: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @ns_knowledge.doc('create_entity')
    @ns_knowledge.expect(entity_model)
    def post(self):
        """엔티티 생성"""
        try:
            data = request.json
            
            # 필수 필드 확인
            if 'name' not in data:
                return jsonify({
                    'status': 'error',
                    'message': '필수 필드 누락: name'
                }), 400
            if 'type' not in data:
                return jsonify({
                    'status': 'error',
                    'message': '필수 필드 누락: type'
                }), 400
                
            db = get_db()
            
            try:
                from memory_engine import KnowledgeGraphManager
                kg_manager = KnowledgeGraphManager(db)
                
                entity_id = kg_manager.add_entity_to_graph(
                    name=data['name'],
                    entity_type=data['type'],
                    confidence=data.get('confidence', 0.7)
                )
                
                if not entity_id:
                    return jsonify({
                        'status': 'error',
                        'message': '엔티티 생성 실패'
                    }), 500
                
                entity = kg_manager.get_entity(entity_id)
                
                return jsonify({
                    'status': 'success',
                    'entity_id': entity_id,
                    'data': entity
                })
            except ImportError:
                return jsonify({
                    'status': 'error',
                    'message': '지식 그래프 모듈을 사용할 수 없습니다.'
                }), 500
        except Exception as e:
            logger.error(f"엔티티 생성 오류: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

@ns_knowledge.route('/entities/<int:entity_id>')
@ns_knowledge.param('entity_id', '엔티티 ID')
class Entity(Resource):
    @ns_knowledge.doc('get_entity_relationships')
    def get(self, entity_id):
        """엔티티 및 관계 조회"""
        try:
            db = get_db()
            
            try:
                from memory_engine import KnowledgeGraphManager
                kg_manager = KnowledgeGraphManager(db)
                
                result = kg_manager.get_entity_relationships(entity_id)
                
                if 'error' in result:
                    return jsonify({
                        'status': 'error',
                        'message': result['error']
                    }), 404
                
                return jsonify({
                    'status': 'success',
                    'data': result
                })
            except ImportError:
                return jsonify({
                    'status': 'error',
                    'message': '지식 그래프 모듈을 사용할 수 없습니다.'
                }), 500
        except Exception as e:
            logger.error(f"엔티티 관계 조회 오류: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

# 루트 엔드포인트
@app.route('/')
def index():
    """API 정보 페이지"""
    return jsonify({
        'name': 'MemoryBlockEngine API',
        'version': '0.1.0',
        'description': 'LLM 독립적 메모리 시스템 API',
        'endpoints': {
            'memory': '/memory',
            'search': '/search',
            'evolution': '/evolution',
            'knowledge': '/knowledge'
        },
        'docs': '/swagger'
    })

if __name__ == '__main__':
    # 로컬 개발 시 사용할 포트
    port = int(os.environ.get("PORT", 8000))
    
    # 서버 실행
    app.run(debug=True, host='0.0.0.0', port=port) 