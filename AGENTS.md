# Repository Guidelines

사용자가 별도로 지시하기 전까지는 모든 답변은 한국어로 답변합니다.

## Project Structure & Module Organization
The core package lives in `greeum/`, providing the STM/LTM memory managers, graph index logic, and shared utilities. Command-line tooling is under `cli/`, while `api/` exposes the REST/MCP layers used by Claude and other integrations. Reusable examples and smoke assets live in `examples/` and `data/`. Automated documentation, migration notes, and design briefs live under `docs/` and the top-level `*.md` reports. Tests are grouped in `tests/` for pytest suites, with scenario-specific regression harnesses in the `test_*/` directories that mirror production incidents.

## Agent Operational Workflow
- 아래의 `greeum` MCP 도구 사용은 선택이 아닌 필수임을 명심해야 한다. 하기 조건마다 반드시 사용하여 맥락의 휘발을 상시 방지할 수 있어야 한다. 
- Codex·Claude 환경에서는 **로컬 STDIO MCP 경로**를 기본으로 사용한다. CLI 명령 대신 `greeum` MCP 툴(add_memory, search_memory, get_memory_stats, usage_analytics, analyze 등)을 우선 호출해 작업을 기록·조회한다.
- 세션 컨텍스트가 비어 있거나 축약돼 있을 때는 `get_memory_stats`와 `usage_analytics`로 맥락을 빠르게 복원한다.
- 새 작업 요청이 들어오면 `search_memory`로 최신 기록을 우선 탐색하고, 이어서 팔로우업을 진행한다.
- 작업 중간에 새로운 추론이 나오거나 완료 직후에는 `add_memory`로 즉시 경과를 남긴다(액탄트 패턴 유지).
- 필요할 때마다 에이전트는 greeum 도구를 자율적으로 호출할 수 있으며, 사용자는 이 권한을 상시 보증한다.
- SentenceTransformer가 필요한 경우 `greeum mcp warmup`으로 모델을 미리 로드하고, 응답 지연 시 `/tmp/greeum_codex_stdio.log`에서 원인을 확인한다.
- CLI, REST 호출은 MCP 도구로 해결할 수 없을 때만 사용한다.

## Build, Test, and Development Commands
- `pip install -e .[dev]`: set up an editable checkout with linting and testing extras.
- `pytest`: run the fast unit and integration suite in `tests/`.
- `python run_all_tests.py`: execute the curated end-to-end suites used before releases.
- `tox -e py311`: run pytest in the supported interpreter matrix (py310–py312).
- `greeum mcp serve`: start the STDIO MCP server (Claude Desktop).
- `greeum mcp serve -t http --host 0.0.0.0 --port 8800`: launch the HTTP MCP endpoint for Codex/OpenAI agents.

## Coding Style & Naming Conventions
Target Python 3.10+ with 4-space indentation, type hints on public APIs, and descriptive snake_case identifiers. The repo favors single-purpose modules and keeps CLI entry points in `cli/*_commands.py`. Run `ruff check .` (line length 120, selected ignores in `pyproject.toml`) before submitting. Use `black .` to normalize formatting and `isort .` to order imports if you touch modules that mix CLI and service layers.

## Testing Guidelines
Place new tests under `tests/` mirroring the package path, and name files `test_<feature>.py`. Prefer `pytest` fixtures for database setup; avoid writing to real `data/` assets—use temporary directories. Keep long-running integration checks behind `@pytest.mark.slow` so `pytest -m "not slow"` stays quick. When altering memory flows or MCP tooling, extend the suites invoked by `run_all_tests.py` to cover regression cases.

## Commit & Pull Request Guidelines
Commits in this project emphasize clear release notes (`Release v3.1.1rc2.dev9: …`) or component tags (`cli:`, `stm:`) followed by an imperative change summary. Structure PRs with a concise description, linked issues, and verification steps (`pytest`, `tox`, or `run_all_tests.py`). Include configuration notes (e.g., env vars, new assets) and screenshots for CLI/API UX changes so agents consuming these docs can quickly validate behavior.

## Security & Configuration Tips
Never commit personal conversation logs or production data; scrub fixtures before upload. Document any required environment variables in the PR (notably `GREEUM_DATA_DIR`, `GREEUM_DISABLE_ST`, and tokens for external embeddings). Store secrets in a local `.env` and load them through `python-dotenv`; avoid hard-coding paths inside modules.
