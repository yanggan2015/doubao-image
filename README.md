# doubao-image

Cursor Skill：Chrome CDP 控制 **豆包**，双提示词生图并下载。

- 第1轮：快速四张草稿（4选1）  
- 第2轮：自选最优并优化到 **>1080P**（不要4K）

设计见 [DESIGN.md](DESIGN.md)，Agent 说明见 [SKILL.md](SKILL.md)。

## 任意电脑

```bash
git clone https://github.com/yanggan2015/doubao-image.git
cd doubao-image
bash scripts/setup.sh
HEADLESS=0 python scripts/wait_login.py
HEADLESS=0 bash scripts/run.sh "你的提示词"
```

装为 Cursor Skill：复制到 `~/.cursor/skills/doubao-image/`。

## 要求

- Python 3.9+、Google Chrome、可登录 [豆包](https://www.doubao.com/chat/create-image)

## License

MIT
