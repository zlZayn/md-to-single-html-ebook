# md-to-single-html-ebook — 维护索引

## 全局规则（本项目特有）

机制与根因 → [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

- 产物零外部依赖、字节可复现、以 bytes + LF 写出：三条都是硬契约。
- 改完必跑 `tests/verify.py`，只改 CSS 也要跑（分页对样式极敏感）。
- `column-width` 只用绝对长度，真实宽度由 JS 实测注入 `--col-w`。
- `overflow: hidden` 只放 `#stage`，加到多列容器 `#book` 会让第 3 栏之后整片不显示。
- JSON 注入绕过 autoescape；正文区点击只翻页；沉浸与全屏成对翻转。
- `dist/` 与 `content/` 永不加入 `.gitignore`：产物是模板的唯一备份源。
- 发布产物必须与源码同步；发布哪一本看 `content/*.md` 的提交时间，不看产物。

## 常用命令

```bash
uv sync                                                       # 按 uv.lock 重建环境
uv run python src/generator.py                                # 编译 content/ 全部
uv run python src/generator.py content/xxx.md -o dist/book.html   # 编译单个文件
uv run python tests/verify.py dist/逆流.html                   # 回归验证（需 chromium），可指定产物
uv run python src/pick_artifact.py dist _site                 # 试跑发布产物挑选
uv run playwright install chromium                            # 首次安装浏览器
grep -oE '(src|href)="https?://[^"]*"' dist/*.html             # 零外部依赖检查（应无输出）
gh run watch                                                  # 跟踪发布流水线
gh workflow run publish.yml -f artifact=逆流.html              # 指定产物发布
```

## 验证快照（2026-09-12 实测）

- 回归：每份产物 43 项全绿，两份合计 86 / 0 failed（390×844，Chromium 148）。
- 产物：`the-lighthouse-keepers-cat.html` 86.5 KB / 10 章 / 34 页；`逆流.html` 107.0 KB / 12 章。
- 自包含：外部资源 0 处。可复现：重编译后 `dist/` 逐字节无 diff。
- 发布链路：push `main` 触发，三道闸门；首跑 build 1m10s / deploy 9s。
- 链接校验 13 文件 / 26 链接 0 错误；换行 38 文件 0 不一致。
- 用例覆盖 → [tests/README.md](tests/README.md)

## 待办

- [ ] 真实移动端上机验证（iOS Safari 全屏 API 走降级分支）
- [ ] 书稿超 10 万字时评估分页懒渲染
- [ ] 多书并存缺目录页：`index.html` 恒指向一本，其余到不了
- [ ] 线上只保留最新一份，旧版本无法回看

## 活跃坑

- 页数绑定 Chromium 版本与系统字体度量 → 断言只写相对变化，不写死页数。
- CI 里 mtime 全是检出时刻；产物提交时间恒等于「最后一次重建」→ 判据只看 `content/*.md`。
- 私有仓库开不了 Pages（个人 Free 账号）；站点级访问控制只有 Enterprise Cloud 组织提供。
- 本地 `uv run` 会整篇改写 `uv.lock`，提交前 `git restore uv.lock`。
- 整理历史禁用 `checkout` / `rebase`，只用 `git reset --soft|--mixed` + `add` + `commit`。
- 本机 shell shim 无 coreutils（`ls` / `cp` / `rm` / `tail` / `grep` 不可用）→ 文件操作走编辑工具，别依赖 shell。
- 新增任何写文件的地方都要守 LF。

## 文档地图

- [README.md](README.md) — 门面：用途、能力、快速上手
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — 设计决策、约束、契约、防错清单、模板可恢复性
- [docs/postmortem/](docs/postmortem/) — 事故复盘
- [src/README.md](src/README.md) — 脚本手册；[src/AGENTS.md](src/AGENTS.md) — 脚本层约束
- [tests/README.md](tests/README.md) — 回归覆盖范围与特殊坑；[tests/AGENTS.md](tests/AGENTS.md) — 断言约定
- [templates/README.md](templates/README.md) — 模板职责与变更影响路由
- [templates/AGENTS.md](templates/AGENTS.md) — 模板层约束
- [.agents/notes/](.agents/notes/) — 决策记录
- [.github/workflows/publish.yml](.github/workflows/publish.yml) — 发布流水线
