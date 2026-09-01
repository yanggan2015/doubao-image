# 豆包双提示词 · 参考

## 入口

- AI 创作图像：`https://www.doubao.com/chat/create-image`
- 发送后常跳转：`https://www.doubao.com/chat/<id>`

## 实测（本机）

| 轮次 | 结果 |
|------|------|
| 第1轮 | 约 4 张，常见 `1728×2304` |
| 第2轮 | 豆包说明选第 N 张后重绘；再出 1 张 |

发送必须点 `.send-btn-wrapper button`（单按 Enter 可能只换行）。

## 故障排查

1. 未登录：右上角登录 / `wait_login.py`  
2. 无图：过滤掉 `rounded-full` 小头像；等「正在生成图片」结束  
3. 端口：默认 `9334`；与元宝 `9333` 可并存  
4. 找不到 Chrome：设 `CHROME_PATH`
