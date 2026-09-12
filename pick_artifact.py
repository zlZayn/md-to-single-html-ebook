"""挑出要发布的产物，并把它生成为站点入口 index.html。

选定规则（按优先级）：
1. `--requested NAME` 显式指定 dist/ 下的文件名
2. 最后提交时间（`git log -1 --format=%ct`）最新的产物
3. 平局时回落到「该产物对应的 content/ 源文件」的最后提交时间 ——
   一次重建（改模板、CSS、生成器）会同时改动全部产物，**平局在本仓库是常态而非边缘情况**，
   而源文件的时间能反映维护者实际在写哪一本
4. 再平局按文件名升序取第一个，保证结果确定

选中产物复制为 `<site>/index.html`，站点入口因此恒为根路径，同时规避中文文件名的
URL 编码（逆流.html → %E9%80%86%E6%B5%81.html）。

为什么不用 mtime：CI 里 `actions/checkout` 会把所有文件的修改时间统一写成检出时刻，
`dist/*.html` 的 mtime 全部相等，按 mtime 取必然挑错。提交时间来自真实 commit，
与检出行为无关，但需要 `fetch-depth: 0`（浅克隆取不到完整历史）。

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

# 复用生成器的同名规则：产物文件名怎么来，这里就怎么反查回去，避免两处漂移。
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generator import slugify  # noqa: E402

ROOT = Path(__file__).resolve().parent


def last_commit_time(path: Path | None) -> int:
    """取文件最后一次被提交的时间戳；未入库或查询失败返回 0。"""
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

    scored = []
    for t in targets:
        built = last_commit_time(t)
        src = source_for(t, content_dir)
        scored.append((built, last_commit_time(src), t.name, t, src))
    # 提交时间降序 → 源文件时间降序 → 文件名升序
    scored.sort(key=lambda s: (-s[0], -s[1], s[2]))
    built, authored, _, target, src = scored[0]

    reason = f"提交时间最新 {built}"
    if len(scored) > 1 and scored[1][0] == built:
        reason += f"，平局经源文件时间裁定 {authored}"
        if src is not None:
            reason += f"（{src.name}）"
    return target, reason


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="挑出要发布的产物并生成站点入口 index.html")
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
