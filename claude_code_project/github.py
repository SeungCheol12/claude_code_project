"""GitHub REST API 연동: 멤버별 이번 주차 커밋 조회."""

import datetime
import sys

import requests

GITHUB_API_BASE = "https://api.github.com"
DIFF_TRUNCATE_LEN = 3000


class GitHubAPIError(Exception):
    """GitHub API 호출 실패. 이를 fatal로 다룰지(die) 개별 멤버만 건너뛸지는 호출부(main.py)가 결정한다."""


def _to_github_datetime(d):
    return datetime.datetime.combine(d, datetime.time.min).strftime("%Y-%m-%dT%H:%M:%SZ")


def _error_reason(resp):
    """GitHub 에러 응답에서 한 줄짜리 사람이 읽을 수 있는 이유를 뽑아낸다."""
    try:
        message = resp.json().get("message")
        if message:
            return message
    except ValueError:
        pass
    return " ".join(resp.text.split())[:200]


def get_member_commits(repo, github_id, week_num, week_start, week_end, token):
    """해당 멤버의 이번 주차 폴더(week{N}/{github_id}/)를 건드린 커밋 목록을 반환한다.

    실패 시 GitHubAPIError를 던진다. 조용히 넘어가지 않는다.
    """
    if not token:
        raise GitHubAPIError(
            "GITHUB_TOKEN 환경 변수가 설정되지 않았습니다. .env 파일에 GITHUB_TOKEN을 설정하세요."
        )

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
        raise GitHubAPIError(f"API 요청 실패 (repo={repo}, path={path}): {e}") from e

    if resp.status_code == 404:
        raise GitHubAPIError(
            f"레포를 찾을 수 없거나 접근 권한이 없습니다: {repo} "
            f"(GITHUB_TOKEN 권한 또는 config.yaml의 study_repo 값을 확인하세요)"
        )

    if resp.status_code != 200:
        raise GitHubAPIError(
            f"API 호출 실패 (status={resp.status_code}, path={path}): {_error_reason(resp)}"
        )

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


def get_commit_diff(repo, sha, token):
    """해당 커밋의 diff를 가져와 3000자로 truncate해서 반환한다.

    실패 시 GitHubAPIError를 던진다. 조용히 넘어가지 않는다.
    """
    if not token:
        raise GitHubAPIError(
            "GITHUB_TOKEN 환경 변수가 설정되지 않았습니다. .env 파일에 GITHUB_TOKEN을 설정하세요."
        )

    url = f"{GITHUB_API_BASE}/repos/{repo}/commits/{sha}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.diff",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
    except requests.RequestException as e:
        raise GitHubAPIError(f"diff 요청 실패 (sha={sha}): {e}") from e

    if resp.status_code != 200:
        raise GitHubAPIError(f"diff 조회 실패 (status={resp.status_code}, sha={sha}): {_error_reason(resp)}")

    return resp.text[:DIFF_TRUNCATE_LEN]


_MOCK_COMMITS = {
    "kim-chulsoo": [],
    "lee-younghee": [
        {
            "sha": "e4f5a6b",
            "message": "3장 예외처리 요약 작성",
            "author_date": "2026-07-28T10:12:00Z",
            "url": "https://github.com/org/study-repo/commit/e4f5a6b",
        },
    ],
}


# --mock용 diff 픽스처: 진짜 "3장 예외처리 요약" 작업 (이영희)
_MOCK_DIFFS = {
    "e4f5a6b": """diff --git a/week4/lee-younghee/exception_summary.md b/week4/lee-younghee/exception_summary.md
new file mode 100644
index 0000000..3c4d5e6
--- /dev/null
+++ b/week4/lee-younghee/exception_summary.md
@@ -0,0 +1,15 @@
+# 3장 예외처리 요약
+
+## try-except 기본 구조
+파이썬은 try 블록에서 예외가 발생하면 except 블록으로 제어가 넘어간다.
+
+```python
+try:
+    result = 10 / 0
+except ZeroDivisionError as e:
+    print(f"에러 발생: {e}")
+```
+
+## finally와 else
+- finally: 예외 발생 여부와 상관없이 항상 실행
+- else: 예외가 없을 때만 실행
""",
}


def get_mock_member_commits(github_id, week_num):
    """--mock 데모용: 실제 GitHub API 호출 없이 샘플 커밋을 반환한다."""
    return list(_MOCK_COMMITS.get(github_id, []))


def get_mock_commit_diff(sha):
    """--mock 데모용: 실제 GitHub API 호출 없이 샘플 diff를 반환한다."""
    if sha not in _MOCK_DIFFS:
        print(f"[GitHub 오류] --mock용 diff 데이터가 없는 커밋입니다: {sha}", file=sys.stderr)
        sys.exit(1)
    return _MOCK_DIFFS[sha][:DIFF_TRUNCATE_LEN]
