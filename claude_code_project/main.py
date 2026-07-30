"""스터디 저격봇 CLI."""

import argparse
import os
import sys

from dotenv import load_dotenv

import config as config_module
import github
import judge
import messages
import notify

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def _fetch_commits(cfg, github_id, week, token, resilient):
    """실제 GitHub 커밋 조회. resilient=True면 실패 시 죽지 않고 (None, 에러메시지)를 반환한다."""
    try:
        commits = github.get_member_commits(
            repo=cfg["study_repo"],
            github_id=github_id,
            week_num=week["week_num"],
            week_start=week["week_start"],
            week_end=week["week_end"],
            token=token,
        )
        return commits, None
    except github.GitHubAPIError as e:
        if resilient:
            return None, str(e)
        print(f"[GitHub 오류] {e}", file=sys.stderr)
        sys.exit(1)


def _fetch_diff(cfg, sha, token, resilient):
    """실제 GitHub diff 조회. resilient=True면 실패 시 죽지 않고 (None, 에러메시지)를 반환한다."""
    try:
        diff = github.get_commit_diff(cfg["study_repo"], sha, token)
        return diff, None
    except github.GitHubAPIError as e:
        if resilient:
            return None, str(e)
        print(f"[GitHub 오류] {e}", file=sys.stderr)
        sys.exit(1)


def cmd_check(args):
    load_dotenv()

    cfg = config_module.load_config(args.config)
    week = config_module.compute_current_week(cfg["start_date"])

    print(f"레포: {cfg['study_repo']}")
    print(f"주차: {week['week_num']}주차 ({week['week_start']} ~ {week['week_end']})")
    print(f"이번 주 주제: {cfg['weekly_topic']}")
    if args.mock:
        print("(--mock 모드: 실제 GitHub API 호출 없이 샘플 데이터를 사용합니다)")
    print("-" * 50)

    token = os.environ.get("GITHUB_TOKEN")
    deadline_label = messages.compute_deadline_label(week["week_start"], cfg["deadline_weekday"])
    member_messages = []

    # 하이브리드 모드: --mock이어도 member.mock=false면 그 멤버는 실제 GitHub 조회 대상
    real_fetch_members = [m for m in cfg["members"] if not args.mock or not m["mock"]]
    if real_fetch_members and not token:
        names = ", ".join(m["name"] for m in real_fetch_members)
        print(
            f"[GitHub 오류] 실제 GitHub 조회가 필요한 멤버가 있는데 ({names}) "
            "GITHUB_TOKEN 환경 변수가 설정되지 않았습니다. .env 파일에 GITHUB_TOKEN을 설정하세요.",
            file=sys.stderr,
        )
        sys.exit(1)

    for member in cfg["members"]:
        github_id = member["github_id"]
        name = member["name"]
        use_mock = args.mock and member["mock"]
        # --mock 실행 중 특정 멤버만 실제 조회하는 하이브리드 오버라이드는
        # 발표 중 사고를 막기 위해 실패해도 죽지 않고 그 멤버만 건너뛴다.
        hybrid_override = args.mock and not member["mock"]

        print(f"[{name} ({github_id})]" + (" (실제 조회)" if hybrid_override else ""))

        fetch_error = None
        if use_mock:
            commits = github.get_mock_member_commits(github_id, week["week_num"])
        else:
            commits, fetch_error = _fetch_commits(cfg, github_id, week, token, resilient=hybrid_override)

        if fetch_error:
            print(f"  ⚠️ 조회 실패: {fetch_error}")
        elif not commits:
            print("  커밋 없음")
        else:
            for c in commits:
                print(f"  - {c['sha']} {c['message']} ({c['author_date']})")

        if fetch_error:
            message = messages.build_fetch_failed_message(name, fetch_error)
        elif not commits:
            message = messages.build_sniper_message(name, deadline_label)
        else:
            judge_results = []
            diff_error = None
            for c in commits:
                if use_mock:
                    diff = github.get_mock_commit_diff(c["sha"])
                else:
                    diff, diff_error = _fetch_diff(cfg, c["sha"], token, resilient=hybrid_override)
                    if diff_error:
                        break

                # --mock-ai는 mock 커밋에만 적용한다. 실제로 조회한 커밋(하이브리드 오버라이드)은
                # sha를 미리 알 수 없어 mock 판정 데이터가 있을 수 없으므로 항상 실제로 판정한다.
                if args.mock_ai and use_mock:
                    result = judge.get_mock_judge_result(c["sha"])
                else:
                    result = judge.judge_diff(cfg["weekly_topic"], diff)
                judge_results.append(result)

            if diff_error:
                print(f"  ⚠️ diff 조회 실패: {diff_error}")
                message = messages.build_fetch_failed_message(name, diff_error)
            else:
                meaningful_results = [r for r in judge_results if r["meaningful"]]
                if meaningful_results:
                    best = max(meaningful_results, key=lambda r: r["progress_pct"])
                    message = messages.build_progress_message(name, best["summary"], best["progress_pct"])
                else:
                    reasons = [r["summary"] for r in judge_results]
                    message = messages.build_cheat_detected_message(name, len(commits), reasons)

        member_messages.append(message)
        if args.dry_run:
            print(f"  📨 {message}")
        print()

    header = f"📋 {week['week_num']}주차 진행 현황"

    print("-" * 50)
    if args.dry_run:
        print("[Slack 리포트 미리보기 (dry-run이라 실제 전송하지 않음)]")
        print(header)
        print()
        for m in member_messages:
            print(m)
    else:
        notify.send_report(header, member_messages)


def main():
    parser = argparse.ArgumentParser(prog="main.py", description="스터디 저격봇")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="이번 주차 멤버별 커밋 현황 조회")
    check_parser.add_argument("--config", default="config.yaml", help="설정 파일 경로 (기본: config.yaml)")
    check_parser.add_argument("--mock", action="store_true", help="실제 GitHub API 대신 샘플 데이터 사용")
    check_parser.add_argument("--dry-run", action="store_true", help="Slack 전송 대신 콘솔에 메시지 출력")
    check_parser.add_argument(
        "--mock-ai", action="store_true", help="실제 Claude API 대신 정해진 판정 결과 사용 (ANTHROPIC_API_KEY 불필요)"
    )
    check_parser.set_defaults(func=cmd_check)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n중단되었습니다.", file=sys.stderr)
        sys.exit(1)
