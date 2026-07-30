"""Slack Incoming Webhook으로 멤버별 메시지를 묶은 리포트 전송."""

import os
import sys

import requests


def send_report(header, member_messages, webhook_url=None):
    """header + 멤버별 메시지를 하나의 리포트로 묶어 Slack에 전송한다.

    채널 도배 방지를 위해 멤버 수만큼 여러 건을 보내지 않고, 한 번의 요청으로 전송한다.
    실패 시 조용히 넘어가지 않고 명확한 에러 메시지와 함께 프로세스를 종료한다.
    """
    webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print(
            "[Slack 오류] SLACK_WEBHOOK_URL 환경 변수가 설정되지 않았습니다. "
            ".env에 웹훅 URL을 추가하거나, --dry-run으로 콘솔 출력만 확인하세요.",
            file=sys.stderr,
        )
        sys.exit(1)

    text = header + "\n\n" + "\n\n".join(member_messages)
    payload = {"text": text}

    try:
        resp = requests.post(webhook_url, json=payload, timeout=15)
    except requests.RequestException as e:
        print(f"[Slack 오류] 전송 실패: {e}", file=sys.stderr)
        sys.exit(1)

    if resp.status_code != 200:
        print(
            f"[Slack 오류] 전송 실패 (status={resp.status_code}): {resp.text}",
            file=sys.stderr,
        )
        sys.exit(1)

    print("[Slack] 전송 성공 ✅")
