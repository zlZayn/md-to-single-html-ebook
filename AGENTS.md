# md-to-single-html-ebook — 维护索引

## 全局规则（本项目特有）

- **产物零外部依赖**：`dist/*.html` 不得出现 `http(s)://` 的 `src`/`href`。
- **产物字节可复现**：写产物一律写 bytes 并归一 LF，不用 `write_text`。
- **改完必须跑 `verify.py`**：全绿才算完成，只改 CSS 也要跑（分页对样式极敏感）。
- **`column-width` 只用绝对长度**：真实宽度由 JS 实测注入 `--col-w`。
- **`overflow: hidden` 只放 `#stage`**：加到多列容器 `#book` 会让第 3 栏之后整片不显示。
- **JSON 注入绕过 autoescape**：`Markup()` 包裹 + `< > &` 转 `\uXXXX`，否则 `JSON.parse` 失败。
- **正文区点击只翻页**：按中轴线分左右半屏，中部不弹菜单；工具栏只能由小圆点开关。
- **沉浸 = 全屏**：收起工具栏必进全屏，展开工具栏必退全屏，两者成对翻转，不翻一半。
- **`dist/` 与 `content/` 永不加入 `.gitignore`**：`content/` 是书稿源文件，`dist/` 是编译产物且为模板的唯一备份源（模板丢失时可从产物反推），两者必须入库。`.gitignore` 只忽略运行时产物（`__pycache__/`、`.venv/`、`.DS_Store`、`.workbuddy/` 等）。
- **发布产物必须与源码同步**：CI 重编译后跑 `git diff --exit-code -- dist/`，不一致即整条中断。改了 `content/` 或 `templates/` 必须本地重跑 `generator.py` 并提交产物，否则发布流水线会红。
- **站点入口固定为 `index.html`**：发布时把最新产物重命名为 `index.html`，避开中文文件名的 URL 编码。「最新」按 **git 提交时间**（`git log -1 --format=%ct`）判定，**不用 mtime** —— CI 检出后所有文件 mtime 相等，按 mtime 取必然挑错。
- 每条规则的机制与根因见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 常用命令

```bash
uv sync                                                  # 按 uv.lock 重建环境
uv run python generator.py                               # 编译 content/ 全部
uv run python generator.py content/xxx.md -o dist/book.html   # 编译单个文件
uv run python verify.py                                  # 回归验证（需 chromium）
uv run python verify.py dist/逆流.html                    # 指定验证哪一份产物
uv run playwright install chromium                       # 首次安装浏览器
grep -oE '(src|href)="https?://[^"]*"' dist/*.html        # 零外部依赖检查（应无输出）
gh run watch                                             # 跟踪发布流水线
gh run list --workflow=publish.yml --limit 5             # 查看发布历史
gh workflow run publish.yml -f artifact=逆流.html         # 手动指定产物发布
```

发布流水线：push 到 `main` → 编译 → 三道闸门 → 取最新产物 → Pages。站点 <https://zlzayn.github.io/md-to-single-html-ebook/>

## 验证快照（2026-09-12 实测 · 中文优化后）

- **Playwright 回归：每份产物 43 项全绿，两份合计 86 / 0 failed**（390×844，`is_mobile=true, has_touch=true`，Chromium 148.0.7778.96）
- 覆盖：点击翻页与页码同步、中轴线左右分区（含中线归属与不弹菜单）、横滑不翻页、圆点位置与静默、翻页不唤醒圆点、沉浸与全屏成对翻转、首次手势补齐全屏、目录跳章 4/4、首页边界反馈、工具栏已无拖拉条、抽屉对齐（序号右边缘 / 标题左边缘 / 设置标签与控件左右边缘各自单值）、四机型（320/390/430/820）横向溢出 0px、全程零 JS 错误
- **产物**：
  - `dist/the-lighthouse-keepers-cat.html` = 86.5 KB，10 章 / 4238 词，34 页（390×844），lang=en
  - `dist/逆流.html` = 107.0 KB，12 章 / 11264 字，lang=zh
- **中文支持**：slug 保留中文、字数按字符统计、lang 自动检测、`[lang="zh"]` 专属排版（禁首字下沉 / 禁斜体标题 / 段首两字符缩进 / 着重号强调 / 严格断行）
- **自包含**：外部资源 0 处，外部脚本 0，外部样式表 0
- **可复现**：同源码二次重建逐字节相同，CRLF 计数 0；`generator.py` 重跑后 `git diff --exit-code -- dist/` 为空（发布流水线的同步闸门据此成立）
- **断言与书稿解耦**：章数取自 `#bookdata` 的结构化 `chapterCount`，跳章抽样改为首 / 两个三分位 / 末章，页码取相对位置；规格常量（工具栏按钮数、设置分组数）提到文件顶部具名。此前写死「目录 10 行」「跳章 [0,3,6,9]」，换一本 12 章的书即误报，且末章永远测不到
- **回归覆盖面**：`verify.py` 支持指定产物路径，CI 对 `dist/*.html` **逐个**执行；有失败项返回非零退出码（此前恒返回 0，接 CI 会假绿）
- **发布链路**：`.github/workflows/publish.yml`，push 到 `main` 触发；三道闸门 = 产物与源码同步 / 零外部依赖 / 全产物回归
- **未验证项**：真实 iOS Safari / Android Chrome 上机（只有 Chromium）；`localStorage` 只在本机生效

## 待办

- [ ] 真实移动端上机验证（iOS Safari 全屏 API 走降级分支，未被真实覆盖）
- [ ] 书稿超过 10 万字时评估分页懒渲染（当前全量渲染，未做虚拟化）
- [ ] 多书并存时缺一个目录页：`index.html` 恒指向最近改动的一本，其余书无法从站点入口到达
- [ ] 线上只保留最新一份：产物被覆盖后旧版本无法回看，需要的话改成按 slug 分路径发布

## 活跃坑

- **页数与 Chromium 版本 / 系统字体绑定**：产物逐字节相同也可能算出不同总页数 → 断言只写相对变化，不写死页数。
- **CI 里 mtime 不可信**：`actions/checkout` 把所有文件的 mtime 统一写成检出时刻 → 「取最新产物」必须用 git 提交时间，用 mtime 必然挑错。
- **私有仓库开不了 Pages**：个人 Free 账号的 Pages 只支持公开仓库（`GET /repos/.../branches/main/protection` 返回 403 就是同一道付费墙）。站点级访问控制只有 Enterprise Cloud 组织提供，Free / Pro / Team 发布的站点一律公开 —— 书稿里不要放密钥或内部信息。
- **本地 `uv run` 会整篇改写 `uv.lock`**：uv 版本或镜像配置与锁定文件不一致时（本项目锁文件记的是 aliyun 镜像、本地配置是清华），跑一次 `uv run` 就把源 URL 全量换掉并补上 `size` / `upload-time` 字段。提交前看一眼 `git status`，别把这噪声混进功能提交。
- **新增任何写文件的地方都要守 LF**：一旦回退到默认换行，Windows 上每次重建都产生整篇假 diff。
- **动模板前确认 `dist` 与源码同步**：模板只存在于工作区与产物里，产物是唯一备份源，反推方法见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。
- 历史坑的完整机制见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 文档地图

- 门面、用途、快速上手 → [README.md](README.md)
- 设计决策、约束、防错清单、契约、模板可恢复性 → [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- 模板文件职责与变更影响路由 → [templates/README.md](templates/README.md)
- 模板层特有约束 → [templates/AGENTS.md](templates/AGENTS.md)
- 决策记录 → [.agents/notes/](.agents/notes/)
- 回归用例 → [verify.py](verify.py)；解析与渲染管线 → [generator.py](generator.py)
