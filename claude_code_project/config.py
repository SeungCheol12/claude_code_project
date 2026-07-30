"""config.yaml 로딩 및 주차 계산."""

import datetime
import sys

import yaml

REQUIRED_KEYS = ["study_repo", "start_date", "deadline_weekday", "members", "weekly_topic"]


def load_config(path="config.yaml"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"[설정 오류] 설정 파일을 찾을 수 없습니다: {path}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"[설정 오류] config.yaml 파싱 실패: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(raw, dict):
        print(f"[설정 오류] config.yaml 형식이 올바르지 않습니다: {path}", file=sys.stderr)
        sys.exit(1)

    missing = [k for k in REQUIRED_KEYS if k not in raw]
    if missing:
        print(f"[설정 오류] config.yaml에 필수 항목이 없습니다: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    if not raw["members"]:
        print("[설정 오류] config.yaml의 members 목록이 비어 있습니다.", file=sys.stderr)
        sys.exit(1)

    for m in raw["members"]:
        if "github_id" not in m or "name" not in m:
            print(f"[설정 오류] members 항목에 github_id/name이 모두 필요합니다: {m}", file=sys.stderr)
            sys.exit(1)
        if "mock" in m and not isinstance(m["mock"], bool):
            print(f"[설정 오류] members의 mock 필드는 true/false여야 합니다: {m}", file=sys.stderr)
            sys.exit(1)
        m.setdefault("mock", True)

    try:
        raw["start_date"] = datetime.datetime.strptime(raw["start_date"], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        print(f"[설정 오류] start_date 형식이 잘못되었습니다 (YYYY-MM-DD): {raw.get('start_date')}", file=sys.stderr)
        sys.exit(1)

    return raw


def compute_current_week(start_date, today=None):
    """start_date(월요일 기준)로부터 오늘이 몇 주차인지, 해당 주의 시작/끝을 계산한다."""
    if today is None:
        today = datetime.date.today()

    if today < start_date:
        print(
            f"[설정 오류] 스터디 시작일({start_date.isoformat()})이 아직 도래하지 않았습니다. "
            f"오늘: {today.isoformat()}",
            file=sys.stderr,
        )
        sys.exit(1)

    days_elapsed = (today - start_date).days
    week_num = days_elapsed // 7 + 1
    week_start = start_date + datetime.timedelta(days=(week_num - 1) * 7)
    week_end = week_start + datetime.timedelta(days=7)

    return {
        "week_num": week_num,
        "week_start": week_start,
        "week_end": week_end,
    }
