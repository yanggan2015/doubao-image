"""等待用户在 Chrome 中登录豆包。"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
import launch_chrome  # noqa: E402


def get_page(browser):
    for ctx in browser.contexts:
        for pg in ctx.pages:
            if "doubao.com" in pg.url:
                return pg
    page = browser.contexts[0].new_page()
    page.goto(launch_chrome.DOUBAO_URL, wait_until="domcontentloaded")
    return page


def is_logged_in(page) -> bool:
    """启发式判断：出现登录弹层/未登录文案则视为未登录。"""
    try:
        text = page.locator("body").inner_text(timeout=8000)
    except Exception:
        return False
    # 明显未登录信号
    neg = ("登录后免费使用", "手机号登录", "扫码登录", "未登录", "请先登录")
    # 已登录常见信号（侧栏用户区、输入可用等）
    if any(x in text for x in neg):
        # 若同时有输入框且没有强制登录遮罩，可能仍可用；优先看登录按钮可见性
        pass
    # 登录按钮大量可见且无用户头像时偏未登录
    try:
        login_btns = page.get_by_role("button", name="登录")
        if login_btns.count() and login_btns.first.is_visible():
            # 有些页面登录后仍有「登录」文案在别处，再看是否有「退出登录」
            if page.get_by_text("退出登录").count() == 0 and page.get_by_text("退出").count() == 0:
                # create-image 未登录时常有明显登录引导
                if "登录" in text[:500] or page.locator('[class*="login"]').count():
                    return False
    except Exception:
        pass
    # 能找到可编辑输入且没有「请登录」
    try:
        editors = page.locator('textarea, [contenteditable="true"], [role="textbox"]')
        if editors.count() == 0:
            return False
        ph = (editors.first.get_attribute("placeholder") or "") + (editors.first.inner_text(timeout=1000) or "")
        if "登录" in ph:
            return False
    except Exception:
        return False
    # 若仍有大号「登录豆包」类文案
    if page.locator("text=登录豆包").count() and page.locator("text=登录豆包").first.is_visible():
        return False
    return True


def click_login(page) -> None:
    for loc in (
        page.get_by_role("button", name="登录"),
        page.locator("button:has-text('登录')"),
        page.locator("text=登录"),
    ):
        try:
            if loc.count() and loc.first.is_visible():
                loc.first.click(timeout=3000)
                print("[登录] 已点击登录入口", flush=True)
                return
        except Exception:
            continue
    print("[登录] 请在窗口中手动点「登录」", flush=True)


def wait_login(timeout_sec: int = 300) -> bool:
    if not launch_chrome.ensure_running():
        return False
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{launch_chrome.PORT}")
        page = get_page(browser)
        page.bring_to_front()
        page.wait_for_timeout(2000)
        if is_logged_in(page):
            print("[登录] 已登录", flush=True)
            page.screenshot(path=str(Path(__file__).resolve().parent.parent / "output" / "logged_in.png"))
            return True
        click_login(page)
        print(f"[登录] 请在 Chrome 完成豆包登录（扫码/手机号），最长 {timeout_sec}s …", flush=True)
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            try:
                if is_logged_in(page):
                    print("[登录] ✅ 成功，登录态保存在 .chrome-profile", flush=True)
                    page.screenshot(path=str(Path(__file__).resolve().parent.parent / "output" / "logged_in.png"))
                    return True
            except Exception:
                pass
            time.sleep(2)
        print("[登录] ❌ 超时", flush=True)
        page.screenshot(path=str(Path(__file__).resolve().parent.parent / "output" / "login_timeout.png"))
        return False


if __name__ == "__main__":
    sys.exit(0 if wait_login(int(sys.argv[1]) if len(sys.argv) > 1 else 300) else 1)
