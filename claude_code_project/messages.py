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


def build_progress_check_message(member_name, commits):
    """커밋 있음 → 잠정 '진행 확인' 메시지.

    AI 판정(judge.py)이 붙기 전까지 쓰는 자리표시자.
    다음 단계에서 judge.py 결과(meaningful/summary/progress_pct)를 받아
    "✅ ... 60% 진행 중" / "🕵️ ... 전부 공백 수정" 메시지로 교체될 예정이므로,
    호출부(main.py)는 이 함수만 바꿔 끼우면 되도록 분리해둔다.
    """
    return f"🔍 {member_name}님의 커밋 {len(commits)}개를 확인했습니다. (진행 내용 AI 판정 예정)"


def build_member_message(member_name, commits, deadline_label):
    """멤버의 이번 주 커밋 유무에 따라 적절한 메시지를 생성한다."""
    if not commits:
        return build_sniper_message(member_name, deadline_label)
    return build_progress_check_message(member_name, commits)
