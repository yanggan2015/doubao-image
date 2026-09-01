"""路径约定：默认全部落在 skill 目录内。"""
from __future__ import annotations

import os
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent


def work_dir() -> Path:
    raw = os.environ.get("DOUBAO_WORK", "").strip()
    root = Path(raw).expanduser() if raw else SKILL_ROOT
    root.mkdir(parents=True, exist_ok=True)
    return root


def profile_dir() -> Path:
    raw = os.environ.get("DOUBAO_PROFILE", "").strip()
    p = Path(raw).expanduser() if raw else (work_dir() / ".chrome-profile")
    p.mkdir(parents=True, exist_ok=True)
    return p


def downloads_dir() -> Path:
    raw = os.environ.get("DOUBAO_DOWNLOADS", "").strip()
    p = Path(raw).expanduser() if raw else (work_dir() / "downloads")
    p.mkdir(parents=True, exist_ok=True)
    return p
