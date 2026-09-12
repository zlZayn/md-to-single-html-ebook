# templates/ — 版式与交互手册

- 职责：页面骨架、全部样式、全部交互逻辑。
- 编译期由 [src/generator.py](../src/generator.py) 读入并内联进 `dist/*.html`，不产出独立文件。
- 三份文件都是纯文本资产：CSS / JS 原样内联，只有 HTML 走 Jinja 渲染。

## 文件

| 文件 | 职责 | 关键导出 |
|---|---|---|
| `reader.html.j2` | 页面骨架与 DOM 结构 | Jinja 变量 `book.*` / `chapters` / `payload` / `css` / `js` / `payload_json` |
| `reader.css.j2` | 全部样式 | 状态由 `<html>` 上的 `data-theme` / `data-layout` / `data-style` / `data-ui` 驱动 |
| `reader.js.j2` | 全部交互逻辑 | `window.__reader` = `{book, store, settings, paginator, progress, ui, pager}` |

`reader.js.j2` 内部模块：`Store`（localStorage 封装）、`Settings`（字号 / 行距 / 主题 / 页宽）、`Progress`（字符偏移进度）、`Paginator`（分页与测量）、`Pager`（翻页动作）、`UI`（工具栏、抽屉、提示、圆点状态）。

## 交互与版式规格

### 常驻控件

整个界面平时只有一个极淡的小圆点。

- 静默态不透明度 18%。
- 展开态圆点变为胶囊，提示可收起。
- 首次进入短暂显现 1.6 s，之后保持静默。

### 沉浸态与全屏是同一个状态

小圆点切换的两个方向都是复合动作，不存在只改一半的中间态。

| 状态 | 下方工具栏 | 浏览器全屏 |
|---|---|---|
| 沉浸 | 收起 | 进全屏 |
| 展开 | 显示 | 退全屏 |

三条配套规则：

- 首次手势补全：浏览器要求全屏由用户手势触发，默认沉浸态无法在加载时进全屏，因此首次真实交互（非小圆点）时补一次。
- 系统层面退出全屏要跟着走：按 `Esc` 或用手势退出全屏时，自动展开工具栏并唤醒圆点。
- `Esc` 收起工具栏即回沉浸：走同一条切换路径，全屏一并跟上。

- 全屏 API 不可用时（如 iOS Safari）静默降级，只保留工具栏的收放。

### 抽屉排版

两个抽屉共用一套栅格，保证纵向对齐可校验。

| 抽屉 | 栅格 |
|---|---|
| 目录 | 序号列定宽右对齐（tabular-nums）+ 标题列左对齐；长标题换行后悬挂对齐在标题列 |
| 设置 | 标签列定宽 + 控件列自适应；7 组行共用同一对左右边界 |

- 当前章用底色 + 左侧 2px 强调条标记。
- 设置组之间用 1px 分隔线，最后一组不加线。

### 翻页反馈

- 翻页瞬间从对应方向扫过一道极淡渐变光影（`#pagehint`），提供方向反馈。
- 首 / 末页不静默无响应，给一次 14px 回弹 + 文字提示。

- 不变量与设计理由 → 见 [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)。

## 变更影响路由

| 改这里 | 必跑 / 必查 |
|---|---|
| 任何一份 `.j2` | [src/generator.py](../src/generator.py) 重建 → [tests/verify.py](../tests/verify.py) → 零外部引用 grep |
| `reader.css.j2` 的列宽、`overflow`、`#stage` padding | [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) 的「不可破坏的约束」逐条核对 |
| `reader.js.j2` 的 `handleTap` | [tests/verify.py](../tests/verify.py)【4】中轴线分区（中线归属、不弹菜单） |
| `reader.js.j2` 的分页与测量 | [tests/verify.py](../tests/verify.py)【14】多机型无横向溢出 |
| `reader.js.j2` 的章节跳转 | [tests/verify.py](../tests/verify.py)【9】目录跳章 |
| `reader.js.j2` 的圆点与工具栏 | [tests/verify.py](../tests/verify.py)【6】【7】【8】【8b】【8c】【8d】【12】 |
| `reader.html.j2` 的目录 / 设置结构 | [tests/verify.py](../tests/verify.py)【13】抽屉对齐 |
| 新增对外可见行为 | 同一次改动内同步 [README.md](../README.md)（怎么用）与 [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)（设计怎么变） |

- 依赖方向：三份模板只被 [src/generator.py](../src/generator.py) 依赖，模板之间不互相引用。
- 使用约束与工作偏好 → 见 [AGENTS.md](AGENTS.md)。
- 根索引 → 见 [../AGENTS.md](../AGENTS.md)。
