"""点击翻页 + 圆点右上角 + 抽屉排版 —— 回归验证。

目标产物按脚本位置解析 dist/*.html，不写死路径。
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
_TARGETS = sorted((ROOT / "dist").glob("*.html"))
if not _TARGETS:
    sys.exit("dist/ 下没有 .html 产物，先跑 generator.py 编译")
URL = _TARGETS[0].as_uri()

OK, FAIL = [], []


def check(name, cond, extra=""):
    (OK if cond else FAIL).append(name)
    print(f"  [{'OK ' if cond else 'FAIL'}] {name}" + (f"  {extra}" if extra else ""))


def tap(page, x, y):
    """派发一次真实的 touchstart/touchend（500ms 内，位移 0）。"""
    page.evaluate(
        """([x, y]) => {
            const vp = document.querySelector('#viewport');
            const mk = (type) => {
                const t = new Touch({identifier: 1, target: vp, clientX: x, clientY: y});
                return new TouchEvent(type, {
                    bubbles: true, cancelable: true,
                    touches: type === 'touchend' ? [] : [t],
                    changedTouches: [t],
                });
            };
            vp.dispatchEvent(mk('touchstart'));
            vp.dispatchEvent(mk('touchend'));
        }""",
        [x, y],
    )


def text_edges(page, selector):
    """取元素内文本的实际视觉盒，用于判断文字是否对齐（不是元素盒）。"""
    return page.evaluate(
        """(sel) => [...document.querySelectorAll(sel)].map((el) => {
            const r = document.createRange();
            r.selectNodeContents(el);
            const b = r.getBoundingClientRect();
            return {left: Math.round(b.left), right: Math.round(b.right)};
        })""",
        selector,
    )


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(viewport={"width": 390, "height": 844},
                              is_mobile=True, has_touch=True, device_scale_factor=3)
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append("console:" + m.text) if m.type == "error" else None)
    page.goto(URL)
    page.wait_for_timeout(1400)

    W, H = 390, 844

    print("\n【1】初始渲染")
    check("无 JS 错误", not errors, str(errors[:2]))
    total = page.evaluate("window.__reader.paginator.total")
    check("分页已生成", total > 5, f"共 {total} 页")
    check("页码可见", page.inner_text("#pageinfo").strip() != "",
          page.inner_text("#pageinfo").strip())

    print("\n【2】点击右侧 → 下一页")
    p0 = page.evaluate("window.__reader.paginator.page")
    tap(page, W * 0.9, H * 0.5)
    page.wait_for_timeout(520)
    p1 = page.evaluate("window.__reader.paginator.page")
    check("页码 +1", p1 == p0 + 1, f"{p0} → {p1}")
    check("页码文本同步", page.inner_text("#pageinfo").strip().startswith(str(p1 + 1)),
          page.inner_text("#pageinfo").strip())

    print("\n【3】点击左侧 → 上一页")
    tap(page, W * 0.08, H * 0.5)
    page.wait_for_timeout(520)
    p2 = page.evaluate("window.__reader.paginator.page")
    check("页码 -1", p2 == p1 - 1, f"{p1} → {p2}")

    print("\n【4】中轴线分区：中部点击不再弹菜单")
    page.evaluate("window.__reader.ui.closeToolbar()")
    pb = page.evaluate("window.__reader.paginator.page")
    tap(page, W * 0.5, H * 0.5)                # 正中线，归右半屏
    page.wait_for_timeout(520)
    pa = page.evaluate("window.__reader.paginator.page")
    check("正中线 = 下一页", pa == pb + 1, f"{pb} → {pa}")
    check("中部点击不弹工具栏",
          page.evaluate("document.body.dataset.toolbar") == "closed",
          page.evaluate("document.body.dataset.toolbar"))
    tap(page, W * 0.5 - 6, H * 0.5)            # 线左侧 6px，应回退
    page.wait_for_timeout(520)
    pc = page.evaluate("window.__reader.paginator.page")
    check("线左侧 = 上一页", pc == pa - 1, f"{pa} → {pc}")
    check("整屏无中间态热区",
          page.evaluate("document.querySelectorAll('#tapzones, .tapzone').length") == 0)

    print("\n【5】横向滑动不应翻页（拖拽已移除）")
    p3 = page.evaluate("window.__reader.paginator.page")
    page.evaluate(
        """() => {
            const vp = document.querySelector('#viewport');
            const mk = (type, x) => {
                const t = new Touch({identifier: 1, target: vp, clientX: x, clientY: 420});
                return new TouchEvent(type, {
                    bubbles: true, cancelable: true,
                    touches: type === 'touchend' ? [] : [t], changedTouches: [t],
                });
            };
            vp.dispatchEvent(mk('touchstart', 300));
            for (let x = 290; x >= 60; x -= 23) vp.dispatchEvent(mk('touchmove', x));
            vp.dispatchEvent(mk('touchend', 60));
        }"""
    )
    page.wait_for_timeout(600)
    p4 = page.evaluate("window.__reader.paginator.page")
    check("横滑不翻页", p4 == p3, f"{p3} → {p4}")

    print("\n【6】小圆点位于右上角")
    box = page.locator("#immersiveToggle").bounding_box()
    right_gap = W - (box["x"] + box["width"])
    check("水平靠右", box["x"] > W * 0.75,
          f'x={box["x"]:.0f}, 右边距={right_gap:.0f}px')
    check("垂直靠上", box["y"] < H * 0.15, f'y={box["y"]:.0f}px')
    check("尺寸合理", 30 < box["width"] < 60, f'{box["width"]:.0f}×{box["height"]:.0f}')

    print("\n【7】小圆点静默淡显")
    page.wait_for_timeout(1900)          # 等首次提示的唤醒窗口过去
    op = page.evaluate("getComputedStyle(document.querySelector('#immersiveToggle')).opacity")
    check("平时极淡", float(op) <= 0.35, f"opacity={op}")

    print("\n【8】点小圆点 → 展开 + 提示")
    page.click("#immersiveToggle")
    page.wait_for_timeout(400)
    check("工具栏展开", page.evaluate("document.body.dataset.toolbar") == "open")

    print("\n【8b】翻页不应唤醒圆点（避免频闪）")
    page.evaluate("window.__reader.ui.closeToolbar()")
    page.wait_for_timeout(2000)
    tap(page, W * 0.9, H * 0.5)
    page.wait_for_timeout(260)
    awake = page.evaluate("document.querySelector('#immersiveToggle').classList.contains('is-awake')")
    check("翻页后圆点保持静默", not awake)

    print("\n【9】目录跳章仍准确")
    page.evaluate("window.__reader.ui.openDrawer('toc')")
    page.wait_for_timeout(400)
    results = []
    for idx in [0, 3, 6, 9]:
        page.evaluate(f"""() => {{
            const b = document.querySelector('[data-toc-index="{idx}"]');
            b.click();
        }}""")
        page.wait_for_timeout(420)
        cur = page.evaluate("window.__reader.paginator._pinnedChapter")
        results.append(cur == idx)
    check("跳章 4/4 精确", all(results), str(results))

    print("\n【10】边界反馈")
    page.evaluate("window.__reader.paginator.goto(0)")
    page.wait_for_timeout(400)
    tap(page, W * 0.08, H * 0.5)
    page.wait_for_timeout(300)
    check("首页不再往前 / 有提示",
          page.evaluate("window.__reader.paginator.page") == 0
          and page.evaluate("document.querySelector('#toast').classList.contains('is-open')"))

    print("\n【11】夜间 + 沉浸截图状态")
    page.evaluate("window.__reader.settings.apply({theme:'night'})")
    page.evaluate("window.__reader.paginator.goto(12)")
    page.evaluate("window.__reader.ui.closeToolbar()")
    page.wait_for_timeout(600)
    check("沉浸式页码可见", page.inner_text("#pageinfo").strip() != "")

    print("\n【12】底部工具栏已瘦身")
    page.evaluate("window.__reader.settings.apply({theme:'day'})")
    page.evaluate("window.__reader.ui.openToolbar()")
    page.wait_for_timeout(400)
    check("不再有拖拉条",
          page.evaluate("document.querySelectorAll('#toolbar input, .tb-slider').length") == 0)
    check("工具栏只剩 2 个按钮",
          page.evaluate("document.querySelectorAll('#toolbar .tb-btn').length") == 2,
          str(page.evaluate("[...document.querySelectorAll('#toolbar .tb-btn')].map(b => b.textContent.trim())")))

    print("\n【13】抽屉排版成栅格")
    page.evaluate("window.__reader.ui.openDrawer('toc')")
    page.wait_for_timeout(450)
    nums = text_edges(page, ".toc-num")
    titles = text_edges(page, ".toc-title")
    check("目录 10 行", len(nums) == 10 and len(titles) == 10, f"{len(nums)} 行")
    check("序号右边缘对齐",
          len({n["right"] for n in nums}) == 1,
          str(sorted({n["right"] for n in nums})))
    check("标题左边缘对齐",
          len({t["left"] for t in titles}) == 1,
          str(sorted({t["left"] for t in titles})))

    page.evaluate("window.__reader.ui.openDrawer('settings')")
    page.wait_for_timeout(450)
    grid = page.evaluate("""() => {
        const rows = [...document.querySelectorAll('.set-group')];
        const round = (v) => Math.round(v);
        return {
            rows: rows.length,
            label: [...new Set(rows.map(r => round(r.children[0].getBoundingClientRect().left)))],
            ctrl:  [...new Set(rows.map(r => round(r.children[1].getBoundingClientRect().left)))],
            right: [...new Set(rows.map(r => round(r.children[1].getBoundingClientRect().right)))],
        };
    }""")
    check("设置 7 组", grid["rows"] == 7, str(grid["rows"]))
    check("标签左边缘同线", len(grid["label"]) == 1, str(grid["label"]))
    check("控件左边缘同线", len(grid["ctrl"]) == 1, str(grid["ctrl"]))
    check("控件右边缘同线", len(grid["right"]) == 1, str(grid["right"]))
    page.evaluate("window.__reader.ui.closeDrawers()")

    print("\n【14】多机型无溢出")
    page.evaluate("document.exitFullscreen && document.fullscreenElement && document.exitFullscreen()")
    page.wait_for_timeout(300)
    for w, h, label in [(320, 568, "iPhone SE"), (390, 844, "iPhone 14"),
                        (430, 932, "iPhone Pro Max"), (820, 1180, "iPad")]:
        page.set_viewport_size({"width": w, "height": h})
        page.wait_for_timeout(700)
        ov = page.evaluate("""() => {
            // 分页模式下 #book 的 scrollWidth 本来就等于全书总宽度，
            // 真正要检查的是「文档/视口有没有横向溢出」。
            const d = document.documentElement, b = document.body;
            return {
                docX: d.scrollWidth - d.clientWidth,
                bodyX: b.scrollWidth - b.clientWidth,
                total: window.__reader.paginator.total,
            };
        }""")
        dot = page.locator("#immersiveToggle").bounding_box()
        check(f"{label} {w}×{h} 页面无横向溢出",
              ov["docX"] <= 0 and ov["bodyX"] <= 0,
              f'doc={ov["docX"]} body={ov["bodyX"]} 共{ov["total"]}页')
        check(f"{label} 圆点在右上", dot["x"] > w * 0.75 and dot["y"] < h * 0.15,
              f'x={dot["x"]:.0f} y={dot["y"]:.0f}')

    check("全程无 JS 错误", not errors, str(errors[:3]))

    browser.close()

print("\n" + "=" * 52)
print(f"通过 {len(OK)} / {len(OK) + len(FAIL)}")
if FAIL:
    print("失败项：")
    for f in FAIL:
        print("  -", f)
print("=" * 52)
