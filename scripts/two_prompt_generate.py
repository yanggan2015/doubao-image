#!/usr/bin/env python3
"""豆包双提示词生图（Chrome CDP）。

第1轮：快速四张草稿（4选1）
第2轮：元宝同款设想——自选最贴合一张并优化到 >1080P（不要4K）
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import launch_chrome  # noqa: E402
from paths import downloads_dir, work_dir  # noqa: E402
from wait_login import get_page, is_logged_in, wait_login  # noqa: E402


def build_prompt1(user_prompt: str) -> str:
    base = user_prompt.strip().rstrip("。")
    extra = []
    if not re.search(r"四张|4张", base):
        extra.append("一次快速生成四张图")
    if not re.search(r"草稿|快速|不要求分辨率|不用高清", base):
        extra.append("先出草稿即可，不要求分辨率、不要求高清，尽快生成方便挑选")
    if extra:
        return base + "。" + "，".join(extra) + "。"
    return base + "。"


def build_prompt2(user_prompt: str) -> str:
    short = user_prompt.strip().rstrip("。")
    return (
        f"帮我在上面生成的四张图中，找出最符合「{short}」描述的一张，"
        "对这张图进行优化重绘：提升细节与画质，分辨率大于1080P即可，不要4K。"
        "请直接出图，只输出这一张最终图。"
    )


def dismiss(page: Page) -> None:
    page.keyboard.press("Escape")
    time.sleep(0.2)


def ensure_create_image(page: Page) -> None:
    if "doubao.com" not in page.url:
        page.goto(launch_chrome.DOUBAO_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
    # 若在普通对话页也可继续；首次建议 create-image
    if "/chat/" in page.url and "create-image" not in page.url:
        # 已在某次对话中则留在当前会话，便于第2轮承接上下文
        return


def send_prompt(page: Page, text: str) -> None:
    editor = page.locator("div.tiptap.ProseMirror, [contenteditable='true']").last
    editor.wait_for(state="visible", timeout=20000)
    editor.click()
    page.keyboard.press("Control+a")
    page.keyboard.press("Backspace")
    page.keyboard.insert_text(text)
    page.wait_for_timeout(400)
    btn = page.locator(".send-btn-wrapper button")
    if btn.count():
        btn.first.click(force=True, timeout=8000)
    else:
        # 备用：回车不一定发送
        page.keyboard.press("Control+Enter")
    print(f"[发送] {text}", flush=True)


def image_srcs(page: Page) -> set[str]:
    return set(
        page.evaluate(
            """() => [...document.querySelectorAll('img')]
                .map(i => i.currentSrc || i.src).filter(Boolean)"""
        )
    )


def collect_generated(page: Page, before: set[str], min_side: int = 400) -> list[dict]:
    return page.evaluate(
        """({ before, minSide }) => {
          const s = new Set(before);
          return [...document.querySelectorAll('img')].map(img => ({
            src: img.currentSrc || img.src,
            w: img.naturalWidth,
            h: img.naturalHeight,
            cls: (typeof img.className === 'string' ? img.className : ''),
            alt: img.alt || ''
          })).filter(x =>
            x.w >= minSide && x.h >= minSide && x.src && !s.has(x.src)
            && !x.cls.includes('rounded-full')
            && /byteimg|imagex|tos-cn|lf\\d+-|doubao|ibyteimg/.test(x.src)
          );
        }""",
        {"before": list(before), "minSide": min_side},
    )


def wait_images(page: Page, before: set[str], min_count: int, timeout: int, label: str) -> list[dict]:
    t0 = time.time()
    last = -1
    while time.time() - t0 < timeout:
        imgs = collect_generated(page, before)
        # 去重
        uniq, seen = [], set()
        for im in imgs:
            if im["src"] in seen:
                continue
            seen.add(im["src"])
            uniq.append(im)
        imgs = uniq
        if len(imgs) != last:
            print(f"[{label}] {len(imgs)} 张 {[(x['w'], x['h']) for x in imgs]}", flush=True)
            last = len(imgs)
        if len(imgs) >= min_count:
            time.sleep(2.5)
            return collect_generated(page, before)
        time.sleep(2)
    return collect_generated(page, before)


def download_images(page: Page, imgs: list[dict], folder: Path, prefix: str) -> list[Path]:
    folder.mkdir(parents=True, exist_ok=True)
    saved, seen = [], set()
    for i, im in enumerate(imgs, 1):
        if im["src"] in seen:
            continue
        seen.add(im["src"])
        body = page.request.get(im["src"]).body()
        if body.startswith(b"\x89PNG"):
            ext = ".png"
        elif body[:3] == b"\xff\xd8\xff":
            ext = ".jpg"
        else:
            ext = ".png"
        path = folder / f"{prefix}_{i:02d}_{im['w']}x{im['h']}{ext}"
        path.write_bytes(body)
        print(f"[保存] {path} ({len(body)} bytes)", flush=True)
        saved.append(path)
    return saved


def run(user_prompt: str, keep_round1: bool, timeout: int, out_dir: Path | None) -> Path:
    if not launch_chrome.ensure_running():
        raise RuntimeError("Chrome 启动失败")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{launch_chrome.PORT}")
        page = get_page(browser)
        page.bring_to_front()
        dismiss(page)
        page.wait_for_timeout(800)

        if not is_logged_in(page):
            print("[登录] 需要登录", flush=True)
            if not wait_login(300):
                raise RuntimeError("登录失败/超时")
            page = get_page(browser)

        # 新开 create-image，保证干净一轮
        page.goto(launch_chrome.DOUBAO_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        dismiss(page)
        ensure_create_image(page)

        p1 = build_prompt1(user_prompt)
        p2 = build_prompt2(user_prompt)

        before1 = image_srcs(page)
        send_prompt(page, p1)
        imgs1 = wait_images(page, before1, 4, timeout, "第1轮")
        # 去重后取末尾最多 4 张
        uniq, seen = [], set()
        for im in imgs1:
            if im["src"] in seen:
                continue
            seen.add(im["src"])
            uniq.append(im)
        imgs1 = uniq[-4:] if len(uniq) >= 4 else uniq
        if len(imgs1) < 1:
            raise RuntimeError("第1轮未生成图片")
        if len(imgs1) < 4:
            print(f"[警告] 第1轮只拿到 {len(imgs1)} 张", flush=True)

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", user_prompt)[:28]
        root = out_dir or (downloads_dir() / f"{stamp}_{slug}")
        root.mkdir(parents=True, exist_ok=True)
        print(f"[工作区] {work_dir()}", flush=True)

        if keep_round1:
            download_images(page, imgs1, root / "round1", "r1")

        before2 = image_srcs(page)
        send_prompt(page, p2)
        imgs2 = wait_images(page, before2, 1, timeout, "第2轮")
        uniq2, seen2 = [], set()
        for im in imgs2:
            if im["src"] in seen2:
                continue
            seen2.add(im["src"])
            uniq2.append(im)
        imgs2 = uniq2
        if not imgs2:
            raise RuntimeError("第2轮未生成最终图")

        best = max(imgs2, key=lambda x: x["w"] * x["h"])
        finals = download_images(page, [best], root / "final", "final")
        meta = {
            "user_prompt": user_prompt,
            "prompt1": p1,
            "prompt2": p2,
            "round1": imgs1,
            "round2": imgs2,
            "best": best,
            "final_files": [str(x) for x in finals],
            "note": "豆包：第1轮快草稿；第2轮优选优化 >1080P（非4K）。以 final 真实宽高为准。",
        }
        (root / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[完成] 最终图: {finals[0]}", flush=True)
        print(f"[完成] 分辨率: {best['w']}x{best['h']}", flush=True)
        return root


def main() -> None:
    ap = argparse.ArgumentParser(description="豆包双提示词：快速四张 → 4选1优化(>1080P)")
    ap.add_argument("prompt", nargs="+", help="画面描述")
    ap.add_argument("--keep-round1", action="store_true")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    try:
        run(" ".join(args.prompt), args.keep_round1, args.timeout, args.out)
    except Exception as exc:
        print(f"[失败] {exc}", file=sys.stderr, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
