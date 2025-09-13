"""
Greeum v3.1: Semantic Tagging System
체계적인 의미 기반 태깅 구현
"""

import re
import time
import json
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class TagStructure:
    """태그 구조 정의"""
    
    # Level 1: Categories (고정)
    CATEGORIES = {
        'work': '업무',
        'personal': '개인',
        'learning': '학습',
        'social': '소셜',
        'system': '시스템'
    }
    
    # Level 2: Activities (고정)
    ACTIVITIES = {
        'create': '생성',
        'fix': '수정',
        'plan': '계획',
        'review': '리뷰',
        'document': '문서화',
        'meeting': '회의',
        'research': '조사',
        'test': '테스트',
        'deploy': '배포',
        'maintain': '유지보수'
    }
    
    # Level 3: Domains (동적, 최대 50개)
    @staticmethod
    def get_initial_domains():
        return {
            # Technical
            'api', 'database', 'frontend', 'backend', 'auth',
            'performance', 'security', 'ui', 'ux', 'algorithm',
            
            # Languages
            'python', 'javascript', 'java', 'go', 'rust',
            
            # Concepts
            'bug', 'feature', 'refactor', 'optimization', 'migration'
        }


@dataclass
class MemoryTag:
    """개별 메모리의 태그"""
    category: str
    activity: str
    domains: List[str] = field(default_factory=list)
    auto_generated: bool = True
    confidence: float = 0.5
    user_verified: bool = False
    language: str = 'ko'
    
    def to_dict(self) -> Dict:
        return {
            'category': self.category,
            'activity': self.activity,
            'domains': self.domains,
            'metadata': {
                'auto': self.auto_generated,
                'confidence': self.confidence,
                'verified': self.user_verified,
                'language': self.language
            }
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class SemanticTagger:
    """의미 기반 태거"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.tag_structure = TagStructure()
        self.domain_tags = set(TagStructure.get_initial_domains())
        self.tag_stats = defaultdict(lambda: {'count': 0, 'last_used': None})
        
        # Tag consolidation rules
        self.synonyms = {
            'bug': {'bugs', '버그', 'error', '에러', 'issue'},
            'api': {'API', 'endpoint', '엔드포인트', 'rest', 'REST'},
            'auth': {'authentication', '인증', 'login', '로그인', 'jwt', 'token'},
            'database': {'db', 'DB', '데이터베이스', 'sql', 'SQL'},
            'test': {'testing', '테스트', 'spec', 'unit', 'integration'}
        }
        
        # Keyword to category/activity mapping
        self.keyword_mappings = {
            'category': {
                'work': ['작업', '개발', '코드', '프로젝트', 'api', '버그'],
                'personal': ['개인', '일상', '휴식', '식사', '운동'],
                'learning': ['학습', '공부', '연구', '분석', '조사'],
                'social': ['회의', '대화', '미팅', '논의', '토론'],
                'system': ['시스템', '설정', '환경', '도구', '자동화']
            },
            'activity': {
                'create': ['생성', '개발', '구현', '작성', '추가'],
                'fix': ['수정', '버그', '고침', '해결', '픽스'],
                'plan': ['계획', '설계', '기획', '구상', '전략'],
                'review': ['리뷰', '검토', '분석', '평가', '피드백'],
                'test': ['테스트', '검증', '확인', '실험', '시험']
            }
        }
        
        if db_manager:
            self._ensure_tables()
    
    def _ensure_tables(self):
        """태그 관련 테이블 생성"""
        cursor = self.db_manager.conn.cursor()
        
        # Tag definitions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tag_definitions (
                tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_name TEXT UNIQUE NOT NULL,
                tag_level INTEGER,
                usage_count INTEGER DEFAULT 0,
                last_used REAL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # Memory-tag associations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_tags (
                memory_id INTEGER,
                tag_name TEXT,
                tag_type TEXT,  -- 'category', 'activity', 'domain'
                confidence REAL DEFAULT 1.0,
                added_by TEXT DEFAULT 'system',
                added_at REAL DEFAULT (strftime('%s', 'now')),
                PRIMARY KEY (memory_id, tag_name, tag_type)
            )
        ''')
        
        # Tag synonyms
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tag_synonyms (
                synonym TEXT PRIMARY KEY,
                canonical TEXT NOT NULL
            )
        ''')
        
        self.db_manager.conn.commit()
        
        # Initialize synonyms
        self._init_synonyms()
    
    def _init_synonyms(self):
        """동의어 초기화"""
        cursor = self.db_manager.conn.cursor()
        
        for canonical, synonyms in self.synonyms.items():
            for synonym in synonyms:
                cursor.execute('''
                    INSERT OR IGNORE INTO tag_synonyms (synonym, canonical)
                    VALUES (?, ?)
                ''', (synonym, canonical))
        
        self.db_manager.conn.commit()
    
    def quick_tag(self, content: str) -> MemoryTag:
        """빠른 동기 태깅 (규칙 기반)"""
        
        # 1. Language detection
        language = self._detect_language(content)
        
        # 2. Extract keywords
        keywords = self._extract_keywords(content)
        
        # 3. Infer category
        category = self._infer_category(keywords, content)
        
        # 4. Infer activity
        activity = self._infer_activity(keywords, content)
        
        # 5. Extract domain tags
        domains = self._extract_domains(keywords, content)
        
        return MemoryTag(
            category=category,
            activity=activity,
            domains=domains[:5],  # Max 5 domains
            auto_generated=True,
            confidence=0.6,
            language=language
        )
    
    def _detect_language(self, text: str) -> str:
        """언어 감지"""
        korean_chars = len(re.findall(r'[가-힣]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        if korean_chars > english_chars:
            return 'ko'
        elif english_chars > korean_chars:
            return 'en'
        else:
            return 'mixed'
    
    def _extract_keywords(self, text: str) -> List[str]:
        """키워드 추출"""
        # 한글과 영어 모두 처리
        words = re.findall(r'\b[a-zA-Z]+\b|[가-힣]+', text.lower())
        
        # Stop words
        stop_words = {
            '은', '는', '이', '가', '을', '를', '에', '의', '과', '와',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to'
        }
        
        return [w for w in words if w not in stop_words and len(w) > 1]
    
    def _infer_category(self, keywords: List[str], content: str) -> str:
        """카테고리 추론"""
        content_lower = content.lower()
        
        scores = defaultdict(int)
        for category, indicators in self.keyword_mappings['category'].items():
            for indicator in indicators:
                if indicator in content_lower:
                    scores[category] += 1
        
        if scores:
            return max(scores, key=scores.get)
        return 'work'  # Default
    
    def _infer_activity(self, keywords: List[str], content: str) -> str:
        """활동 타입 추론"""
        content_lower = content.lower()
        
        scores = defaultdict(int)
        for activity, indicators in self.keyword_mappings['activity'].items():
            for indicator in indicators:
                if indicator in content_lower:
                    scores[activity] += 1
        
        if scores:
            return max(scores, key=scores.get)
        return 'create'  # Default
    
    def _extract_domains(self, keywords: List[str], content: str) -> List[str]:
        """도메인 태그 추출"""
        domains = []
        content_lower = content.lower()
        
        # Check known domains
        for domain in self.domain_tags:
            if domain in content_lower:
                domains.append(domain)
        
        # Check synonyms and map to canonical
        for canonical, synonyms in self.synonyms.items():
            for synonym in synonyms:
                if synonym in content_lower and canonical not in domains:
                    domains.append(canonical)
                    break
        
        return domains
    
    def save_tags(self, memory_id: int, tags: MemoryTag):
        """태그 저장"""
        if not self.db_manager:
            return
        
        cursor = self.db_manager.conn.cursor()
        
        # Save category
        cursor.execute('''
            INSERT OR REPLACE INTO memory_tags 
            (memory_id, tag_name, tag_type, confidence, added_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (memory_id, tags.category, 'category', tags.confidence, 'auto'))
        
        # Save activity
        cursor.execute('''
            INSERT OR REPLACE INTO memory_tags 
            (memory_id, tag_name, tag_type, confidence, added_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (memory_id, tags.activity, 'activity', tags.confidence, 'auto'))
        
        # Save domains
        for domain in tags.domains:
            cursor.execute('''
                INSERT OR REPLACE INTO memory_tags 
                (memory_id, tag_name, tag_type, confidence, added_by)
                VALUES (?, ?, ?, ?, ?)
            ''', (memory_id, domain, 'domain', tags.confidence, 'auto'))
            
            # Update stats
            self._update_tag_stats(domain)
        
        self.db_manager.conn.commit()
    
    def _update_tag_stats(self, tag: str):
        """태그 사용 통계 업데이트"""
        self.tag_stats[tag]['count'] += 1
        self.tag_stats[tag]['last_used'] = time.time()
        
        # Add to domain tags if new and popular
        if tag not in self.domain_tags and self.tag_stats[tag]['count'] > 3:
            if len(self.domain_tags) < 50:
                self.domain_tags.add(tag)
                logger.info(f"Added new domain tag: {tag}")
    
    def search_by_tags(
        self,
        category: Optional[str] = None,
        activity: Optional[str] = None,
        domains: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None
    ) -> List[int]:
        """태그 기반 검색"""
        if not self.db_manager:
            return []
        
        cursor = self.db_manager.conn.cursor()
        
        # Build query
        conditions = []
        params = []
        
        if category:
            conditions.append("EXISTS (SELECT 1 FROM memory_tags mt WHERE mt.memory_id = m.memory_id AND mt.tag_name = ? AND mt.tag_type = 'category')")
            params.append(category)
        
        if activity:
            conditions.append("EXISTS (SELECT 1 FROM memory_tags mt WHERE mt.memory_id = m.memory_id AND mt.tag_name = ? AND mt.tag_type = 'activity')")
            params.append(activity)
        
        if domains:
            for domain in domains:
                canonical = self._get_canonical_tag(domain)
                conditions.append("EXISTS (SELECT 1 FROM memory_tags mt WHERE mt.memory_id = m.memory_id AND mt.tag_name = ? AND mt.tag_type = 'domain')")
                params.append(canonical)
        
        if exclude:
            for tag in exclude:
                canonical = self._get_canonical_tag(tag)
                conditions.append("NOT EXISTS (SELECT 1 FROM memory_tags mt WHERE mt.memory_id = m.memory_id AND mt.tag_name = ?)")
                params.append(canonical)
        
        if not conditions:
            return []
        
        query = f"""
            SELECT DISTINCT m.memory_id 
            FROM memory_tags m
            WHERE {' AND '.join(conditions)}
        """
        
        cursor.execute(query, params)
        return [row[0] for row in cursor.fetchall()]
    
    def _get_canonical_tag(self, tag: str) -> str:
        """동의어를 정규 태그로 변환"""
        tag_lower = tag.lower()
        
        # Check if it's already canonical
        if tag_lower in self.synonyms:
            return tag_lower
        
        # Check if it's a synonym
        for canonical, synonyms in self.synonyms.items():
            if tag_lower in synonyms:
                return canonical
        
        return tag_lower
    
    def consolidate_tags(self):
        """태그 통합 및 정리"""
        if not self.db_manager:
            return
        
        cursor = self.db_manager.conn.cursor()
        
        # 1. Merge synonyms
        for canonical, synonyms in self.synonyms.items():
            for synonym in synonyms:
                cursor.execute('''
                    UPDATE memory_tags 
                    SET tag_name = ? 
                    WHERE tag_name = ?
                ''', (canonical, synonym))
        
        # 2. Remove rare tags (used < 3 times)
        cursor.execute('''
            DELETE FROM memory_tags
            WHERE tag_name IN (
                SELECT tag_name 
                FROM memory_tags 
                GROUP BY tag_name 
                HAVING COUNT(*) < 3
            )
            AND tag_type = 'domain'
        ''')
        
        self.db_manager.conn.commit()
        logger.info("Tag consolidation completed")
    
    def get_tag_analytics(self) -> Dict:
        """태그 사용 분석"""
        if not self.db_manager:
            return {}
        
        cursor = self.db_manager.conn.cursor()
        
        # Top tags by category
        cursor.execute('''
            SELECT tag_type, tag_name, COUNT(*) as count
            FROM memory_tags
            GROUP BY tag_type, tag_name
            ORDER BY tag_type, count DESC
        ''')
        
        analytics = defaultdict(list)
        for row in cursor.fetchall():
            tag_type, tag_name, count = row
            analytics[tag_type].append({
                'tag': tag_name,
                'count': count
            })
        
        return dict(analytics)