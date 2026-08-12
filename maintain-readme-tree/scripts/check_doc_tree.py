#!/usr/bin/env python3
"""Check that repository Markdown docs are reachable from the root README."""

from __future__ import annotations

import argparse
import fnmatch
import re
import sys
import urllib.parse
from collections import deque
from pathlib import Path


DEFAULT_EXCLUDES = (
    ".git/**",
    ".venv/**",
    "venv/**",
    "node_modules/**",
    "vendor/**",
    "dist/**",
    "build/**",
    "**/__pycache__/**",
    "**/.pytest_cache/**",
    "**/.mypy_cache/**",
    "**/.ruff_cache/**",
    "**/*backup*.md",
)
AGENT_INSTRUCTIONS = {"AGENTS.md", "CLAUDE.md"}
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def discover_docs(
    root: Path,
    excludes: tuple[str, ...],
    include_agent_instructions: bool,
) -> set[Path]:
    docs: set[Path] = set()
    for path in root.rglob("*.md"):
        relative = path.relative_to(root).as_posix()
        if matches_any(relative, excludes):
            continue
        if not include_agent_instructions and path.name in AGENT_INSTRUCTIONS:
            continue
        docs.add(path.resolve())
    return docs


def clean_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    elif " " in target:
        target = target.split(" ", 1)[0]
    target = urllib.parse.unquote(target)
    target = target.split("#", 1)[0].split("?", 1)[0]
    return target


def resolve_local_target(source: Path, raw_target: str) -> Path | None:
    target = clean_target(raw_target)
    if not target or target.startswith(("#", "/", "mailto:", "data:")):
        return None
    parsed = urllib.parse.urlparse(target)
    if parsed.scheme or parsed.netloc:
        return None

    resolved = (source.parent / target).resolve()
    if resolved.is_dir():
        resolved = resolved / "README.md"
    return resolved


def read_links(path: Path) -> list[Path]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise RuntimeError(f"cannot read {path}: {exc}") from exc

    links: list[Path] = []
    for match in LINK_PATTERN.finditer(text):
        target = resolve_local_target(path, match.group(1))
        if target is not None:
            links.append(target)
    return links


def relative_display(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def check_tree(
    root: Path,
    excludes: tuple[str, ...],
    include_agent_instructions: bool,
) -> tuple[list[tuple[Path, Path]], list[Path], int]:
    root_readme = (root / "README.md").resolve()
    if not root_readme.is_file():
        raise RuntimeError(f"root README not found: {root_readme}")

    docs = discover_docs(root, excludes, include_agent_instructions)
    graph: dict[Path, list[Path]] = {}
    broken: list[tuple[Path, Path]] = []

    for doc in docs:
        targets = read_links(doc)
        graph[doc] = [target for target in targets if target.suffix.lower() == ".md"]
        for target in targets:
            try:
                target.relative_to(root)
            except ValueError:
                continue
            if not target.exists():
                broken.append((doc, target))

    reachable: set[Path] = set()
    queue: deque[Path] = deque([root_readme])
    while queue:
        current = queue.popleft()
        if current in reachable or current not in docs:
            continue
        reachable.add(current)
        for target in graph.get(current, []):
            if target in docs and target not in reachable:
                queue.append(target)

    unreachable = sorted(docs - reachable, key=lambda path: str(path))
    return broken, unreachable, len(docs)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="检查长期 Markdown 文档是否能从根 README 递归到达",
    )
    parser.add_argument("root", nargs="?", default=".", help="仓库根目录")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="GLOB",
        help="额外排除的仓库相对 glob，可重复传入",
    )
    parser.add_argument(
        "--include-agent-instructions",
        action="store_true",
        help="把 AGENTS.md 和 CLAUDE.md 也纳入文档树",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.root).expanduser().resolve()
    excludes = DEFAULT_EXCLUDES + tuple(args.exclude)

    try:
        broken, unreachable, total = check_tree(
            root,
            excludes,
            args.include_agent_instructions,
        )
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Scanned Markdown docs: {total}")
    if broken:
        print("\nBroken local links:")
        for source, target in broken:
            print(
                f"- {relative_display(source, root)}"
                f" -> {relative_display(target, root)}"
            )
    if unreachable:
        print("\nDocs not reachable from README.md:")
        for path in unreachable:
            print(f"- {relative_display(path, root)}")

    if broken or unreachable:
        return 1
    print("README tree: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
