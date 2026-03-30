# ja-agent

> **Job Assistant** 프로젝트의 AI 에이전트 서버입니다.

## 프로젝트 소개

Job Assistant는 취업 준비생을 위한 AI 기반 면접 준비 플랫폼입니다.

`ja-agent`는 LangGraph 기반 멀티 에이전트 아키텍처로 구성된 AI 서비스 서버로, 문서 임베딩, 트리플 RAG 질문 생성, 답변 평가, 역질문 생성, STT 등 AI 관련 기능 전반을 FastAPI REST API로 제공합니다.

`ja-backend`(Spring Boot)는 파일 저장 및 비즈니스 로직을 담당하고, AI 처리가 필요한 시점에 `ja-agent`를 호출하는 구조로 동작합니다.

## 관련 레포지토리

| 레포 | 설명 |
|------|------|
| [ja-infra](https://github.com/job-assistant/ja-infra) | Docker Compose, PostgreSQL+pgvector, Redis |
| [ja-backend](https://github.com/job-assistant/ja-backend) | Spring Boot REST API 서버 |
| [ja-frontend](https://github.com/job-assistant/ja-frontend) | React + TypeScript 프론트엔드 |

## 기술 스택

| 분류 | 기술 |
|------|------|
| 언어 / 패키지 관리 | Python 3.12, uv |
| API 서버 | FastAPI, uvicorn |
| AI 오케스트레이션 | LangGraph, LangChain |
| LLM | OpenAI API (GPT-4o, GPT-4o-mini) |
| 문서 파싱 | LlamaParse |
| 임베딩 | BGE-M3 (BAAI/bge-m3, 1024차원) |
| 벡터 DB | PostgreSQL + pgvector (HNSW) |
| 세션 관리 | Redis |
| STT | Whisper (large-v2) |
| ORM | SQLAlchemy (async) |

## 프로젝트 구조

```
ja-agent/
├── main.py                     # FastAPI 애플리케이션 진입점
├── pyproject.toml              # 프로젝트 의존성 및 메타데이터
├── .env.example                # 환경 변수 템플릿
└── app/
    ├── agent/                  # LangGraph 에이전트 구현
    ├── api/                    # FastAPI 라우터 및 엔드포인트
    └── core/
        ├── config.py           # 환경 변수 기반 설정 관리
        ├── logging.py          # 로깅 설정
        ├── db/
        │   └── database.py     # 비동기 DB 세션 및 커넥션 풀
        └── error/
            ├── exceptions.py       # 커스텀 예외 클래스
            ├── errors.py           # 에러 응답 스키마
            └── exception_handlers.py  # FastAPI 예외 핸들러
```

## 시작하기

### 사전 요구사항

- Python 3.12
- [uv](https://docs.astral.sh/uv/) 패키지 관리자
- PostgreSQL (pgvector 확장 포함)
- Redis

인프라 구성은 [ja-infra](https://github.com/job-assistant/ja-infra) 레포지토리를 참고하세요.

### 설치

```bash
# 저장소 클론
git clone https://github.com/job-assistant/ja-agent.git
cd ja-agent

# 의존성 설치
uv sync

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 필요한 값을 채워주세요
```

### 환경 변수 설정

`.env` 파일에서 아래 항목을 설정합니다.

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `OPENAI_API_KEY` | OpenAI API 키 | `sk-...` |
| `LLAMA_CLOUD_API_KEY` | LlamaCloud API 키 | `llx-...` |
| `HF_TOKEN` | HuggingFace 토큰 (화자 분리용) | `hf_...` |
| `POSTGRES_HOST` | PostgreSQL 호스트 | `localhost` |
| `POSTGRES_EXTERNAL_PORT` | PostgreSQL 포트 | `5433` |
| `POSTGRES_USER` | DB 사용자명 | `postgres` |
| `POSTGRES_PASSWORD` | DB 비밀번호 | `postgres` |
| `POSTGRES_DB` | DB 이름 | `ai_agent` |
| `ENVIRONMENT` | 실행 환경 | `development` |
| `LOG_LEVEL` | 로그 레벨 | `INFO` |

전체 설정 목록은 `.env.example`을 참고하세요.

### 서버 실행

```bash
uv run python main.py
```

서버는 기본적으로 `http://0.0.0.0:8888`에서 실행됩니다.

## API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 서버 상태 확인 |

## 에러 처리

모든 에러는 아래 형식의 JSON으로 반환됩니다.

```json
{
  "error": true,
  "type": "ErrorType",
  "message": "에러 메시지",
  "path": "/endpoint/path",
  "details": {},
  "status_code": 400
}
```

| 예외 클래스 | HTTP 상태 코드 | 설명 |
|-------------|----------------|------|
| `ValidationException` | 400 | 입력값 검증 실패 |
| `DocumentProcessingException` | 422 | 문서 처리 오류 |
| `LLMException` | 503 | LLM 호출 오류 |
| `WorkflowException` | 500 | 워크플로우 실행 오류 |
| `DatabaseException` | 500 | DB 오류 |