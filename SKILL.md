---
name: doubao-image
description: >-
  Portable Chrome-CDP automation for Doubao (豆包 / doubao.com) image generation.
  Two-prompt design: (1) fast four draft images for 4-to-1 picking with no
  resolution requirement, (2) Doubao picks the best match and optimizes above
  1080P (not 4K), then download. Use when the user asks for 豆包生图、豆包画图、
  doubao 文生图、AI创作、Seedream、4选1、双提示词, or to run this skill on any
  machine. Prefer scripts here; put constraints in prompt text.
---

# 豆包双提示词生图（可移植 Skill）

用本机 Chrome（CDP）打开 [豆包 AI 创作](https://www.doubao.com/chat/create-image)，**主要只发两次提示词**：先快速四张草稿做 4 选 1，再优化成 **大于 1080P** 的终图并下载。

设计设想见 **[DESIGN.md](DESIGN.md)**。排障见 **[references/workflow.md](references/workflow.md)**。

## 设计设想（摘要）

1. 信任提示词，少点 UI  
2. 第1轮快草稿（4选1）→ 第2轮优选优化到 >1080P（不要4K）  
3. 豆包负责选图与画质，脚本负责登录/等待/下载  
4. 自包含目录，任意电脑 clone 可跑（端口默认 9334）

## 换机安装

**依赖**：Python 3.9+、Google Chrome、图形界面（首次登录）、能访问 `doubao.com`。

```bash
git clone <本仓库URL>
mkdir -p ~/.cursor/skills && cp -a doubao-image ~/.cursor/skills/doubao-image
cd ~/.cursor/skills/doubao-image
bash scripts/setup.sh
HEADLESS=0 python scripts/wait_login.py
HEADLESS=0 bash scripts/run.sh "生成一个美女在海边散步的图片，动漫风格"
```

| 路径 | 说明 | Git |
|------|------|-----|
| `.venv/` | Python | 否 |
| `.chrome-profile/` | 登录态 | 否 |
| `downloads/` | 图片 | 否 |

环境变量：`DOUBAO_WORK`、`DOUBAO_PROFILE`、`DOUBAO_DOWNLOADS`、`DOUBAO_CDP_PORT`（默认 9334）、`CHROME_PATH`、`HEADLESS`。

## Agent 工作流

```
进度:
- [ ] 1. bash scripts/setup.sh（若无 venv）
- [ ] 2. 未登录则 wait_login
- [ ] 3. bash scripts/run.sh "<用户描述>"
- [ ] 4. 汇报 final 路径与宽高
```

### 两次提示词

**P1**

```text
{用户描述}。一次快速生成四张图，先出草稿即可，不要求分辨率、不要求高清，尽快生成方便挑选。
```

**P2**

```text
帮我在上面生成的四张图中，找出最符合「{用户描述}」描述的一张，对这张图进行优化重绘：提升细节与画质，分辨率大于1080P即可，不要4K。请直接出图，只输出这一张最终图。
```

### 关键选择器

| 用途 | 选择器 |
|------|--------|
| 输入 | `div.tiptap.ProseMirror` |
| 发送 | `.send-btn-wrapper button` |
| 生成图 | `img`（byteimg/imagex，边长≥400，排除 `rounded-full`） |

## 脚本

| 脚本 | 作用 |
|------|------|
| `scripts/setup.sh` | venv + Playwright |
| `scripts/run.sh` | 一键 |
| `scripts/launch_chrome.py` | CDP Chrome |
| `scripts/wait_login.py` | 登录 |
| `scripts/two_prompt_generate.py` | 主流程 |
| `scripts/paths.py` | 路径 |

## 向用户回复时

- 给出 `final/` 路径与真实宽×高  
- 说明是「草稿四选一 + 优化」，不是 4K
