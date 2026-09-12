# .github/workflows/ — 规则层

继承根规则，见 [../../AGENTS.md](../../AGENTS.md)。

本目录特有约束：

- 三道闸门不得绕过或降级：产物与源码同步、零外部依赖、全产物回归，任一失败即整条中断。
- 流水线不在云端提交任何东西；`dist/` 只由维护者本地重跑 [src/generator.py](../../src/generator.py) 后提交。
- `paths` 触发列表与目录布局联动，目录一改必须同步，否则该改动不再触发发布。
- `run` 里的命令与 [../../AGENTS.md](../../AGENTS.md) 的常用命令保持同一套写法。
- 站点入口恒为 `index.html`，线上只保留一份产物。
- 不写「有什么文件 / 怎么改」，那是 [README.md](README.md) 的职责。
