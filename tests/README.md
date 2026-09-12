# tests/ — 回归用例

- 职责：用 Playwright 驱动产物，验证阅读器行为。
- 覆盖范围（按类别）：初始渲染与 JS 错误、点击翻页与页码同步、中轴线左右分区、横滑不翻页、小圆点位置与静默、沉浸与全屏成对翻转、首次手势补齐全屏、目录跳章、首页边界反馈、夜间与沉浸态、工具栏瘦身、抽屉栅格对齐、四机型（320 / 390 / 430 / 820）横向溢出。
- 运行方式：`uv run python tests/verify.py [产物路径]`，首次需 `uv run playwright install chromium`。
- 缺省验证 `dist/` 下排序第一份产物；CI 对 `dist/*.html` 逐个执行。

## 特殊坑

- 页数绑定 Chromium 版本与系统字体度量：产物逐字节相同也可能算出不同总页数 → 只断言相对变化。
- 全屏断言用 spy 记录 `requestFullscreen` / `exitFullscreen` 并伪造 `fullscreenElement`，不依赖 headless 真实全屏。
- 断言与产物随行书稿解耦，写死书稿数据会让用例只对某一本成立。

## 参考

- 断言约定与工作偏好 → 见 [AGENTS.md](AGENTS.md)。
- 设计与约束理由 → 见 [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)。
- 根索引 → 见 [../AGENTS.md](../AGENTS.md)。
