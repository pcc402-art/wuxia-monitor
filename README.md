# ⚔ 武俠修煉場 — Claude Code Monitor

把 Claude Code 的工作狀態變成武俠場景！每個 agent 化身武林弟子，在修煉場中各展身手。

## 功能

- 即時監控 Claude Code 的 JSONL transcript
- 根據工具使用自動判斷狀態（讀檔 → 翻閱秘笈、執行指令 → 施展輕功、寫檔 → 出劍攻伐...）
- 最多同時顯示 6 個 agent（1 主 session + 5 subagent）
- 多人同區域時以軸心向外擴散，不重疊
- 支援 HiDPI 全螢幕自適應

## 使用

```bash
python3 wuxia-monitor.py [port]
```

預設 port 3000，開瀏覽器到 http://localhost:3000

## 狀態對照

| Claude Code 動作 | 武俠狀態 | 區域 |
|---|---|---|
| 閒置 | 🧘 打坐修煉 | 打坐區 |
| 思考 / 規劃 | 🌀 運功催動 | 運功台 |
| Read / Glob / Grep | 📜 翻閱秘笈 | 藏經閣 |
| Write / Edit | ⚔ 出劍攻伐 | 練劍場 |
| Bash / 執行 | 💨 施展輕功 | 跑道 |
| 完成 | ✨ 大功告成 | 演武廳 |

## 致謝

- 靈感來自 [pixel-agents](https://github.com/pablodelucca/pixel-agents)
- 角色與背景圖片由 Google Gemini 生成
