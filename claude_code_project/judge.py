"""AI 판정: 커밋 diff가 이번 주차 주제에 맞는 유의미한 진행인지 Claude에게 판정받는다."""

import json
import os
import sys

import anthropic

MODEL = os.environ.get("JUDGE_MODEL", "claude-haiku-4-5-20251001")
MAX_TOKENS = 500
DIFF_TRUNCATE_LEN = 3000

SYSTEM_PROMPT = (
    "너는 스터디 그룹원의 커밋 diff를 보고 이번 주 과제 주제에 맞는 유의미한 진행인지 "
    "판정하는 심사관이다. 빈 커밋, 공백/줄바꿈만 수정한 커밋, 주제와 무관한 파일 변경은 "
    "meaningful: false로 판정한다. "
    "반드시 아래 형식의 JSON만 출력하라. 설명, 코드블록 표시(```) 등 다른 텍스트는 "
    "절대 포함하지 마라.\n"
    '{"meaningful": bool, "summary": str, "progress_pct": int}'
)


def judge_diff(weekly_topic, diff_text, api_key=None):
    """주차 주제와 diff를 Claude에 보내 유의미한 진행인지 판정한다.

    반환: {"meaningful": bool, "summary": str, "progress_pct": int}
    API 호출 실패, JSON 파싱 실패 시 명확한 에러 메시지 후 프로세스를 종료한다.
    """
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "[Claude 오류] ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다. "
            ".env에 키를 추가하거나, 데모용으로 --mock-ai 플래그를 사용하세요.",
            file=sys.stderr,
        )
        sys.exit(1)

    truncated_diff = diff_text[:DIFF_TRUNCATE_LEN]
    user_prompt = f"이번 주 주제: {weekly_topic}\n\n커밋 diff:\n{truncated_diff}"

    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except anthropic.APIError as e:
        print(f"[Claude 오류] API 호출 실패: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        text = response.content[0].text
    except (IndexError, AttributeError):
        print(f"[Claude 오류] 응답 형식이 예상과 다릅니다: {response}", file=sys.stderr)
        sys.exit(1)

    return _parse_judge_response(text)


def _strip_code_fence(text):
    """모델이 지시를 어기고 ```json ... ``` 코드펜스로 감싸 응답한 경우를 대비해 벗겨낸다."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[1] if "\n" in stripped else stripped[3:]
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3]
    return stripped.strip()


def _parse_judge_response(text):
    try:
        result = json.loads(_strip_code_fence(text))
    except json.JSONDecodeError:
        print(f"[Claude 오류] 응답이 JSON 형식이 아닙니다:\n{text}", file=sys.stderr)
        sys.exit(1)

    required_keys = ("meaningful", "summary", "progress_pct")
    missing = [k for k in required_keys if k not in result]
    if missing:
        print(
            f"[Claude 오류] 응답 JSON에 필수 필드가 없습니다 ({', '.join(missing)}): {result}",
            file=sys.stderr,
        )
        sys.exit(1)

    return result


_MOCK_JUDGE_RESULTS = {
    "e4f5a6b": {"meaningful": True, "summary": "예외처리 요약", "progress_pct": 60},
}


def get_mock_judge_result(sha):
    """--mock-ai 데모용: 실제 Claude 호출 없이 정해진 판정 결과를 반환한다."""
    if sha not in _MOCK_JUDGE_RESULTS:
        print(f"[Claude 오류] --mock-ai용 판정 데이터가 없는 커밋입니다: {sha}", file=sys.stderr)
        sys.exit(1)
    return dict(_MOCK_JUDGE_RESULTS[sha])
