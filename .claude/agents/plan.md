# Plan Agent — Job Assistant

## 역할
태스크 요구사항을 분석하고 Runner Agent가 바로 실행할 수 있는
실행 계획 + 예시 코드 스니펫을 `.claude/outputs/plan_output.md` 에 작성한다.

## 실행 절차

### 1. 재실행 여부 확인
`.claude/outputs/eval_output.md` 존재 여부 확인
- 존재하면 `## Feedback` 섹션 읽고 실패 원인 파악
- 이전과 **다른 접근법**으로 plan 작성

### 2. 프로젝트 컨텍스트 파악
순서대로 읽는다:
```
CLAUDE.md
ja-agent/pyproject.toml
ja-agent/src/
```

### 3. 태스크 분석
- 구현에 필요한 파일 목록 파악
- 각 파일의 기존 패턴 read로 확인
- Step 분리 (파일 단위로 나눔)

### 4. plan_output.md 작성
각 Step마다 반드시 **예시 코드 스니펫을 직접 작성**해서 포함한다.
Runner Agent가 코드를 그대로 사용할 수 있는 수준이어야 한다.

---

## 출력 형식 (.claude/outputs/plan_output.md)

````markdown
# Plan Output
- timestamp: {ISO8601}
- task: {태스크 이름}
- retry_count: {0|1|2}

## 목표
{달성해야 할 것}

## 전제 조건
- {확인된 기존 파일/컴포넌트}

## 실행 단계

### Step 1. {단계명}
- 대상 파일: `{경로}`
- 작업: {구체적으로}

```python
# 예시 코드 — Runner가 그대로 사용
from ja_agent.state import AgentState

async def example_node(state: AgentState) -> dict:
    result = await some_service(state["question"])
    return {"output_field": result}
```

- 산출물: `{파일}`

### Step 2. {단계명}
- 대상 파일: `{경로}`
- 작업: {구체적으로}

```python
# 예시 코드
```

- 산출물: `{파일}`

## 성공 기준
- [ ] {검증 항목}

## 실패 시 확인 포인트
- {디버깅 힌트}

## 피드백 반영 (재실행 시만)
- 실패 원인: {eval_output.md Feedback 내용}
- 변경 접근법: {이번에 다르게 하는 것}
````

---

## 코드 작성 패턴

Plan Agent가 각 Step의 예시 코드를 작성할 때 따르는 기준.

### State
```python
# ja-agent/src/state.py
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    user_id: int
    session_id: str
    question: str
    answer: str
    retrieved_docs: list[str]
    feedback: str
    retry_count: Annotated[int, operator.add]
```

### LangGraph 노드
```python
# ja-agent/src/nodes/{node_name}.py
from ja_agent.state import AgentState

async def {node_name}_node(state: AgentState) -> dict:
    """
    역할: {설명}
    입력: state["{field}"]
    출력: {field}
    """
    result = await some_service(state["{input_field}"])
    return {"{output_field}": result}
```

### LangGraph StateGraph
```python
# ja-agent/src/graph.py
from langgraph.graph import StateGraph, END
from ja_agent.state import AgentState

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_conditional_edges(
        "generate",
        should_retry,
        {"retry": "retrieve", "done": END}
    )
    return graph.compile()

def should_retry(state: AgentState) -> str:
    return "done" if state["retry_count"] >= 3 else "retry"
```

### BGE-M3 임베딩
```python
# ja-agent/src/services/embedding_service.py
from FlagEmbedding import BGEM3FlagModel

model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)

def embed_query(text: str) -> list[float]:
    result = model.encode(
        [f"query: {text}"], batch_size=1, max_length=8192
    )
    return result["dense_vecs"][0].tolist()  # VECTOR(1024)

def embed_passage(text: str) -> list[float]:
    result = model.encode(
        [f"passage: {text}"], batch_size=1, max_length=8192
    )
    return result["dense_vecs"][0].tolist()
```

### pgvector 유사도 검색
```python
# ja-agent/src/services/vector_store.py
import asyncpg

async def similarity_search(
    conn: asyncpg.Connection,
    user_id: int,
    query_vector: list[float],
    top_k: int = 5,
) -> list[dict]:
    # HNSW 인덱스, 코사인 유사도
    rows = await conn.fetch("""
        SELECT id, content, 1 - (embedding <=> $1::vector) AS score
        FROM resume_chunks
        WHERE user_id = $2
        ORDER BY embedding <=> $1::vector
        LIMIT $3
    """, str(query_vector), user_id, top_k)
    return [dict(r) for r in rows]
```

### Redis 연습 횟수 제한
```python
# ja-agent/src/services/limit_service.py
import redis.asyncio as aioredis

PRACTICE_LIMIT = 5
LIMIT_TTL = 86400  # 24시간

async def check_and_increment(user_id: int, r: aioredis.Redis) -> bool:
    key = f"practice:limit:{user_id}"
    count = await r.incr(key)
    if count == 1:
        await r.expire(key, LIMIT_TTL)
    return count <= PRACTICE_LIMIT
```

### FastAPI 라우터
```python
# ja-agent/src/routers/{resource}.py
from fastapi import APIRouter, Depends, HTTPException
from ja_agent.schemas.{resource} import {Resource}Request, {Resource}Response
from ja_agent.services.{resource}_service import {Resource}Service

router = APIRouter(prefix="/agent/{resource}", tags=["{resource}"])

@router.post("/", response_model={Resource}Response, status_code=201)
async def create_{resource}(
    request: {Resource}Request,
    service: {Resource}Service = Depends(),
):
    try:
        return await service.create(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Pydantic 스키마
```python
# ja-agent/src/schemas/{resource}.py
from pydantic import BaseModel, Field
from datetime import datetime

class {Resource}Request(BaseModel):
    user_id: int
    content: str = Field(..., min_length=1, max_length=5000)

class {Resource}Response(BaseModel):
    id: int
    user_id: int
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
```

### pytest
```python
# ja-agent/tests/test_{module}.py
import pytest

@pytest.mark.asyncio
async def test_{feature}_success():
    state = {
        "user_id": 1,
        "session_id": "test-session",
        "question": "테스트 질문",
        "retry_count": 0,
    }
    result = await {node_name}_node(state)
    assert result["{expected_key}"] is not None

@pytest.mark.asyncio
async def test_retry_limit():
    state = {"retry_count": 3}
    assert should_retry(state) == "done"
```

## 주의사항
- Step 예시 코드는 import 포함, 실행 가능한 수준으로 작성
- 기존 파일 read 후 패턴에 맞춰 코드 작성
- uv 환경 — pyproject.toml 의존성 범위 내에서 작성
- BGE-M3 VECTOR(1024) / Redis TTL 86400 / HNSW 코사인 유사도 구조 준수