# Joplin Setup

## Desktop Setup

在 Joplin 桌面端启用：

```text
Joplin -> Preferences -> Web Clipper -> Enable Web Clipper service
```

默认 API 地址：

```text
http://127.0.0.1:41184
```

端口不同时设置：

```bash
export JOPLIN_URL="http://127.0.0.1:41185"
```

## Token

脚本不保存 token，按以下顺序读取：

1. `--token`
2. 环境变量 `JOPLIN_TOKEN`
3. `~/.config/joplin-desktop/settings.json` 中的 `api.token`

不要把 token 写入仓库或 Markdown 文档。

## Troubleshooting

- 无法连接：确认 Joplin 正在运行，Web Clipper 已启用，端口与 `JOPLIN_URL` 一致。
- 找不到笔记：确认标题正确，或者传入 `--note-id`。
- 多条同名笔记：传入明确的 `--note-id`。
- 找不到 token：设置 `JOPLIN_TOKEN`，或者确认 Joplin 设置文件包含 `api.token`。
