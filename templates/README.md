# templates/ — 版式与交互手册

- 职责：页面骨架、全部样式、全部交互逻辑。
- 编译期由 `generator.py` 读入并内联进 `dist/*.html`，不产出独立文件。
- 三份文件都是纯文本资产：CSS / JS 原样内联，只有 HTML 走 Jinja 渲染。

## 文件

| 文件 | 职责 | 关键导出 |
|---|---|---|
| `reader.html.j2` | 页面骨架与 DOM 结构 | Jinja 变量 `book.*` / `chapters` / `payload` / `css` / `js` / `payload_json` |
| `reader.css.j2` | 全部样式 | 状态由 `<html>` 上的 `data-theme` / `data-layout` / `data-style` / `data-ui` 驱动 |
| `reader.js.j2` | 全部交互逻辑 | `window.__reader` = `{book, store, settings, paginator, progress, ui, pager}` |

`reader.js.j2` 内部模块：`Store`（localStorage 封装）、`Settings`（字号 / 行距 / 主题 / 页宽）、`Progress`（字符偏移进度）、`Paginator`（分页与测量）、`Pager`（翻页动作）、`UI`（工具栏、抽屉、提示、圆点状态）。

## 变更影响路由

| 改这里 | 必跑 / 必查 |
|---|---|
| 任何一份 `.j2` | `generator.py` 重建 → `verify.py` → 零外部引用 grep |
| `reader.css.j2` 的列宽、`overflow`、`#stage` padding | [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) 的「不可破坏的约束」逐条核对 |
| `reader.js.j2` 的 `handleTap` | `verify.py`【4】中轴线分区（中线归属、不弹菜单） |
| `reader.js.j2` 的分页与测量 | `verify.py`【14】多机型无横向溢出 |
| `reader.js.j2` 的章节跳转 | `verify.py`【9】目录跳章 |
| `reader.js.j2` 的圆点与工具栏 | `verify.py`【6】【7】【8】【8b】【12】 |
| `reader.html.j2` 的目录 / 设置结构 | `verify.py`【13】抽屉对齐 |
| 新增对外可见行为 | 同一次改动内同步 [README.md](../README.md)（怎么用）与 [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)（设计怎么变） |

- 依赖方向：三份模板只被 `generator.py` 依赖，模板之间不互相引用。
- 使用约束与工作偏好 → 见 [AGENTS.md](AGENTS.md)。
- 根索引 → 见 [../AGENTS.md](../AGENTS.md)。
