from typing import List, Dict, Any, Optional, Set, Tuple
import json
import re
from datetime import datetime

class KnowledgeGraphManager:
    """지식 그래프 관리 클래스"""
    
    def __init__(self, db_manager=None):
        """
        지식 그래프 관리자 초기화
        
        Args:
            db_manager: 데이터베이스 관리자 (없으면 작동 불가)
        """
        self.db_manager = db_manager
        self.entity_types = {
            "PERSON": "사람",
            "ORG": "조직",
            "LOC": "장소",
            "DATE": "날짜",
            "TIME": "시간",
            "MONEY": "금액",
            "PERCENT": "비율",
            "PRODUCT": "제품",
            "EVENT": "이벤트",
            "WORK_OF_ART": "작품",
            "CONCEPT": "개념",
            "TECH": "기술"
        }
        
        # 관계 유형 정의
        self.relation_types = {
            "관련됨": 0.5,  # 일반적인 관련성
            "소속": 0.7,    # 사람-조직
            "위치": 0.7,    # 개체-장소
            "생성": 0.7,    # 사람-작품/제품
            "사용": 0.6,    # 사람-제품/기술
            "참여": 0.6,    # 사람-이벤트
            "포함": 0.6,    # 상위-하위 개념
            "발생": 0.7     # 이벤트-시간/장소
        }
        
        # 초기화 시 스키마 확인
        if db_manager:
            self._ensure_graph_schemas()
    
    def _ensure_graph_schemas(self):
        """그래프 관련 스키마 확인 및 생성"""
        if not self.db_manager or not hasattr(self.db_manager, "conn"):
            return
            
        cursor = self.db_manager.conn.cursor()
        
        # 엔티티 테이블
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS entities (
            entity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            first_seen_block INTEGER,
            confidence REAL DEFAULT 0.7,
            FOREIGN KEY (first_seen_block) REFERENCES blocks(block_index),
            UNIQUE(name, type)
        )
        ''')
        
        # 관계 테이블
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS relationships (
            rel_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_entity INTEGER NOT NULL,
            target_entity INTEGER NOT NULL,
            relationship_type TEXT NOT NULL,
            confidence REAL DEFAULT 0.7,
            source_block INTEGER,
            FOREIGN KEY (source_entity) REFERENCES entities(entity_id),
            FOREIGN KEY (target_entity) REFERENCES entities(entity_id),
            FOREIGN KEY (source_block) REFERENCES blocks(block_index),
            UNIQUE(source_entity, target_entity, relationship_type)
        )
        ''')
        
        # 인덱스 생성
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_entity_name ON entities(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_relationship_type ON relationships(relationship_type)')
        
        self.db_manager.conn.commit()
    
    def extract_simple_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        간단한 규칙 기반 엔티티 추출 (NER 모델 없을 때)
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            추출된 엔티티 목록
        """
        entities = []
        
        # 1. 인물 패턴 (이름 뒤에 씨, 님 등이 붙는 경우)
        person_patterns = [
            r'([가-힣]{2,4})\s*씨',
            r'([가-힣]{2,4})\s*님',
            r'([가-힣]{2,4})\s*교수',
            r'([가-힣]{2,4})\s*박사',
            r'([가-힣]{2,4})\s*선생님'
        ]
        
        for pattern in person_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(1)
                entities.append({
                    "name": name,
                    "type": "사람",
                    "char_start": match.start(1),
                    "char_end": match.end(1),
                    "confidence": 0.8
                })
        
        # 2. 조직 패턴 (회사, 대학 등)
        org_patterns = [
            r'([가-힣a-zA-Z0-9]+대학교)',
            r'([가-힣a-zA-Z0-9]+\s*(주식회사|회사))',
            r'([가-힣a-zA-Z0-9]+\s*(연구소|학교|협회|재단))'
        ]
        
        for pattern in org_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(1)
                entities.append({
                    "name": name,
                    "type": "조직",
                    "char_start": match.start(1),
                    "char_end": match.end(1),
                    "confidence": 0.7
                })
        
        # 3. 장소 패턴
        loc_patterns = [
            r'([가-힣]+시)',
            r'([가-힣]+도)',
            r'([가-힣]+군)',
            r'([가-힣]+구)'
        ]
        
        for pattern in loc_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(1)
                if len(name) > 1:  # 1글자 지명 무시
                    entities.append({
                        "name": name,
                        "type": "장소",
                        "char_start": match.start(1),
                        "char_end": match.end(1),
                        "confidence": 0.6
                    })
        
        # 4. 날짜 패턴
        date_patterns = [
            r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일',
            r'(\d{4})-(\d{2})-(\d{2})',
            r'(\d{4})/(\d{1,2})/(\d{1,2})'
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append({
                    "name": match.group(0),
                    "type": "날짜",
                    "char_start": match.start(),
                    "char_end": match.end(),
                    "confidence": 0.9
                })
        
        # 5. 기술/제품 패턴 (단순 예시)
        tech_patterns = [
            r'([가-힣a-zA-Z0-9]+\s*(기술|시스템))',
            r'([a-zA-Z0-9]+[\.][a-zA-Z0-9]+)',  # 프로그래밍 언어, 라이브러리 등
            r'([a-zA-Z][a-zA-Z0-9]*\s*[0-9]+)'  # 제품명 패턴 (iPhone 12 등)
        ]
        
        for pattern in tech_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(1)
                entities.append({
                    "name": name,
                    "type": "기술" if "기술" in name else "제품",
                    "char_start": match.start(1),
                    "char_end": match.end(1),
                    "confidence": 0.6
                })
        
        # 중복 제거
        unique_entities = []
        seen = set()
        
        for entity in entities:
            key = (entity["name"], entity["type"])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def add_entity_to_graph(self, name: str, entity_type: str, 
                           block_index: Optional[int] = None,
                           confidence: float = 0.7) -> Optional[int]:
        """
        엔티티를 그래프에 추가
        
        Args:
            name: 엔티티 이름
            entity_type: 엔티티 유형
            block_index: 엔티티가 처음 발견된 블록 인덱스
            confidence: 신뢰도 (0~1)
            
        Returns:
            엔티티 ID (실패 시 None)
        """
        if not self.db_manager:
            return None
            
        cursor = self.db_manager.conn.cursor()
        
        # 기존 엔티티 확인
        cursor.execute(
            "SELECT entity_id FROM entities WHERE name = ? AND type = ?", 
            (name, entity_type)
        )
        
        result = cursor.fetchone()
        
        if result:
            # 기존 엔티티 발견
            entity_id = result[0]
            
            # 필요시 신뢰도 업데이트
            cursor.execute(
                "UPDATE entities SET confidence = MAX(confidence, ?) WHERE entity_id = ?",
                (confidence, entity_id)
            )
        else:
            # 새 엔티티 추가
            cursor.execute(
                "INSERT INTO entities (name, type, first_seen_block, confidence) VALUES (?, ?, ?, ?)",
                (name, entity_type, block_index, confidence)
            )
            entity_id = cursor.lastrowid
        
        self.db_manager.conn.commit()
        return entity_id
    
    def add_relationship(self, source_entity_id: int, target_entity_id: int, 
                        relationship_type: str, block_index: Optional[int] = None,
                        confidence: Optional[float] = None) -> Optional[int]:
        """
        관계를 그래프에 추가
        
        Args:
            source_entity_id: 출발 엔티티 ID
            target_entity_id: 도착 엔티티 ID
            relationship_type: 관계 유형
            block_index: 관계가 발견된 블록 인덱스
            confidence: 신뢰도 (0~1)
            
        Returns:
            관계 ID (실패 시 None)
        """
        if not self.db_manager:
            return None
            
        # 기본 신뢰도 설정
        if confidence is None:
            confidence = self.relation_types.get(relationship_type, 0.5)
        
        cursor = self.db_manager.conn.cursor()
        
        # 기존 관계 확인
        cursor.execute(
            """SELECT rel_id, confidence FROM relationships 
               WHERE source_entity = ? AND target_entity = ? AND relationship_type = ?""",
            (source_entity_id, target_entity_id, relationship_type)
        )
        
        result = cursor.fetchone()
        
        if result:
            # 기존 관계 발견, 신뢰도 업데이트
            rel_id, old_confidence = result
            new_confidence = max(old_confidence, confidence)
            
            cursor.execute(
                "UPDATE relationships SET confidence = ? WHERE rel_id = ?",
                (new_confidence, rel_id)
            )
        else:
            # 새 관계 추가
            cursor.execute(
                """INSERT INTO relationships 
                   (source_entity, target_entity, relationship_type, confidence, source_block)
                   VALUES (?, ?, ?, ?, ?)""",
                (source_entity_id, target_entity_id, relationship_type, confidence, block_index)
            )
            rel_id = cursor.lastrowid
        
        self.db_manager.conn.commit()
        return rel_id
    
    def process_block_for_graph(self, block: Dict[str, Any]) -> Dict[str, Any]:
        """
        블록 텍스트에서 엔티티 및 관계 추출하여 그래프 구축
        
        Args:
            block: 메모리 블록
            
        Returns:
            처리 결과
        """
        if not self.db_manager:
            return {"error": "데이터베이스 관리자가 설정되지 않았습니다."}
        
        block_index = block.get("block_index")
        context = block.get("context", "")
        
        # 1. 엔티티 추출
        entities = self.extract_simple_entities(context)
        
        # 2. 엔티티를 그래프에 추가
        entities_with_ids = []
        for entity in entities:
            entity_id = self.add_entity_to_graph(
                name=entity["name"],
                entity_type=entity["type"],
                block_index=block_index,
                confidence=entity.get("confidence", 0.7)
            )
            
            if entity_id:
                entity["entity_id"] = entity_id
                entities_with_ids.append(entity)
        
        # 3. 관계 추론 및 추가
        relationships = []
        for i, entity1 in enumerate(entities_with_ids):
            for entity2 in entities_with_ids[i+1:]:
                # 엔티티 유형에 따른 관계 추론
                rel_type = self._infer_relationship_type(entity1, entity2)
                if rel_type:
                    rel_id = self.add_relationship(
                        source_entity_id=entity1["entity_id"],
                        target_entity_id=entity2["entity_id"],
                        relationship_type=rel_type,
                        block_index=block_index
                    )
                    
                    if rel_id:
                        relationships.append({
                            "rel_id": rel_id,
                            "source": entity1["name"],
                            "source_type": entity1["type"],
                            "target": entity2["name"],
                            "target_type": entity2["type"],
                            "relationship_type": rel_type
                        })
        
        return {
            "block_index": block_index,
            "entities": entities_with_ids,
            "relationships": relationships
        }
    
    def _infer_relationship_type(self, entity1: Dict[str, Any], entity2: Dict[str, Any]) -> Optional[str]:
        """
        엔티티 유형 조합에 따른 관계 추론
        
        Args:
            entity1: 첫 번째 엔티티
            entity2: 두 번째 엔티티
            
        Returns:
            추론된 관계 유형 (없으면 None)
        """
        type1 = entity1.get("type")
        type2 = entity2.get("type")
        
        # 엔티티 유형 조합에 따른 관계 추론
        if type1 == "사람" and type2 == "조직":
            return "소속"
        elif type1 == "조직" and type2 == "사람":
            return "소속"
        elif (type1 == "사람" or type1 == "조직") and type2 == "제품":
            return "생성"
        elif (type1 == "사람" or type1 == "조직") and type2 == "기술":
            return "사용"
        elif type1 == "사람" and type2 == "이벤트":
            return "참여"
        elif (type1 == "사람" or type1 == "제품" or type1 == "조직") and type2 == "장소":
            return "위치"
        elif type1 == "이벤트" and (type2 == "시간" or type2 == "날짜"):
            return "발생"
        
        # 일반적인 관계
        return "관련됨"
    
    def get_entity(self, entity_id: int) -> Optional[Dict[str, Any]]:
        """
        엔티티 조회
        
        Args:
            entity_id: 엔티티 ID
            
        Returns:
            엔티티 정보 (없으면 None)
        """
        if not self.db_manager:
            return None
            
        cursor = self.db_manager.conn.cursor()
        
        cursor.execute(
            "SELECT entity_id, name, type, first_seen_block, confidence FROM entities WHERE entity_id = ?",
            (entity_id,)
        )
        
        row = cursor.fetchone()
        if not row:
            return None
            
        return {
            "entity_id": row[0],
            "name": row[1],
            "type": row[2],
            "first_seen_block": row[3],
            "confidence": row[4]
        }
    
    def search_entities(self, query: str, entity_type: Optional[str] = None, 
                       limit: int = 10) -> List[Dict[str, Any]]:
        """
        엔티티 검색
        
        Args:
            query: 검색어
            entity_type: 엔티티 유형 필터 (옵션)
            limit: 최대 결과 수
            
        Returns:
            검색된 엔티티 목록
        """
        if not self.db_manager:
            return []
            
        cursor = self.db_manager.conn.cursor()
        
        if entity_type:
            cursor.execute(
                """SELECT entity_id, name, type, first_seen_block, confidence 
                   FROM entities 
                   WHERE name LIKE ? AND type = ?
                   ORDER BY confidence DESC
                   LIMIT ?""",
                (f"%{query}%", entity_type, limit)
            )
        else:
            cursor.execute(
                """SELECT entity_id, name, type, first_seen_block, confidence 
                   FROM entities 
                   WHERE name LIKE ?
                   ORDER BY confidence DESC
                   LIMIT ?""",
                (f"%{query}%", limit)
            )
        
        entities = []
        for row in cursor.fetchall():
            entities.append({
                "entity_id": row[0],
                "name": row[1],
                "type": row[2],
                "first_seen_block": row[3],
                "confidence": row[4]
            })
            
        return entities
    
    def get_entity_relationships(self, entity_id: int, 
                               include_incoming: bool = True) -> Dict[str, Any]:
        """
        엔티티 관계 조회
        
        Args:
            entity_id: 엔티티 ID
            include_incoming: 들어오는 관계도 포함할지 여부
            
        Returns:
            엔티티와 관계 정보
        """
        if not self.db_manager:
            return {"error": "데이터베이스 관리자가 설정되지 않았습니다."}
            
        # 엔티티 정보 가져오기
        entity = self.get_entity(entity_id)
        if not entity:
            return {"error": f"엔티티 ID {entity_id}를 찾을 수 없습니다."}
            
        cursor = self.db_manager.conn.cursor()
        
        # 나가는 관계 (source)
        cursor.execute(
            """SELECT r.rel_id, r.relationship_type, r.confidence, r.source_block,
                      e.entity_id, e.name, e.type, e.confidence
               FROM relationships r
               JOIN entities e ON r.target_entity = e.entity_id
               WHERE r.source_entity = ?
               ORDER BY r.confidence DESC""",
            (entity_id,)
        )
        
        outgoing = []
        for row in cursor.fetchall():
            outgoing.append({
                "rel_id": row[0],
                "relationship_type": row[1],
                "confidence": row[2],
                "source_block": row[3],
                "target_entity": {
                    "entity_id": row[4],
                    "name": row[5],
                    "type": row[6],
                    "confidence": row[7]
                },
                "direction": "outgoing"
            })
        
        # 들어오는 관계 (target)
        incoming = []
        if include_incoming:
            cursor.execute(
                """SELECT r.rel_id, r.relationship_type, r.confidence, r.source_block,
                          e.entity_id, e.name, e.type, e.confidence
                   FROM relationships r
                   JOIN entities e ON r.source_entity = e.entity_id
                   WHERE r.target_entity = ?
                   ORDER BY r.confidence DESC""",
                (entity_id,)
            )
            
            for row in cursor.fetchall():
                incoming.append({
                    "rel_id": row[0],
                    "relationship_type": row[1],
                    "confidence": row[2],
                    "source_block": row[3],
                    "source_entity": {
                        "entity_id": row[4],
                        "name": row[5],
                        "type": row[6],
                        "confidence": row[7]
                    },
                    "direction": "incoming"
                })
        
        return {
            "entity": entity,
            "outgoing_relationships": outgoing,
            "incoming_relationships": incoming
        }
    
    def find_path_between_entities(self, source_id: int, target_id: int, 
                                  max_depth: int = 3) -> List[Dict[str, Any]]:
        """
        두 엔티티 사이의 경로 탐색
        
        Args:
            source_id: 시작 엔티티 ID
            target_id: 목표 엔티티 ID
            max_depth: 최대 탐색 깊이
            
        Returns:
            찾은 경로 목록
        """
        if not self.db_manager or source_id == target_id:
            return []
            
        # BFS 경로 탐색 (간소화)
        visited = set()
        queue = [[(source_id, None, None)]]  # (엔티티ID, 관계ID, 방향)의 경로
        
        paths = []
        
        while queue and max_depth > 0:
            path = queue.pop(0)
            current_id = path[-1][0]
            
            if current_id in visited:
                continue
                
            visited.add(current_id)
            
            # 목표 도달
            if current_id == target_id:
                paths.append(path)
                continue
                
            # 관계 가져오기
            entity_data = self.get_entity_relationships(current_id)
            
            # 나가는 관계 탐색
            for rel in entity_data.get("outgoing_relationships", []):
                next_id = rel["target_entity"]["entity_id"]
                if next_id not in visited:
                    new_path = path + [(next_id, rel["rel_id"], "outgoing")]
                    queue.append(new_path)
            
            # 들어오는 관계 탐색
            for rel in entity_data.get("incoming_relationships", []):
                next_id = rel["source_entity"]["entity_id"]
                if next_id not in visited:
                    new_path = path + [(next_id, rel["rel_id"], "incoming")]
                    queue.append(new_path)
            
            max_depth -= 1
        
        # 경로 정보 보강
        detailed_paths = []
        for path in paths:
            detailed_path = []
            for i, (entity_id, rel_id, direction) in enumerate(path):
                entity = self.get_entity(entity_id)
                
                path_item = {"entity": entity}
                
                # 첫 번째 항목이 아니면 관계 정보 추가
                if i > 0:
                    prev_entity_id = path[i-1][0]
                    
                    # 관계 정보 가져오기
                    cursor = self.db_manager.conn.cursor()
                    cursor.execute(
                        """SELECT relationship_type, confidence 
                           FROM relationships WHERE rel_id = ?""",
                        (rel_id,)
                    )
                    
                    rel_data = cursor.fetchone()
                    if rel_data:
                        path_item["relationship"] = {
                            "rel_id": rel_id,
                            "type": rel_data[0],
                            "confidence": rel_data[1],
                            "direction": direction
                        }
                
                detailed_path.append(path_item)
            
            detailed_paths.append(detailed_path)
        
        return detailed_paths 