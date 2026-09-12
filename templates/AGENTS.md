# templates/ — 规则层

继承根规则，见 [../AGENTS.md](../AGENTS.md)。

templates/ 特有约束：

- 三份 `.j2` 在编译期内联进产物；只有 `reader.html.j2` 走 Jinja 渲染逻辑，改 CSS / JS 不需要懂 Jinja。
- 改任何一份后必须重跑 [src/generator.py](../src/generator.py) 与 [tests/verify.py](../tests/verify.py)，并确认产物零外部引用。
- 布局与交互的约束清单见 [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)，不在此重复。
- 不写「有什么文件 / 怎么改」，那是 [README.md](README.md) 的职责。
