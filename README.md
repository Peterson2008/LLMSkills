# Skills

这个仓库目前维护 6 个可复用 skill：

| Skill | 用途 |
| --- | --- |
| [`algorithm-report`](algorithm-report/SKILL.md) | 把一次策略、算法或模型工作整理成可信、易读的效果报告或实验记录，讲清问题、做法、结果和认知。 |
| [`cotti-gitlab`](cotti-gitlab/SKILL.md) | 访问 Cotti 内网 host 时绕开本机代理：诊断并解决 SSL_ERROR_SYSCALL / 502 等被 clash 劫持的问题，git 优先走 SSH。 |
| [`joplin-notes`](joplin-notes/SKILL.md) | 通过 Joplin Web Clipper API 查找、读取、创建、更新或追加任意 Joplin 笔记。 |
| [`maintain-readme-tree`](maintain-readme-tree/SKILL.md) | 把根 README 和子目录 README 组织成递归的全局文档索引，并检查断链和未注册文档。 |
| [`project-progress`](project-progress/SKILL.md) | 整理项目当前状态、结果、里程碑和下一步，把零散日志收敛成简洁的进度文档。 |
| [`work-journal`](work-journal/SKILL.md) | 把每天完成的工作整理成项目条目，并更新 Joplin 中固定的「工作日志」笔记。 |

每个 skill 以自己的 `SKILL.md` 为唯一入口，可按需包含：

- `agents/openai.yaml`：OpenAI 产品侧 skill 列表和调用入口所需的界面元数据。
- `references/`：正文按需读取的模板、案例或领域资料。
- `scripts/`：需要稳定、重复执行的工具脚本。
- `assets/`：生成最终产物时使用的模板、图片等资源。

skill 不按 Claude、Codex 分叉；平台或项目的特殊约束由各自的仓库级指令处理。

## References

- [`algorithm-report/references/skeleton.md`](algorithm-report/references/skeleton.md)：算法效果报告骨架。
- [`algorithm-report/references/越送越快.md`](algorithm-report/references/%E8%B6%8A%E9%80%81%E8%B6%8A%E5%BF%AB.md)：算法报告示例。
- [`joplin-notes/references/joplin-setup.md`](joplin-notes/references/joplin-setup.md)：Joplin Web Clipper 启用、token 和故障排查。
- [`maintain-readme-tree/references/readme-template.md`](maintain-readme-tree/references/readme-template.md)：README 文档树模板。
- [`project-progress/references/template.md`](project-progress/references/template.md)：项目进度文档模板。
