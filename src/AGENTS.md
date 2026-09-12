# src/ — 规则层

继承根规则，见 [../AGENTS.md](../AGENTS.md)。

src/ 特有约束：

- 两个脚本都从项目根定位资源（`ROOT = Path(__file__).resolve().parents[1]`），不得改回 `__file__.parent`。
- 产物命名规则只有一份：`pick_artifact.py` 同目录导入 `generator.slugify`，不另写一套。
- 写产物一律写 bytes 并归一 LF，否则 Windows 上每次重建产生整篇假 diff。
- 改任一脚本后必须重建并核 `git diff --exit-code -- dist/` 为空，再跑 [../tests/verify.py](../tests/verify.py)。
- 布局与契约约束见 [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)，不在此重复。
- 不写「有什么文件 / 怎么改」，那是 [README.md](README.md) 的职责。
