"""CLAUDE.md 메시지 톤 가이드에 따른 멤버별 저격/진행 메시지 생성."""

import datetime

WEEKDAY_INDEX = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}


def compute_deadline_label(week_start, deadline_weekday, today=None):
    """이번 주 마감일까지 D-N 라벨을 계산한다. (예: "D-2", "D-day", "마감 1일 초과")"""
    if today is None:
        today = datetime.date.today()

    idx = WEEKDAY_INDEX[deadline_weekday.upper()]
    deadline_date = week_start + datetime.timedelta(days=idx)
    delta = (deadline_date - today).days

    if delta > 0:
        return f"D-{delta}"
    if delta == 0:
        return "D-day"
    return f"마감 {-delta}일 초과"


def build_sniper_message(member_name, deadline_label):
    """커밋 없음 → 저격 메시지."""
    return f"🔔 {member_name}님, 이번 주 폴더가 아직 조용하네요. 마감까지 {deadline_label}!"


def build_cheat_detected_message(member_name, commit_count, reasons):
    """AI 판정 결과 전부 meaningful=false → 꼼수 감지 메시지."""
    reason_text = ", ".join(reasons) if reasons else "의미 없는 변경"
    return (
        f"🕵️ {member_name}님의 커밋 {commit_count}개를 확인했지만... "
        f"전부 의미 없는 변경이었습니다. ({reason_text})"
    )


def build_progress_message(member_name, summary, progress_pct):
    """AI 판정 결과 meaningful=true인 커밋이 있음 → 진행 요약 + 진행률 메시지."""
    return f"✅ {member_name}님: {summary} (진행률 {progress_pct}%). 순항하고 있어요!"
