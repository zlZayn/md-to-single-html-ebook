# 决策：锁文件源由 pyproject 钉死，顺带消掉「本地 uv run 改写 uv.lock」的老坑（2026-11-18）

状态：生效

## 问题

- uv.lock 的 9 行 registry 全是清华镜像 `https://pypi.tuna.tsinghua.edu.cn/simple/`
- 成因：本机全局 `%APPDATA%\uv\uv.toml` 配了 `index-url` 指向镜像，其优先级高于锁文件里既有的 registry 记录
- 于是 `uv lock` 会把锁文件整片改写成镜像源；`uv run` 触发的隐式 relock 同样中招
- 这正是本仓活跃坑里那条「本地 `uv run` 会整篇改写 `uv.lock`，提交前 `git restore uv.lock`」的真正机制 —— 以前只当成本地噪声，靠人肉还原
- 该噪声在境外 CI 会升级为硬故障：GitHub Actions 拉清华镜像 tcp 超时，`uv sync --frozen` 失败（同批事故已在 AI-batch-raw-to-offline-guide 的 Pages 部署上复现）

## 决策

- `pyproject.toml` 的 `[tool.uv]` 段加 `[[tool.uv.index]]`，声明官方源并 `default = true`
- 项目级配置优先级高于用户级 `uv.toml`，`uv lock` / `uv run` 都不再被本机镜像改写
- 判定标准：在配了镜像的机器上，不带任何参数跑 `uv lock`，`uv.lock` 里 `tsinghua` 出现次数必须为 0
- uv.lock 的 9 个包 registry 全部回 `https://pypi.org/simple`，**包版本零变化**（纯 URL 改写）

## 替代方案

- **保留「提交前 git restore uv.lock」的人工纪律**：这是症状处置不是修因，且只在有纪律的人手里成立；CI 侧一旦 relock 落到 main 就是硬故障
- **`[tool.uv] default-index = "..."`**：uv 0.11 不认该字段，报 `unknown field` 并整体忽略 `[tool.uv]` 节，看起来配了其实没生效（实测），必须用 `[[tool.uv.index]]` 表
- **让每台机器删掉 uv.toml 的 index-url**：属个人环境，换机器/换人即失效，不能作为仓库约束
- **只在 CI 侧覆盖 `UV_DEFAULT_INDEX`**：能救 CI，但本地仍会污染锁文件，问题只被推迟

## 影响

- 收益：锁文件不再可能被本机镜像改写；原「`uv run` 后必须 `git restore uv.lock`」的纪律可撤销（实测 `uv run` 前后 uv.lock 哈希一致）
- 代价：本机下载依赖走官方源，速度低于镜像（如需加速，用命令行 `--default-index` 临时覆盖，不落盘）
- 验证：`uv lock`（无参数）后 tsinghua=0；`uv sync --frozen --group dev` 正常；ruff check/format 全绿；两份产物 `tests/verify.py` 各 43/43 通过
- 关联：[2026-09-12-github-pages-deploy.md](2026-09-12-github-pages-deploy.md)（发布链路对依赖安装的依赖）
