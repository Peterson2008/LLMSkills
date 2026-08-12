---
name: joplin-notes
description: 通过 Joplin 桌面端 Web Clipper API 查找、读取、创建、更新或追加任意 Joplin 笔记。用户要求把内容写进 Joplin、新建 Joplin 笔记、更新指定笔记、读取或检查 Joplin 笔记、或其他不限定为“工作日志”的 Joplin 写入任务时使用。
---

# Joplin Notes

提供通用 Joplin 笔记读写能力。只处理 Joplin 连接、笔记定位和正文写入；面向具体场景的内容整理规则应放在调用方 skill 中。

## Workflow

1. 确认目标：读取、检查、创建、覆盖、追加，还是把 Markdown 内容写入指定位置。
2. 如果用户没有明确目标笔记，优先按标题定位；同名笔记多于一条时不要猜测，要求 `--note-id`。
3. 写入前如用户要求核对，或写入目标/内容有歧义，先使用 `--dry-run`。
4. 通过 `scripts/joplin_notes.py` 操作 Joplin API，不直接修改 Joplin SQLite 数据库。
5. 完成后报告笔记标题、操作结果和 Joplin 内部链接 `[:/note_id]`。

## Common Commands

从本 skill 目录运行脚本：

```bash
python3 scripts/joplin_notes.py check --title "目标笔记"
```

读取笔记正文：

```bash
python3 scripts/joplin_notes.py read --title "目标笔记"
```

创建笔记：

```bash
printf '%s\n' '# 标题' '' '正文' \
  | python3 scripts/joplin_notes.py create --title "目标笔记"
```

覆盖笔记正文：

```bash
printf '%s\n' '新的 Markdown 正文' \
  | python3 scripts/joplin_notes.py update --title "目标笔记"
```

追加到笔记末尾：

```bash
printf '%s\n' '追加的 Markdown 内容' \
  | python3 scripts/joplin_notes.py append --title "目标笔记"
```

## Safety

- 不把 Joplin token 写入 Markdown、日志、命令示例或 skill 文件。
- token 按顺序从 `--token`、`JOPLIN_TOKEN`、Joplin 桌面设置文件读取。
- Joplin 连接配置和故障排查见 `references/joplin-setup.md`。
- 连接失败时保留整理好的 Markdown，并提醒用户打开 Joplin、启用 Web Clipper。
