---
name: lark-doc
description: 飞书云文档（Docx / Wiki）内容操作：读取、创建、编辑文档，插入或下载图片附件。用户提供飞书文档 URL 或 token 时使用；通过本机 lark-cli 和已授权飞书用户身份调用飞书开放 API。
---

# lark-doc

通过本机 `lark-cli` 和已授权的飞书用户身份读取或修改飞书云文档。

## 调用链路

```
大模型 → lark-doc Skill → lark-cli → 飞书开放 API（--as user）
```

能否访问某篇文档，取决于本机飞书授权状态和当前用户对该文档的权限。

## 快速参考

```bash
# 读取文档目录
lark-cli docs +fetch --doc "文档URL" --as user --scope outline --max-depth 3

# 读取某节（含 block ID，用于后续编辑）
lark-cli docs +fetch --doc "文档URL" --as user --scope section --start-block-id <id> --detail with-ids

# 文本替换
lark-cli docs +update --doc "文档URL" --as user --command str_replace --pattern "旧文本" --content "新文本"

# 替换整个 block 或连续范围
lark-cli docs +update --doc "文档URL" --as user --command block_replace --start-block-id <id> --end-block-id <id> --content '<p>新内容</p>'

# 在指定 block 后插入
lark-cli docs +update --doc "文档URL" --as user --command block_insert_after --block-id <id> --content '<p>内容</p>'

# 删除 block
lark-cli docs +update --doc "文档URL" --as user --command block_delete --block-id <id>
```

## 完整操作规范

详细参数说明、XML 格式和安全规则见：

```
/Users/jw/.agents/skills/lark-doc/
├── SKILL.md                       # 场景路由与操作规程
└── references/
    ├── lark-doc-fetch.md          # 读取参数与 scope 选择
    ├── lark-doc-update.md         # 编辑命令与推荐流程
    └── lark-doc-xml.md            # 写入时支持的 XML 格式
```

执行非平凡操作前先读取对应参考文件。
