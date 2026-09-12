# .github/workflows/ — 发布流水线手册

- 职责：把 `dist/` 里最近在写的那一本编译、验证、发布到 GitHub Pages。
- 站点：<https://zlzayn.github.io/md-to-single-html-ebook/>
- 触发：push 到 `main`，且改动落在 `content/**`、`templates/*.j2`、`src/*.py`、`tests/*.py`、`pyproject.toml`、`uv.lock` 或本 workflow。
- 只改文档（含各目录的 `README.md` / `AGENTS.md`）不触发发布。
- 兜底入口：`workflow_dispatch` 的 `artifact` 输入，可手动指定产物。

## 文件

| 文件 | 职责 | 关键内容 |
|---|---|---|
| `publish.yml` | 编译 → 三道闸门 → 挑选产物 → 部署 Pages | 两个 job：`build` 产出 `_site/index.html`；`deploy` 经 `upload-pages-artifact` 与 `deploy-pages` 上线 |

`build` 需要 `fetch-depth: 0`：产物挑选要读完整提交历史。

## 三道闸门

| 闸门 | 判据命令 | 挡住什么 |
|---|---|---|
| 产物与源码同步 | 重编译后 `git diff --exit-code -- dist/` 为空 | 产物与源码漂移，破坏「产物是模板唯一备份源」 |
| 零外部依赖 | `grep -oE '(src\|href)="https?://[^"]*"' dist/*.html` 无命中 | 外链样式 / 脚本 / 字体混进产物，破坏离线能力 |
| 全产物回归 | `for f in dist/*.html; do uv run python tests/verify.py "$f"; done` | 阅读器行为回归 |

闸门只圈 `dist/`，本地因 uv 镜像配置改写 `uv.lock` 之类的噪声不会误触。

## 产物挑选与站点入口

- 入口：`uv run python src/pick_artifact.py dist "$SITE_DIR" --requested "$REQUESTED"`。
- 实现细节与导出 → 见 [../../src/README.md](../../src/README.md)。
- 判据为何是书稿源提交时间、站点为何必然公开 → 见 [../../docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md) 的设计决策与约束。
- 选中产物复制为 `_site/index.html`：入口恒为根路径，规避中文文件名的 URL 编码。
- 判定过程把候选表与选定依据打进日志，线上选错时可回溯。

## 变更影响路由

| 改这里 | 必跑 / 必查 |
|---|---|
| 任一 `run` 命令 | 与 [../../AGENTS.md](../../AGENTS.md) 常用命令保持同一套写法 |
| `paths` 触发列表 | 目录布局变化时必须同步，否则相关改动不再触发发布 |
| 闸门判据 | 同步 [../../docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md) 的契约节 |
| 新增步骤 | 确认不写入工作区，流水线不在云端提交任何东西 |
| 增减闸门 | 同步 [../../docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md) 的契约节与本文的闸门表 |

- 约束与工作偏好 → 见 [AGENTS.md](AGENTS.md)。
- 根索引 → 见 [../../AGENTS.md](../../AGENTS.md)。
