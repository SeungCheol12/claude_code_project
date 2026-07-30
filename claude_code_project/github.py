"""GitHub REST API 연동: 멤버별 이번 주차 커밋 조회."""

import datetime
import sys

import requests

GITHUB_API_BASE = "https://api.github.com"


def _to_github_datetime(d):
    return datetime.datetime.combine(d, datetime.time.min).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_member_commits(repo, github_id, week_num, week_start, week_end, token):
    """해당 멤버의 이번 주차 폴더(week{N}/{github_id}/)를 건드린 커밋 목록을 반환한다.

    실패 시 조용히 넘어가지 않고 명확한 에러 메시지와 함께 프로세스를 종료한다.
    """
    if not token:
        print(
            "[GitHub 오류] GITHUB_TOKEN 환경 변수가 설정되지 않았습니다. "
            ".env 파일에 GITHUB_TOKEN을 설정하세요.",
            file=sys.stderr,
        )
        sys.exit(1)

    path = f"week{week_num}/{github_id}"
    url = f"{GITHUB_API_BASE}/repos/{repo}/commits"
    params = {
        "path": path,
        "since": _to_github_datetime(week_start),
        "until": _to_github_datetime(week_end),
        "per_page": 100,
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
    except requests.RequestException as e:
        print(f"[GitHub 오류] API 요청 실패 (repo={repo}, path={path}): {e}", file=sys.stderr)
        sys.exit(1)

    if resp.status_code == 404:
        print(
            f"[GitHub 오류] 레포를 찾을 수 없거나 접근 권한이 없습니다: {repo} "
            f"(GITHUB_TOKEN 권한 또는 config.yaml의 study_repo 값을 확인하세요)",
            file=sys.stderr,
        )
        sys.exit(1)

    if resp.status_code != 200:
        print(
            f"[GitHub 오류] API 호출 실패 (status={resp.status_code}, path={path}): {resp.text}",
            file=sys.stderr,
        )
        sys.exit(1)

    commits = resp.json()

    return [
        {
            "sha": c["sha"][:7],
            "message": c["commit"]["message"].splitlines()[0],
            "author_date": c["commit"]["author"]["date"],
            "url": c["html_url"],
        }
        for c in commits
    ]


_MOCK_COMMITS = {
    "hong-gildong": [],
    "kim-chulsoo": [
        {
            "sha": "a1b2c3d",
            "message": "공백 수정",
            "author_date": "2026-07-27T23:50:00Z",
            "url": "https://github.com/org/study-repo/commit/a1b2c3d",
        },
        {
            "sha": "e4f5a6b",
            "message": "3장 예외처리 요약 작성",
            "author_date": "2026-07-28T10:12:00Z",
            "url": "https://github.com/org/study-repo/commit/e4f5a6b",
        },
    ],
}


def get_mock_member_commits(github_id, week_num):
    """--mock 데모용: 실제 GitHub API 호출 없이 샘플 커밋을 반환한다."""
    return list(_MOCK_COMMITS.get(github_id, []))
