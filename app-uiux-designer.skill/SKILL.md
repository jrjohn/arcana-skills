---
name: app-uiux-designer
description: |
  Enterprise UI/UX design expert using Chain of Repository (CoR) architecture.
  SRS/SDD → 100% UI/UX + 100% Navigation.
  Platform: iOS HIG / Material Design 3 / WCAG.

  ⚠️ 本 Skill 僅負責 Phase 3: UI Flow 產生
  智慧預測已在 Phase 2 (app-requirements-skill) 完成
---

# UI/UX Designer Skill (Chain of Repository)

**Core:** SDD (含完整畫面清單) → 100% UI/UX 生成 → 100% Navigation 驗證
**Architecture:** Chain of Repository - 按需載入節點，減少 token 使用

---

## 與 app-requirements-skill 整合

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1-2: 由 app-requirements-skill 負責                        │
├─────────────────────────────────────────────────────────────────┤
│ • SRS 撰寫                                                      │
│ • SDD 撰寫 + 智慧預測 + 畫面補充                                  │
│ • 確認完整畫面清單 (Appendix A)                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
              ⚠️ 進入條件: SDD 完整 + 智慧預測完成
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 3: 由 app-uiux-designer.skill 負責 ← 本 Skill              │
├─────────────────────────────────────────────────────────────────┤
│ Step 1: UI Flow 框架初始化 (00-init)                             │
│ Step 2: 產出完整 UI Flow HTML (03-generation)                    │
│ Step 3: 導航驗證 (04-validation)                                 │
│ Step 4: UI Flow Diagram 產出 (05-diagram)                        │
│ Step 5: 產出截圖 (06-screenshot)                                 │
│ Step 6: 回補 SDD/SRS + 重新產生 DOCX (07-feedback) ⚠️            │
│ Step 7: 最終驗證 + 完成報告 (08-finalize)                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                        ✅ UI Flow 完成
```

### 07-feedback 回補內容 (MANDATORY)

| 文件 | 回補內容 |
|------|----------|
| **SDD** | 每個 SCR-* 區塊加入 UI 原型參考 (iPad/iPhone 截圖)、確認 `對應需求` 欄位 |
| **SRS** | 新增 Screen References 章節、Inferred Requirements、User Flows、**加入 `SDD 追蹤` 欄位** |
| **DOCX** | 重新產生 SDD.docx 和 SRS.docx (含嵌入圖片) |

### IEC 62304 雙向追蹤 (MANDATORY)

> ⚠️ **強制要求**：回補時必須建立 SRS ↔ SDD 雙向追蹤

| 方向 | 欄位 | 範例 |
|------|------|------|
| SRS → SDD | `\| **SDD 追蹤** \| SCR-xxx \|` | `SCR-AUTH-001-login, SCR-AUTH-002-register` |
| SDD → SRS | `\| **對應需求** \| REQ-xxx \|` | `REQ-AUTH-001, REQ-AUTH-002` |

---

## 設計理念

> **目標是 100% 完成 UI/UX，不是部分實作！**

### 驗證標準 (全部必須達成)

| 項目 | 要求 |
|------|------|
| UI/UX 覆蓋率 | 100% - 所有 SDD 畫面都已生成 |
| 導航覆蓋率 | 100% - 所有可點擊元素都有有效導航 |
| 空按鈕 | 0 個 - 禁止 `onclick=""` |
| Alert 佔位符 | 0 個 - 禁止 `onclick="alert('...')"` |

### 禁止項目

- ❌ `onclick=""` 或無 onclick
- ❌ `onclick="alert('功能說明')"`
- ❌ `href="#"` 懸空連結
- ❌ 部分畫面實作

---

## 🚨 onclick 生成強制規則 (CRITICAL)

> **生成任何 `<button>` 標籤時，必須同時寫入 `onclick` 屬性！**

### 生成時強制檢查流程

```
寫 <button> 標籤時：
1. 查 SDD Button Navigation → 有目標 → 使用指定目標
                           ↓ 無
2. 根據按鈕文字預測 → 可預測 → 使用預測目標
                   ↓ 無法預測
3. 使用合理預設 → 查看類 → 相關詳情頁
               → 操作類 → history.back() 或來源頁
```

### 常見按鈕文字預設目標

| 按鈕文字 | 預設目標 |
|----------|----------|
| 查看獎勵/成就 | `../engage/SCR-ENGAGE-004-badges.html` |
| 查看報表 | `../progress/SCR-PROGRESS-001-overview.html` |
| 開始學習 | `../train/SCR-TRAIN-001-select-vocab.html` |
| 儲存/保存/取消 | `history.back()` |
| 設定 | `../setting/SCR-SETTING-001-main.html` |

### 生成後自檢命令

```bash
# 每個畫面生成後立即執行
grep -n '<button' SCR-*.html | grep -v 'onclick='
# 若有輸出 → 必須立即修復！
```

**詳細規則**: 見 `process/03-generation/README.md` Step 3

---

## Quick Start

1. **檢查進入條件**: 確認 SDD 已完成智慧預測
2. **檢查狀態**: 讀取 `{PROJECT}/04-ui-flow/workspace/current-process.json`
3. **進入節點**: 讀取對應的 `[SKILL_DIR]/process/XX/README.md`
4. **執行步驟**: 依照 README.md 執行
5. **⚠️ 自動驗證**: 每個節點完成前**必須**執行驗證 (見下方 Auto-Validation 規則)
6. **更新狀態**: 驗證通過後更新 `workspace/current-process.json`

> ⚠️ **重要**: `workspace/` 目錄位於**專案的 04-ui-flow/** 下，不是 skill 目錄！

---

## ⚠️ Auto-Validation Rules (MANDATORY - 不可跳過)

> **Claude 必須在每個節點完成前自動執行驗證，無需用戶提醒！**

### 驗證觸發時機

| 節點 | 何時驗證 | 驗證內容 |
|------|----------|----------|
| 00-init | 模板複製完成後 | 模板完整性、變數替換 |
| 03-generation | 畫面生成完成後 | **Template Compliance Gate** |
| 04-validation | 修復完成後 | 導航 100% + 一致性 |
| 06-screenshot | 截圖產生後 | 截圖檔案存在 |
| 07-feedback | 回補完成後 | **UI 原型參考完整性 + Use Case 完整性** |

### 03-generation Template Compliance Gate (Critical)

> **在標記 03-generation 為 completed 前，必須通過以下所有驗證！**

```bash
#!/bin/bash
# === Template Compliance Gate (自動執行) ===
cd {PROJECT}/04-ui-flow

ERRORS=0

echo "🔍 執行 Template Compliance Gate..."

# 1. index.html 完整性
echo ""
echo "📊 驗證 index.html 模板合規..."
grep -q 'flow-iframe' index.html || { echo "❌ 缺少 UI Flow Diagram iframe"; ERRORS=$((ERRORS+1)); }
grep -q 'switchDevice' index.html || { echo "❌ 缺少裝置切換功能"; ERRORS=$((ERRORS+1)); }
grep -q 'device-toggle-btn' index.html || { echo "❌ 缺少裝置切換按鈕"; ERRORS=$((ERRORS+1)); }
grep -q 'sidebar' index.html || { echo "❌ 缺少模組圖例側邊欄"; ERRORS=$((ERRORS+1)); }
grep -q '{{' index.html && { echo "❌ 有未替換變數"; ERRORS=$((ERRORS+1)); }
[ $ERRORS -eq 0 ] && echo "✅ index.html 基本合規"

# 2. index.html 雙版本 Diagram 切換檢核 (MANDATORY)
echo ""
echo "📱 驗證 index.html 引用 iPad/iPhone 雙版本 Diagram..."
grep -q 'ui-flow-diagram-ipad.html' index.html || { echo "❌ index.html 缺少 ui-flow-diagram-ipad.html 引用"; ERRORS=$((ERRORS+1)); }
grep -q 'ui-flow-diagram-iphone.html' index.html || { echo "❌ index.html 缺少 ui-flow-diagram-iphone.html 引用"; ERRORS=$((ERRORS+1)); }
# 確認 switchDevice 使用獨立檔案而非 query parameter
grep -q "ui-flow-diagram.html?device=" index.html && { echo "❌ index.html 使用舊版 query parameter 切換方式，應使用獨立檔案"; ERRORS=$((ERRORS+1)); }
[ $ERRORS -eq 0 ] && echo "✅ index.html 雙版本切換正確"

# 3. docs/ui-flow-diagram-ipad.html 存在與畫面同步
echo ""
echo "📱 驗證 ui-flow-diagram-ipad.html..."
IPAD_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*" | wc -l | tr -d ' ')
[ -f "docs/ui-flow-diagram-ipad.html" ] || { echo "❌ 缺少 docs/ui-flow-diagram-ipad.html"; ERRORS=$((ERRORS+1)); }
if [ -f "docs/ui-flow-diagram-ipad.html" ]; then
  IPAD_DIAGRAM_COUNT=$(grep -c 'onclick="openScreen\|screen-card' docs/ui-flow-diagram-ipad.html 2>/dev/null | head -1 || echo "0")
  # 使用 onclick 計數更準確
  IPAD_DIAGRAM_COUNT=$(grep -c 'onclick="openScreen' docs/ui-flow-diagram-ipad.html 2>/dev/null || echo "0")
  [ "$IPAD_DIAGRAM_COUNT" -eq "$IPAD_COUNT" ] && echo "✅ iPad Diagram 畫面數: $IPAD_DIAGRAM_COUNT" || { echo "❌ iPad Diagram ($IPAD_DIAGRAM_COUNT) ≠ 實際 ($IPAD_COUNT)"; ERRORS=$((ERRORS+1)); }
fi

# 4. docs/ui-flow-diagram-iphone.html 存在與畫面同步
echo ""
echo "📱 驗證 ui-flow-diagram-iphone.html..."
[ -f "docs/ui-flow-diagram-iphone.html" ] || { echo "❌ 缺少 docs/ui-flow-diagram-iphone.html"; ERRORS=$((ERRORS+1)); }
if [ -f "docs/ui-flow-diagram-iphone.html" ]; then
  IPHONE_DIAGRAM_COUNT=$(grep -c 'onclick="openScreen\|onclick="loadScreen' docs/ui-flow-diagram-iphone.html 2>/dev/null || echo "0")
  [ "$IPHONE_DIAGRAM_COUNT" -eq "$IPAD_COUNT" ] && echo "✅ iPhone Diagram 畫面數: $IPHONE_DIAGRAM_COUNT" || { echo "❌ iPhone Diagram ($IPHONE_DIAGRAM_COUNT) ≠ 實際 ($IPAD_COUNT)"; ERRORS=$((ERRORS+1)); }
fi

# 5. device-preview.html 側邊欄同步
echo ""
echo "📱 驗證 device-preview.html 側邊欄同步..."
SIDEBAR_COUNT=$(grep -c 'screen-item' device-preview.html 2>/dev/null || echo "0")
[ "$SIDEBAR_COUNT" -eq "$IPAD_COUNT" ] && echo "✅ device-preview 側邊欄: $SIDEBAR_COUNT" || { echo "❌ device-preview ($SIDEBAR_COUNT) ≠ 實際 ($IPAD_COUNT)"; ERRORS=$((ERRORS+1)); }

# 6. 執行 Post-Generation Gate (整合所有驗證)
echo ""
echo "🚨 執行 Post-Generation Gate..."
node ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/post-generation-gate.js || ERRORS=$((ERRORS+1))

# 結果
echo ""
echo "======================================"
if [ $ERRORS -eq 0 ]; then
  echo "✅ Template Compliance Gate PASSED"
  echo "可以標記 03-generation 為 completed"
else
  echo "❌ Template Compliance Gate FAILED ($ERRORS errors)"
  echo "禁止進入下一階段！請修復問題後重新驗證。"
  exit 1
fi
```

> **Claude 必須在產生 index.html / device-preview.html 後立即執行 post-generation-gate.js**

### 驗證失敗處理

| 失敗項目 | 修復動作 |
|----------|----------|
| 缺少 UI Flow Diagram iframe | 從 `templates/ui-flow/index.html` 複製區塊 |
| 缺少裝置切換功能 | 從模板複製 `switchDevice()` 函數 |
| 缺少模組圖例側邊欄 | 從模板複製 sidebar 區塊 |
| index.html 缺少 iPad/iPhone 雙版本引用 | 確保 `switchDevice()` 使用 `ui-flow-diagram-ipad.html` 和 `ui-flow-diagram-iphone.html` |
| 使用舊版 query parameter 切換 | 將 `ui-flow-diagram.html?device=X` 改為獨立檔案路徑 |
| 缺少 ui-flow-diagram-ipad.html | 建立 iPad 版本 Diagram (橫向框架 200x140) |
| 缺少 ui-flow-diagram-iphone.html | 建立 iPhone 版本 Diagram (直向框架 120x260) |
| iPad/iPhone Diagram 畫面數不符 | 同步更新對應的 Diagram HTML |
| device-preview 側邊欄不符 | 同步更新 `device-preview.html` |
| 一致性驗證失敗 | 依據錯誤訊息修復 |

### 🚨 iframe src Path Validation (BLOCKING - 強制驗證)

> **所有 iframe src 路徑必須指向實際存在的 HTML 檔案！**

```bash
#!/bin/bash
# === iframe src Path Validation (BLOCKING) ===
cd {PROJECT}/04-ui-flow

ERRORS=0
echo "🔍 執行 iframe src 路徑完整性驗證..."

# 1. 取得實際畫面檔案清單
IPAD_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*" | wc -l | tr -d ' ')
IPHONE_COUNT=$(find ./iphone -name "SCR-*.html" 2>/dev/null | wc -l | tr -d ' ')
echo "📊 實際畫面: iPad=$IPAD_COUNT, iPhone=$IPHONE_COUNT"

# 2. 驗證 ui-flow-diagram-ipad.html 的 iframe src
echo ""
echo "📱 驗證 ui-flow-diagram-ipad.html iframe src..."
if [ -f "docs/ui-flow-diagram-ipad.html" ]; then
  IPAD_MISSING=0
  for src in $(grep -oE "src=\"\.\./[^\"]+\.html\"" docs/ui-flow-diagram-ipad.html | sed 's/src="\.\.\/\([^"]*\)"/\1/' | sort -u); do
    if [ ! -f "$src" ]; then
      echo "❌ 缺少檔案: $src"
      IPAD_MISSING=$((IPAD_MISSING+1))
    fi
  done
  [ $IPAD_MISSING -eq 0 ] && echo "✅ iPad Diagram: 全部路徑正確" || { echo "❌ iPad Diagram 缺少 $IPAD_MISSING 個檔案"; ERRORS=$((ERRORS+IPAD_MISSING)); }
fi

# 3. 驗證 ui-flow-diagram-iphone.html 的 iframe src
echo ""
echo "📱 驗證 ui-flow-diagram-iphone.html iframe src..."
if [ -f "docs/ui-flow-diagram-iphone.html" ]; then
  IPHONE_MISSING=0
  for src in $(grep -oE "src=\"\.\./[^\"]+\.html\"" docs/ui-flow-diagram-iphone.html | sed 's/src="\.\.\/\([^"]*\)"/\1/' | sort -u); do
    if [ ! -f "$src" ]; then
      echo "❌ 缺少檔案: $src"
      IPHONE_MISSING=$((IPHONE_MISSING+1))
    fi
  done
  [ $IPHONE_MISSING -eq 0 ] && echo "✅ iPhone Diagram: 全部路徑正確" || { echo "❌ iPhone Diagram 缺少 $IPHONE_MISSING 個檔案"; ERRORS=$((ERRORS+IPHONE_MISSING)); }
fi

# 4. 驗證 device-preview.html 的 loadScreen 路徑
echo ""
echo "📱 驗證 device-preview.html loadScreen 路徑..."
if [ -f "device-preview.html" ]; then
  PREVIEW_MISSING=0
  for src in $(grep -oE "loadScreen\('[^']+\.html'" device-preview.html | sed "s/loadScreen('//" | sed "s/'$//" | sort -u); do
    if [ ! -f "$src" ]; then
      echo "❌ 缺少檔案: $src"
      PREVIEW_MISSING=$((PREVIEW_MISSING+1))
    fi
  done
  [ $PREVIEW_MISSING -eq 0 ] && echo "✅ device-preview: 全部路徑正確" || { echo "❌ device-preview 缺少 $PREVIEW_MISSING 個檔案"; ERRORS=$((ERRORS+PREVIEW_MISSING)); }
fi

# 5. 驗證 loadScreen 數量與實際畫面數量一致
PREVIEW_COUNT=$(grep -oE "loadScreen\('[^']+\.html'" device-preview.html | sort -u | wc -l | tr -d ' ')
[ "$PREVIEW_COUNT" -eq "$IPAD_COUNT" ] && echo "✅ device-preview 畫面數: $PREVIEW_COUNT" || { echo "❌ device-preview ($PREVIEW_COUNT) ≠ 實際 ($IPAD_COUNT)"; ERRORS=$((ERRORS+1)); }

# 結果
echo ""
echo "======================================"
if [ $ERRORS -eq 0 ]; then
  echo "✅ iframe src Path Validation PASSED"
else
  echo "❌ iframe src Path Validation FAILED ($ERRORS errors)"
  echo "⚠️ 禁止進入下一階段！"
  echo "📋 修復方式:"
  echo "   1. 確認所有畫面已正確生成"
  echo "   2. 更新 Diagram 檔案使用正確的畫面路徑"
  echo "   3. 更新 device-preview.html 側邊欄"
  exit 1
fi
```

### 驗證時機

| 節點完成後 | 必須執行此驗證 |
|------------|----------------|
| 03-generation | ✅ 產生畫面後必須驗證 |
| 05-diagram | ✅ 產生 Diagram 後必須驗證 |
| 06-screenshot 之前 | ✅ 截圖前必須驗證路徑正確 |

> ⚠️ **Critical**: 若驗證失敗，**禁止**進入下一節點！必須修復所有路徑問題。

### 自動驗證行為要求

1. **Claude 必須主動執行**：不需用戶提醒或詢問
2. **驗證失敗時不能繼續**：必須修復後重新驗證
3. **記錄驗證結果**：在 `current-process.json` 中記錄
4. **每次 compaction 後恢復**：重新執行驗證確認狀態

### 07-feedback UI 原型參考完整性驗證 (Critical)

> **在標記 07-feedback 為 completed 前，必須通過以下驗證！**

```bash
#!/bin/bash
# === UI 原型參考完整性驗證 ===
cd {PROJECT}/02-design
SDD_FILE=$(ls SDD-*.md | head -1)

ERRORS=0
echo "🔍 執行 UI 原型參考完整性驗證..."

# 1. 統計 SDD 本文畫面數
SCREEN_COUNT=$(grep -c "^#### SCR-" "$SDD_FILE")

# 2. 統計有圖片參考的畫面數 (iPad)
IPAD_REF=$(grep -c "images/ipad/SCR-.*\.png" "$SDD_FILE")

# 3. 統計有圖片參考的畫面數 (iPhone)
IPHONE_REF=$(grep -c "images/iphone/SCR-.*\.png" "$SDD_FILE")

echo "📊 統計結果:"
echo "   SDD 畫面數: $SCREEN_COUNT"
echo "   iPad 圖片參考: $IPAD_REF"
echo "   iPhone 圖片參考: $IPHONE_REF"

# 4. 驗證一致性
[ "$SCREEN_COUNT" != "$IPAD_REF" ] && { echo "❌ iPad 圖片參考不足"; ERRORS=$((ERRORS+1)); }
[ "$SCREEN_COUNT" != "$IPHONE_REF" ] && { echo "❌ iPhone 圖片參考不足"; ERRORS=$((ERRORS+1)); }

# 5. 驗證圖片檔案存在
MISSING_IPAD=$(for f in $(grep -oE "images/ipad/SCR-[^)\"]+\.png" "$SDD_FILE" | sort -u); do [ ! -f "$f" ] && echo "$f"; done | wc -l)
MISSING_IPHONE=$(for f in $(grep -oE "images/iphone/SCR-[^)\"]+\.png" "$SDD_FILE" | sort -u); do [ ! -f "$f" ] && echo "$f"; done | wc -l)
[ "$MISSING_IPAD" -gt 0 ] && { echo "❌ 缺少 $MISSING_IPAD 個 iPad 圖片檔案"; ERRORS=$((ERRORS+1)); }
[ "$MISSING_IPHONE" -gt 0 ] && { echo "❌ 缺少 $MISSING_IPHONE 個 iPhone 圖片檔案"; ERRORS=$((ERRORS+1)); }

# 結果
echo ""
if [ $ERRORS -eq 0 ]; then
  echo "✅ UI 原型參考完整性驗證 PASSED"
else
  echo "❌ UI 原型參考完整性驗證 FAILED ($ERRORS errors)"
  exit 1
fi
```

| 驗證項目 | 預期結果 |
|----------|----------|
| SDD 畫面數 = iPad 圖片參考數 | 100% 一致 |
| SDD 畫面數 = iPhone 圖片參考數 | 100% 一致 |
| 所有參考的圖片檔案都存在 | 0 缺失 |

### SDD Use Case 完整性驗證 (Critical)

> **在回補 SDD 時，必須同時驗證 Use Case 完整性！**

```bash
#!/bin/bash
# === Use Case 完整性驗證 ===
cd {PROJECT}/02-design
SDD_FILE=$(ls SDD-*.md | head -1)

echo "🔍 執行 Use Case 完整性驗證..."

# 1. 統計 Use Case 總覽表中的 UC 數量
TABLE_UC=$(grep -E "^\| UC-" "$SDD_FILE" | grep -v "^| UC-ID" | wc -l | tr -d ' ')

# 2. 統計詳細描述章節中的 UC 數量
DETAIL_UC=$(grep -c "^#### UC-" "$SDD_FILE")

echo "📊 統計結果:"
echo "   總覽表 UC 數: $TABLE_UC"
echo "   詳細描述 UC 數: $DETAIL_UC"

# 3. 驗證一致性
if [ "$TABLE_UC" != "$DETAIL_UC" ]; then
  echo ""
  echo "❌ Use Case 數量不一致！"
  echo ""
  echo "📋 總覽表中的 UC:"
  grep -E "^\| UC-" "$SDD_FILE" | grep -v "^| UC-ID" | awk -F'|' '{print "   " $2}'
  echo ""
  echo "📋 詳細描述中的 UC:"
  grep "^#### UC-" "$SDD_FILE" | sed 's/^#### /   /'
  echo ""
  echo "⚠️ 請補充缺少的 Use Case 詳細描述！"
  exit 1
else
  echo "✅ Use Case 完整性驗證 PASSED ($TABLE_UC 個)"
fi
```

| 驗證項目 | 預期結果 |
|----------|----------|
| 總覽表 UC 數 = 詳細描述 UC 數 | 100% 一致 |
| 每個 UC 都有前置/後置條件 | 必備 |
| 每個 UC 都有主要流程 | 必備 |

### ASCII Art 禁止驗證 (Critical)

> **回補文件前，必須確認無 ASCII Art！**

```bash
#!/bin/bash
# ASCII Art 偵測驗證
cd {PROJECT}
echo "🔍 驗證是否有禁用的 ASCII Art..."

ERRORS=0
for FILE in 01-requirements/SRS-*.md 02-design/SDD-*.md; do
  if [ -f "$FILE" ]; then
    ASCII_BLOCKS=$(awk '/^```[^m]|^```$/{flag=1; next} /^```/{flag=0} flag && /[┌┐└┘│─├┤┬┴┼→←↑↓▶◀■□●○]/' "$FILE" | wc -l | tr -d ' ')
    if [ "$ASCII_BLOCKS" -gt 0 ]; then
      echo "❌ $FILE 含有 ASCII Art ($ASCII_BLOCKS 行)"
      ERRORS=$((ERRORS+1))
    fi
  fi
done

[ $ERRORS -eq 0 ] && echo "✅ 無 ASCII Art 違規" || { echo "⚠️ 請改用 Mermaid"; exit 1; }
```

---

## Process Chain (完整版)

| Step | Process | 進入條件 | 退出條件 |
|------|---------|----------|----------|
| 00 | init | SDD 完整 + 智慧預測完成 | 模板已複製、變數已替換 |
| 03 | generation | 00 完成 | **100% 畫面** HTML 已產生 |
| 04 | validation | 03 完成 | **100% Navigation + 0 alert** (BLOCKING) |
| 05 | diagram | 04 完成 | UI Flow Diagram (iPad/iPhone 雙版本) |
| 06 | screenshot | 05 完成 + 路徑驗證通過 | iPad/iPhone 截圖已產生 (見 Error Recovery) |
| **07** | **feedback** | 06 完成 | **SDD/SRS 已回補 + DOCX 已重新產生** ⚠️ |
| 08 | finalize | 07 完成 | 追溯驗證通過 + 完成報告 |

> ⚠️ **注意**: 01-discovery 和 02-planning 已由 app-requirements-skill 完成，本 Skill 跳過

### 🚨 06-screenshot Error Recovery Logic (BLOCKING)

> **若截圖過程中發現畫面不存在，必須返回 03-generation 重新生成！**

#### 截圖前必須驗證

```bash
#!/bin/bash
# === 06-screenshot Pre-Validation (BLOCKING) ===
cd {PROJECT}/04-ui-flow

echo "🔍 截圖前驗證..."

# 1. 執行 iframe src Path Validation (見上方)
# 2. 若失敗，禁止進入 06-screenshot

# 3. 額外驗證：確認 Diagram 畫面數與實際一致
ACTUAL_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*" | wc -l | tr -d ' ')
DIAGRAM_IPAD_COUNT=$(grep -c 'onclick="openScreen' docs/ui-flow-diagram-ipad.html 2>/dev/null || echo "0")
DIAGRAM_IPHONE_COUNT=$(grep -c 'onclick="openScreen' docs/ui-flow-diagram-iphone.html 2>/dev/null || echo "0")

if [ "$ACTUAL_COUNT" != "$DIAGRAM_IPAD_COUNT" ] || [ "$ACTUAL_COUNT" != "$DIAGRAM_IPHONE_COUNT" ]; then
  echo "❌ 畫面數不一致！"
  echo "   實際畫面: $ACTUAL_COUNT"
  echo "   iPad Diagram: $DIAGRAM_IPAD_COUNT"
  echo "   iPhone Diagram: $DIAGRAM_IPHONE_COUNT"
  echo ""
  echo "⚠️ 必須返回 05-diagram 重新生成 Diagram！"
  exit 1
fi

echo "✅ 截圖前驗證通過，可以執行截圖"
```

#### 截圖錯誤處理流程

```
06-screenshot 執行時：

1. Puppeteer 嘗試載入畫面
   ├── 成功 → 繼續截圖
   └── 失敗 (404/無法載入) → Error Recovery 流程

2. Error Recovery 流程：
   ├── 記錄缺少的畫面 ID 到 error-log.json
   ├── 統計錯誤數量
   └── 若有任何錯誤 → 返回 03-generation

3. 返回 03-generation：
   ├── 重設 current-process.json: current_process = "03-generation"
   ├── 重設 progress: 03-generation = "in_progress"
   ├── 讀取 error-log.json 找出缺少的畫面
   ├── 補充生成缺少的畫面
   └── 完成後重新走 04 → 05 → 06 流程
```

#### capture-screenshots.js Error Recovery 實作

```javascript
// 在 capture-screenshots.js 中加入
async function captureScreen(page, screenPath, outputPath) {
  try {
    const response = await page.goto(`file://${screenPath}`, {
      waitUntil: 'networkidle0',
      timeout: 10000
    });

    if (!response || response.status() === 404) {
      throw new Error(`Screen not found: ${screenPath}`);
    }

    await page.screenshot({ path: outputPath });
    return { success: true, path: screenPath };
  } catch (error) {
    console.error(`❌ 截圖失敗: ${screenPath}`);
    return {
      success: false,
      path: screenPath,
      error: error.message,
      recovery: 'return-to-03-generation'
    };
  }
}

// 執行完畢後檢查
async function processResults(results) {
  const failures = results.filter(r => !r.success);

  if (failures.length > 0) {
    console.log('');
    console.log('🚨 截圖失敗統計:');
    console.log(`   失敗數量: ${failures.length}`);
    console.log(`   缺少畫面: ${failures.map(f => f.path).join(', ')}`);
    console.log('');
    console.log('⚠️ 必須返回 03-generation 補充缺少的畫面！');

    // 寫入 error-log.json
    const errorLog = {
      timestamp: new Date().toISOString(),
      phase: '06-screenshot',
      failures: failures,
      recovery_action: 'return-to-03-generation',
      missing_screens: failures.map(f => f.path.match(/SCR-[^/]+/)?.[0]).filter(Boolean)
    };

    fs.writeFileSync(
      path.join(process.cwd(), 'workspace/screenshot-error-log.json'),
      JSON.stringify(errorLog, null, 2)
    );

    // 更新 current-process.json
    const processFile = path.join(process.cwd(), 'workspace/current-process.json');
    const processData = JSON.parse(fs.readFileSync(processFile, 'utf8'));
    processData.current_process = '03-generation';
    processData.progress['03-generation'] = 'in_progress';
    processData.progress['04-validation'] = 'pending';
    processData.progress['05-diagram'] = 'pending';
    processData.progress['06-screenshot'] = 'pending';
    processData.context.last_action = `Screenshot failed: ${failures.length} screens missing`;
    fs.writeFileSync(processFile, JSON.stringify(processData, null, 2));

    process.exit(1);
  }

  console.log('✅ 所有截圖完成');
}
```

#### 失敗原因與修復

| 失敗原因 | 修復方式 |
|----------|----------|
| 畫面檔案不存在 | 返回 03-generation 生成缺少的畫面 |
| 路徑錯誤 (typo) | 修正 Diagram/device-preview 中的路徑 |
| 畫面 ID 不一致 | 確認 SDD 與實際生成的畫面 ID 一致 |
| 模組資料夾錯誤 | 確認模組名稱對應 (auth → AUTH) |

### 07-feedback 回補步驟詳解

```
1. 更新 SDD 每個 SCR-* 區塊:
   ├── 加入 UI 原型參考 (不使用表格)
   ├── iPad 版本：![](images/ipad/SCR-*.png)
   └── iPhone 版本：![](images/iphone/SCR-*.png)

2. 更新 SRS:
   ├── 新增 Screen References 章節 (REQ → SCR 對照)
   ├── 新增 Inferred Requirements (從 UI Flow 推導)
   └── 更新 User Flows (Mermaid 流程圖)

3. 重新產生 DOCX:
   ├── node md-to-docx.js SDD-*.md → SDD.docx (含截圖)
   └── node md-to-docx.js SRS-*.md → SRS.docx
```

---

## Node Loading Protocol

```
Claude 收到 skill 啟用時：
1. 讀取此 SKILL.md (本檔案)
2. 從 skill args 取得專案路徑 (PROJECT_PATH)
3. 驗證進入條件:
   - 檢查 SDD 是否存在
   - 檢查 screen-prediction.json 是否存在且 completion_status = "completed"
   - 若未完成 → 拒絕進入，提示先完成 Phase 2
4. 讀取 {PROJECT_PATH}/04-ui-flow/workspace/current-process.json
   - 若檔案不存在 → 從 00-init 開始
   - 若 current_process 存在 → 恢復到該節點
5. 讀取 [SKILL_DIR]/process/{current}/README.md
6. 執行節點步驟
7. 完成後更新專案的 workspace/current-process.json
8. 進入下一節點
```

**路徑說明：**
- `[SKILL_DIR]` = `~/.claude/skills/app-uiux-designer.skill/` (skill 本身)
- `{PROJECT_PATH}` = 專案根目錄 (從 args 取得)
- workspace 在專案: `{PROJECT_PATH}/04-ui-flow/workspace/`

---

## 進入條件驗證 (Critical)

在開始 UI Flow 生成前，必須驗證：

```json
// 檢查 {PROJECT}/04-ui-flow/workspace/screen-prediction.json
{
  "completion_status": "completed",  // 必須為 completed
  "sdd_updated": true,               // 必須為 true
  "analysis": {
    "total_screens": 53              // 必須 > 0
  }
}
```

若驗證失敗，顯示訊息：
```
⚠️ 無法進入 UI Flow 階段
原因: 智慧預測尚未完成
請先完成 Phase 2 (app-requirements-skill):
- 執行智慧預測
- 補充所有預測畫面
- 確認 Appendix A 畫面清單
```

---

## Workspace Management

| 檔案 (專案內) | 說明 |
|---------------|------|
| `04-ui-flow/workspace/current-process.json` | 目前流程狀態 |
| `04-ui-flow/workspace/screen-prediction.json` | 智慧預測結果 (Phase 2 產生) |
| `04-ui-flow/workspace/state/` | Compaction 保存點 |

### 初始化 workspace

```bash
# 在專案的 04-ui-flow/ 下建立 workspace
mkdir -p {PROJECT}/04-ui-flow/workspace/{context,state}
```

---

## Blocking Checkpoints

| 節點 | 阻斷條件 |
|------|----------|
| 進入條件 | **智慧預測必須完成** (screen-prediction.json) |
| 00-init | 模板必須完整複製、變數必須替換 |
| 03-generation | **100% 畫面已生成**，無遺漏 |
| 04-validation | **100% Navigation + 0 空按鈕 + 0 alert** |
| **05-diagram** | **iframe src Path Validation 必須通過** (見驗證章節) |
| **06-screenshot** | **Pre-Validation 必須通過 + 若截圖失敗 → 返回 03-generation** |

---

## Device Specifications

| Device | Viewport | Body Style |
|--------|----------|------------|
| iPad Pro 11" | 1194 x 834 | `width: 1194px; height: 834px;` |
| iPhone 15/16 Pro | 393 x 852 | `width: 393px; height: 852px;` |

---

## Key Scripts

| 腳本 | 位置 | 說明 |
|------|------|------|
| init-project.sh | `process/00-init/templates/` | 專案初始化 |
| **post-generation-gate.js** | `templates/ui-flow/` | **🚨 產生後閘門 (BLOCKING - 自動執行所有驗證)** |
| validate-navigation.js | `templates/ui-flow/` | 導航驗證 |
| validate-iframe-src.js | `templates/ui-flow/` | iframe src 路徑驗證 |
| validate-consistency.js | `templates/ui-flow/` | 一致性驗證 |
| capture-screenshots.js | `templates/ui-flow/` | 截圖生成 |
| convert-to-iphone.sh | 專案內 `scripts/` | iPad→iPhone 轉換 |

### 🚨 post-generation-gate.js (MANDATORY)

> **產生 index.html / device-preview.html / Diagram 後必須執行！**

```bash
# 產生檔案後立即執行
node ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/post-generation-gate.js

# 或指定專案路徑
node ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/post-generation-gate.js /path/to/04-ui-flow
```

**自動執行的驗證:**
1. ✅ 必要檔案存在檢查 (index.html, device-preview.html, Diagrams)
2. ✅ `validate-iframe-src.js` - iPad/iPad mini/iPhone 路徑驗證
3. ✅ `validate-consistency.js` - 一致性驗證
4. ✅ `validate-navigation.js` - 導航驗證

**驗證結果:**
- `PASSED` → 可以進入下一階段
- `FAILED` → **禁止進入下一階段**，自動重設 progress

**自動行為:**
- 更新 `workspace/current-process.json` 的 validation_passed 狀態
- 若失敗，自動將 03-generation / 05-diagram 重設為 in_progress
- 產生 `workspace/validation-report.json` 詳細報告

---

### validate-iframe-src.js 使用方式

```bash
# 驗證當前目錄
node ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/validate-iframe-src.js

# 驗證指定專案
node ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/validate-iframe-src.js /path/to/project/04-ui-flow
```

**驗證內容:**
- `docs/ui-flow-diagram-ipad.html` 的所有 iframe src
- `docs/ui-flow-diagram-iphone.html` 的所有 iframe src
- `device-preview.html` 的 loadScreen() / iframe src / data-iphone 路徑
- 畫面數量一致性 (實際檔案 = Diagram = device-preview)

**Exit Code:**
- `0` - 驗證通過
- `1` - 驗證失敗 (BLOCKING)

---

## References (按需載入)

| 類別 | 檔案 |
|------|------|
| **文件標準** | `~/.claude/skills/app-requirements-skill/references/iec62304-document-standards.md` |
| **必要模組 HTML** | `templates/common-modules/{auth,profile,setting,common}/` |
| 平台 | `references/platforms/{ios-hig,material-design,wcag}.md` |
| 心理學 | `references/psychology/{gestalt,cognitive,emotional}.md` |
| 程式碼生成 | `references/code-gen/{react,angular,swiftui,compose}.md` |

### 必要模組 HTML 模板

在 **00-init** 階段，可從 `templates/common-modules/` 複製必要模組模板：

| 模組 | 模板數量 | 說明 |
|------|----------|------|
| auth | 3 個 | login, register, forgot |
| profile | 2 個 | view, edit |
| setting | 4 個 | main, account, privacy, about |
| common | 4 個 | loading, empty, error, no-network |

> 📁 模板包含 `{{VARIABLE}}` 佔位符，需根據專案設定替換

> ⚠️ **07-feedback 回補時必須遵循 `iec62304-document-standards.md`**
> - Mermaid 圖表使用 `flowchart TB` (直式)
> - 禁止 ASCII Art
> - SCR 區塊格式需包含 UI 原型表格
> - DOCX 轉換使用 `md-to-docx.js`

---

## Commands

| 指令 | 動作 |
|------|------|
| `進入節點 XX` | 讀取 `process/XX/README.md` |
| `下一步` | 自動判斷並進入下一節點 |
| `保存狀態` | 複製 current-process.json 到 state/ |
| `恢復狀態` | 從 state/ 讀取並恢復 |
| `顯示進度` | 讀取 current-process.json 的 progress |

---

## Screen ID Format

| 類型 | 格式 | 範例 |
|------|------|------|
| 畫面 | `SCR-{MODULE}-{NNN}-{name}` | SCR-AUTH-001-login |
| 需求 | `REQ-{MODULE}-{NNN}` | REQ-AUTH-001 |

**Module Codes:** AUTH, ONBOARD, HOME, VOCAB, TRAIN, REPORT, SETTING, PARENT, PROFILE, COMMON

---

## 輸出結果

完成 Phase 3 後，產生以下檔案供 Phase 4 使用：

```
📁 04-ui-flow/
├── 📁 ipad/
│   ├── SCR-AUTH-001-login.html
│   ├── SCR-AUTH-002-register.html
│   └── ... (所有畫面)
├── 📁 iphone/
│   └── ... (iPhone 版本)
├── 📁 screenshots/
│   ├── 📁 ipad/
│   │   └── *.png
│   └── 📁 iphone/
│       └── *.png
└── 📁 workspace/
    └── current-process.json (progress.06-screenshot = "completed")
```

---

## Architecture Benefits

1. **減少 Token 使用** - 只載入當前節點相關檔案
2. **Compaction 恢復** - 狀態保存在 workspace/
3. **清晰流程** - 每個節點有明確進入/退出條件
4. **整合簡化** - 智慧預測在 Phase 2 完成，本 Skill 專注 UI Flow

---

## 🚨 Anti-Forgetting Protocol (CRITICAL)

> **防止 Claude 在 Compaction 或長對話中遺忘驗證步驟的機制**

### 問題背景

Claude AI 有以下限制可能導致遺忘：
1. **Context Window 限制** - 對話過長會觸發 compaction（壓縮）
2. **Compaction 資訊損失** - 壓縮時 "how" 比 "what" 更容易遺失
3. **注意力分散** - 長對話中後面的指令優先級可能降低
4. **狀態不一致** - 記憶中的狀態與實際檔案狀態可能不同

### 核心原則

```
每個節點完成前：
1. 必須執行 exit-validation.sh
2. 必須更新 current-process.json 的 validation_state
3. 必須記錄到 validation-chain.json

Compaction 後恢復：
1. 執行 quick-health-check.sh
2. 讀取 validation-chain.json 確認已完成的驗證
3. 從最後一個有效狀態繼續
```

### Enhanced current-process.json 結構

```json
{
  "project_name": "WordPlay",
  "current_process": "04-validation",
  "last_updated": "2026-01-16T10:30:00Z",
  "progress": {
    "00-init": "completed",
    "03-generation": "completed",
    "04-validation": "in_progress",
    "05-diagram": "pending",
    "06-screenshot": "pending",
    "07-feedback": "pending",
    "08-finalize": "pending"
  },
  "validation_state": {
    "00-init": {
      "passed": true,
      "timestamp": "2026-01-16T09:00:00Z",
      "checks": ["templates_copied", "variables_replaced"]
    },
    "03-generation": {
      "passed": true,
      "timestamp": "2026-01-16T09:30:00Z",
      "checks": ["all_screens_generated", "onclick_coverage", "index_populated"]
    },
    "04-validation": {
      "passed": false,
      "timestamp": null,
      "pending_checks": ["navigation_100%", "zero_alerts", "consistency"]
    }
  },
  "recovery_hints": {
    "last_action": "Fixed onclick handlers in parent module",
    "pending_fixes": [],
    "files_modified": ["parent/SCR-PARENT-002.html", "parent/SCR-PARENT-003.html"]
  },
  "context": {
    "total_screens": 48,
    "modules": ["auth", "common", "dash", "parent", "profile", "progress", "setting", "train", "vocab"]
  }
}
```

### validation-chain.json 結構

```json
{
  "chain": [
    {
      "node": "00-init",
      "validation": "exit-validation",
      "result": "PASSED",
      "timestamp": "2026-01-16T09:00:00Z",
      "details": {
        "templates_copied": true,
        "variables_replaced": true
      }
    },
    {
      "node": "03-generation",
      "validation": "template-compliance-gate",
      "result": "PASSED",
      "timestamp": "2026-01-16T09:30:00Z",
      "details": {
        "ipad_screens": 48,
        "iphone_screens": 48,
        "onclick_coverage": "100%",
        "index_populated": true
      }
    }
  ],
  "last_valid_checkpoint": "03-generation"
}
```

### Exit Validation Scripts

每個節點都需要一個 `exit-validation.sh`：

| 節點 | 驗證腳本 | 驗證內容 |
|------|----------|----------|
| 00-init | `process/00-init/exit-validation.sh` | 模板完整、變數替換 |
| 03-generation | `process/03-generation/exit-validation.sh` | 畫面 100%、onclick、index.html |
| 04-validation | `process/04-validation/exit-validation.sh` | 導航 100%、0 alert |
| 05-diagram | `process/05-diagram/exit-validation.sh` | Diagram 完整、路徑正確 |
| 06-screenshot | `process/06-screenshot/exit-validation.sh` | 截圖存在 |
| 07-feedback | `process/07-feedback/exit-validation.sh` | SDD/SRS 回補完整 |

### Compaction Recovery Protocol

當 Claude 從 compaction 恢復時，**必須立即執行**：

```bash
# 1. 執行快速健康檢查
bash ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/quick-health-check.sh

# 2. 檢查輸出並恢復狀態
node ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/recover-state.js
```

### quick-health-check.sh 內容

```bash
#!/bin/bash
# Quick Health Check - Compaction 後立即執行
cd "${1:-.}"

echo "🏥 Quick Health Check..."
echo ""

# 1. 確認 workspace 存在
[ -d "workspace" ] || { echo "❌ workspace/ 不存在"; exit 1; }

# 2. 讀取當前狀態
if [ -f "workspace/current-process.json" ]; then
  CURRENT=$(cat workspace/current-process.json | grep -o '"current_process": "[^"]*"' | cut -d'"' -f4)
  echo "📍 當前節點: $CURRENT"
else
  echo "⚠️ current-process.json 不存在"
  CURRENT="unknown"
fi

# 3. 快速計數
IPAD_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*" 2>/dev/null | wc -l | tr -d ' ')
IPHONE_COUNT=$(find ./iphone -name "SCR-*.html" 2>/dev/null | wc -l | tr -d ' ')
echo "📊 畫面數: iPad=$IPAD_COUNT, iPhone=$IPHONE_COUNT"

# 4. 檢查關鍵檔案
echo ""
echo "📁 關鍵檔案檢查:"
[ -f "index.html" ] && echo "  ✅ index.html" || echo "  ❌ index.html"
[ -f "device-preview.html" ] && echo "  ✅ device-preview.html" || echo "  ❌ device-preview.html"
[ -f "docs/ui-flow-diagram-ipad.html" ] && echo "  ✅ ui-flow-diagram-ipad.html" || echo "  ❌ ui-flow-diagram-ipad.html"
[ -f "docs/ui-flow-diagram-iphone.html" ] && echo "  ✅ ui-flow-diagram-iphone.html" || echo "  ❌ ui-flow-diagram-iphone.html"

# 5. 讀取 validation chain
echo ""
if [ -f "workspace/validation-chain.json" ]; then
  echo "📋 已完成的驗證:"
  cat workspace/validation-chain.json | grep -o '"node": "[^"]*"' | cut -d'"' -f4 | while read node; do
    echo "  ✅ $node"
  done
else
  echo "⚠️ validation-chain.json 不存在，需要重新驗證"
fi

echo ""
echo "🏥 Health Check 完成"
echo "📍 請從節點 '$CURRENT' 繼續"
```

### 強制執行規則

| 情境 | 必須執行 |
|------|----------|
| 節點完成時 | `exit-validation.sh` + 更新 `validation-chain.json` |
| Compaction 後恢復 | `quick-health-check.sh` + `recover-state.js` |
| 用戶詢問進度 | 讀取 `current-process.json` + `validation-chain.json` |
| 開始新節點 | 確認前一節點的 validation_state.passed = true |

### Claude 行為要求

1. **每次對話開始時**：檢查是否需要執行 health check
2. **完成任何修改後**：更新 recovery_hints.last_action
3. **完成節點前**：必須執行 exit-validation 並記錄
4. **發現不一致時**：優先相信檔案狀態而非記憶
