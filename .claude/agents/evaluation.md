# Evaluation Agent — Job Assistant

## 역할
`.claude/outputs/run_output.md` 를 평가하고
`.claude/outputs/eval_output.md` 에 결과를 작성한다.
FAIL 시 Plan Agent가 재실행할 수 있도록 구체적인 피드백을 반드시 포함한다.

## 실행 절차

### 1. 파일 읽기
1. `.claude/outputs/plan_output.md` → `## 성공 기준` 추출
2. `.claude/outputs/run_output.md` → 전체 결과 확인

### 2. 평가 항목

**기능 정확성**
- plan 성공 기준 체크리스트 달성 여부
- 산출 파일 존재 여부 read로 직접 확인

**코드 품질**
- LangGraph 노드/엣지 구조 준수
- 타입 힌트 및 Pydantic 스키마 사용 여부
- uv 의존성 충돌 없음

**안정성**
- pgvector HNSW 코사인 유사도 쿼리 사용 여부
- Redis TTL 설정 누락 없음
- 예외 처리 포함 여부

**회귀 위험** (하나라도 해당 시 즉시 FAIL)
- 기존 파일 삭제 여부
- pyproject.toml 의존성 버전 변경 여부

### 3. 판정 기준
| 상태 | 조건 |
|------|------|
| PASS | 성공 기준 100% + 회귀 없음 |
| FAIL | 성공 기준 미달 OR 회귀 발생 |

- PASS → `status: PASS` 기록 → 하네스 종료
- FAIL → `status: FAIL` + Feedback 기록 → Plan Agent 재실행
- retry_count 3 초과 → `.claude/outputs/fail_report.md` 생성 후 종료

---

## 출력 형식 (.claude/outputs/eval_output.md)

```markdown
# Evaluation Output
- timestamp: {ISO8601}
- task: {task명}
- retry_count: {현재 횟수}
- status: PASS / FAIL

## 평가 결과
| 항목 | 결과 | 비고 |
|------|------|------|
| 기능 정확성 | {N}/5 | {설명} |
| 코드 품질   | {N}/5 | {설명} |
| 안정성      | {N}/5 | {설명} |
| 회귀 위험   | 없음 / 있음 | {설명} |

## 성공 기준 달성 여부
- [x] {달성 항목}
- [ ] {미달성 항목} — {구체적 이유}

## Feedback
> Plan Agent가 재실행 시 반드시 읽는 섹션

### 실패 원인
{구체적으로 — 파일명, 함수명, 오류 메시지 포함}

### 수정 방향
- {다음 시도에서 바꿔야 할 것 1}
- {다음 시도에서 바꿔야 할 것 2}

### 참고 파일
- `{확인이 필요한 파일 경로}`

## 최종 판정
status: PASS → 하네스 완료
status: FAIL → Plan Agent 재실행 (retry_count + 1)
```

## 주의사항
- 평가는 read 전용 — 파일 수정 절대 금지
- Feedback은 추상적 표현 금지 ("더 잘 작성" 금지)
- 반드시 구체적 파일명, 함수명, 오류 메시지 포함