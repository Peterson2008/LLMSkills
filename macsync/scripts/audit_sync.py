#!/usr/bin/env python3
"""Read-only Git worktree audit for two repositories connected over SSH."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def run(
    command: list[str],
    cwd: Path | None = None,
    input_text: str | None = None,
) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        input=input_text,
    )
    return result.stdout.rstrip("\n")


def local_state(repo: Path) -> dict[str, object]:
    if not (repo / ".git").exists():
        raise ValueError(f"not a Git repository: {repo}")
    status = run(["git", "status", "--short"], repo).splitlines()
    return {
        "path": str(repo),
        "branch": run(["git", "branch", "--show-current"], repo),
        "head": run(["git", "rev-parse", "HEAD"], repo),
        "status": status,
        "dirty": bool(status),
    }


def remote_state(host: str, repo: str) -> dict[str, object]:
    script = """
set -eu
repo=$1
test -d "$repo/.git"
printf 'BRANCH\\t'
git -C "$repo" branch --show-current
printf 'HEAD\\t'
git -C "$repo" rev-parse HEAD
printf 'STATUS_BEGIN\\n'
git -C "$repo" status --short
printf 'STATUS_END\\n'
"""
    output = run(["ssh", host, "sh", "-s", "--", repo], input_text=script)
    lines = output.splitlines()
    branch = next(line.split("\t", 1)[1] for line in lines if line.startswith("BRANCH\t"))
    head = next(line.split("\t", 1)[1] for line in lines if line.startswith("HEAD\t"))
    start = lines.index("STATUS_BEGIN") + 1
    end = lines.index("STATUS_END")
    status = lines[start:end]
    return {"host": host, "path": repo, "branch": branch, "head": head, "status": status, "dirty": bool(status)}
def classify(local: dict[str, object], remote: dict[str, object]) -> str:
    if local["head"] != remote["head"]:
        return "HEADS_DIFFER_REVIEW_GIT_HISTORY"
    if local["dirty"] and remote["dirty"]:
        return "BOTH_DIRTY_STOP_AND_RECONCILE"
    if local["dirty"]:
        return "LOCAL_WORKTREE_HANDOFF_CANDIDATE"
    if remote["dirty"]:
        return "REMOTE_WORKTREE_HANDOFF_CANDIDATE"
    return "ALREADY_SYNCHRONIZED"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", type=Path, required=True)
    parser.add_argument("--remote-host", required=True)
    parser.add_argument("--remote", required=True)
    args = parser.parse_args()

    local = local_state(args.local.resolve())
    remote = remote_state(args.remote_host, args.remote)
    print(json.dumps({"decision": classify(local, remote), "local": local, "remote": remote}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
