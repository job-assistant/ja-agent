# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`ja-agent` is the AI agent server for the **Job Assistant** platform — an AI-powered interview preparation service for job seekers. It exposes AI features (document embedding, triple RAG question generation, answer evaluation, counter-question generation, STT) as a FastAPI REST API, called by `ja-backend` (Spring Boot) when AI processing is needed.

Infrastructure (PostgreSQL + pgvector, Redis) is managed separately in `ja-infra`.

## Commands

```bash
# Install dependencies
uv sync

# Run development server (hot reload, port 8888)
uv run python main.py

# Run with uvicorn directly
uv run uvicorn main:app --host 0.0.0.0 --port 8888 --reload
```

There are no configured test or lint commands yet.

## Architecture

**Runtime flow:** `main.py` creates the FastAPI app with a `lifespan` handler that initializes logging on startup and closes the DB engine on shutdown. Exception handlers are registered globally via `setup_exception_handlers`.

**Key layers:**

- `app/core/config.py` — Single `Settings` (pydantic-settings) singleton `settings` loaded from `.env`. All configuration — DB, models, chunking, embedding, RAG params, WhisperX — is centralized here. Computed fields build `DATABASE_URL` (async `asyncpg`) and `CHECKPOINTER_CONNECTION_STRING` (sync psycopg2-style) from individual Postgres env vars.

- `app/core/db/database.py` — Async SQLAlchemy engine + `AsyncSessionLocal` factory. `get_database_session()` is the FastAPI dependency for DB-backed endpoints. `Base` (DeclarativeBase) is the ORM base class for all models. Table creation is commented out — schema is managed externally.

- `app/core/error/` — Custom exception hierarchy rooted at `AIAgentException`. Subclasses: `WorkflowException` (500), `LLMException` (503), `DocumentProcessingException` (422), `DatabaseException` (500), `ValidationException` (400). All errors return a unified JSON shape with `error`, `type`, `message`, `path`, `details`, `status_code`.

- `app/agent/` — LangGraph multi-agent implementations (currently skeleton).

- `app/api/` — FastAPI routers (currently skeleton; register in `main.py` under `# 라우터 등록`).

**AI stack:** LangGraph/LangChain for agent orchestration → OpenAI GPT-4o / GPT-4o-mini for LLM calls → `BAAI/bge-m3` (1024-dim) for embeddings → PostgreSQL + pgvector (HNSW) for vector storage → LangGraph checkpointer (PostgreSQL) for agent state persistence → WhisperX (large-v2) for STT → LlamaParse for document parsing.

**RAG strategy:** Corrective RAG (CRAG) with triple retrieval (dense + sparse + hybrid), RRF re-ranking. Parameters: `RAG_SEARCH_LIMIT=10` candidates per method, `RAG_TOP_K=5` final results, `RAG_RRF_K=60`.

## Environment Setup

Copy `.env.example` to `.env` and fill in:
- `OPENAI_API_KEY` — required for all LLM calls
- `LLAMA_CLOUD_API_KEY` — required for document parsing
- `HF_TOKEN` — required for WhisperX speaker diarization
- Postgres credentials (`POSTGRES_HOST`, `POSTGRES_EXTERNAL_PORT`, etc.) — default port is `5433` (external Docker port)

## Harness (Orchestrator) Mode

### 에이전트 구성

| 에이전트 | 지침 파일 | 출력 파일 |
|----------|-----------|-----------|
| Plan     | `.claude/agents/plan.md`       | `.claude/outputs/plan_output.md`  |
| Runner   | `.claude/agents/runner.md`     | `.claude/outputs/run_output.md`   |
| Evaluate | `.claude/agents/evaluation.md` | `.claude/outputs/eval_output.md`  |

### 실행 순서

```
1. Plan Agent    → .claude/agents/plan.md 읽고 실행
                 → .claude/outputs/plan_output.md 생성

2. Runner Agent  → .claude/agents/runner.md 읽고 실행
                 → .claude/outputs/plan_output.md 참고
                 → .claude/outputs/run_output.md 생성

3. Eval Agent    → .claude/agents/evaluation.md 읽고 실행
                 → .claude/outputs/run_output.md 참고
                 → .claude/outputs/eval_output.md 생성

4. 판정
   PASS → 완료
   FAIL → .claude/outputs/plan_output.md에 피드백 주입 후 1번 재실행
   3회 초과 → .claude/outputs/fail_report.md 생성 후 중단
```

### 도구 권한

| 에이전트 | 허용 도구 |
|----------|-----------|
| Plan Agent | Read, LS, Glob |
| Runner Agent | Read, Write, Edit, Bash (테스트 한정) |
| Eval Agent | Read, LS, Glob |

### 공통 규칙

- 모든 출력 파일은 `.claude/outputs/` 에만 저장
- 파일 수정 전 반드시 read 먼저 수행
- 기존 파일 삭제 금지, 기존 의존성 버전 변경 금지
- 파일 경로는 프로젝트 루트 기준 상대경로 사용