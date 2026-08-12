#!/usr/bin/env python3
"""Update a Joplin work-log note while keeping the newest date at the top."""

from __future__ import annotations

import argparse
import datetime
import os
import re
import sys
from pathlib import Path


JOPLIN_NOTES_SCRIPTS = Path(__file__).resolve().parents[2] / "joplin-notes" / "scripts"
sys.path.insert(0, str(JOPLIN_NOTES_SCRIPTS))

from joplin_notes import (  # noqa: E402
    DEFAULT_SETTINGS,
    DEFAULT_URL,
    JoplinClient,
    JoplinError,
    find_note_id,
    read_token,
)


DEFAULT_TITLE = "工作日志"


def parse_items(raw: str) -> list[tuple[str, str]]:
    raw = raw.strip("\n")
    if not raw.strip():
        raise JoplinError("没有日志内容；请从 stdin 传入 Markdown")

    headings = list(re.finditer(r"(?m)^###\s+(.*)$", raw))
    if not headings:
        lines = raw.splitlines()
        return [(lines[0].strip(), "\n".join(lines[1:]).strip())]

    items: list[tuple[str, str]] = []
    for index, match in enumerate(headings):
        title = re.sub(r"^\d+[.、\\]*\s*", "", match.group(1).strip())
        start = match.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(raw)
        items.append((title, raw[start:end].strip()))
    return items


def format_item(number: int, title: str, body: str) -> str:
    block = f"### {number}. {title}"
    if body:
        block += f"\n\n{body}"
    return block


def build_new_body(
    body: str,
    items: list[tuple[str, str]],
    date: str,
) -> str:
    h1 = re.search(r"(?m)^#[ \t]+工作日志[ \t]*$", body)
    if not h1:
        body = f"# 工作日志\n\n{body.strip()}"
        h1 = re.search(r"(?m)^#[ \t]+工作日志[ \t]*$", body)
    assert h1 is not None

    day_headings = list(
        re.finditer(r"(?m)^##[ \t]+(\d{4}-\d{2}-\d{2})(?:[ \t].*)?$", body)
    )
    first_day = day_headings[0] if day_headings else None

    if first_day and first_day.group(1) == date:
        next_day = day_headings[1] if len(day_headings) > 1 else None
        block_end = next_day.start() if next_day else len(body)
        current_day = body[first_day.end() : block_end]
        used_numbers = [
            int(number)
            for number in re.findall(r"(?m)^###[ \t]+(\d+)[.、]", current_day)
        ]
        start_number = max(used_numbers, default=0) + 1
        addition = "\n\n".join(
            format_item(start_number + index, title, item_body)
            for index, (title, item_body) in enumerate(items)
        )
        head = body[:block_end].rstrip()
        tail = body[block_end:].lstrip()
        return f"{head}\n\n{addition}" + (f"\n\n{tail}" if tail else "\n")

    addition = "\n\n".join(
        format_item(index + 1, title, item_body)
        for index, (title, item_body) in enumerate(items)
    )
    new_day = f"## {date}\n\n{addition}"
    head = body[: h1.end()]
    tail = body[h1.end() :].lstrip()
    return f"{head}\n\n{new_day}" + (f"\n\n{tail}" if tail else "\n")


def make_client(args: argparse.Namespace) -> JoplinClient:
    token = read_token(args.token, args.settings)
    return JoplinClient(args.url, token)


def cmd_check(args: argparse.Namespace) -> int:
    client = make_client(args)
    client.ping()
    note_id = find_note_id(client, args.note_id, args.title)
    print(f"OK: Joplin 可连接，目标笔记 ID：{note_id}")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    date = args.date or datetime.date.today().isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise JoplinError(f"日期格式必须是 YYYY-MM-DD：{date}")

    items = parse_items(sys.stdin.read())
    client = make_client(args)
    client.ping()
    note_id = find_note_id(client, args.note_id, args.title)
    note = client.request(
        "GET",
        f"/notes/{note_id}",
        params={"fields": "body,title"},
    )
    new_body = build_new_body(str(note.get("body", "")), items, date)

    if args.dry_run:
        print("=== DRY RUN：正文顶部 40 行 ===\n")
        print("\n".join(new_body.splitlines()[:40]))
        print(f"\n=== 未写入；日期 {date}，共 {len(items)} 个条目 ===")
        return 0

    client.request("PUT", f"/notes/{note_id}", payload={"body": new_body})
    print(f"已写入「{args.title}」：{date}，共 {len(items)} 个条目")
    print(f"链接：[{args.title}](:/{note_id})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="更新 Joplin 工作日志")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_connection_arguments(command: argparse.ArgumentParser) -> None:
        command.add_argument(
            "--url",
            default=os.environ.get("JOPLIN_URL", DEFAULT_URL),
        )
        command.add_argument(
            "--token",
            help="Joplin API token；优先使用 JOPLIN_TOKEN",
        )
        command.add_argument("--settings", default=str(DEFAULT_SETTINGS))
        command.add_argument("--note-id")
        command.add_argument("--title", default=DEFAULT_TITLE)

    check = subparsers.add_parser("check", help="检查连接和目标笔记")
    add_connection_arguments(check)
    check.set_defaults(func=cmd_check)

    update = subparsers.add_parser("update", help="从 stdin 更新日志")
    add_connection_arguments(update)
    update.add_argument("--date", help="覆盖当天日期，格式 YYYY-MM-DD")
    update.add_argument("--dry-run", action="store_true")
    update.set_defaults(func=cmd_update)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.func(args))
    except JoplinError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
