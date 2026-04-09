# Runner Agent — Job Assistant

## 역할
`.claude/outputs/plan_output.md` 를 읽고 각 Step을 순서대로 실행한다.
실행 결과를 `.claude/outputs/run_output.md` 에 작성한다.

## 실행 절차

### 1. plan_output.md 확인
`.claude/outputs/plan_output.md` 읽기
- 없으면 즉시 중단 — "plan_output.md 없음" 오류 기록
- `## 실행 단계` Step 목록 파악
- `## 성공 기준` 체크리스트 파악

### 2. Step별 실행
각 Step 순서대로:
1. 대상 파일 read
2. 예시 코드 확인
3. 작업 수행 (Write / Edit)
4. run_output.md에 해당 Step 결과 즉시 기록

### 3. 테스트 실행
```bash
# Python Agent 테스트 (bash 허용 범위)
cd ja-agent && uv run pytest tests/{test_file}.py -v
```

### 4. 오류 처리
- 동일 Step 최대 2회 재시도
- 2회 실패 시 FAILED 기록 후 다음 Step 진행
- 기존 코드 삭제 금지 — 추가/수정만 허용

---

## 출력 형식 (.claude/outputs/run_output.md)

```markdown
# Run Output
- timestamp: {ISO8601}
- task: {plan_output의 task}
- retry_count: {plan_output의 retry_count}

## 실행 요약
| Step | 상태 | 산출물 |
|------|------|--------|
| Step 1. {단계명} | ✅ PASS / ❌ FAIL | `{파일}` |
| Step 2. {단계명} | ✅ PASS / ❌ FAIL | `{파일}` |

## Step별 상세 결과

### Step 1. {단계명}
- 상태: PASS / FAIL
- 실행 내용: {실제로 한 작업}
- 산출물:
  ```python
  {작성/수정된 코드}
  ```
- 오류 (있을 경우): {메시지}

## 성공 기준 체크
- [x] {달성 항목}
- [ ] {미달성 항목} — {이유}

## 전체 상태
PASS / PARTIAL / FAIL
```

## 주의사항
- 파일 수정 전 반드시 read 먼저
- bash는 테스트 명령어만 허용 (서버 기동 / DB 마이그레이션 금지)
- 기존 파일 삭제 금지
- uv 환경 — pyproject.toml 의존성 변경 금지