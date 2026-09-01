"""启动本机 Chrome（CDP）控制豆包网页。默认端口 9334，避免与元宝 9333 冲突。"""
from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

from paths import profile_dir, work_dir

PORT = int(os.environ.get("DOUBAO_CDP_PORT", "9334"))
DOUBAO_URL = os.environ.get("DOUBAO_URL", "https://www.doubao.com/chat/create-image")


def chrome_path() -> str:
    if custom := os.environ.get("CHROME_PATH"):
        return custom
    system = platform.system()
    if system == "Windows":
        for c in (
            os.path.join(os.environ.get("PROGRAMFILES", r"C:\Program Files"), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
        ):
            if c and Path(c).is_file():
                return c
        return "chrome.exe"
    if system == "Darwin":
        mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if Path(mac).is_file():
            return mac
    for name in ("google-chrome", "google-chrome-stable", "chromium-browser", "chromium", "chrome"):
        if found := shutil.which(name):
            return found
    return "google-chrome"


def use_headless() -> bool:
    mode = os.environ.get("HEADLESS", "").strip().lower()
    if mode in {"1", "true", "yes"}:
        return True
    if mode in {"0", "false", "no"}:
        return False
    return platform.system() != "Windows" and not os.environ.get("DISPLAY")


def is_port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def ensure_running() -> str:
    if is_port_open(PORT):
        print(f"[Chrome] 端口 {PORT} 已有实例，直接复用。", flush=True)
        return "reuse"

    prof = profile_dir()
    mode = "无头" if use_headless() else "有界面"
    print(f"[Chrome] 启动（{mode}，work={work_dir()}，profile={prof}，port={PORT}）", flush=True)
    cmd = [
        chrome_path(),
        f"--remote-debugging-port={PORT}",
        f"--user-data-dir={prof}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--window-size=1400,900",
        DOUBAO_URL,
    ]
    if use_headless():
        cmd.append("--headless=new")
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(80):
        if is_port_open(PORT):
            print("[Chrome] 已启动。", flush=True)
            return "started"
        time.sleep(0.5)
    print("[Chrome] 启动失败。请安装 Chrome 或设置 CHROME_PATH。", file=sys.stderr, flush=True)
    return ""


if __name__ == "__main__":
    if not ensure_running():
        sys.exit(1)
