# src/ — 脚本手册

- 职责：书稿解析渲染、发布产物挑选。两个命令行入口。
- 两者都从项目根定位 `templates/` `content/` `dist/`，可在任意工作目录运行。

## 文件

| 文件 | 职责 | 关键导出 | 被谁依赖 |
|---|---|---|---|
| `generator.py` | 解析 front matter 与 `##` 章节 → 渲染模板 → 写单文件 HTML | `slugify` · `build_book` · `render_book` · `compile_one` · `main` | `pick_artifact.py`（复用 `slugify`）；[发布流水线](../.github/workflows/publish.yml) |
| `pick_artifact.py` | 挑出要发布的一本，生成站点入口 `index.html` | `pick` · `source_for` · `last_commit_time` · `main` | [发布流水线](../.github/workflows/publish.yml) |

`generator.py` 内部：`split_front_matter` / `make_renderer` / `split_chapters` / `detect_lang` / `count_words` 为纯函数，`make_env` 装配 Jinja 环境，`compile_one` 串联单个文件的完整链路。

## 变更影响路由

| 改这里 | 必跑 / 必查 |
|---|---|
| `generator.py` 的解析或渲染 | 重建 → [../tests/verify.py](../tests/verify.py) → `git diff --exit-code -- dist/` 必须为空 |
| `generator.py` 的 `slugify` | 同步核对 `pick_artifact.py` 的产物到源文件映射 |
| `generator.py` 的写产物 | 必须写 bytes 并归一 LF |
| `pick_artifact.py` 的判定 | [../tests/verify.py](../tests/verify.py) 两本都跑；`pick_artifact.py` 三条路径（自动 / 手动 / 指定不存在） |
| 新增对外可见命令 | 同一次改动内同步 [../README.md](../README.md)（怎么用）与 [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)（设计怎么变） |

- 依赖方向：`pick_artifact.py` → `generator.py`，单向；两者都不依赖 `tests/`。
- 约束与工作偏好 → 见 [AGENTS.md](AGENTS.md)。
- 根索引 → 见 [../AGENTS.md](../AGENTS.md)。
