"""
Greeum Memory Visualization API
기억 데이터를 시각화용 JSON으로 제공
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class MemoryNode:
    """시각화용 기억 노드"""
    id: str
    label: str
    slot: str
    importance: float
    timestamp: str
    group: int  # 슬롯별 그룹 (색상 구분용)


@dataclass
class MemoryLink:
    """시각화용 연결"""
    source: str
    target: str
    type: str  # tree, semantic, temporal
    strength: float


class VisualizationDataProvider:
    """시각화 데이터 제공자"""

    SLOT_GROUPS = {'A': 1, 'B': 2, 'C': 3, 'D': 4, None: 0, '': 0}

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # 환경 변수에서 먼저 확인
            db_path = os.environ.get("GREEUM_VIZ_DB_PATH")

        if db_path is None:
            # 기본 경로 탐색 (MCP DB 우선)
            candidates = [
                Path.home() / ".greeum" / "memory.db",  # MCP DB 우선
                Path("data/memory.db"),
            ]
            for p in candidates:
                if p.exists():
                    db_path = str(p)
                    break

        if not db_path or not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found: {db_path}")

        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def get_tree_data(self, limit: int = 100) -> Dict[str, Any]:
        """트리 구조 데이터 반환 (D3.js 호환) - 분기점 우선, 중요도순"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 1. 전체 블록과 부모-자식 관계 조회
        cursor.execute("""
            SELECT block_index, context, root, before, hash, slot, importance, timestamp
            FROM blocks
        """)

        all_blocks = {}
        hash_to_index = {}
        children_count = {}  # 각 노드의 자식 수

        for row in cursor.fetchall():
            block_index, context, root, before, hash_val, slot, importance, timestamp = row
            all_blocks[block_index] = {
                'block_index': block_index,
                'context': context,
                'root': root,
                'before': before,
                'hash': hash_val,
                'slot': slot,
                'importance': importance or 0.5,
                'timestamp': timestamp
            }
            if hash_val:
                hash_to_index[hash_val] = block_index
            children_count[block_index] = 0

        # 2. 자식 수 계산 (분기점 판별용)
        for block_index, block in all_blocks.items():
            if block['before'] and block['before'] in hash_to_index:
                parent_index = hash_to_index[block['before']]
                children_count[parent_index] = children_count.get(parent_index, 0) + 1

        # 3. 분기점 노드 (자식 2개 이상) 먼저 선택
        branch_nodes = []
        linear_nodes = []

        for block_index, block in all_blocks.items():
            if children_count.get(block_index, 0) >= 2:
                branch_nodes.append(block)
            else:
                linear_nodes.append(block)

        # 4. 선형 노드는 중요도순 정렬
        linear_nodes.sort(key=lambda x: x['importance'], reverse=True)

        # 5. 분기점 우선, 그 다음 중요도순 선형 노드
        selected_blocks = branch_nodes + linear_nodes
        selected_blocks = selected_blocks[:limit]

        # 6. 노드와 링크 생성
        nodes = []
        links = []
        node_ids = set()

        for block in selected_blocks:
            block_index = block['block_index']
            context = block['context']
            node_id = str(block_index)
            label = (context[:40] + "...") if context and len(context) > 40 else (context or "")

            # 분기점 여부 표시를 라벨에 추가
            is_branch = children_count.get(block_index, 0) >= 2

            nodes.append(MemoryNode(
                id=node_id,
                label=label,
                slot=block['slot'] or "",
                importance=block['importance'],
                timestamp=block['timestamp'] or "",
                group=self.SLOT_GROUPS.get(block['slot'], 0)
            ))
            node_ids.add(node_id)

        # 7. 링크 생성 (선택된 노드 간에만)
        for block in selected_blocks:
            block_index = block['block_index']
            before_hash = block['before']

            if before_hash and before_hash in hash_to_index:
                parent_index = hash_to_index[before_hash]
                if str(parent_index) in node_ids:
                    links.append(MemoryLink(
                        source=str(parent_index),
                        target=str(block_index),
                        type="tree",
                        strength=1.0
                    ))

        conn.close()

        return {
            "nodes": [asdict(n) for n in nodes],
            "links": [asdict(l) for l in links]
        }

    def get_graph_data(self, limit: int = 100) -> Dict[str, Any]:
        """그래프 연결 데이터 반환 (associations 기반)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 기억 블록 조회
        cursor.execute("""
            SELECT block_index, context, slot, importance, timestamp
            FROM blocks
            ORDER BY block_index DESC
            LIMIT ?
        """, (limit,))

        nodes = []
        node_map = {}  # block_index -> node_id

        for row in cursor.fetchall():
            block_index, context, slot, importance, timestamp = row

            node_id = str(block_index)
            label = (context[:40] + "...") if context and len(context) > 40 else (context or "")

            nodes.append(MemoryNode(
                id=node_id,
                label=label,
                slot=slot or "",
                importance=importance or 0.5,
                timestamp=timestamp or "",
                group=self.SLOT_GROUPS.get(slot, 0)
            ))
            node_map[block_index] = node_id

        # memory_nodes와 blocks 매핑 조회 먼저
        cursor.execute("SELECT node_id, memory_id FROM memory_nodes")
        node_to_block = {row[0]: str(row[1]) for row in cursor.fetchall()}

        # associations 조회
        cursor.execute("""
            SELECT source_node_id, target_node_id, association_type, strength
            FROM associations
            ORDER BY strength DESC
            LIMIT ?
        """, (limit * 2,))

        links = []
        node_ids = set(node_map.values())

        for row in cursor.fetchall():
            source_node, target_node, assoc_type, strength = row

            source_block = node_to_block.get(source_node)
            target_block = node_to_block.get(target_node)

            if source_block and target_block and source_block in node_ids and target_block in node_ids:
                links.append(MemoryLink(
                    source=source_block,
                    target=target_block,
                    type=assoc_type or "unknown",
                    strength=strength or 0.5
                ))

        conn.close()

        return {
            "nodes": [asdict(n) for n in nodes],
            "links": [asdict(l) for l in links]
        }

    def get_combined_data(self, limit: int = 100) -> Dict[str, Any]:
        """트리 + 그래프 통합 데이터"""
        tree_data = self.get_tree_data(limit)
        graph_data = self.get_graph_data(limit)

        # 노드는 트리 데이터 사용 (중복 방지)
        # 링크는 병합
        all_links = tree_data["links"] + graph_data["links"]

        # 중복 링크 제거
        seen = set()
        unique_links = []
        for link in all_links:
            key = (link["source"], link["target"])
            if key not in seen:
                seen.add(key)
                unique_links.append(link)

        return {
            "nodes": tree_data["nodes"],
            "links": unique_links
        }

    def get_memory_detail(self, block_index: int) -> Optional[Dict[str, Any]]:
        """개별 기억 상세 정보 반환"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT block_index, context, timestamp, importance, slot,
                   root, before, after, hash
            FROM blocks
            WHERE block_index = ?
        """, (block_index,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        # 연결된 기억들 조회
        cursor.execute("""
            SELECT b.block_index, b.context, b.slot
            FROM blocks b
            WHERE b.before = ? OR b.hash IN (
                SELECT value FROM json_each(?)
            )
            LIMIT 10
        """, (row[8], row[7] or '[]'))  # hash, after

        connected = []
        for conn_row in cursor.fetchall():
            ctx = (conn_row[1][:40] + "...") if conn_row[1] and len(conn_row[1]) > 40 else conn_row[1]
            connected.append({
                "id": conn_row[0],
                "label": ctx,
                "slot": conn_row[2]
            })

        # 키워드 조회
        cursor.execute("""
            SELECT keyword FROM block_keywords WHERE block_index = ?
        """, (block_index,))
        keywords = [row[0] for row in cursor.fetchall()]

        # 태그 조회
        cursor.execute("""
            SELECT tag FROM block_tags WHERE block_index = ?
        """, (block_index,))
        tags = [row[0] for row in cursor.fetchall()]

        conn.close()

        return {
            "id": row[0],
            "content": row[1],
            "timestamp": row[2],
            "importance": row[3],
            "slot": row[4],
            "root": row[5][:12] + "..." if row[5] else None,
            "keywords": keywords,
            "tags": tags,
            "connected": connected
        }

    def get_stats(self) -> Dict[str, Any]:
        """통계 정보"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM blocks")
        total_memories = cursor.fetchone()[0]

        cursor.execute("SELECT slot, COUNT(*) FROM blocks GROUP BY slot")
        slot_counts = {row[0] or "None": row[1] for row in cursor.fetchall()}

        cursor.execute("SELECT COUNT(*) FROM associations")
        total_links = cursor.fetchone()[0]

        cursor.execute("SELECT association_type, COUNT(*) FROM associations GROUP BY association_type")
        link_types = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        return {
            "total_memories": total_memories,
            "slot_distribution": slot_counts,
            "total_links": total_links,
            "link_types": link_types
        }

    def get_slot_analysis(self, top_n: int = 5) -> Dict[str, Any]:
        """슬롯별 주제/키워드 분석"""
        conn = self._get_connection()
        cursor = conn.cursor()

        slots = ['A', 'B', 'C', 'D']
        result = {}

        for slot in slots:
            # 해당 슬롯의 키워드 빈도 분석
            cursor.execute("""
                SELECT bk.keyword, COUNT(*) as cnt
                FROM block_keywords bk
                JOIN blocks b ON bk.block_index = b.block_index
                WHERE b.slot = ?
                GROUP BY bk.keyword
                ORDER BY cnt DESC
                LIMIT ?
            """, (slot, top_n))
            keywords = [{"keyword": row[0], "count": row[1]} for row in cursor.fetchall()]

            # 해당 슬롯의 태그 빈도 분석
            cursor.execute("""
                SELECT bt.tag, COUNT(*) as cnt
                FROM block_tags bt
                JOIN blocks b ON bt.block_index = b.block_index
                WHERE b.slot = ?
                GROUP BY bt.tag
                ORDER BY cnt DESC
                LIMIT ?
            """, (slot, top_n))
            tags = [{"tag": row[0], "count": row[1]} for row in cursor.fetchall()]

            # 해당 슬롯의 대표 기억 (최근 + 중요도 높은 것)
            cursor.execute("""
                SELECT context, importance
                FROM blocks
                WHERE slot = ?
                ORDER BY importance DESC, timestamp DESC
                LIMIT 3
            """, (slot,))
            samples = []
            for row in cursor.fetchall():
                ctx = row[0][:60] + "..." if row[0] and len(row[0]) > 60 else row[0]
                samples.append(ctx)

            # 슬롯 요약 생성 (상위 키워드 기반)
            top_keywords = [k["keyword"] for k in keywords[:3]]
            summary = ", ".join(top_keywords) if top_keywords else "Empty"

            result[slot] = {
                "keywords": keywords,
                "tags": tags,
                "samples": samples,
                "summary": summary,
                "theme": self._infer_slot_theme(top_keywords, tags)
            }

        conn.close()
        return result

    def _infer_slot_theme(self, keywords: List[str], tags: List[Dict]) -> str:
        """키워드/태그 기반 슬롯 테마 추론"""
        # 간단한 휴리스틱 기반 테마 추론
        all_terms = [k.lower() for k in keywords]
        all_terms += [t["tag"].lower() for t in tags[:3]]

        # 테마 패턴 매칭
        if any(t in all_terms for t in ["구현", "완료", "fix", "개발", "코드"]):
            return "개발 작업"
        elif any(t in all_terms for t in ["분석", "설계", "전략", "계획"]):
            return "전략/설계"
        elif any(t in all_terms for t in ["테스트", "검증", "확인", "버그"]):
            return "테스트/검증"
        elif any(t in all_terms for t in ["문서", "readme", "설명"]):
            return "문서화"
        elif any(t in all_terms for t in ["사용자", "질문", "요청"]):
            return "사용자 상호작용"
        elif any(t in all_terms for t in ["greeum", "grettel", "mcp"]):
            return "프로젝트 기록"
        else:
            return "일반 기억"


# FastAPI 엔드포인트 (선택적)
def create_viz_router():
    """FastAPI 라우터 생성"""
    try:
        from fastapi import APIRouter, HTTPException, Query
        from fastapi.responses import HTMLResponse, FileResponse
    except ImportError:
        return None

    router = APIRouter(prefix="/viz", tags=["visualization"])

    @router.get("/data/tree")
    async def get_tree(limit: int = Query(100, ge=1, le=500)):
        """트리 구조 데이터"""
        try:
            provider = VisualizationDataProvider()
            return provider.get_tree_data(limit)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/data/graph")
    async def get_graph(limit: int = Query(100, ge=1, le=500)):
        """그래프 연결 데이터"""
        try:
            provider = VisualizationDataProvider()
            return provider.get_graph_data(limit)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/data/combined")
    async def get_combined(limit: int = Query(100, ge=1, le=500)):
        """통합 데이터"""
        try:
            provider = VisualizationDataProvider()
            return provider.get_combined_data(limit)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/stats")
    async def get_stats():
        """통계 정보"""
        try:
            provider = VisualizationDataProvider()
            return provider.get_stats()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/memory/{block_index}")
    async def get_memory_detail(block_index: int):
        """개별 기억 상세 정보"""
        try:
            provider = VisualizationDataProvider()
            result = provider.get_memory_detail(block_index)
            if result is None:
                raise HTTPException(status_code=404, detail=f"Memory #{block_index} not found")
            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/slots/analysis")
    async def get_slot_analysis():
        """슬롯별 주제/키워드 분석"""
        try:
            provider = VisualizationDataProvider()
            return provider.get_slot_analysis()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/", response_class=HTMLResponse)
    async def viz_page():
        """시각화 페이지"""
        html_path = Path(__file__).parent / "index.html"
        if html_path.exists():
            return html_path.read_text(encoding="utf-8")
        raise HTTPException(status_code=404, detail="Visualization page not found")

    return router


if __name__ == "__main__":
    # 테스트
    provider = VisualizationDataProvider()

    print("=== Stats ===")
    print(json.dumps(provider.get_stats(), indent=2))

    print("\n=== Tree Data (5 nodes) ===")
    tree = provider.get_tree_data(5)
    print(f"Nodes: {len(tree['nodes'])}, Links: {len(tree['links'])}")

    print("\n=== Graph Data (5 nodes) ===")
    graph = provider.get_graph_data(5)
    print(f"Nodes: {len(graph['nodes'])}, Links: {len(graph['links'])}")
