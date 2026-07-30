"""GitHub REST API 연동: 멤버별 이번 주차 커밋 조회."""

import datetime
import sys

import requests

GITHUB_API_BASE = "https://api.github.com"
DIFF_TRUNCATE_LEN = 3000


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


def get_commit_diff(repo, sha, token):
    """해당 커밋의 diff를 가져와 3000자로 truncate해서 반환한다.

    실패 시 조용히 넘어가지 않고 명확한 에러 메시지와 함께 프로세스를 종료한다.
    """
    if not token:
        print(
            "[GitHub 오류] GITHUB_TOKEN 환경 변수가 설정되지 않았습니다. "
            ".env 파일에 GITHUB_TOKEN을 설정하세요.",
            file=sys.stderr,
        )
        sys.exit(1)

    url = f"{GITHUB_API_BASE}/repos/{repo}/commits/{sha}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.diff",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
    except requests.RequestException as e:
        print(f"[GitHub 오류] diff 요청 실패 (sha={sha}): {e}", file=sys.stderr)
        sys.exit(1)

    if resp.status_code != 200:
        print(
            f"[GitHub 오류] diff 조회 실패 (status={resp.status_code}, sha={sha}): {resp.text}",
            file=sys.stderr,
        )
        sys.exit(1)

    return resp.text[:DIFF_TRUNCATE_LEN]


_MOCK_COMMITS = {
    "hong-gildong": [],
    "kim-chulsoo": [
        {
            "sha": "e4f5a6b",
            "message": "3장 예외처리 요약 작성",
            "author_date": "2026-07-28T10:12:00Z",
            "url": "https://github.com/org/study-repo/commit/e4f5a6b",
        },
    ],
    "lee-younghee": [
        {
            "sha": "b7c8d9e",
            "message": "공백 수정",
            "author_date": "2026-07-27T23:50:00Z",
            "url": "https://github.com/org/study-repo/commit/b7c8d9e",
        },
        {
            "sha": "c9d0e1f",
            "message": "todo 정리",
            "author_date": "2026-07-28T09:00:00Z",
            "url": "https://github.com/org/study-repo/commit/c9d0e1f",
        },
    ],
}


# --mock용 diff 픽스처 3종
# ① 공백/줄바꿈만 수정
_MOCK_DIFFS = {
    "b7c8d9e": """diff --git a/week4/lee-younghee/exception_summary.md b/week4/lee-younghee/exception_summary.md
index 1a2b3c4..5d6e7f8 100644
--- a/week4/lee-younghee/exception_summary.md
+++ b/week4/lee-younghee/exception_summary.md
@@ -1,5 +1,5 @@
-# 3장 예외처리 요약
-
-## try-except 기본 구조
+# 3장 예외처리 요약
+
+
+## try-except 기본 구조
""",
    # ② 주제와 무관한 파일 수정
    "c9d0e1f": """diff --git a/week4/lee-younghee/todo.txt b/week4/lee-younghee/todo.txt
index 2b3c4d5..6e7f8a9 100644
--- a/week4/lee-younghee/todo.txt
+++ b/week4/lee-younghee/todo.txt
@@ -1,3 +1,4 @@
 우유 사기
 세탁소 들르기
+저녁 약속 8시
 책 반납하기
""",
    # ③ 진짜 "3장 예외처리 요약" 작업
    "e4f5a6b": """diff --git a/week4/kim-chulsoo/exception_summary.md b/week4/kim-chulsoo/exception_summary.md
new file mode 100644
index 0000000..3c4d5e6
--- /dev/null
+++ b/week4/kim-chulsoo/exception_summary.md
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
