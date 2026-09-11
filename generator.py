#!/usr/bin/env python3
"""单文件 HTML 电子书生成器。

把 Markdown 小说编译成一个自包含的单文件 HTML 阅读器：
所有 CSS / JS / 正文全部内联，无任何外部依赖，可离线双击阅读。

用法:
    python3 generator.py                          # 编译 content/ 下全部书
    python3 generator.py content/book.md          # 编译指定文件
    python3 generator.py content/book.md -o out/x.html
    python3 generator.py --all

内容格式契约（Markdown）:
    ---
    title: 书名          # 可选，缺省取一级标题
    author: 作者         # 可选
    lang: en             # 可选，默认 en
    slug: file-name      # 可选，默认取文件名
    ---
    # 书名               # 一级标题，作为书名
    ## 第一章            # 二级标题，每个是一个章节
    正文段落……
    ---                  # 章节内的分节符，渲染为装饰性分隔
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown_it import MarkdownIt
from markupsafe import Markup

ROOT = Path(__file__).resolve().parent
TEMPLATE_DIR = ROOT / "templates"
DEFAULT_CONTENT_DIR = ROOT / "content"
DEFAULT_DIST_DIR = ROOT / "dist"

# 生成 dist 文件名 slug 时允许的字符
SLUG_RE = re.compile(r"[^a-z0-9]+")


# --------------------------------------------------------------------------- #
# 数据模型
# --------------------------------------------------------------------------- #
@dataclass
class Chapter:
    """一个章节：标题 + 已渲染的 HTML 正文 + 用于定位的锚点。"""

    index: int
    title: str
    anchor: str
    html: str
    word_count: int = 0


@dataclass
class Book:
    """一本书的完整数据，最终喂给模板。"""

    title: str
    author: str
    lang: str
    slug: str
    chapters: list[Chapter] = field(default_factory=list)
    source: str = ""

    @property
    def word_count(self) -> int:
        return sum(c.word_count for c in self.chapters)


# --------------------------------------------------------------------------- #
# 解析
# --------------------------------------------------------------------------- #
def split_front_matter(text: str) -> tuple[dict[str, str], str]:
    """剥离可选的 YAML 风格 front-matter，返回 (meta, 正文)。

    只支持简单的 `key: value` 单行写法，不引入 yaml 依赖——
    对元数据来说足够了。
    """
    if not text.startswith("---"):
        return {}, text

    lines = text.splitlines()
    if lines[0].strip() != "---":
        return {}, text

    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break

    if end is None:
        return {}, text

    meta: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip().lower()] = value.strip()

    return meta, "\n".join(lines[end + 1 :])


def make_renderer() -> MarkdownIt:
    """构造 markdown-it 实例（GFM 风格，禁掉会引入外链的规则）。"""
    md = MarkdownIt("gfm-like", {"html": False, "linkify": False, "typographer": True})
    # gfm-like 预设开了 linkify，会生成 http 外链；阅读器要求自包含，关掉
    md.disable("linkify")
    return md


def slugify(value: str) -> str:
    slug = SLUG_RE.sub("-", value.lower()).strip("-")
    return slug or "book"


def count_words(html: str) -> int:
    """粗略统计词数：去掉标签后按空白切分。"""
    text = re.sub(r"<[^>]+>", " ", html)
    return len([w for w in text.split() if any(ch.isalnum() for ch in w)])


def split_chapters(body: str, md: MarkdownIt) -> tuple[str, list[tuple[str, str]]]:
    """按二级标题切分正文。

    返回 (书名或空, [(章节标题, 该章 markdown 正文), ...])。
    一级标题到首个二级标题之间的内容若无标题，会作为「序」保留。
    """
    lines = body.splitlines()
    title = ""
    sections: list[tuple[str, str]] = []
    current_title: str | None = None
    buffer: list[str] = []
    preamble: list[str] = []

    def flush() -> None:
        """把当前累积的 buffer 落到 sections（或用作序章）。"""
        nonlocal buffer
        chunk = "\n".join(buffer).strip()
        if current_title is None:
            if chunk:
                preamble.append(chunk)
        else:
            sections.append((current_title, chunk))
        buffer = []

    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            # 一级标题即书名，不进入章节正文
            if not title:
                title = line[2:].strip()
                continue
        if line.startswith("## "):
            flush()
            current_title = line[3:].strip()
            continue
        buffer.append(line)
    flush()

    if preamble and sections:
        # 有独立前言内容，作为「序」放在最前
        sections.insert(0, ("Prologue", "\n".join(preamble)))

    return title, sections


def build_book(path: Path) -> Book:
    """读一个 md 文件，产出 Book 数据模型。"""
    raw = path.read_text(encoding="utf-8")
    meta, body = split_front_matter(raw)

    md = make_renderer()
    title, sections = split_chapters(body, md)

    book = Book(
        title=meta.get("title") or title or path.stem,
        author=meta.get("author", ""),
        lang=meta.get("lang", "en"),
        slug=meta.get("slug") or slugify(path.stem),
        source=path.name,
    )

    for i, (chapter_title, chapter_md) in enumerate(sections):
        html = md.render(chapter_md)
        anchor = f"ch-{i + 1}"
        book.chapters.append(
            Chapter(
                index=i,
                title=chapter_title,
                anchor=anchor,
                html=html,
                word_count=count_words(html),
            )
        )

    if not book.chapters:
        raise ValueError(f"{path.name}: 未找到任何 `## 标题` 章节，无法生成电子书")

    return book


# --------------------------------------------------------------------------- #
# 渲染
# --------------------------------------------------------------------------- #
def make_env() -> Environment:
    """构造 Jinja 环境：autoescape 打开，加载器指向 templates/。"""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env


def render_book(book: Book, env: Environment) -> str:
    """把一个 Book 渲染成完整的单文件 HTML 字符串。"""
    tpl = env.get_template("reader.html.j2")

    # 章节正文是已渲染的 HTML，必须标记为安全，否则会被转义
    chapters = [
        {
            "index": c.index,
            "title": c.title,
            "anchor": c.anchor,
            "html": Markup(c.html),
            "word_count": c.word_count,
        }
        for c in book.chapters
    ]

    # 给 JS 用的纯数据（不含 HTML），一并以 JSON 注入
    toc = [{"index": c.index, "title": c.title, "anchor": c.anchor} for c in book.chapters]
    payload = {
        "title": book.title,
        "author": book.author,
        "lang": book.lang,
        "slug": book.slug,
        "chapterCount": len(book.chapters),
        "toc": toc,
    }

    css = (TEMPLATE_DIR / "reader.css.j2").read_text(encoding="utf-8")
    js = (TEMPLATE_DIR / "reader.js.j2").read_text(encoding="utf-8")

    return tpl.render(
        book=book,
        chapters=chapters,
        payload=payload,
        # 必须用 Markup 关掉 autoescape：否则引号会被转成 &quot; / &#34;，
        # 导致浏览器 JSON.parse 直接失败。JSON 本身已由 json.dumps 保证安全，
        # 再把 < > & 转成 \uXXXX 形式即可杜绝 </script> 逃逸。
        payload_json=Markup(json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")),
        css=Markup(css),
        js=Markup(js),
    )


# --------------------------------------------------------------------------- #
# 入口
# --------------------------------------------------------------------------- #
def compile_one(src: Path, dst: Path, env: Environment) -> Book:
    book = build_book(src)
    html = render_book(book, env)
    dst.parent.mkdir(parents=True, exist_ok=True)
    # 产物必须字节级可复现：写 bytes 而非 write_text，否则 Windows 会把 LF 翻成
    # CRLF，同一份源码每次重建都产生整篇假 diff。
    dst.write_bytes(html.replace("\r\n", "\n").encode("utf-8"))
    return book


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="把 Markdown 小说编译成自包含的单文件 HTML 电子书",
    )
    parser.add_argument("inputs", nargs="*", help="要编译的 md 文件，缺省编译 content/ 全部")
    parser.add_argument("-o", "--output", help="输出 html 路径（仅单个输入时有效）")
    parser.add_argument("--all", action="store_true", help="编译 content/ 下全部 md")
    parser.add_argument(
        "-d", "--dist", default=str(DEFAULT_DIST_DIR), help="输出目录，默认 dist/"
    )
    args = parser.parse_args(argv)

    env = make_env()
    dist_dir = Path(args.dist)

    if args.inputs and not args.all:
        sources = [Path(p) for p in args.inputs]
    else:
        sources = sorted(DEFAULT_CONTENT_DIR.glob("*.md"))

    if not sources:
        print("没有找到任何 .md 源文件", file=sys.stderr)
        return 1

    ok = 0
    for src in sources:
        if not src.exists():
            print(f"[跳过] 文件不存在: {src}", file=sys.stderr)
            continue
        try:
            if args.output and len(sources) == 1:
                dst = Path(args.output)
            else:
                dst = dist_dir / f"{slugify(src.stem)}.html"

            book = compile_one(src, dst, env)
            size_kb = dst.stat().st_size / 1024
            print(
                f"[完成] {src.name} -> {dst}\n"
                f"       书名: {book.title}\n"
                f"       章节: {len(book.chapters)} 章 / {book.word_count} 词\n"
                f"       体积: {size_kb:.1f} KB（单文件，无外部依赖）"
            )
            ok += 1
        except Exception as exc:  # noqa: BLE001 — 编译期错误要打到用户脸上
            print(f"[失败] {src.name}: {exc}", file=sys.stderr)

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
