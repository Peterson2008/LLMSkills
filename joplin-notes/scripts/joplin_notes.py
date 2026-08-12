#!/usr/bin/env python3
"""Read and write Joplin notes through the Web Clipper API."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_URL = "http://127.0.0.1:41184"
DEFAULT_SETTINGS = Path.home() / ".config" / "joplin-desktop" / "settings.json"


class JoplinError(RuntimeError):
    pass


def read_token(explicit: str | None, settings_path: str) -> str:
    if explicit and explicit.strip():
        return explicit.strip()

    environment_token = os.environ.get("JOPLIN_TOKEN")
    if environment_token and environment_token.strip():
        return environment_token.strip()

    path = Path(settings_path).expanduser()
    if path.exists():
        try:
            settings = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise JoplinError(f"无法读取 Joplin 设置文件：{path}") from exc
        token = settings.get("api.token")
        if isinstance(token, str) and token.strip():
            return token.strip()

    raise JoplinError(
        "找不到 Joplin token；请设置 JOPLIN_TOKEN，"
        f"或确认 {path} 中存在 api.token"
    )


class JoplinClient:
    def __init__(self, url: str, token: str) -> None:
        self.url = url.rstrip("/")
        self.token = token

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        query = dict(params or {})
        query["token"] = self.token
        url = f"{self.url}{path}?{urllib.parse.urlencode(query)}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                text = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise JoplinError(f"Joplin API 返回 HTTP {exc.code}：{detail[:300]}") from exc
        except urllib.error.URLError as exc:
            raise JoplinError(
                f"无法连接 Joplin（{self.url}）；请打开 Joplin 并启用 Web Clipper"
            ) from exc

        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise JoplinError(f"Joplin API 返回了无效 JSON：{text[:300]}") from exc

    def ping(self) -> None:
        request = urllib.request.Request(f"{self.url}/ping", method="GET")
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                text = response.read().decode("utf-8").strip()
        except urllib.error.URLError as exc:
            raise JoplinError(
                f"无法连接 Joplin（{self.url}）；请打开 Joplin 并启用 Web Clipper"
            ) from exc
        if text != "JoplinClipperServer":
            raise JoplinError(f"Joplin ping 返回异常内容：{text}")


def find_note_id(client: JoplinClient, note_id: str | None, title: str) -> str:
    if note_id:
        return note_id

    result = client.request(
        "GET",
        "/search",
        params={"query": title, "type": "note", "fields": "id,title"},
    )
    matches = [
        item
        for item in result.get("items", [])
        if isinstance(item, dict) and item.get("title") == title
    ]
    if len(matches) == 1:
        return str(matches[0]["id"])
    if not matches:
        raise JoplinError(f"没有找到标题为「{title}」的笔记；可用 --note-id 指定")
    ids = ", ".join(str(item.get("id")) for item in matches)
    raise JoplinError(f"存在多条「{title}」笔记；请用 --note-id 指定：{ids}")


def make_client(args: argparse.Namespace) -> JoplinClient:
    token = read_token(args.token, args.settings)
    return JoplinClient(args.url, token)


def read_stdin() -> str:
    body = sys.stdin.read()
    if not body.strip():
        raise JoplinError("没有内容；请从 stdin 传入 Markdown")
    return body.rstrip("\n") + "\n"


def read_note(client: JoplinClient, note_id: str) -> dict[str, str]:
    note = client.request(
        "GET",
        f"/notes/{note_id}",
        params={"fields": "id,title,body,parent_id"},
    )
    return {key: str(note.get(key, "")) for key in ("id", "title", "body", "parent_id")}


def note_link(title: str, note_id: str) -> str:
    return f"[{title}](:/{note_id})"


def cmd_check(args: argparse.Namespace) -> int:
    client = make_client(args)
    client.ping()
    note_id = find_note_id(client, args.note_id, args.title)
    print(f"OK: Joplin 可连接，目标笔记 ID：{note_id}")
    return 0


def cmd_read(args: argparse.Namespace) -> int:
    client = make_client(args)
    client.ping()
    note_id = find_note_id(client, args.note_id, args.title)
    note = read_note(client, note_id)
    print(note["body"], end="" if note["body"].endswith("\n") else "\n")
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    body = read_stdin()
    client = make_client(args)
    client.ping()
    payload: dict[str, str] = {"title": args.title, "body": body}
    if args.parent_id:
        payload["parent_id"] = args.parent_id

    if args.dry_run:
        print(f"=== DRY RUN：将创建「{args.title}」 ===\n")
        print(body, end="")
        print("\n=== 未写入 ===")
        return 0

    note = client.request("POST", "/notes", payload=payload)
    note_id = str(note.get("id", ""))
    print(f"已创建「{args.title}」")
    print(f"链接：{note_link(args.title, note_id)}")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    body = read_stdin()
    client = make_client(args)
    client.ping()
    note_id = find_note_id(client, args.note_id, args.title)
    if args.dry_run:
        print(f"=== DRY RUN：将覆盖「{args.title}」 ===\n")
        print(body, end="")
        print("\n=== 未写入 ===")
        return 0

    client.request("PUT", f"/notes/{note_id}", payload={"body": body})
    print(f"已更新「{args.title}」")
    print(f"链接：{note_link(args.title, note_id)}")
    return 0


def cmd_append(args: argparse.Namespace) -> int:
    addition = read_stdin()
    client = make_client(args)
    client.ping()
    note_id = find_note_id(client, args.note_id, args.title)
    note = read_note(client, note_id)
    current = note["body"].rstrip()
    separator = "\n\n" if current else ""
    new_body = f"{current}{separator}{addition}"

    if args.dry_run:
        print(f"=== DRY RUN：将追加到「{args.title}」；正文末尾预览 ===\n")
        print("\n".join(new_body.splitlines()[-40:]))
        print("\n=== 未写入 ===")
        return 0

    client.request("PUT", f"/notes/{note_id}", payload={"body": new_body})
    print(f"已追加到「{args.title}」")
    print(f"链接：{note_link(args.title, note_id)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="读写 Joplin 笔记")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_connection_arguments(command: argparse.ArgumentParser) -> None:
        command.add_argument("--url", default=os.environ.get("JOPLIN_URL", DEFAULT_URL))
        command.add_argument("--token", help="Joplin API token；优先使用 JOPLIN_TOKEN")
        command.add_argument("--settings", default=str(DEFAULT_SETTINGS))

    def add_note_arguments(command: argparse.ArgumentParser) -> None:
        command.add_argument("--note-id")
        command.add_argument("--title", required=True)

    check = subparsers.add_parser("check", help="检查连接和目标笔记")
    add_connection_arguments(check)
    add_note_arguments(check)
    check.set_defaults(func=cmd_check)

    read = subparsers.add_parser("read", help="读取目标笔记正文")
    add_connection_arguments(read)
    add_note_arguments(read)
    read.set_defaults(func=cmd_read)

    create = subparsers.add_parser("create", help="从 stdin 创建笔记")
    add_connection_arguments(create)
    create.add_argument("--title", required=True)
    create.add_argument("--parent-id", help="目标 notebook/folder ID")
    create.add_argument("--dry-run", action="store_true")
    create.set_defaults(func=cmd_create)

    update = subparsers.add_parser("update", help="从 stdin 覆盖目标笔记正文")
    add_connection_arguments(update)
    add_note_arguments(update)
    update.add_argument("--dry-run", action="store_true")
    update.set_defaults(func=cmd_update)

    append = subparsers.add_parser("append", help="从 stdin 追加到目标笔记末尾")
    add_connection_arguments(append)
    add_note_arguments(append)
    append.add_argument("--dry-run", action="store_true")
    append.set_defaults(func=cmd_append)

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
