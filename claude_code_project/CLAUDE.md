# Study Sniper Bot (스터디 저격봇)

## 프로젝트 개요
스터디 마감 직전에 몰아서 하는 멤버의 문제를 해결하는 봇.
벌금(돈) 대신 **평판(공개 알림)**을 강제 장치로 사용한다.
GitHub 커밋을 진행률 신호로 삼되, 커밋 "유무"가 아니라 AI가 diff "내용"을 읽고
유의미한 진행인지 판단한다. (빈 커밋, 공백 수정 꼼수 차단)

## 페르소나 & 문제
- 페르소나: 스터디에 가입했지만 매주 일요일 밤에 몰아서 하다 벌금만 내는 개발자
- 기존 해법의 실패: 벌금은 "돈 내면 그만"이라 행동을 바꾸지 못함
- 해결: 마감 D-2부터 진행 상황을 스터디 슬랙에 공개 → 평판을 담보로 잡음

## MVP 범위 (오늘 안에 완성할 것만)
1. CLI 명령 하나: `python main.py check` (또는 `npm run check`)
2. GitHub API로 스터디 레포에서 멤버별 이번 주차 커밋 수집
3. 커밋 없음 → 저격 메시지 생성
4. 커밋 있음 → diff를 Claude API에 보내 판정:
   - 유의미한 진행인가? (true/false)
   - 한 줄 진행 요약 + 대략적 진행률(%)
5. 결과를 Slack Incoming Webhook으로 전송
6. `--dry-run` 플래그: Slack 전송 대신 콘솔 출력 (데모/테스트용)

## 명시적 Non-Goals (오늘 하지 않는 것)
- 웹 대시보드, DB, 사용자 인증
- 자동 스케줄링 (cron/GitHub Actions는 발표에서 "향후 계획"으로만 언급)
- 디스코드 지원, 멀티 스터디 지원

## 기술 스택
- Python 3.11+ (표준 라이브러리 + requests + anthropic SDK)
- GitHub REST API (커밋 목록 + diff 조회)
- Anthropic Messages API (모델: claude-sonnet-4-6 계열)
- Slack Incoming Webhook

## 레포 컨벤션 (측정 규칙)
- 스터디 레포 구조: `/week{N}/{github_id}/` 폴더에 각자 과제 제출
- "이번 주차 진행" = 해당 주차 폴더를 건드린 커밋
- 주차 계산: config의 시작일 기준 (config.yaml 참고)

## 설정 파일 (config.yaml)
```yaml
study_repo: "org/study-repo"
start_date: "2026-07-06"      # 1주차 시작 월요일
deadline_weekday: "SUN"        # 매주 일요일 마감
members:
  - github_id: "hong-gildong"
    name: "홍길동"
  - github_id: "kim-chulsoo"
    name: "김철수"
weekly_topic: "3장 예외처리 요약"   # AI 판정 기준으로 전달
```

## 환경 변수 (.env)
- `GITHUB_TOKEN`: 레포 읽기 권한
- `ANTHROPIC_API_KEY`
- `SLACK_WEBHOOK_URL`

## AI 판정 프롬프트 설계 원칙
- 입력: 주차 주제(weekly_topic) + 커밋 diff (너무 길면 앞 3000자 truncate)
- 출력: 반드시 JSON only — `{"meaningful": bool, "summary": str, "progress_pct": int}`
- 빈 커밋, 공백/줄바꿈만 수정, 주제와 무관한 파일 변경은 meaningful: false

## 메시지 톤 가이드
- 저격이지만 유머러스하게. 비난 금지, 팩트 + 가벼운 압박
- 미진행 예: "🔔 홍길동님, 이번 주 폴더가 아직 조용하네요. 마감까지 D-2!"
- 꼼수 감지 예: "🕵️ 김철수님의 커밋 3개를 확인했지만... 전부 공백 수정이었습니다."
- 진행 중 예: "✅ 김철수님: 예외처리 요약 60% 진행 중. 순항하고 있어요."

## 개발 규칙 (Claude Code에게)
- 단계별로 작업하고, 각 단계가 끝나면 실행 방법을 알려줄 것
- 외부 API 호출부는 함수로 분리 (github.py / judge.py / notify.py / main.py)
- GitHub API, Claude API 호출 실패 시 에러 메시지를 명확히 출력하고 죽을 것 (silent fail 금지)
- 테스트용 fixture: 실제 API 없이도 데모 가능하도록 `--mock` 플래그로 샘플 diff 사용 가능하게

## 데모 시나리오 (발표용 — 이 순서가 동작해야 함)
1. 커밋이 없는 멤버 → 저격 메시지가 슬랙에 뜸
2. 빈 커밋/공백 커밋을 일부러 푸시 → AI가 걸러내고 "꼼수 감지" 메시지
3. 진짜 과제 커밋 → 진행 요약 + 진행률 메시지
