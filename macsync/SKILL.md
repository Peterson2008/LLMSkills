---
name: macsync
description: Safely synchronize a Git project and optional uncommitted working changes between the current Mac and a Mac mini over SSH. Use when the user asks to sync, hand off, compare, push, pull, or reconcile a local project with Mac mini, especially when development may happen on either machine. Detect dirty worktrees and divergent commits before writing, prefer Git for committed work, use guarded rsync only for explicit worktree handoff, preserve machine-private files, and verify both sides afterward.
---

# Macsync

Synchronize projects without assuming which Mac has the newest copy. Treat Git history as canonical and rsync as a guarded handoff mechanism for uncommitted work.

## Start with an audit

1. Resolve the local repository, peer SSH host, and peer repository path. Do not infer a destructive target from an unresolved variable.
2. Run `scripts/audit_sync.py` with explicit paths.
3. Read both `git status --short`, branches, and HEADs before writing.
4. Preserve unrelated untracked files on either machine.

Example from the laptop:

```bash
python3 <skill-dir>/scripts/audit_sync.py \
  --local /Users/jw/PycharmProjects/VRP_PostProcessing \
  --remote-host macmini \
  --remote /Users/jw/macmini/projects/VRP_PostProcessing
```

Resolve `<skill-dir>` from this `SKILL.md` location.

Known machine mapping:

```text
MacBook project root:  /Users/jw/PycharmProjects/<project>
Mac mini project root: /Users/jw/macmini/projects/<project>
MacBook -> Mac mini:    SSH host macmini
Mac mini -> MacBook:    SSH host macbook
LLMSkills on both:      /Users/jw/PycharmProjects/LLMSkills
```

When running on Mac mini, reverse the audit explicitly:

```bash
python3 <skill-dir>/scripts/audit_sync.py \
  --local /Users/jw/macmini/projects/VRP_PostProcessing \
  --remote-host macbook \
  --remote /Users/jw/PycharmProjects/VRP_PostProcessing
```

## Choose the synchronization path

### Both worktrees clean

- If HEADs match, report already synchronized.
- If one branch is behind, use `git fetch` and fast-forward/push through the configured remote.
- If histories diverged, stop and inspect commits. Do not overwrite with rsync.

### Only one worktree is dirty

- Treat the dirty side as the candidate source only after confirming the user wants that direction.
- Prefer committing the changes, then push/fetch/fast-forward.
- If the user wants an uncommitted handoff, run rsync dry-run first with relative paths and exclusions.
- Transfer only project-owned changed/new files. Remove old paths only when they are confirmed moves or deletions from the source diff.

### Both worktrees dirty

- Do not sync automatically.
- Compare file lists and diffs, identify overlaps, and ask the user how to reconcile them.
- Never choose a winner based only on modification time.

### Branches or HEADs differ

- Use Git to determine ancestry before copying files.
- Fast-forward when possible. For true divergence, merge or rebase only with user authorization.
- Do not use rsync to conceal divergent history.

## Guarded worktree handoff

Use rsync only after the destination worktree is clean for the in-scope files.

Always exclude at least:

```text
.git/
.env
.venv/
__pycache__/
*.pyc
.DS_Store
.claude/
.codex/
```

- Use `-aR` for explicit paths so nested files keep their relative directories.
- Run `-acnR` afterward for checksum dry-run verification.
- Do not use `--delete` by default.
- Before deleting replaced paths, list the exact remote targets and confirm they correspond to source-side moves/deletions.
- Preserve machine-local logs, credentials, IDE state, virtual environments, caches, and generated data unless the user explicitly includes them.

## Verify

After synchronization:

1. Run `git status --short` on both sides.
2. Confirm expected root files and moved paths.
3. Run the project's relevant tests on the destination.
4. Run `git diff --check` on both sides.
5. For worktree handoff, run checksum dry-run and require no output for the transferred scope.
6. Report direction, paths, exclusions, test results, and any intentionally preserved differences.

Never claim full repository equality when only a selected path set was compared.
