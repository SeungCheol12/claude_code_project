# 스터디 저격봇 (Study Sniper Bot)

## 문제

스터디에 가입은 했지만 매주 일요일 밤에 몰아서 과제를 하고, 벌금만 내고 끝나는 멤버가 꼭 있다.
벌금은 "돈 내면 그만"이라 행동을 바꾸지 못한다.

이 봇은 벌금(돈) 대신 **평판(공개 알림)**을 강제 장치로 쓴다. 마감 D-2부터 스터디 슬랙에
진행 상황을 공개해서, 평판을 담보로 잡는다.

GitHub 커밋을 진행률 신호로 삼되, 커밋 "유무"가 아니라 AI(Claude)가 diff "내용"을 읽고
유의미한 진행인지 판단한다. 빈 커밋, 공백만 고친 커밋, 주제와 무관한 파일을 건드린 커밋으로
숫자만 채우는 꼼수를 걸러낸다.

## 동작 방식

1. `config.yaml`에서 스터디 레포, 시작일, 멤버 목록, 이번 주 주제를 읽는다.
2. GitHub API로 멤버별 `week{N}/{github_id}/` 폴더를 건드린 이번 주 커밋을 조회한다.
3. 커밋이 없으면 → 저격 메시지 (마감까지 D-N 포함).
4. 커밋이 있으면 → 각 커밋의 diff를 가져와 Claude에게 판정 요청.
   - 판정 기준: 이번 주 주제 + diff 내용 → `{"meaningful": bool, "summary": str, "progress_pct": int}`
   - 빈 커밋/공백 수정/주제 무관 파일 변경은 `meaningful: false`
   - 커밋 중 하나라도 `meaningful: true`면 → 진행 요약 + 진행률 메시지
   - 전부 `meaningful: false`면 → 꼼수 감지 메시지
5. 전체 멤버 메시지를 "📋 N주차 진행 현황" 리포트 하나로 묶어 Slack에 전송 (채널 도배 방지).

## 설치

```bash
pip install -r requirements.txt
```

`.env.example`을 복사해 `.env`를 만들고 값을 채운다.

```bash
cp .env.example .env
```

| 환경변수 | 용도 |
|---|---|
| `GITHUB_TOKEN` | 스터디 레포 읽기 권한 (커밋 목록/diff 조회) |
| `ANTHROPIC_API_KEY` | Claude API로 diff 판정 |
| `SLACK_WEBHOOK_URL` | 결과 리포트 전송 |
| `JUDGE_MODEL` (선택) | 판정에 쓸 모델 ID. 미설정 시 `claude-sonnet-4-6` 사용 |

`config.yaml`도 실제 스터디에 맞게 수정한다 (`study_repo`, `start_date`, `members`, `weekly_topic`).

## 실행

```bash
python main.py check [옵션]
```

| 플래그 | 설명 |
|---|---|
| `--config PATH` | 설정 파일 경로 (기본값: `config.yaml`) |
| `--mock` | 실제 GitHub API 대신 샘플 커밋/diff 사용 (`GITHUB_TOKEN` 불필요) |
| `--mock-ai` | 실제 Claude API 대신 정해진 판정 결과 사용 (`ANTHROPIC_API_KEY` 불필요) |
| `--dry-run` | Slack 전송 대신 콘솔에 리포트 미리보기 출력 (`SLACK_WEBHOOK_URL` 불필요) |

`--mock`과 `--mock-ai`는 서로 독립적인 플래그다. 예를 들어 `--mock`만 주면 GitHub는 가짜
데이터를 쓰지만 Claude는 실제로 호출한다. 완전히 오프라인으로 돌려보려면 둘 다 붙인다.

`GITHUB_TOKEN` / `ANTHROPIC_API_KEY` / `SLACK_WEBHOOK_URL`이 필요한 상황에서 값이 없으면
에러 메시지와 함께 즉시 종료한다 (silent fail 없음). 에러 메시지가 해당 상황에서 쓸 수 있는
`--mock` / `--mock-ai` / `--dry-run`을 안내해준다.

## 데모 시나리오

`config.yaml`의 데모 멤버 3명은 각각 다른 케이스를 보여주도록 구성되어 있다.

- **홍길동**: 이번 주 커밋 없음 → 🔔 저격 메시지
- **김철수**: "3장 예외처리 요약" 관련 진짜 작업 커밋 → ✅ 진행 요약 + 진행률 메시지
- **이영희**: 공백만 고친 커밋 + 주제와 무관한 파일(개인 todo)을 고친 커밋뿐 → 🕵️ 꼼수 감지 메시지

완전 오프라인 데모 (API 키 불필요, 콘솔 출력만):

```bash
python main.py check --mock --mock-ai --dry-run
```

GitHub만 mock, Claude는 실제 호출 (`ANTHROPIC_API_KEY` 필요, 콘솔 출력만):

```bash
python main.py check --mock --dry-run
```

실제로 Slack까지 전송하려면 `--dry-run`을 빼고 `SLACK_WEBHOOK_URL`을 설정한 뒤 실행한다:

```bash
python main.py check --mock --mock-ai
```

## Non-Goals (지금 하지 않는 것)

- 웹 대시보드, DB, 사용자 인증
- 자동 스케줄링 (cron/GitHub Actions는 향후 계획)
- 디스코드 지원, 멀티 스터디 지원
