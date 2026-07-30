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

    for member in cfg["members"]:
        github_id = member["github_id"]
        name = member["name"]

        if args.mock:
            commits = github.get_mock_member_commits(github_id, week["week_num"])
        else:
            commits = github.get_member_commits(
                repo=cfg["study_repo"],
                github_id=github_id,
                week_num=week["week_num"],
                week_start=week["week_start"],
                week_end=week["week_end"],
                token=token,
            )

        print(f"[{name} ({github_id})]")
        if not commits:
            print("  커밋 없음")
        else:
            for c in commits:
                print(f"  - {c['sha']} {c['message']} ({c['author_date']})")

        if not commits:
            message = messages.build_sniper_message(name, deadline_label)
        else:
            judge_results = []
            for c in commits:
                if args.mock:
                    diff = github.get_mock_commit_diff(c["sha"])
                else:
                    diff = github.get_commit_diff(cfg["study_repo"], c["sha"], token)

                if args.mock_ai:
                    result = judge.get_mock_judge_result(c["sha"])
                else:
                    result = judge.judge_diff(cfg["weekly_topic"], diff)
                judge_results.append(result)

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
