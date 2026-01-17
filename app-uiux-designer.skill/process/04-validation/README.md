# Process 04: 導航驗證 (Navigation Validation)

> **⚠️ Claude 行為要求：進入此節點後，必須自動執行所有驗證步驟，無需用戶提醒！**

---

## Claude 自動執行規則 (MANDATORY)

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️ 進入 04-validation 後，Claude 必須自動執行：                  │
├─────────────────────────────────────────────────────────────────┤
│  1. Step 0.5: 預驗證 (device-preview + index.html 同步)          │
│  2. Step 1-5: 導航驗證 (validate-navigation.js)                  │
│  3. Step 6: 一致性驗證 (validate-consistency.js)                 │
│  4. Step 7: 完整驗證 (validate-all.js)                           │
│  5. 自動修復任何失敗項目                                          │
│  6. 重新驗證直到 100% 通過                                        │
└─────────────────────────────────────────────────────────────────┘

❌ 禁止行為：
   - 跳過任何驗證步驟
   - 等待用戶詢問才執行驗證
   - 驗證失敗後不修復就繼續

✅ 正確行為：
   - 自動執行所有驗證
   - 發現問題立即修復
   - 修復後自動重新驗證
   - 100% 通過後才標記完成
```

---

## 設計理念

> **app-uiux-designer.skill 的目標是 100% 完成 UI/UX，不是部分實作！**

### 完整流程

```
SRS/SDD 輸入 → 智慧預測所有畫面 → 100% UI/UX 生成 → 100% Navigation 驗證
```

### 驗證標準 (全部必須達成)

| 驗證項目 | 要求 | 說明 |
|----------|------|------|
| **UI/UX 覆蓋率** | 100% | 所有需要的畫面都已生成 |
| **導航覆蓋率** | 100% | 所有可點擊元素都有有效導航 |
| **空按鈕** | 0 個 | 禁止 `onclick=""` 或無 onclick |
| **Alert 佔位符** | 0 個 | 禁止 `onclick="alert('...')"` |

### 禁止的實作方式

| 禁止項目 | 原因 |
|----------|------|
| ❌ `onclick=""` | 空處理，無實際功能 |
| ❌ `onclick="alert('功能說明')"` | 佔位符，非真實導航 |
| ❌ `href="#"` | 懸空連結 |
| ❌ 部分畫面實作 | 必須 100% 完成所有畫面 |

### 正確的實作方式

| 元素類型 | 正確處理 |
|----------|----------|
| 導航按鈕 | `onclick="location.href='SCR-*.html'"` |
| 返回按鈕 | `onclick="history.back()"` 或指向具體頁面 |
| 關閉按鈕 | `onclick="location.href='來源頁.html'"` |
| 表單提交 | `onclick="location.href='結果頁.html'"` |
| Modal 觸發 | `onclick="showModal('modal-id')"` + Modal 內有關閉導航 |

---

## 進入條件

- [ ] 03-generation 已完成（所有畫面 HTML 已產生）
- [ ] iPad 和 iPhone 畫面都存在

## 執行步驟

### Step 0.5: 預驗證 - device-preview.html 和 index.html 同步 (MANDATORY)

**⚠️ 在執行 validate-navigation.js 前，必須先驗證同步狀態！**

#### 預驗證腳本

```bash
#!/bin/bash
cd 04-ui-flow

echo "======================================"
echo "  UI Flow 預驗證 - 同步狀態檢查"
echo "======================================"

ERRORS=0

# 1. 檢查 device-preview.html
echo ""
echo "📱 device-preview.html 檢查"
echo "----------------------------------------"

# 1.1 iframe src 存在性
IFRAME_SRCS=$(grep -o 'src="[^"]*SCR-[^"]*\.html"' device-preview.html | sed 's/src="//;s/"//g' | sort -u)
for src in $IFRAME_SRCS; do
  if [ -f "$src" ]; then
    echo "✅ iframe src 存在: $src"
  else
    echo "❌ iframe src 不存在: $src"
    ERRORS=$((ERRORS + 1))
  fi
done

# 1.2 側邊欄畫面數量
SIDEBAR_COUNT=$(grep -c 'class="screen-item"' device-preview.html || echo "0")
IPAD_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" 2>/dev/null | wc -l | tr -d ' ')
echo ""
echo "側邊欄畫面數: $SIDEBAR_COUNT"
echo "實際 iPad 畫面數: $IPAD_COUNT"

if [ "$SIDEBAR_COUNT" -eq "$IPAD_COUNT" ]; then
  echo "✅ 側邊欄同步完成"
else
  echo "❌ 側邊欄未同步 (差 $((IPAD_COUNT - SIDEBAR_COUNT)) 個畫面)"
  ERRORS=$((ERRORS + 1))
fi

# 1.3 onclick 目標存在性
echo ""
echo "驗證 onclick 目標..."
ONCLICK_TARGETS=$(grep -o "loadScreen('[^']*'" device-preview.html | sed "s/loadScreen('//;s/'//g")
MISSING_TARGETS=0
for target in $ONCLICK_TARGETS; do
  if [ ! -f "$target" ]; then
    echo "❌ 目標不存在: $target"
    MISSING_TARGETS=$((MISSING_TARGETS + 1))
  fi
done
[ "$MISSING_TARGETS" -eq 0 ] && echo "✅ 所有 onclick 目標存在" || ERRORS=$((ERRORS + MISSING_TARGETS))

# 2. 檢查 index.html
echo ""
echo "📊 index.html 檢查"
echo "----------------------------------------"

# 2.1 覆蓋率
COVERAGE=$(grep -oE '[0-9]+%' index.html | head -1 | tr -d '%')
echo "覆蓋率: ${COVERAGE}%"
if [ "${COVERAGE:-0}" -gt 0 ]; then
  echo "✅ 覆蓋率 > 0%"
else
  echo "❌ 覆蓋率為 0% (需要更新 index.html)"
  ERRORS=$((ERRORS + 1))
fi

# 2.2 模組卡片畫面數
INDEX_SCREEN_COUNT=$(grep -c 'status-done' index.html || echo "0")
echo "index.html 模組卡片畫面數: $INDEX_SCREEN_COUNT"
if [ "$INDEX_SCREEN_COUNT" -eq "$IPAD_COUNT" ]; then
  echo "✅ 模組卡片同步完成"
else
  echo "❌ 模組卡片未同步"
  ERRORS=$((ERRORS + 1))
fi

# 3. 結果
echo ""
echo "======================================"
if [ "$ERRORS" -eq 0 ]; then
  echo "✅ 預驗證通過 - 可以執行 validate-navigation.js"
  exit 0
else
  echo "❌ 預驗證失敗 - 發現 $ERRORS 個問題"
  echo ""
  echo "請返回 03-generation Step 5.6 修復同步問題"
  exit 1
fi
```

#### 阻斷條件

| 檢查項 | 條件 | 後果 |
|--------|------|------|
| iframe src 存在 | 所有 src 指向的檔案必須存在 | **禁止繼續** |
| 側邊欄同步 | 側邊欄畫面數 = 實際 iPad 畫面數 | **禁止繼續** |
| onclick 目標存在 | 所有 loadScreen 目標必須存在 | **禁止繼續** |
| 覆蓋率 > 0% | index.html 覆蓋率不能為 0% | **禁止繼續** |
| 模組卡片同步 | index.html 模組卡片數 = 實際畫面數 | **禁止繼續** |

**⚠️ 任一檢查失敗，必須返回 03-generation Step 5.6 修復！**

---

### Step 1: 執行驗證腳本

```bash
cd 04-ui-flow
node ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/validate-navigation.js
```

### Step 2: 查看驗證結果

**成功輸出 (100% 覆蓋):**
```
📊 Summary
Total Screens:    57
Total Elements:   203
Valid Elements:   203
Invalid Elements: 0
Coverage:         100.0%

✅ Navigation validation PASSED
```

**失敗輸出 (< 100%):**
```
⚠️ auth/SCR-AUTH-001-login.html
   Elements: 5, Valid: 4, Issues: 1
   ❌ Line 58: Button has no onclick handler
```

### Step 3: 修復問題

執行 `--fix` 取得修復建議：

```bash
node validate-navigation.js --fix
```

**常見問題與修復:**

| 問題 | 修復方式 |
|------|----------|
| Button has no onclick | 加上 `onclick="location.href='...'` 或 `onclick="alert('...')"` |
| Close icon (X) has no onclick | 加上返回導航 `onclick="location.href='上一頁.html'"` |
| type="submit" without onclick | 改為 `type="button"` 並加 onclick |
| href="#" | 改為實際 URL 或移除 href 改用 onclick |

### Step 4: 重複驗證直到 100%

```bash
# 修復後重新驗證
node validate-navigation.js

# 必須達到 100% 才能進入下一節點
```

### Step 5: 輸出驗證報告

```bash
node validate-navigation.js --report > validation-report.md
```

### Step 6: 執行一致性驗證 (Consistency Validation)

驗證產出的 UI Flow 是否符合 reference-example 標準規格。

```bash
cd 04-ui-flow
node ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/validate-consistency.js
```

**驗證項目:**

| 類別 | 檢查項目 |
|------|----------|
| 檔案結構 | index.html, device-preview.html, docs/, shared/ |
| iPhone 規格 | 框架 120x260px, scale(0.305), notch 40x6px |
| iPad 規格 | 框架 200x140px, scale(0.168), camera 6x6px |
| 必要元素 | flow-container, screen-card, device-frame, device-switcher |
| 功能行為 | openScreen() → device-preview.html, URL 參數 |
| CSS 一致性 | 模組顏色 (9 modules), badge-{module} classes |

**成功輸出:**
```
✅ UI FLOW CONSISTENCY VALIDATED
   Output matches reference-example standards
```

**失敗時:** 根據錯誤訊息修復後重新執行。

### Step 7: 執行完整驗證 (Optional)

一次執行所有驗證腳本:

```bash
node ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/validate-all.js
```

---

## 退出條件 (BLOCKING - 必須 100%)

- [ ] 導航覆蓋率 = 100%
- [ ] 無 Invalid Elements
- [ ] 導航驗證報告已產生
- [ ] 一致性驗證通過 (PASSED)

## 阻斷條件

| 條件 | 後果 |
|------|------|
| 導航覆蓋率 < 100% | **禁止進入 05-diagram** |
| 存在 CRITICAL 問題 | 必須立即修復 |
| 一致性驗證失敗 | **禁止進入 05-diagram** |

---

## 驗證規則詳細

### 偵測的可點擊元素

| 類型 | 偵測方式 |
|------|----------|
| Button | `<button>` 標籤 |
| Link | `<a href>` 標籤 |
| Clickable div | 含 `onclick` 屬性 |
| Close icon (X) | SVG path 含 `M6 18L18 6` |
| Settings row | 含 chevron `>` 圖示 |
| Tab bar item | `.tab-item`, `.nav-item` class |

### 有效 onclick 模式

```javascript
// ✅ 有效
onclick="location.href='SCR-*.html'"
onclick="alert('說明文字')"
onclick="window.open('...')"
onclick="history.back()"

// ❌ 無效
onclick=""
onclick="javascript:void(0)"
// 無 onclick 屬性
```

---

## 相關檔案

| 檔案 | 說明 |
|------|------|
| `templates/ui-flow/validate-navigation.js` | 導航驗證腳本 |
| `templates/ui-flow/validate-consistency.js` | 一致性驗證腳本 |
| `templates/ui-flow/validate-all.js` | 整合驗證入口 |
| `templates/ui-flow/reference-example/standards.json` | 標準規格定義 |
| `coverage-rules.md` | 覆蓋規則詳細 |
| `fix-suggestions.md` | 修復建議 |

## 下一節點

→ `process/05-diagram/README.md` (流程圖生成)

**注意**: 只有在 100% 覆蓋時才能進入下一節點！

---

## 常見 False Positive

驗證腳本可能誤報以下情況：

| 情況 | 處理方式 |
|------|----------|
| Close button 的 onclick 在父元素 | 確認父元素有 onclick 即可 |
| 動態生成的 onclick | 檢查 JavaScript 是否正確綁定 |
| CSS hover 樣式無 onclick | 若非可點擊，移除 hover 樣式 |

---

## ⚠️ Claude 完成 04-validation 的行為清單

```
進入 04-validation 後，Claude 自動執行：

□ 1. 執行預驗證 (Step 0.5)
     └─ 失敗? → 返回 03-generation 修復

□ 2. 執行 validate-navigation.js (Step 1-4)
     └─ 覆蓋率 < 100%? → 自動修復 → 重新驗證

□ 3. 產生驗證報告 (Step 5)

□ 4. 執行 validate-consistency.js (Step 6)
     └─ 失敗? → 自動修復 → 重新驗證

□ 5. 執行 validate-all.js (Step 7)
     └─ 任何失敗? → 自動修復 → 重新驗證

□ 6. 全部通過後：
     └─ 更新 current-process.json
     └─ progress.04-validation = "completed"
     └─ 自動進入 06-screenshot
```

### 驗證通過的 current-process.json 範例

```json
{
  "current_process": "completed",
  "progress": {
    "03-generation": "completed",
    "04-validation": "completed"
  },
  "validation_results": {
    "empty_onclick": 0,
    "alert_placeholders": 0,
    "navigation_coverage": "100%",
    "consistency_check": "PASSED",
    "total_screens": 49,
    "status": "PASSED"
  },
  "context": {
    "last_action": "04-validation completed: 100% navigation + consistency PASSED"
  }
}
```
