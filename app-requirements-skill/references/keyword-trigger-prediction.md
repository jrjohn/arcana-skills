# 關鍵字觸發模組預測 (Keyword-Triggered Module Prediction)

> **用途**：在 Phase 2 (Step 4) 智慧預測時，根據用戶需求文字中的關鍵字自動觸發模組預測

---

## 核心原則

1. **掃描用戶原始需求**：不只看 SDD，也要回溯 SRS 和原始對話
2. **關鍵字匹配**：使用關鍵字表觸發模組預測
3. **雙向驗證**：預測後驗證 SDD 是否已包含，未包含則補充
4. **優先級排序**：P0 模組必須存在，P1 強烈建議，P2 可選

---

## 關鍵字觸發表

### ENGAGE 模組 (遊戲化/黏著度)

| 觸發關鍵字 | 預測畫面 | 優先級 |
|------------|----------|--------|
| 黏著度、留存、活躍 | 全部 ENGAGE 畫面 | P0 |
| 遊戲化、gamification | SCR-ENGAGE-001-pet, 002-shop, 004-badges | P0 |
| 徽章、成就、badge | SCR-ENGAGE-004-badges | P0 |
| 獎勵、reward、points | SCR-ENGAGE-006-daily-reward | P0 |
| 寵物、pet、角色養成 | SCR-ENGAGE-001-pet, 002-accessories | P1 |
| 商店、shop、兌換 | SCR-ENGAGE-003-shop | P1 |
| 排行榜、leaderboard、排名 | SCR-ENGAGE-005-leaderboard | P1 |
| 連續、streak、每日簽到 | SCR-ENGAGE-006-daily-reward | P1 |

**ENGAGE 模組完整畫面清單**：
```
SCR-ENGAGE-001-pet          寵物/角色
SCR-ENGAGE-002-accessories  配件/裝飾
SCR-ENGAGE-003-shop         商店/兌換
SCR-ENGAGE-004-badges       徽章/成就
SCR-ENGAGE-005-leaderboard  排行榜
SCR-ENGAGE-006-daily-reward 每日獎勵
```

---

### SOCIAL 模組 (社群/分享)

| 觸發關鍵字 | 預測畫面 | 優先級 |
|------------|----------|--------|
| 公開、public、分享給他人 | 全部 SOCIAL 畫面 | P0 |
| 分享、share | SCR-SOCIAL-001-share | P0 |
| 邀請、invite、好友 | SCR-SOCIAL-003-invite | P1 |
| 社群、community | SCR-SOCIAL-002-public-list | P1 |
| 回饋、feedback、意見 | SCR-SOCIAL-004-feedback | P2 |
| 評分、rating、review | SCR-SOCIAL-004-feedback | P2 |

**SOCIAL 模組完整畫面清單**：
```
SCR-SOCIAL-001-share        分享
SCR-SOCIAL-002-public-list  公開內容瀏覽
SCR-SOCIAL-003-invite       邀請好友
SCR-SOCIAL-004-feedback     意見回饋
```

---

### VOCAB 模組擴充 (字庫管理)

| 觸發關鍵字 | 預測畫面 | 優先級 |
|------------|----------|--------|
| 合併、merge | SCR-VOCAB-XXX-merge | P1 |
| 分群、group、分類 | SCR-VOCAB-XXX-group | P1 |
| 匯出、export、導出 | SCR-VOCAB-XXX-export | P0 |
| 批次、batch | SCR-VOCAB-XXX-batch | P1 |
| 發布、publish | SCR-VOCAB-XXX-publish | P1 |
| 編輯單字 | SCR-VOCAB-XXX-edit-word | P0 |
| 快篩、filter、篩選 | SCR-VOCAB-XXX-filter | P1 |

**VOCAB 擴充畫面清單**：
```
SCR-VOCAB-XXX-edit-word     編輯單字
SCR-VOCAB-XXX-export        匯出字庫
SCR-VOCAB-XXX-merge         合併字庫
SCR-VOCAB-XXX-group         分群管理
SCR-VOCAB-XXX-filter        快篩過濾
SCR-VOCAB-XXX-batch         批次操作
SCR-VOCAB-XXX-publish       發布公開
SCR-VOCAB-XXX-ocr-result    OCR 結果確認
```

---

### PROGRESS 模組擴充 (進度/報表)

| 觸發關鍵字 | 預測畫面 | 優先級 |
|------------|----------|--------|
| 報表、report、統計 | 全部 PROGRESS 擴充 | P0 |
| 週報、weekly | SCR-PROGRESS-XXX-weekly | P1 |
| 日曆、calendar | SCR-PROGRESS-XXX-calendar | P1 |
| 趨勢、trend | SCR-PROGRESS-XXX-trend | P2 |
| 技能、skill、能力 | SCR-PROGRESS-XXX-skills | P1 |
| 排名、ranking | SCR-PROGRESS-XXX-ranking | P2 |

**PROGRESS 擴充畫面清單**：
```
SCR-PROGRESS-XXX-weekly     週報
SCR-PROGRESS-XXX-calendar   學習日曆
SCR-PROGRESS-XXX-skills     技能分析
SCR-PROGRESS-XXX-trend      趨勢圖表
SCR-PROGRESS-XXX-ranking    排名統計
SCR-PROGRESS-XXX-daily      每日詳情
```

---

### TRAIN 模組擴充 (訓練模式)

| 觸發關鍵字 | 預測畫面 | 優先級 |
|------------|----------|--------|
| 冒險、adventure、關卡 | SCR-TRAIN-XXX-adventure-map, level-start | P1 |
| 混合、mixed、綜合 | SCR-TRAIN-XXX-mixed | P1 |
| 闖關、stage、level | SCR-TRAIN-XXX-level-start | P1 |
| 挑戰、challenge | SCR-TRAIN-XXX-challenge | P2 |
| 限時、timer、計時 | (UI 元件，非獨立畫面) | - |

**TRAIN 擴充畫面清單**：
```
SCR-TRAIN-XXX-mixed         混合模式
SCR-TRAIN-XXX-adventure-map 冒險地圖
SCR-TRAIN-XXX-level-start   關卡開始
SCR-TRAIN-XXX-challenge     挑戰模式
```

---

### SETTING 模組擴充 (設定頁)

| 觸發關鍵字 | 預測畫面 | 優先級 |
|------------|----------|--------|
| 條款、terms | SCR-SETTING-XXX-terms | P1 |
| 隱私政策、privacy policy | SCR-SETTING-XXX-privacy-policy | P1 |
| 授權、licenses | SCR-SETTING-XXX-licenses | P2 |
| 更新日誌、changelog | SCR-SETTING-XXX-changelog | P2 |
| 幫助、help、FAQ | SCR-SETTING-XXX-help | P1 |
| 學習設定、learning | SCR-SETTING-XXX-learning | P1 |
| 提醒、reminder | SCR-SETTING-XXX-reminder | P1 |
| 同步、sync | SCR-SETTING-XXX-sync | P1 |
| 主題、theme、外觀 | SCR-SETTING-XXX-theme | P1 |

**SETTING 擴充畫面清單**：
```
SCR-SETTING-XXX-terms           服務條款
SCR-SETTING-XXX-privacy-policy  隱私政策
SCR-SETTING-XXX-licenses        開源授權
SCR-SETTING-XXX-changelog       更新日誌
SCR-SETTING-XXX-help            幫助中心
SCR-SETTING-XXX-learning        學習設定
SCR-SETTING-XXX-reminder        提醒設定
SCR-SETTING-XXX-sync            同步設定
SCR-SETTING-XXX-theme           主題設定
```

---

### HOME/DASH 模組 (首頁)

| 觸發關鍵字 | 預測畫面 | 優先級 |
|------------|----------|--------|
| 家長、parent、監護人 | SCR-HOME-002-parent 或獨立 PARENT 模組 | P0 |
| 學生、student、孩童 | SCR-HOME-001-student 或 DASH | P0 |
| 多角色、role | HOME-001 + HOME-002 分離 | P0 |

---

## 智慧預測執行流程

```
Step 4: 執行智慧預測
│
├── 4.1 掃描原始需求文字
│   ├── 讀取用戶原始對話
│   ├── 讀取 SRS 功能需求
│   └── 提取關鍵字列表
│
├── 4.2 關鍵字匹配
│   ├── 對照本文件的觸發表
│   ├── 記錄觸發的模組和畫面
│   └── 按優先級排序
│
├── 4.3 與現有 SDD 比對
│   ├── 檢查 Appendix A 畫面清單
│   ├── 標記已存在的畫面
│   └── 列出缺失的畫面
│
├── 4.4 產生預測報告
│   ├── 必須補充 (P0)
│   ├── 強烈建議 (P1)
│   └── 可選補充 (P2)
│
└── 4.5 更新 screen-prediction.json
    └── 輸出到 04-ui-flow/workspace/
```

---

## 預測報告格式

```json
{
  "prediction_date": "2026-01-16",
  "source_keywords": [
    "極大化提升用戶黏著度",
    "使用者可以選擇公開字庫",
    "字庫可以選擇性合併或分群、導出"
  ],
  "triggered_modules": {
    "ENGAGE": {
      "trigger": "黏著度",
      "priority": "P0",
      "screens": ["pet", "shop", "badges", "leaderboard", "daily-reward"],
      "status": "missing"
    },
    "SOCIAL": {
      "trigger": "公開字庫",
      "priority": "P0",
      "screens": ["share", "public-list", "invite"],
      "status": "missing"
    },
    "VOCAB_EXTEND": {
      "trigger": "合併、分群、導出",
      "priority": "P1",
      "screens": ["merge", "group", "export"],
      "status": "partial"
    }
  },
  "analysis": {
    "existing_screens": 49,
    "predicted_missing": 25,
    "total_recommended": 74
  },
  "action_required": [
    "新增 ENGAGE 模組 (6 畫面)",
    "新增 SOCIAL 模組 (4 畫面)",
    "擴充 VOCAB 模組 (+5 畫面)",
    "擴充 SETTING 模組 (+6 畫面)",
    "擴充 PROGRESS 模組 (+2 畫面)",
    "擴充 TRAIN 模組 (+2 畫面)"
  ]
}
```

---

## 驗證腳本

```bash
#!/bin/bash
# keyword-prediction-check.sh
# 檢查 SRS/用戶需求中的關鍵字並預測缺失模組

SRS_FILE="$1"
SDD_FILE="$2"

echo "🔍 關鍵字觸發預測檢查..."

# ENGAGE 關鍵字
ENGAGE_KEYWORDS="黏著度|留存|活躍|遊戲化|徽章|獎勵|寵物|商店|排行榜"
if grep -qE "$ENGAGE_KEYWORDS" "$SRS_FILE"; then
  echo "⚠️ 檢測到 ENGAGE 關鍵字"
  if ! grep -q "SCR-ENGAGE" "$SDD_FILE"; then
    echo "  ❌ SDD 缺少 ENGAGE 模組！建議新增 6 個畫面"
  fi
fi

# SOCIAL 關鍵字
SOCIAL_KEYWORDS="公開|分享|社群|邀請|好友"
if grep -qE "$SOCIAL_KEYWORDS" "$SRS_FILE"; then
  echo "⚠️ 檢測到 SOCIAL 關鍵字"
  if ! grep -q "SCR-SOCIAL" "$SDD_FILE"; then
    echo "  ❌ SDD 缺少 SOCIAL 模組！建議新增 4 個畫面"
  fi
fi

# VOCAB 擴充關鍵字
VOCAB_EXT="合併|分群|匯出|導出|批次"
if grep -qE "$VOCAB_EXT" "$SRS_FILE"; then
  echo "⚠️ 檢測到 VOCAB 擴充關鍵字"
  VOCAB_COUNT=$(grep -c "SCR-VOCAB" "$SDD_FILE")
  if [ "$VOCAB_COUNT" -lt 12 ]; then
    echo "  ⚠️ VOCAB 模組可能不完整 (現有 $VOCAB_COUNT，建議 12+)"
  fi
fi

echo ""
echo "完成關鍵字預測檢查"
```

---

## 與 common-modules 的整合

關鍵字觸發預測應在 common-modules 驗證之後執行：

```
Phase 2 智慧預測順序：
1. common-modules 必要模組檢核 (AUTH, PROFILE, SETTING, COMMON)
2. App 類型需求載入 (education-requirements.md 等)
3. 關鍵字觸發預測 (本文件) ← 新增
4. Button Navigation 導航缺口分析
5. 命名約定推測 (詳情頁、編輯頁等)
```

---

## 注意事項

1. **不重複預測**：若模組已存在於 SDD，不重複新增
2. **保持 ID 連續**：新增畫面時使用下一個可用編號
3. **更新 Appendix A**：預測後必須更新 SDD 的畫面清單
4. **用戶確認**：P1/P2 優先級的預測建議向用戶確認
