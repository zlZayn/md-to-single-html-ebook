# tests/ — 规则层

继承根规则，见 [../AGENTS.md](../AGENTS.md)。

tests/ 特有约束：

- 断言不得写死与书稿相关的量（章数、页数、词数），一律从产物自身读取或写成相对关系。
- 章数取自 `#bookdata` 的结构化 `chapterCount`，不解析渲染后的中文文案。
- 模板层的规格常量（工具栏按钮数、设置分组数）具名提到文件顶部，断言名由常量拼出。
- 跳章抽样取首 / 两个三分位 / 末章，随章数自适应。
- 有失败项必须返回非零退出码，否则接 CI 会假绿。
- 覆盖范围、运行方式与特殊坑见 [README.md](README.md)；设计约束见 [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)。
