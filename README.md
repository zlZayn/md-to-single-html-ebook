# md-to-single-html-ebook

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12.10-blue.svg)](.python-version)

把一份 Markdown 书稿编译成**一个自包含的 HTML 文件**：双击即读，可离线、可发到手机、可当附件传。

给写小说和写长文的人用：不需要站点、不需要服务器、不需要读者装任何东西。

## 能力

- **编译**：一份 Markdown → 单个 `.html`，样式、脚本、正文全部内联
- **阅读**：左右分页 / 上下滚动两种模式，日间 / 护眼 / 夜间三套主题
- **调节**：字号无级、行距三档、衬线 / 无衬线、页宽三档
- **导航**：自动生成目录并高亮当前章节，配进度条与页码
- **操控**：点屏幕左半页上一页、右半页下一页；键盘翻页与切沉浸；软键全屏
- **记忆**：阅读进度与偏好存本机，刷新自动恢复
- **安静**：平时界面只有一个极淡的小圆点，轻点才展开工具栏

## 快速上手

```bash
uv sync                                  # 按 uv.lock 重建环境（Python 3.12.10）
uv run python generator.py               # 编译 content/ 下全部 .md
uv run python generator.py content/xxx.md -o dist/book.html   # 编译指定文件
```

产物默认落在 `dist/<slug>.html`，双击即可阅读。

跑回归验证需要 playwright 的 chromium：

```bash
uv run playwright install chromium
uv run python verify.py
```

## 书稿格式

```markdown
---
title: 书名          # 可选，缺省取一级标题
author: 作者         # 可选
lang: en             # 可选，默认 en
slug: file-name      # 可选，默认取文件名
---
# 书名               # 一级标题即书名

## 第一章            # 二级标题，每个即一个章节
正文段落……

---                  # 章节内的分节符，渲染为装饰性分隔

## 第二章
……
```

只有一个硬性要求：**章节必须用 `##` 标记**。目录、页码与章节编号全部自动生成。

## 边界

- 产物不含任何外部请求：没有外链样式、外链脚本、远程字体。
- 阅读进度与偏好只存在本机 `localStorage`，不上传、不跨设备同步。
- 打开即离线阅读，不依赖网络。

## License

[MIT](LICENSE)。

## 贡献

欢迎提 Issue 与 PR。

- 改代码前先看 [AGENTS.md](AGENTS.md) 的全局规则，改完必须跑 `verify.py`。
- 设计与约束的理由见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

---

维护者文档地图见 [AGENTS.md](AGENTS.md)。
