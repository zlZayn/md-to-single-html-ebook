## Postmortem: git 历史整理回退整个工作区（2026-09-12）

- 摘要：用 `git checkout -b <tmp> <root-sha>` + `git rebase --onto` 补正根提交，工作区被回退到非目标提交，`.git` / `templates/` / `docs/` / `README.md` / `AGENTS.md` 全部消失。
- 时间线：rebase 后工作区文件消失 → `git reflog` 定位原 HEAD → 由 `dist/*.html` 反推三份 `.j2` → 重建产物与既有产物逐字节比对无损（87530 B == 87530 B）。
- 根因：本机 shell 的 `cd: null directory` 缺陷叠加 `checkout -b` + `rebase --onto` 的历史重写，把工作区指针带到了非目标提交。
- 防再犯：整理历史只用 `git reset --soft|--mixed` + `add` + `commit`（不碰工作区）；按文件还原用 `git restore <path>`；`--amend` 只在 HEAD 上生效，禁止用于非 HEAD 提交。
- 关联：[模板可恢复性](../ARCHITECTURE.md) · [决策记录](../../.agents/notes/)
