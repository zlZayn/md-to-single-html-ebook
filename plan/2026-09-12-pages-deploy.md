# GitHub Pages 自动发布 — 设计

日期：2026-09-12
状态：已实施

## 目标

`content/*.md` 变更推到 `main` 后，自动完成编译、回归、发布，把**最新一份产物**送到 GitHub Pages。本地不保留任何手动发布动作。

## 路线选择

| 候选 | 结论 |
|---|---|
| 私有仓库直接开 Pages | ❌ 个人账号为 GitHub Free，Pages 只支持公开仓库。实测 `GET /repos/.../branches/main/protection` 返回 `403 Upgrade to GitHub Pro or make this repository public`，同一道付费墙 |
| 另建公开产物仓库 | ❌ 能保住源码私有，但需跨仓库 PAT + 多一个仓库，链路非必要地长 |
| **当前仓库转公开** | ✅ **选定**。免费、链路最短、Actions 不限分钟；代价是源码与书稿正文公开，已由维护者确认 |

仓库可见性与站点可见性是两件独立的事：升级到 Pro / Team 也只能让站点**公开**，站点级访问控制只有 Enterprise Cloud 组织的 Pages access control 提供。因此本项目的站点必然对任何拿到链接的人公开。

## 关键决策

### 「最新产物」按 git 提交时间判定，不用 mtime

`actions/checkout` 会把所有文件的修改时间统一写成检出时刻，`dist/*.html` 的 mtime 在 CI 里全部相等 —— 「取 mtime 最大」在本地成立、在 CI 必然挑错。

改用提交时间：

```
git log -1 --format=%ct -- <path>
```

值来自真实 commit，与检出行为无关。代价是需要 `fetch-depth: 0`（浅克隆取不到完整历史）。

平局（同一提交里改了两本）时按 `dist/*.html` 的字典序取第一个；要绕过自动判定时用 `workflow_dispatch` 的 `artifact` 输入直接指定。

### 产物以 `index.html` 发布

`逆流.html` 直接作为站点文件时 URL 会被编码成 `%E9%80%86%E6%B5%81.html`，既难看又易断。固定发布为 `index.html` 后站点入口恒为

```
https://zlzayn.github.io/md-to-single-html-ebook/
```

既是干净地址，也天然满足「只发最新一个」的要求 —— 入口永远指向最近改动的那一本。

### CI 云端重编译 + 三道闸门

1. **产物与源码同步**：CI 重新编译后 `git diff --exit-code -- dist/`，不一致即失败。这道闸门守住「产物是模板唯一备份源」这条既有约定，防止产物与源码悄悄漂移。成立的前提是产物字节可复现，已实测通过。
2. **零外部依赖**：`grep -oE '(src|href)="https?://[^"]*"' dist/*.html` 有命中即失败。
3. **回归验证**：逐个产物跑 `verify.py`。

闸门只圈 `dist/`，因此本地因 uv 镜像配置改写 `uv.lock` 之类的工作区噪声不会误触。

### `verify.py` 的三处修补（本次一并修）

- **失败不返回非零**：脚本原本只打印 `通过 N/M`，任何情况下都 `exit 0`，挂到 CI 上就是假绿。已补 `sys.exit(1 if FAIL else 0)`。
- **只验证排序第一个产物**：原实现 `_TARGETS[0]` 让排序靠后的产物（中文那本）从未被验证过。已支持命令行指定目标，CI 用 `for f in dist/*.html` 逐个覆盖。
- **断言里写死了书稿数据**：一开启逐产物验证，中文书立刻 FAIL 在「目录 10 行」—— 10 是英文书的章数。同源问题还有跳章抽样 `[0, 3, 6, 9]`（隐含「至少 10 章」，末章永远测不到，书更短时还会取到空节点、漏成 JS 错误）与页码 `goto(12)`。修法：
  - 章数改从 `#bookdata` 的结构化 `chapterCount` 读取，不解析渲染后的中文文案（文案格式一变正则就废）
  - 跳章抽样改为首 / 两个三分位 / 末章，随章数自适应
  - 页码改用总页数的相对位置
  - 模板层规格常量（工具栏按钮数、设置分组数）具名提到文件顶部，并让断言名由常量拼出 —— 根治「标签写 10、判据也写 10」这种标签与判据一起漂移的形态

## 触发与并发

- push 到 `main`，且改动落在 `content/`、`templates/`、`generator.py`、`verify.py`、`pyproject.toml`、`uv.lock` 或 workflow 自身。只改文档不触发发布。
- `workflow_dispatch` 作兜底，可手动指定产物。
- `concurrency: group: pages` 且不取消进行中的发布，避免站点停在半成品状态。

## 验证方式

- 本地：`uv run python generator.py` 后 `git diff --exit-code -- dist/` 为空 ⇒ 字节可复现成立，CI 闸门不会误伤。
- 线上：push 后看 Actions 跑完 build 与 deploy，打开站点 URL 确认指向最新产物。
