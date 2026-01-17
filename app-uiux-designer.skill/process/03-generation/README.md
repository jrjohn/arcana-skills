# Process 03: HTML 生成 (Screen Generation)

## 進入條件

- [ ] 00-init 已完成（模板已複製、變數已替換）
- [ ] 02-planning 已完成（SCR-* 清單已建立）
- [ ] SDD 中有 Button Navigation 表格

## 執行步驟

### Step 1: 載入畫面清單

從 SDD 或 02-planning 產出物取得 SCR-* 清單：

```
SCR-AUTH-001-login
SCR-AUTH-002-register
SCR-HOME-001-student
...
```

---

### Step 1.5: 模板確認 (MANDATORY - 必須執行)

**⚠️ 重要：每個畫面生成前必須先確認模板存在**

#### 1.5.1 模板搜尋順序 (響應式優先)

對於每個 SCR-{MODULE}-{NNN}-{name}，依以下順序搜尋模板：

| 優先級 | 模板路徑 | 說明 |
|--------|---------|------|
| **1** | **`templates/ui-flow/screen-template-responsive.html`** | **響應式通用模板（優先）** |
| 2 | `templates/screen-types/{module}/{name}-responsive.html` | 專用響應式模板 |
| 3 | `templates/screen-types/{module}/{name}.html` | 專用模板（通用裝置）|
| 4 | `templates/screen-types/common/{screen-type}.html` | 通用類型模板 |
| 5 | `templates/ui-flow/screen-template-ipad.html` | 僅 iPad 基礎模板（備案）|

**⚠️ 響應式設計強制要求**：所有畫面必須使用響應式佈局，同一份 HTML 同時支援 iPad 和 iPhone。

**範例**：生成 `SCR-AUTH-001-login.html` 時：
```bash
# 搜尋順序
1. templates/ui-flow/screen-template-responsive.html  ← 優先使用響應式
2. templates/screen-types/auth/login-responsive.html
3. templates/screen-types/auth/login.html
4. templates/ui-flow/screen-template-ipad.html        ← 最後備案
```

#### 1.5.2 模板確認指令

```bash
# 檢查專用模板是否存在
SKILL_DIR=~/.claude/skills/app-uiux-designer.skill
ls -la $SKILL_DIR/templates/screen-types/auth/login*.html 2>/dev/null

# 若不存在，使用通用模板
ls -la $SKILL_DIR/templates/ui-flow/screen-template-ipad.html
```

#### 1.5.3 模板變數替換清單

| 變數 | 來源 | 範例 |
|------|------|------|
| `{{PROJECT_NAME}}` | 專案設定 | VocabKids 小小單字王 |
| `{{PROJECT_ID}}` | 專案設定 | vocabkids |
| `{{SCREEN_TITLE}}` | SDD SCR-* 標題 | 登入畫面 |
| `{{SCREEN_ID}}` | SCR ID | SCR-AUTH-001 |
| `{{SCREEN_NAME}}` | SCR 名稱 | login |
| `{{REQUIREMENTS}}` | SDD 相關需求 | REQ-AUTH-001, REQ-AUTH-002 |
| `{{TARGET_*}}` | SDD Button Navigation | SCR-AUTH-004-role.html |

#### 1.5.4 必須加入的 Metadata

每個生成的 HTML 檔案末尾必須包含：

```html
<!--
@template-source: templates/screen-types/auth/login-ipad.html
@requirements: REQ-AUTH-001, REQ-AUTH-002
@screen-id: SCR-AUTH-001
@screen-name: Login Screen (登入畫面)
@description: 使用者登入畫面
@generated: 2026-01-13
-->
```

---

### Step 2: 為每個畫面生成響應式 HTML

**檔案位置**: `04-ui-flow/{module}/SCR-{MODULE}-{NNN}-{name}.html`

**生成流程 (MANDATORY)**：
```
1. 確認模板存在 (Step 1.5)
2. 讀取響應式模板內容
3. 替換所有 {{VARIABLE}}
4. 根據 SDD Button Navigation 設定 onclick 目標
5. 使用響應式 Tailwind 類別 (見下方指南)
6. 加入 @template-source metadata
7. 寫入檔案
```

**必要結構 (響應式)**:
```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>專案名稱 - 畫面名稱</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="../shared/project-theme.css">
  <script>
    tailwind.config = {
      theme: {
        extend: {
          screens: {
            'phone': {'max': '500px'},   // iPhone: 393px
            'tablet': {'min': '501px'},  // iPad: 1194px
          }
        }
      }
    }
  </script>
  <style>
    :root {
      --ipad-width: 1194px;
      --ipad-height: 834px;
      --iphone-width: 393px;
      --iphone-height: 852px;
    }
    body {
      width: var(--ipad-width);
      height: var(--ipad-height);
      overflow: hidden;
      margin: 0;
      padding: 0;
    }
    @media (max-width: 500px) {
      body {
        width: var(--iphone-width);
        height: var(--iphone-height);
      }
    }
  </style>
</head>
<body>
  <!-- 使用響應式類別的畫面內容 -->
  <div class="p-4 tablet:p-6">
    <h1 class="text-lg tablet:text-2xl">標題</h1>
    <div class="flex flex-col tablet:flex-row gap-3 tablet:gap-6">
      <!-- 內容 -->
    </div>
  </div>

  <script src="../shared/notify-parent.js"></script>
</body>
</html>

<!--
@template-source: {使用的模板路徑}
@requirements: {相關需求}
@screen-id: {SCR ID}
@screen-name: {畫面名稱}
-->
```

#### 2.1 響應式設計指南 (MANDATORY)

**詳細參考**: `references/responsive-design-guide.md`

| 元素 | iPhone | iPad |
|------|--------|------|
| 標題 | `text-lg` | `tablet:text-2xl` |
| 內文 | `text-sm` | `tablet:text-base` |
| 間距 | `p-4` | `tablet:p-6` |
| 間隙 | `gap-3` | `tablet:gap-6` |
| 佈局 | `flex-col` | `tablet:flex-row` |
| 欄數 | `grid-cols-1` | `tablet:grid-cols-2` |

**常見響應式模式**:
```html
<!-- 水平排列(iPad) vs 垂直排列(iPhone) -->
<div class="flex flex-col tablet:flex-row gap-4 tablet:gap-8">
  <div class="tablet:w-[300px] p-4 tablet:p-8">Card 1</div>
  <div class="tablet:w-[300px] p-4 tablet:p-8">Card 2</div>
</div>

<!-- 網格佈局 -->
<div class="grid grid-cols-1 tablet:grid-cols-2 gap-3 tablet:gap-4">
  <div>Item 1</div>
  <div>Item 2</div>
</div>

<!-- 僅 iPad 顯示 -->
<div class="hidden tablet:block">iPad sidebar</div>

<!-- 僅 iPhone 顯示 -->
<div class="tablet:hidden">iPhone bottom sheet</div>
```

### Step 3: onclick 規則 (MANDATORY - 100% 實際導航)

> ⚠️ **所有按鈕都必須有實際導航目標，禁止使用 alert 佔位符！**
>
> 🚨 **生成時強制檢查**：每寫一個 `<button>` 標籤時，必須同時寫入 `onclick` 屬性！

#### 3.1 onclick 生成順序 (MANDATORY)

**生成 `<button>` 時必須依此順序處理**：

```
1. 查詢 SDD Button Navigation → 有目標 → 使用 SDD 指定的目標
                             ↓ 無目標
2. 根據按鈕文字/圖示智慧預測 → 可預測 → 使用預測目標
                             ↓ 無法預測
3. 使用合理的預設目標 → 查看類按鈕導向相關詳情頁
                     → 操作類按鈕導向來源頁
```

**⚠️ 絕對禁止**：產生沒有 onclick 的 `<button>` 標籤！

#### 3.2 按鈕類型與 onclick 對照表

| 元素類型 | 正確處理 |
|----------|----------|
| 導航按鈕 | `onclick="location.href='SCR-*.html'"` |
| 返回按鈕 | `onclick="history.back()"` 或 `onclick="location.href='來源頁.html'"` |
| 關閉按鈕 (X) | `onclick="location.href='來源頁.html'"` |
| 表單提交 | `onclick="location.href='結果頁.html'"` |
| Modal 觸發 | `onclick="showModal('id')"` + Modal 內有關閉導航 |
| **查看類按鈕** | `onclick="location.href='相關詳情頁.html'"` ⚠️ 新增 |
| **操作類按鈕** | `onclick="location.href='來源頁或確認頁.html'"` ⚠️ 新增 |
| **功能入口按鈕** | `onclick="location.href='功能主頁.html'"` ⚠️ 新增 |

#### 3.3 常見按鈕文字與預設目標 (智慧預測)

| 按鈕文字 | 預設導航目標 | 備註 |
|----------|-------------|------|
| 查看獎勵 | `../engage/SCR-ENGAGE-004-badges.html` | 成就/徽章頁 |
| 查看詳情 | 對應的 detail 頁面 | |
| 查看更多 | 對應的列表頁面 | |
| 查看報表 | `../progress/SCR-PROGRESS-001-overview.html` | 或 parent/report |
| 開始學習 | `../train/SCR-TRAIN-001-select-vocab.html` | |
| 開始測驗 | `../train/SCR-TRAIN-002-mode-select.html` | |
| 儲存/保存 | 返回列表頁或 `history.back()` | |
| 取消 | `history.back()` | |
| 確認/確定 | 下一步驟頁面或結果頁 | |
| 分享 | `../social/SCR-SOCIAL-001-share.html` | |
| 設定 | `../setting/SCR-SETTING-001-main.html` | |
| 登出 | `../auth/SCR-AUTH-001-welcome.html` | |

#### 3.4 禁止事項 (BLOCKING)

- ❌ `onclick="alert('...')"` - 禁止 alert 佔位符
- ❌ `href="#"` - 禁止懸空連結
- ❌ `onclick=""` - 禁止空處理
- ❌ **按鈕無任何 onclick - 禁止無處理按鈕** 🚨
- ❌ `type="submit"` 無 onclick
- ❌ 可點擊樣式 (hover:, active:) 但無 onclick

#### 3.5 智慧預測導航目標

若 SDD 未明確指定目標，根據命名約定預測：
- `btn_login` → 登入成功後導向 `SCR-DASH-001` 或 `SCR-HOME-001`
- `btn_back` → `history.back()` 或上一個畫面
- `btn_save` → 返回列表頁或詳情頁
- `btn_cancel` → 返回上一頁
- `btn_close` → 返回觸發 Modal 的頁面
- `btn_view_*` → 對應的詳情或列表頁面 ⚠️ 新增
- `btn_reward` / `btn_achievement` → `../engage/SCR-ENGAGE-004-badges.html` ⚠️ 新增

#### 3.6 生成後自檢 (每個畫面完成後)

```bash
# 檢查是否有 button 沒有 onclick
grep -n '<button' SCR-*.html | grep -v 'onclick='
# 若有輸出，必須立即修復！
```

### Step 4: 生成 iPhone 版本 (MANDATORY - 必須執行)

**⚠️ 重要：iPhone 版本必須與 iPad 版本同步產生，否則 UI Flow 覆蓋率將顯示不正確！**

**響應式設計說明**：由於 iPad 畫面已使用響應式佈局，iPhone 版本僅需調整 viewport 和 CSS 變數。
內容佈局會透過 CSS media query 和 Tailwind `tablet:` 前綴自動適應。

#### 4.1 複製轉換腳本到專案

```bash
# 從 skill 模板複製腳本
SKILL_DIR=~/.claude/skills/app-uiux-designer.skill
cp "$SKILL_DIR/templates/ui-flow/scripts/convert-to-iphone.sh" ./scripts/
chmod +x ./scripts/convert-to-iphone.sh
```

#### 4.2 執行轉換

```bash
# 在 04-ui-flow 目錄下執行
cd 04-ui-flow
./scripts/convert-to-iphone.sh
```

#### 4.3 轉換規則 (響應式模板)

| iPad 設定 | iPhone 設定 |
|-----------|-------------|
| `width=device-width` | 保持不變 |
| `--ipad-width: 1194px` | `--iphone-width: 393px` |
| `--ipad-height: 834px` | `--iphone-height: 852px` |
| `var(--ipad-width)` | `var(--iphone-width)` |
| `var(--ipad-height)` | `var(--iphone-height)` |
| `../auth/SCR-*.html` | `../iphone/SCR-*.html` |

**傳統模板相容**（若使用非響應式模板）:

| iPad 設定 | iPhone 設定 |
|-----------|-------------|
| `width=1194, height=834` | `width=393, height=852` |
| `width: 1194px` | `width: 393px` |
| `height: 834px` | `height: 852px` |

#### 4.4 驗證轉換結果

```bash
# 確認 iPhone 檔案數量與 iPad 相同
IPAD_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" | wc -l)
IPHONE_COUNT=$(find iphone -name "SCR-*.html" | wc -l)
echo "iPad: $IPAD_COUNT, iPhone: $IPHONE_COUNT"

# 兩者必須相等
[ "$IPAD_COUNT" -eq "$IPHONE_COUNT" ] && echo "✅ 通過" || echo "❌ 失敗"

# 驗證響應式佈局 (檢查 tablet: 類別)
RESPONSIVE_COUNT=$(grep -rl 'tablet:' . --include="SCR-*.html" -not -path "./iphone/*" | wc -l | tr -d ' ')
echo "響應式畫面: $RESPONSIVE_COUNT"
```

**阻斷規則**：若 iPhone 檔案數量為 0 或與 iPad 不一致，**禁止進入下一步**。

### Step 5: 生成 index.html (從模板) - MANDATORY

**⚠️ 必須使用模板並替換所有變數**：

#### 5.1 複製模板

```bash
SKILL_DIR=~/.claude/skills/app-uiux-designer.skill
cp "$SKILL_DIR/templates/ui-flow/index.html" ./index.html
cp "$SKILL_DIR/templates/ui-flow/scripts/update-index-counts.sh" ./scripts/
chmod +x ./scripts/update-index-counts.sh
```

#### 5.2 變數替換清單 (MANDATORY)

| 變數 | 說明 | 範例 |
|------|------|------|
| `{{PROJECT_NAME}}` | 專案名稱 | 單字小達人 |
| `{{PROJECT_ID}}` | 專案 ID | vocabkids |
| `{{PROJECT_ICON}}` | 專案圖示 | 📚 |
| `{{PROJECT_DESCRIPTION}}` | 專案描述 | 國小英文單字學習 App |
| `{{COVERAGE}}` | 覆蓋率百分比 | 100 |
| `{{IPAD_SCREENS}}` | iPad 畫面數 | 40 |
| `{{IPHONE_SCREENS}}` | iPhone 畫面數 | 40 |
| `{{TOTAL_SCREENS}}` | 總畫面數 | 40 |
| `{{AUTH_COUNT}}` | AUTH 模組畫面數 | 6 |
| `{{ONBOARD_COUNT}}` | ONBOARD 模組畫面數 | 0 |
| `{{DASH_COUNT}}` | DASH 模組畫面數 | 1 |
| `{{VOCAB_COUNT}}` | VOCAB 模組畫面數 | 9 |
| `{{TRAIN_COUNT}}` | TRAIN 模組畫面數 | 7 |
| `{{PROGRESS_COUNT}}` | PROGRESS 模組畫面數 | 2 |
| `{{REPORT_COUNT}}` | REPORT 模組畫面數 | 0 |
| `{{SETTING_COUNT}}` | SETTING 模組畫面數 | 10 |
| `{{FEATURE_COUNT}}` | FEATURE 模組畫面數 | 0 |
| `{{PARENT_COUNT}}` | PARENT 模組畫面數 | 5 |
| `{{HOME_COUNT}}` | HOME 模組畫面數 | 0 |

#### 5.3 自動化替換（推薦）

```bash
# 執行自動化腳本
./scripts/update-index-counts.sh
```

#### 5.4 手動替換（備用）

```bash
# 計算並替換各項變數
IPAD_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" | wc -l | tr -d ' ')
IPHONE_COUNT=$(find iphone -name "SCR-*.html" | wc -l | tr -d ' ')
AUTH_COUNT=$(find . -name "SCR-AUTH-*.html" -not -path "./iphone/*" | wc -l | tr -d ' ')
# ... 其他模組類推

sed -i '' "s/{{IPAD_SCREENS}}/$IPAD_COUNT/g" index.html
sed -i '' "s/{{IPHONE_SCREENS}}/$IPHONE_COUNT/g" index.html
sed -i '' "s/{{AUTH_COUNT}}/$AUTH_COUNT/g" index.html
# ... 其他變數類推
```

#### 5.5 驗證變數替換完成

```bash
# 檢查是否還有未替換的變數
grep -o '{{[^}]*}}' index.html 2>/dev/null
# 若有輸出，表示還有變數未替換，必須全部替換完成！
```

**阻斷規則**：若 `grep '{{.*}}' index.html` 有任何輸出，**禁止進入下一步**。

**index.html 必要功能檢查**：
- [ ] Tailwind CSS (`<script src="https://cdn.tailwindcss.com">`)
- [ ] UI Flow Diagram iframe 內嵌
- [ ] iPad/iPhone 切換按鈕
- [ ] `openScreen(ipadPath, iphonePath)` 函數
- [ ] device-preview.html 整合
- [ ] 模組圖例側邊欄
- [ ] Footer 標註 `Template: app-uiux-designer.skill/templates/ui-flow`
- [ ] **所有 `{{變數}}` 已被替換** ⚠️

### Step 5.6: 同步 device-preview.html 和 index.html (MANDATORY - 不可跳過)

**⚠️ 阻斷規則**: 未完成此步驟，禁止進入 04-validation！

每產生畫面後，必須同步更新以下兩個檔案：

#### 5.6.1 同步 device-preview.html 側邊欄

**檔案位置**: `04-ui-flow/device-preview.html`

**更新區間**: `<!-- SCREEN_LIST_START -->` 至 `<!-- SCREEN_LIST_END -->`

**步驟**:
1. 掃描所有已生成的 SCR-*.html 檔案
2. 按模組分類 (AUTH, DASH, VOCAB, TRAIN, SETTING, etc.)
3. 計算每個模組的畫面數量
4. 填入側邊欄 HTML 結構

**每個畫面項目格式**:
```html
<div class="screen-item px-3 py-2.5 rounded-lg cursor-pointer"
     onclick="loadScreen('{module}/SCR-{MODULE}-{NNN}-{name}.html', this)">
  <span class="text-sm text-gray-700">SCR-{MODULE}-{NNN} {畫面名稱}</span>
</div>
```

**每個模組區塊格式**:
```html
<!-- {MODULE} Module -->
<div class="mb-5">
  <p class="text-xs font-semibold text-gray-500 mb-2 flex items-center gap-2">
    <span class="w-2 h-2 rounded-full badge-{module}"></span>
    {MODULE} ({COUNT})
  </p>
  <div class="space-y-1">
    <!-- 畫面項目 -->
  </div>
</div>
```

**同時更新**:
- iframe 預設 src: 必須指向第一個存在的畫面 (如 `auth/SCR-AUTH-001-login.html`)
- currentScreen 變數: 與 iframe src 一致
- SCREENS 總數: 更新 sidebar header 的畫面數量

#### 5.6.2 同步 index.html 統計

**檔案位置**: `04-ui-flow/index.html`

**需更新項目**:

| 項目 | 位置 | 計算方式 |
|------|------|----------|
| UI/UX 覆蓋率 | header | `(已產生畫面數 / SDD 規劃畫面數) * 100` |
| iPad 畫面數 | header | `find . -name "SCR-*.html" -not -path "./iphone/*" \| wc -l` |
| iPhone 畫面數 | header | `find iphone -name "SCR-*.html" \| wc -l` |
| 模組數 | status bar | 實際使用的模組數量 |
| 各模組圖例 | sidebar | 各模組名稱和畫面數 |
| 模組卡片 | main | 每個模組的畫面清單 |

**模組卡片畫面項目格式**:
```html
<div onclick="openScreen('{module}/SCR-{MODULE}-{NNN}-{name}.html', 'iphone/SCR-{MODULE}-{NNN}-{name}.html')"
     class="screen-link flex items-center gap-3 p-2 rounded-lg cursor-pointer">
  <span class="w-2 h-2 rounded-full status-done"></span>
  <span class="text-sm text-gray-700">SCR-{MODULE}-{NNN} {畫面名稱}</span>
</div>
```

#### 5.6.3 驗證同步完成

```bash
#!/bin/bash
cd 04-ui-flow

echo "=== 驗證 device-preview.html ==="
# 1. 側邊欄畫面數量
SIDEBAR_COUNT=$(grep -c 'class="screen-item"' device-preview.html)
echo "側邊欄畫面數: $SIDEBAR_COUNT"

# 2. iframe src 檔案存在
IFRAME_SRC=$(grep -o 'src="[^"]*SCR-[^"]*\.html"' device-preview.html | head -1 | sed 's/src="//;s/"//')
[ -f "$IFRAME_SRC" ] && echo "✅ iframe src 存在: $IFRAME_SRC" || echo "❌ iframe src 不存在: $IFRAME_SRC"

echo ""
echo "=== 驗證 index.html ==="
# 3. 覆蓋率不為 0%
COVERAGE=$(grep -o '[0-9]\+%' index.html | head -1)
echo "覆蓋率: $COVERAGE"

# 4. 實際畫面數
IPAD_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" | wc -l | tr -d ' ')
echo "實際 iPad 畫面數: $IPAD_COUNT"

# 5. 比對
[ "$SIDEBAR_COUNT" -eq "$IPAD_COUNT" ] && echo "✅ 側邊欄與實際畫面數一致" || echo "❌ 側邊欄 ($SIDEBAR_COUNT) ≠ 實際 ($IPAD_COUNT)"
```

**阻斷條件**:
- 側邊欄畫面數必須 = 實際 iPad 畫面數
- iframe src 指向的檔案必須存在
- 覆蓋率必須 > 0%

### Step 6: 更新 workspace 狀態

每完成一個畫面，更新 context：

```json
{
  "current_process": "03-generation",
  "context": {
    "screens_completed": 18,
    "screens_total": 32,
    "last_screen": "SCR-VOCAB-003-create",
    "templates_used": [
      "templates/screen-types/auth/login-ipad.html",
      "templates/ui-flow/screen-template-ipad.html"
    ]
  }
}
```

### Step 7: 定期保存（Compaction 防護）

每完成 5 個畫面，保存狀態到 `workspace/state/`：

```bash
# 保存進度
cp workspace/current-process.json workspace/state/process-state.json
```

---

## 退出條件

- [ ] 所有 iPad 畫面 HTML 已產生
- [ ] 所有 iPhone 畫面 HTML 已產生
- [ ] 每個 HTML 包含 `notify-parent.js`
- [ ] 所有按鈕都有 onclick
- [ ] **每個 HTML 包含 `@template-source` metadata** ⚠️ 新增
- [ ] **index.html 符合模板格式** ⚠️ 新增
- [ ] **所有畫面使用響應式佈局** ⚠️ 新增
- [ ] **⚠️ Template Compliance Gate 已通過** (見 Step 8)

## 阻斷條件 (BLOCKING)

| 條件 | 驗證方式 | 說明 |
|------|----------|------|
| iPad 畫面未產生完畢 | `find . -name "SCR-*.html" -not -path "./iphone/*" \| wc -l` | 必須 > 0 |
| **iPhone 版本缺失** | `find iphone -name "SCR-*.html" \| wc -l` | **必須 = iPad 數量** |
| iPhone 與 iPad 數量不一致 | `[ "$IPAD_COUNT" -eq "$IPHONE_COUNT" ]` | 必須相等 |
| 缺少 notify-parent.js | `grep -rL 'notify-parent.js' . --include="SCR-*.html"` | 應無輸出 |
| **缺少 @template-source** | `grep -rL '@template-source' . --include="SCR-*.html"` | 應無輸出 |
| **index.html 缺少 Tailwind** | `grep -c 'tailwindcss' index.html` | 必須 > 0 |
| **index.html 缺少 openScreen** | `grep -c 'openScreen' index.html` | 必須 > 0 |
| **index.html 有未替換變數** | `grep -c '{{.*}}' index.html` | **必須 = 0** ⚠️ |
| **缺少響應式佈局** | `grep -rl 'tablet:' . --include="SCR-*.html" \| wc -l` | **必須 = iPad 數量** ⚠️ 新增 |
| **device-preview.html 側邊欄未同步** | `grep -c 'screen-item' device-preview.html` | **必須 = iPad 畫面數** ⚠️ 新增 |
| **device-preview.html iframe src 不存在** | 驗證 src 指向的檔案存在 | **必須存在** ⚠️ 新增 |
| **index.html 覆蓋率為 0%** | `grep -oE '[0-9]+%' index.html` | **必須 > 0%** ⚠️ 新增 |
| **index.html 模組卡片未同步** | `grep -c 'status-done' index.html` | **必須 = iPad 畫面數** ⚠️ 新增 |

---

## 相關檔案

| 檔案 | 說明 |
|------|------|
| **`templates/ui-flow/screen-template-responsive.html`** | **響應式通用模板（優先使用）** ⚠️ 新增 |
| **`references/responsive-design-guide.md`** | **響應式設計指南** ⚠️ 新增 |
| `templates/ui-flow/screen-template-ipad.html` | 僅 iPad 畫面模板（備案）|
| `templates/ui-flow/screen-template-iphone.html` | 僅 iPhone 畫面模板（備案）|
| `templates/ui-flow/index.html` | index.html 模板 |
| `templates/ui-flow/device-preview.html` | 裝置預覽頁面模板 |
| `templates/ui-flow/scripts/convert-to-iphone.sh` | **iPad → iPhone 轉換腳本（支援響應式）** ⚠️ |
| `templates/ui-flow/scripts/update-index-counts.sh` | **index.html 變數替換腳本** ⚠️ |
| `templates/screen-types/auth/*.html` | 認證模組專用模板 |
| `templates/screen-types/common/*.html` | 通用類型模板 |

## 下一節點

→ `process/04-validation/README.md` (導航驗證)

---

## Compaction 恢復指南

若發生 compaction，依以下步驟恢復：

1. 讀取 `workspace/state/process-state.json`
2. 取得 `context.last_screen` 確認進度
3. **確認已生成畫面都有 @template-source metadata**
4. 繼續生成剩餘畫面

---

## 模板驗證 Checklist

在進入 04-validation 前，確認：

```bash
cd 04-ui-flow

# 1. 所有畫面都有 @template-source
echo "檢查 @template-source..."
find . -name "SCR-*.html" -exec grep -L '@template-source' {} \;

# 2. iPad 與 iPhone 畫面數量一致
echo "檢查 iPad/iPhone 數量..."
IPAD_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" | wc -l | tr -d ' ')
IPHONE_COUNT=$(find iphone -name "SCR-*.html" 2>/dev/null | wc -l | tr -d ' ')
echo "iPad: $IPAD_COUNT, iPhone: $IPHONE_COUNT"
[ "$IPAD_COUNT" -eq "$IPHONE_COUNT" ] && echo "✅ iPad/iPhone 數量一致" || echo "❌ 數量不一致"

# 3. index.html 符合模板格式
echo "檢查 index.html..."
grep -q 'tailwindcss' index.html && echo "✅ Tailwind" || echo "❌ 缺少 Tailwind"
grep -q 'openScreen' index.html && echo "✅ openScreen" || echo "❌ 缺少 openScreen"
grep -q 'flow-iframe' index.html && echo "✅ Flow iframe" || echo "❌ 缺少 Flow iframe"

# 4. 無遺漏的模板變數 (最重要！)
echo "檢查未替換變數..."
REMAINING=$(grep -ro '{{[^}]*}}' *.html */*.html 2>/dev/null | wc -l | tr -d ' ')
[ "$REMAINING" -eq 0 ] && echo "✅ 所有變數已替換" || echo "❌ 有 $REMAINING 個未替換變數"

# 5. 顯示未替換的變數（如果有）
if [ "$REMAINING" -gt 0 ]; then
  echo "未替換變數列表："
  grep -ro '{{[^}]*}}' *.html */*.html 2>/dev/null | sort | uniq
fi

# 6. 響應式佈局檢查 ⚠️ 新增
echo "檢查響應式佈局..."
RESPONSIVE_COUNT=$(grep -rl 'tablet:' . --include="SCR-*.html" -not -path "./iphone/*" 2>/dev/null | wc -l | tr -d ' ')
echo "響應式畫面: $RESPONSIVE_COUNT / $IPAD_COUNT"
[ "$RESPONSIVE_COUNT" -eq "$IPAD_COUNT" ] && echo "✅ 所有畫面使用響應式佈局" || echo "❌ 有 $((IPAD_COUNT - RESPONSIVE_COUNT)) 個畫面缺少響應式佈局"

# 7. CSS 變數檢查（響應式模板必備）
echo "檢查 CSS 變數..."
CSS_VAR_COUNT=$(grep -rl '\-\-ipad-width' . --include="SCR-*.html" -not -path "./iphone/*" 2>/dev/null | wc -l | tr -d ' ')
echo "使用 CSS 變數: $CSS_VAR_COUNT / $IPAD_COUNT"

# 8. Tailwind config 檢查
echo "檢查 Tailwind config..."
TAILWIND_CONFIG=$(grep -rl "tailwind.config" . --include="SCR-*.html" -not -path "./iphone/*" 2>/dev/null | wc -l | tr -d ' ')
echo "有 Tailwind config: $TAILWIND_CONFIG / $IPAD_COUNT"
```

**⚠️ 所有檢查項目必須通過才能進入 04-validation！**

### 響應式佈局驗證重點

1. **必要 CSS 結構**：
   - `:root` 包含 `--ipad-width`, `--ipad-height`, `--iphone-width`, `--iphone-height`
   - `@media (max-width: 500px)` 區塊用於 iPhone

2. **必要 Tailwind 配置**：
   - `tailwind.config.theme.extend.screens` 包含 `phone` 和 `tablet`

3. **響應式類別使用**：
   - 使用 `tablet:` 前綴控制 iPad 樣式
   - 預設樣式應為 iPhone 尺寸（mobile-first）

---

## ⚠️ Step 8: Template Compliance Gate (MANDATORY - 自動執行)

> **Claude 必須在標記 03-generation 為 completed 之前自動執行此驗證！**
> **無需用戶提醒，這是強制性的自動化步驟。**

### 8.1 驗證腳本 (必須執行)

```bash
#!/bin/bash
# === Template Compliance Gate (自動執行) ===
cd 04-ui-flow

ERRORS=0

echo "======================================"
echo "  🔍 Template Compliance Gate"
echo "  ⚠️ 此驗證由 Claude 自動執行"
echo "======================================"

# 1. index.html 模板合規
echo ""
echo "📊 [1/5] 驗證 index.html 模板合規..."
INDEX_CHECKS=0
grep -q 'flow-iframe' index.html || { echo "  ❌ 缺少 UI Flow Diagram iframe"; INDEX_CHECKS=$((INDEX_CHECKS+1)); }
grep -q 'switchDevice' index.html || { echo "  ❌ 缺少 switchDevice() 函數"; INDEX_CHECKS=$((INDEX_CHECKS+1)); }
grep -q 'device-toggle-btn' index.html || { echo "  ❌ 缺少裝置切換按鈕 (iPad/iPhone)"; INDEX_CHECKS=$((INDEX_CHECKS+1)); }
grep -q 'module-legend\|sidebar\|圖例' index.html || { echo "  ❌ 缺少模組圖例側邊欄"; INDEX_CHECKS=$((INDEX_CHECKS+1)); }
grep -q '{{' index.html && { echo "  ❌ 有未替換的模板變數"; INDEX_CHECKS=$((INDEX_CHECKS+1)); }
[ $INDEX_CHECKS -eq 0 ] && echo "  ✅ index.html 模板合規" || ERRORS=$((ERRORS+INDEX_CHECKS))

# 2. docs/ui-flow-diagram.html 畫面同步
echo ""
echo "📱 [2/5] 驗證 ui-flow-diagram.html..."
if [ -f "docs/ui-flow-diagram.html" ]; then
  IPAD_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" -not -path "./docs/*" 2>/dev/null | wc -l | tr -d ' ')
  DIAGRAM_COUNT=$(grep -c 'screen-card' docs/ui-flow-diagram.html 2>/dev/null || echo "0")
  echo "  實際畫面數: $IPAD_COUNT"
  echo "  Diagram 畫面數: $DIAGRAM_COUNT"
  if [ "$DIAGRAM_COUNT" -eq "$IPAD_COUNT" ]; then
    echo "  ✅ ui-flow-diagram.html 同步完成"
  else
    echo "  ❌ ui-flow-diagram 畫面數不符 ($DIAGRAM_COUNT ≠ $IPAD_COUNT)"
    ERRORS=$((ERRORS+1))
  fi
  # 檢查是否使用模板佔位符
  grep -q 'SCR-EXAMPLE\|template-screen\|placeholder' docs/ui-flow-diagram.html && {
    echo "  ❌ ui-flow-diagram 仍有模板佔位符，需替換為實際畫面"
    ERRORS=$((ERRORS+1))
  }
else
  echo "  ❌ 缺少 docs/ui-flow-diagram.html"
  ERRORS=$((ERRORS+1))
fi

# 3. device-preview.html 側邊欄同步
echo ""
echo "📱 [3/5] 驗證 device-preview.html..."
if [ -f "device-preview.html" ]; then
  SIDEBAR_COUNT=$(grep -c 'screen-item' device-preview.html 2>/dev/null || echo "0")
  echo "  側邊欄畫面數: $SIDEBAR_COUNT"
  if [ "$SIDEBAR_COUNT" -eq "$IPAD_COUNT" ]; then
    echo "  ✅ device-preview.html 同步完成"
  else
    echo "  ❌ device-preview 側邊欄不符 ($SIDEBAR_COUNT ≠ $IPAD_COUNT)"
    ERRORS=$((ERRORS+1))
  fi
  # 檢查 iframe src 是否存在
  IFRAME_SRC=$(grep -o 'src="[^"]*SCR-[^"]*\.html"' device-preview.html | head -1 | sed 's/src="//;s/"//')
  if [ -n "$IFRAME_SRC" ] && [ -f "$IFRAME_SRC" ]; then
    echo "  ✅ iframe src 存在: $IFRAME_SRC"
  else
    echo "  ❌ iframe src 不存在: $IFRAME_SRC"
    ERRORS=$((ERRORS+1))
  fi
else
  echo "  ❌ 缺少 device-preview.html"
  ERRORS=$((ERRORS+1))
fi

# 4. 與模板目錄比對
echo ""
echo "📁 [4/5] 與 reference-example 標準比對..."
SKILL_DIR=~/.claude/skills/app-uiux-designer.skill
if [ -d "$SKILL_DIR/templates/ui-flow/reference-example" ]; then
  # 檢查必要檔案存在
  REQUIRED_FILES=("index.html" "device-preview.html" "docs/ui-flow-diagram.html" "shared/project-theme.css" "shared/notify-parent.js")
  MISSING_FILES=0
  for f in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$f" ]; then
      echo "  ❌ 缺少必要檔案: $f"
      MISSING_FILES=$((MISSING_FILES+1))
    fi
  done
  [ $MISSING_FILES -eq 0 ] && echo "  ✅ 所有必要檔案存在" || ERRORS=$((ERRORS+MISSING_FILES))
else
  echo "  ⚠️ 無 reference-example 可比對 (跳過)"
fi

# 5. 執行 validate-consistency.js
echo ""
echo "🔗 [5/5] 執行一致性驗證 (validate-consistency.js)..."
if [ -f "$SKILL_DIR/templates/ui-flow/validate-consistency.js" ]; then
  node "$SKILL_DIR/templates/ui-flow/validate-consistency.js" 2>&1 | head -20
  CONSISTENCY_RESULT=$?
  [ $CONSISTENCY_RESULT -eq 0 ] || ERRORS=$((ERRORS+1))
else
  echo "  ⚠️ validate-consistency.js 不存在 (跳過)"
fi

# 結果
echo ""
echo "======================================"
if [ $ERRORS -eq 0 ]; then
  echo "✅ Template Compliance Gate PASSED"
  echo ""
  echo "📝 下一步: 可以標記 03-generation 為 completed"
  echo "         然後進入 04-validation"
else
  echo "❌ Template Compliance Gate FAILED"
  echo "   發現 $ERRORS 個問題需要修復"
  echo ""
  echo "⚠️ 禁止進入下一階段！"
  echo "   請修復上述問題後重新執行此驗證。"
fi
echo "======================================"
```

### 8.2 失敗時的修復清單

| 失敗項目 | 修復步驟 |
|----------|----------|
| 缺少 UI Flow Diagram iframe | 從 `$SKILL_DIR/templates/ui-flow/index.html` 複製 `#flow-diagram` 區塊 |
| 缺少 switchDevice() 函數 | 從模板複製 JavaScript 函數 |
| 缺少裝置切換按鈕 | 從模板複製 `device-toggle-btn` HTML |
| 缺少模組圖例側邊欄 | 從模板複製 sidebar 區塊並更新模組清單 |
| 有未替換的模板變數 | 執行 `grep '{{' index.html` 找出並替換 |
| ui-flow-diagram 畫面數不符 | 更新 `docs/ui-flow-diagram.html` 加入所有畫面 |
| device-preview 側邊欄不符 | 更新 `device-preview.html` 側邊欄清單 |
| 一致性驗證失敗 | 根據錯誤訊息逐一修復 |

### 8.3 驗證通過後

```json
// 更新 workspace/current-process.json
{
  "progress": {
    "03-generation": "completed"  // 只有驗證通過才能標記
  },
  "context": {
    "last_action": "Template Compliance Gate PASSED",
    "template_compliance": {
      "verified_at": "2026-01-15T12:00:00Z",
      "index_html": "passed",
      "ui_flow_diagram": "passed",
      "device_preview": "passed",
      "consistency": "passed"
    }
  }
}
```

### 8.4 Claude 行為要求

> **⚠️ 關鍵規則：Claude 必須在完成所有畫面生成後，自動執行 Template Compliance Gate**

1. **不需要用戶提醒** - 這是流程的一部分，必須自動執行
2. **不能跳過** - 即使用戶說「繼續」，也必須先通過驗證
3. **失敗必須修復** - 驗證失敗時，必須立即修復後重新驗證
4. **記錄在 current-process.json** - 驗證結果必須記錄下來

---

## 🚨 Exit Validation (Anti-Forgetting Protocol)

> **在標記 03-generation 為 completed 前，必須執行此驗證！**

### 執行方式

```bash
# 執行 exit-validation.sh
bash ~/.claude/skills/app-uiux-designer.skill/process/03-generation/exit-validation.sh {PROJECT_PATH}
```

### 驗證內容

| 驗證項目 | 通過條件 |
|----------|----------|
| Screen Count | iPad/iPhone 數量一致且 > 0 |
| onclick Coverage | 無空 onclick，無 alert 佔位符 |
| index.html | 無 placeholder，覆蓋率 > 0% |
| device-preview.html | 側邊欄已填充 |
| Diagram Files | iPad/iPhone 版本皆存在 |

### 驗證通過後

更新 `workspace/current-process.json`:
```json
{
  "progress": { "03-generation": "completed" },
  "validation_state": {
    "03-generation": {
      "passed": true,
      "timestamp": "ISO-8601",
      "checks": ["all_screens_generated", "onclick_coverage", "index_populated"]
    }
  }
}
```

更新 `workspace/validation-chain.json` 添加此節點驗證記錄。
