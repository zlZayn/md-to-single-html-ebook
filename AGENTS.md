# md-to-single-html-ebook — 维护索引

## 全局规则（本项目特有）

- **产物零外部依赖**：`dist/*.html` 不得出现 `http(s)://` 的 `src`/`href`。
- **产物字节可复现**：写产物一律写 bytes 并归一 LF，不用 `write_text`。
- **改完必须跑 `verify.py`**：全绿才算完成，只改 CSS 也要跑（分页对样式极敏感）。
- **`column-width` 只用绝对长度**：真实宽度由 JS 实测注入 `--col-w`。
- **`overflow: hidden` 只放 `#stage`**：加到多列容器 `#book` 会让第 3 栏之后整片不显示。
- **JSON 注入绕过 autoescape**：`Markup()` 包裹 + `< > &` 转 `\uXXXX`，否则 `JSON.parse` 失败。
- **正文区点击只翻页**：按中轴线分左右半屏，中部不弹菜单；工具栏只能由小圆点开关。
- 每条规则的机制与根因见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 常用命令

```bash
uv sync                                                  # 按 uv.lock 重建环境
uv run python generator.py                               # 编译 content/ 全部
uv run python generator.py content/xxx.md -o dist/book.html   # 编译单个文件
uv run python verify.py                                  # 回归验证（需 chromium）
uv run playwright install chromium                       # 首次安装浏览器
grep -oE '(src|href)="https?://[^"]*"' dist/*.html        # 零外部依赖检查（应无输出）
```

## 验证快照（2026-09-12 实测）

- **Playwright 回归：38 passed / 0 failed**（390×844，`is_mobile=true, has_touch=true`，Chromium 148.0.7778.96）
- 覆盖：点击翻页与页码同步、中轴线左右分区（含中线归属与不弹菜单）、横滑不翻页、圆点位置与静默、翻页不唤醒圆点、目录跳章 4/4、首页边界反馈、工具栏已无拖拉条、抽屉对齐（序号右边缘 / 标题左边缘 / 设置标签与控件左右边缘各自单值）、四机型（320/390/430/820）横向溢出 0px、全程零 JS 错误
- **产物**：`dist/the-lighthouse-keepers-cat.html` = 83.9 KB，10 章 / 4238 词，34 页（390×844）
- **自包含**：外部资源 0 处，外部脚本 0，外部样式表 0
- **可复现**：同源码二次重建逐字节相同，CRLF 计数 0
- **未验证项**：真实 iOS Safari / Android Chrome 上机（只有 Chromium）；`localStorage` 只在本机生效

## 待办

- [ ] 真实移动端上机验证（iOS Safari 全屏 API 走降级分支，未被真实覆盖）
- [ ] 书稿超过 10 万字时评估分页懒渲染（当前全量渲染，未做虚拟化）
- [ ] 补 CI：把 `verify.py` 与零外部依赖 grep 挂到 push 钩子

## 活跃坑

- **页数与 Chromium 版本 / 系统字体绑定**：产物逐字节相同也可能算出不同总页数 → 断言只写相对变化，不写死页数。
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
