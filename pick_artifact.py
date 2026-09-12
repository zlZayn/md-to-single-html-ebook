"""挑出要发布的那一本，并把它生成为站点入口 index.html。

**判定依据是书稿源 `content/*.md` 的提交时间，不是产物的。**

产物是渲染结果：任何一次重建都会改写 `dist/*.html`，它的提交时间恒等于「最后一次
重建」，对「哪一本最近在动」没有判别力 —— 按它选，每次都会退化到平局。
只有书稿源的提交时间能反映维护者实际在写哪一本。

判定优先级：
1. `--requested NAME` 显式指定 dist/ 下的文件名
2. 对应 `content/*.md` 的提交时间最大者（`git log -1 --format=%ct`）
3. 平局按产物文件名升序，保证结果确定

为什么不用 mtime：CI 里 `actions/checkout` 会把所有文件的修改时间统一写成检出时刻，
所有 mtime 相等，按 mtime 取必然挑错。提交时间来自真实 commit，与检出行为无关，
但需要 `fetch-depth: 0`（浅克隆取不到完整历史）。

选中产物复制为 `<site>/index.html`，站点入口因此恒为根路径，同时规避中文文件名的
URL 编码（逆流.html → %E9%80%86%E6%B5%81.html）。

用法：
    uv run python pick_artifact.py dist _site
    uv run python pick_artifact.py dist _site --requested 逆流.html
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# 复用生成器的同名规则：产物文件名怎么来，这里就怎么反查回书稿源，避免两处漂移。
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generator import slugify  # noqa: E402

ROOT = Path(__file__).resolve().parent


def last_commit_time(path: Path | None) -> int:
    """取文件最后一次被提交的时间戳；无对应记录（未入库）返回 0。"""
    if path is None:
        return 0
    try:
        done = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", str(path)],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
    except subprocess.CalledProcessError:
        return 0
    stamp = done.stdout.strip()
    return int(stamp) if stamp.isdigit() else 0


def source_for(artifact: Path, content_dir: Path) -> Path | None:
    """按 slugify 规则反查产物对应的书稿源文件。"""
    for md in sorted(content_dir.glob("*.md")):
        if f"{slugify(md.stem)}.html" == artifact.name:
            return md
    return None


def pick(dist_dir: Path, content_dir: Path, requested: str | None) -> tuple[Path, str]:
    targets = sorted(dist_dir.glob("*.html"))
    if not targets:
        sys.exit(f"{dist_dir} 下没有 .html 产物")

    if requested:
        target = dist_dir / Path(requested).name
        if not target.is_file():
            sys.exit(f"指定的产物不存在：{target}")
        return target, "手动指定"

    # (源提交时间, 产物文件名, 产物路径, 书稿源)
    rows = []
    for t in targets:
        src = source_for(t, content_dir)
        rows.append((last_commit_time(src), t.name, t, src))

    print(f"候选产物（共 {len(rows)} 份，按书稿源提交时间排序）：")
    for stamp, name, _, src in sorted(rows, key=lambda r: (-r[0], r[1])):
        note = f"{stamp}  {src.name}" if src else "无对应书稿，不参与自动判定"
        print(f"  {name}  ←  {note}")

    # 源提交时间降序 → 产物文件名升序
    rows.sort(key=lambda r: (-r[0], r[1]))
    authored, _, target, src = rows[0]

    if src is None:
        reason = "所有产物都没有对应书稿，退化为按文件名取第一个"
    else:
        reason = f"书稿源提交时间最新 {authored}（{src.name}）"
    return target, reason


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="挑出要发布的那一本并生成站点入口 index.html")
    parser.add_argument("dist", type=Path, help="产物目录，如 dist")
    parser.add_argument("site", type=Path, help="站点目录，选中产物会写成其中的 index.html")
    parser.add_argument("--requested", default="", help="指定要发布的产物文件名（含 .html）")
    parser.add_argument("--content", type=Path, default=None, help="书稿目录，默认 <dist>/../content")
    args = parser.parse_args(argv)

    dist_dir = args.dist.resolve()
    content_dir = (args.content or dist_dir.parent / "content").resolve()
    if not content_dir.is_dir():
        sys.exit(f"书稿目录不存在：{content_dir}")

    target, reason = pick(dist_dir, content_dir, args.requested.strip() or None)

    site_dir = args.site
    site_dir.mkdir(parents=True, exist_ok=True)
    entry = site_dir / "index.html"
    shutil.copyfile(target, entry)

    print(f"发布产物：{target.name}")
    print(f"选定依据：{reason}")
    print(f"站点入口：{entry}（{entry.stat().st_size} B）")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as fh:
            fh.write(f"artifact={target.name}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
