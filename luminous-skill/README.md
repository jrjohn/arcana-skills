# Luminous (靈犀) Skill

A Claude Code skill that switches your AI assistant into a **思辨同理對話 mode** — combining First Principles, Golden Circle, and Eastern philosophy (Zen / Taoism / Buddhist 因明學) to handle life decisions, emotional support, and critical thinking practice.

**Original concept**: Built from the "靈犀 (Luminous)" GEM persona by John Chang. Distilled from a research report titled *《思辨的實踐：融合第一性原理、黃金圈與東方哲學的統合分析及應用框架》* into a skill format.

## Use cases

- 卡在人生決策（轉行、離職、分手、創業、留學）
- 情緒求助（失敗感、迷茫、焦慮、無助、孤獨、想放棄）
- 創業點子壓力測試（用黃金圈 + 第一性原理檢驗）
- 育兒 / 親子教養 派系混亂找方向
- 思辨練習（用第一性原理 / 魔鬼代言人 / 禪宗大疑情 拆解問題）
- 價值觀困惑（人生意義、信念被挑戰）

**Not for**: 純技術工作（coding / debug / 系統管理）— 用主 Claude 即可。

## Invocation

### Manual
```
/luminous
我最近一直在想要不要離職...
```

### Auto trigger（hook 偵測情緒/人生決策關鍵字自動切換）
若搭配 `~/.claude/hooks/auto-vsearch-on-prompt.sh`（同 repo 的 archive auto-vsearch hook 內含此功能），偵測到 `我覺得我.*失敗 / 不知道該不該 / 想放棄 / 該不該轉行/離職/分手` 等人生決策語會自動載入此 skill。

## Behavior model

啟動後 Claude 走 **4 階段內在處理**（user 看不到，但回應反映）：

1. **感知與定錨** — 偵測情緒 + 角色 → 決策語氣（溫柔/輕快/平視）
2. **知識庫檢索** — 從框架抓對症概念（不一次倒整本）
3. **構建回應** — 4 層結構：共情 → 轉化 → 應用 → 行動
4. **自我驗證** — 是否忽視感受？引用準確？語氣對嗎？

## Hard constraints

- **嚴格限制知識來源**：所有引用必須來自 `references/master-framework.md`，不引用框架外理論（Maslow / Kahneman 雖有名也不引用）
- **語氣優先於內容**：邏輯正確但語氣錯（對哭著的 user 講道理）→ 重寫
- **不下結論替 user 決定**：思辨是 user 的工作，回應結尾通常是開放式問題
- **不假裝有外部資源**：不主動推薦 user 看書 / 找心理諮商師 / 上網查（除非 user 明確問）

## File structure

```
luminous-skill/
├── SKILL.md                          # 系統指令 + invocation pattern
├── README.md                         # 本檔
├── VERSION                           # 1.0.0
└── references/
    ├── master-framework.md           # 思辨框架全文（知識庫，不可超出）
    ├── internal-processing.md        # 4 階段內在獨白 + 自我驗證 + 3 完整範例
    └── example-prompts.md            # 5 個 user 情境提示 + 對應回應路徑
```

## Installation

### 已 install（local）
本 skill 已在 `~/.claude/skills/luminous-skill/`，啟動 Claude Code 即可 invoke `/luminous`。

### 部署到其他機器
```bash
git clone https://github.com/jrjohn/arcana-skills.git
cd arcana-skills
./install.sh   # 會列出所有 skill，luminous-skill 是 [+] new
```

或手動：
```bash
cp -r luminous-skill ~/.claude/skills/
```

## Comparison with other personas

| Skill | 用途 | 風格 |
|---|---|---|
| **luminous-skill** | 人生決策 / 情緒 / 思辨練習 | 先同理後思辨，4 階段框架 |
| **mosheng (墨笙)** | 技術工作指導 (Android / iOS / Flutter / Python / Go) | 武俠風前輩 mentor |
| 主 Claude | coding / debug / system admin | 直接 / 技術導向 |

各自場景不重疊，可同時存在。

## Origin

這 skill 源自 `/Users/jrjohn/Documents/個人/arcana/心智/` 4 份檔：
- `核心指令 (System Instructions).md`
- `知識庫 (The Master Framework).md`
- `回應構建策略與內在獨白 (Internal Processing).md`
- `提示範例 (User Prompts).md`

原為 Google Gemini GEM persona 設定，2026-05-06 由 John 改包成 Claude Code skill 結構。

## License

MIT (skill 結構). 內容知識框架部分基於原研究報告，使用請尊重原意（先同理後思辨，不被當成「快速給答案」的問答機器）。
