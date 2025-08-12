Greeum Anchorized Memory — Refactor Work Plan (Markdown Prompt)

목표: v2.1.1 호환을 유지한 채 STM 3슬롯 앵커 + 국소 그래프 탐색을 “얇은 레이어”로 추가한다.

⸻

0) Scope & Acceptance

What: Anchors + GraphIndex 레이어를 기존 4계층(Working/Cache/Checkpoints/LTM) 위에 추가.
Why: 주제 전환 시 LTM 앵커 주변 국소 탐색으로 회상 품질·속도 향상, 연상 경로 형성.
Done: 기존 API/CLI/REST/MCP 그대로 동작 + 새 옵션(slot, radius)이 유효. 회귀 성능 ±10% 이내.

⸻

1) Directory & Files (to add/modify)

greeum/
  anchors/
    manager.py           # NEW: STM 3-slot anchor state + selection/move/pin
    schema.py            # NEW: Anchors snapshot I/O (versioned)
  graph/
    index.py             # NEW: lightweight GraphIndex (adjacency, beam-search)
    snapshot.py          # NEW: graph snapshot I/O (JSONL/Parquet later)
  api/
    search.py            # MOD: search(query, slot?, radius?, fallback?) route
    write.py             # MOD: write(text, slot?, policy?) route
    anchors.py           # NEW: /v1/anchors GET/PATCH
  cli/
    anchors.py           # NEW: anchors status/set/pin/unpin
    memory.py            # MOD: add --slot/--radius options
  core/
    ltm.py               # MOD: block.links neighbors cache (non-breaking)
    checkpoints.py       # KEEP
    cache.py             # KEEP
    working.py           # KEEP
  scripts/
    bootstrap_graphindex.py   # NEW: build edges from sim/time/tags (one-off)
  tests/
    test_anchors_graph.py     # NEW: unit+property tests
    test_api_backcompat.py    # NEW: back-compat regression
docs/
  design/anchorized-memory.md # NEW: this blueprint distilled


⸻

2) High-Level Architecture (Mermaid)

flowchart LR
  subgraph Core[Greeum Core (unchanged)]
    WM[Working]-->CC[Cache]-->CP[Checkpoints]-->LTM[Long-term Memory]
  end
  subgraph Layer[New Layer]
    ANC[AnchorManager\nslots A/B/C]-->GIDX[GraphIndex\nadjacency + beam]
    GIDX-->SRCH[IntelligentSearch扩]
    ANC-->WRITE[WriteRouter扩]
  end
  SRCH-->Core
  WRITE-->Core


⸻

3) Data Schemas (versioned, backward-compatible)

3.1 LTM Block (extend-only; no breaking)

{
  "schema_version": 3,
  "block_id": "blk_abc",
  "created_ts": 1723180000,
  "content": {"text":"...", "meta":{"tags":["tag1"], "source":"cli|api|agent"}},
  "vector": [0.012, ...],
  "links": { "neighbors": [ {"id":"blk_def","w":0.61}, {"id":"blk_xyz","w":0.57} ] }   // optional cache
}

3.2 Anchors snapshot (anchors.schema.json logical)

{
  "version": 1,
  "slots": [
    {"slot":"A","anchor_block_id":"blk_123","topic_vec":[...],
     "summary":"...", "hop_budget":2, "pinned":false, "last_used_ts":1723182200},
    {"slot":"B", ...}, {"slot":"C", ...}
  ],
  "updated_at": 1723182200
}

3.3 GraphIndex snapshot (graph.snapshot.jsonl)

{
  "version": 1,
  "nodes": ["blk_a","blk_b","blk_c"],
  "edges": [{"u":"blk_a","v":"blk_b","w":0.62,"src":["sim","time"]}],
  "built_at": 1723182222,
  "params": {"theta":0.35,"kmax":32,"alpha":0.7,"beta":0.2,"gamma":0.1}
}


⸻

4) Public Interfaces (minimal additive changes)

4.1 API (Python callable)

# greeum.api.search
def search(query: str, *, slot: str|None=None, radius: int|None=None,
           fallback: bool=True, top_k: int=8) -> list[Block]: ...
# greeum.api.write
def write(text: str, *, slot: str|None=None, policy: dict|None=None) -> str: ...

4.2 REST
	•	POST /v1/search { "q": "...", "slot": "A|B|C", "radius": 1|2|3, "fallback": true }
	•	POST /v1/write  { "text": "...", "slot": "A|B|C", "policy": {...} }
	•	GET  /v1/anchors
	•	PATCH /v1/anchors/{slot} { "anchor_block_id": "...", "pinned": true|false, "hop_budget": 1|2|3 }

4.3 CLI

greeum anchors status
greeum anchors set A blk_123
greeum anchors pin A blk_123
greeum anchors unpin A
greeum memory search "topic" --slot A --radius 2 --top-k 8
greeum memory write "new fact..." --slot B --policy link_k=8,min_w=0.35


⸻

5) Core Module Intent & Pseudocode

5.1 anchors/manager.py

Intent: STM 3슬롯을 1급 개체로 관리. 입력 주제 벡터에 따라 활성 슬롯 자동 선택 + 앵커 이동/고정.

class AnchorState(TypedDict):
    slot: Literal['A','B','C']
    anchor_block_id: str
    topic_vec: list[float]
    summary: str
    last_used_ts: int
    hop_budget: int
    pinned: bool

class AnchorManager:
    def __init__(self, store_path: Path):
        self.state: dict[str, AnchorState] = self._load(store_path)

    def select_active_slot(self, input_vec: np.ndarray) -> str:
        # cosine sim with slot.topic_vec + hysteresis; default A if empty
        ...

    def move_anchor(self, slot: str, new_block_id: str, topic_vec: np.ndarray|None=None):
        # update anchor + topic_vec (EMA), unless pinned
        ...

    def profile(self, slot: str) -> dict:
        # returns hop_budget, explore_eps by slot usage
        ...

5.2 graph/index.py

Intent: LTM 블록들 간 인접 리스트 + beam-search. 초기엔 in-proc + JSONL 스냅, 후속 SQLite/Parquet.

class GraphIndex:
    def __init__(self, theta=0.35, kmax=32):
        self.adj: dict[str, list[tuple[str,float]]] = {}

    def neighbors(self, u: str, k=32, min_w=None) -> list[tuple[str,float]]:
        arr = self.adj.get(u, [])
        return arr[:k] if min_w is None else [(v,w) for (v,w) in arr if w>=min_w][:k]

    def beam_search(self, start: str, is_goal: Callable[[str],bool],
                    beam=32, max_hop=2) -> list[str]:
        frontier = [(start, 0.0)]
        visited = set()
        hits = []
        for depth in range(max_hop+1):
            nxt = []
            for u,_ in frontier:
                if u in visited: continue
                visited.add(u)
                if is_goal(u): hits.append(u)
                for v,w in self.neighbors(u, k=beam):
                    if v not in visited: nxt.append((v, w))
            frontier = sorted(nxt, key=lambda x: -x[1])[:beam]
        return hits

    def upsert_edges(self, u: str, neighs: list[tuple[str,float]]):
        # merge with pruning by theta/kmax
        ...

5.3 api/search.py (localized → fallback)

def search(q, *, slot=None, radius=None, fallback=True, top_k=8):
    q_vec = embed(q)
    if slot:
        s = anchors.select_active_slot(q_vec)
        a = anchors.state[s]['anchor_block_id']
        hop = radius or anchors.state[s]['hop_budget']
        hits = gidx.beam_search(a, is_goal=lambda bid: sim(q_vec, vec(bid))>0.75,
                                beam=32, max_hop=hop)
        if hits:
            anchors.move_anchor(s, hits[0], q_vec)
            return ltm.fetch(hits[:top_k])
    if fallback:
        return core_search(q, top_k=top_k)  # existing pipeline
    return []

5.4 api/write.py (near-anchor insert)

def write(text, *, slot=None, policy=None):
    vec_new = embed(text)
    s = slot or anchors.select_active_slot(vec_new)
    a = anchors.state[s]['anchor_block_id']
    neigh = gidx.neighbors(a, k=32)
    target = max(neigh, key=lambda nv: cos(vec_new, vec(nv[0]))) if neigh else (a,1.0)
    blk = ltm.insert(content=text, vector=vec_new)     # existing
    # link new block near anchor neighborhood
    cands = [(target[0], target[1])] + neigh[:7]
    gidx.upsert_edges(blk.block_id, cands)
    anchors.move_anchor(s, blk.block_id, vec_new)
    return blk.block_id


⸻

6) Migration & Compatibility (v2.1.1 → Anchorized)

6.1 Principles
	•	No destructive changes: LTM 포맷 유지, 신규 필드 only.
	•	Anchors/GraphIndex는 별도 파일. 없으면 무시되고 v2.1.1과 동일 동작.

6.2 Bootstrap script (scripts/bootstrap_graphindex.py)
	•	sim-links: 기존 벡터 인덱스 top-k (α)
	•	time-links: 인접 시간 블록 연결 (β)
	•	co-links: 동일 태그/세션 (γ)
	•	weight = α·sim + β·time + γ·co (defaults: 0.7/0.2/0.1)
	•	Output: graph.snapshot.jsonl + LTM 캐시 links.neighbors(optional)

6.3 Rollback
	•	Anchors/GraphIndex 파일 미사용 → 즉시 이전 동작. 데이터 변환 없음.

⸻

7) Adaptive Planner Cadence (Planner-side hooks)
	•	select_active_slot(input_vec) 전/후에 PRC 신호 기록(Novelty = dist to slot.topic_vec).
	•	Economy 모드: radius=1, Reactive: radius=2~3로 탐색 반경 조절.
	•	실패 연속 시 fallback 강제.

⸻

8) Milestones & Task Breakdown (2–3일 “도끼 갈기”)

M0 — Skeleton & Back-compat (반나절)
	•	anchors/manager.py 초안 + snapshot I/O
	•	graph/index.py 초안 + neighbors/beam_search
	•	api/search.py에 파라미터만 추가(기본 경로는 기존 유지)
	•	테스트: 기존 search 호출 영향 0 (flag 미지정)

Exit: 기존 CLI/REST 전부 그린. --slot 없이 동일 결과.

⸻

M1 — Bootstrap & Localized Read (반나절~1일)
	•	scripts/bootstrap_graphindex.py 구현(αβγ 합성)
	•	anchors 자동 초기화(최근 상위 조회/쓰기 기준)
	•	search(q, slot=A, radius=2) 국소 탐색 → 실패 시 fallback
	•	메트릭: local_hit_rate, fallback_rate, avg_hops

Exit: 국소 탐색 히트율 ≥ 60%, fallback 정상.

⸻

M2 — Near-Anchor Write & Edges (반나절)
	•	api/write.py에 near-anchor insert + upsert_edges
	•	LTM block links.neighbors 캐시(옵션 저장)
	•	메트릭: anchor_moves/min, edge_growth_rate

Exit: 쓰기 후 앵커가 새 블록으로 자연 이동 + 이웃 링크 증가.

⸻

M3 — CLI/REST/Docs/Tests (반나절)
	•	cli/anchors.py, api/anchors.py
	•	tests/test_anchors_graph.py(selection, beam, write)
	•	회귀: 기존 검색·쓰기 ±10% 이내
	•	설계 문서 docs/design/anchorized-memory.md

Exit: 문서/CLI/REST 포함 PR 준비 완료.

⸻

9) Test Plan

Unit
	•	select_active_slot: 유사도·히스테리시스, pinned 보호.
	•	beam_search: hop/beam별 hit 수 단조 증가.
	•	write_near_anchor: 새 블록이 이웃들과 링크되는지.

Property
	•	radius↑ ⇒ 탐색 범위/시간 증가, hit-rate 비감소.
	•	pin 상태에서 move_anchor 무시.

Regression
	•	search()(no slot) 성능·결과 동일성(샘플셋 기준).
	•	write() 기존 경로 대비 지연 ±10% 이내.

⸻

10) Metrics & Observability (Prometheus names)
	•	greeum_anchors_switches_per_min
	•	greeum_local_hit_rate / greeum_fallback_rate
	•	greeum_avg_hops / greeum_beam_width
	•	greeum_anchor_moves_total
	•	greeum_edge_count / greeum_edge_growth_rate

⸻

11) Developer Checklist (copy/paste)
	•	Create: greeum/anchors/manager.py, schema.py
	•	Create: greeum/graph/index.py, snapshot.py
	•	Modify: api/search.py, api/write.py, core/ltm.py
	•	Create: api/anchors.py, cli/anchors.py
	•	Create: scripts/bootstrap_graphindex.py
	•	Tests + Docs + Metrics wires

⸻

12) Commit Strategy
	•	PR#1: Layer skeleton (Anchors/GraphIndex + no behavior change)
	•	PR#2: Localized read (slot/radius + fallback)
	•	PR#3: Near-anchor write + edges
	•	PR#4: CLI/REST + docs + tests + metrics

각 PR은 완전 롤백 가능(파일無/플래그無 시 v2.1.1로 동작).

⸻

13) Sample Developer Prompts (for Cursor/Agent)

“Add AnchorManager skeleton and snapshot I/O”

Create greeum/anchors/manager.py with 3-slot state, select_active_slot(input_vec),
move_anchor(), pin/unpin(), and snapshot load/save to anchors.json.
No external deps except numpy. Include minimal unit tests in tests/test_anchors_graph.py.

“Implement GraphIndex and beam_search”

Add greeum/graph/index.py with neighbors(), beam_search(), upsert_edges().
Store snapshot to graph.snapshot.jsonl. Keep in-proc structure, prune by theta/kmax.

“Wire search() with slot/radius and fallback”

In greeum/api/search.py, accept slot?, radius?, fallback?. If slot is given,
run GraphIndex.beam_search from anchor_block_id with hop=radius or slot.hop_budget.
On hits, move anchor to best_hit and return blocks; else fallback to existing pipeline.

“Write near-anchor and link edges”

In greeum/api/write.py, compute new vector, choose active slot, pick best neighbor of
anchor by cosine, insert LTM block, upsert_edges(new_block, neighbors_topk),
and move anchor to new block. Update docs and add metrics.


⸻

FAQ

Q. 기존 v2.1.1 메모리는 호환되나?
A. 네. 기존 블록 포맷을 변경하지 않고, Anchors/GraphIndex를 추가 파일로만 둡니다. 파일이 없어도 기존처럼 동작합니다.

Q. 성능 리스크는?
	•	GraphIndex는 in-proc + k≤32, θ=0.35로 제어.
	•	실패 시 즉시 Checkpoints→LTM로 폴백.
	•	회귀 테스트로 ±10% 가드.

Q. 장기적으로?
	•	GraphIndex를 SQLite/Parquet로 영속화, 엣지 업데이트 배치화.
	•	앵커 프로파일(작업/대화/연구)별 hop/beam 정책 YAML화.

