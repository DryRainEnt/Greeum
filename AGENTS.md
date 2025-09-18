# Repository Guidelines

## Project Structure & Module Organization
The core package lives in `greeum/`, providing the STM/LTM memory managers, graph index logic, and shared utilities. Command-line tooling is under `cli/`, while `api/` exposes the REST/MCP layers used by Claude and other integrations. Reusable examples and smoke assets live in `examples/` and `data/`. Automated documentation, migration notes, and design briefs live under `docs/` and the top-level `*.md` reports. Tests are grouped in `tests/` for pytest suites, with scenario-specific regression harnesses in the `test_*/` directories that mirror production incidents.

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
Never commit personal conversation logs or production data; scrub fixtures before upload. Document any required environment variables in the PR (notably `GREEUM_DATA_DIR` and tokens for external embeddings). Store secrets in a local `.env` and load them through `python-dotenv`; avoid hard-coding paths inside modules.
