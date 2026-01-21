# Process 00: 初始化 (Initialization)

## 進入條件

- [ ] 使用者請求 UI Flow / Screen / Wireframe / Prototype
- [ ] 專案目錄已存在
- [ ] SDD 文件已存在（包含 SCR-* 畫面定義）

---

## ⚠️ 重要原則：完整複製模板

> **MANDATORY**: 此流程必須**完整複製**所有模板檔案，**禁止重新產生** index.html、device-preview.html 等核心檔案。
>
> 這些核心檔案已經過多次迭代優化，包含：
> - 完整的 CSS Design System
> - 響應式佈局（iPad/iPhone）
> - iframe 同步機制
> - 導航驗證功能
> - 截圖自動化腳本
>
> 重新產生這些檔案會**遺失功能**並**浪費 token**。

---

## 執行步驟

### Step 1: 完整複製模板框架 (MANDATORY - 不可跳過)

```bash
# 確保專案 04-ui-flow 目錄存在
mkdir -p ./04-ui-flow

# ⚠️ 完整複製所有模板（包括 HTML、JS、CSS、Shell scripts）
cp -r ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/* ./04-ui-flow/
```

> ⛔ **禁止**：
> - 重新產生 index.html
> - 重新產生 device-preview.html
> - 重新產生 docs/ui-flow-diagram.html
> - 重新產生 capture-screenshots.js
> - 重新產生 validate-navigation.js

### Step 2: 驗證核心檔案完整性 (BLOCKING)

```bash
# 必須驗證所有核心檔案存在
ls -la ./04-ui-flow/index.html              # 主導覽頁
ls -la ./04-ui-flow/device-preview.html     # 設備預覽器
ls -la ./04-ui-flow/capture-screenshots.js  # 截圖工具
ls -la ./04-ui-flow/validate-navigation.js  # 導航驗證
ls -la ./04-ui-flow/docs/ui-flow-diagram.html   # 流程圖
ls -la ./04-ui-flow/shared/project-theme.css    # Design System
ls -la ./04-ui-flow/shared/notify-parent.js     # iframe 同步
```

> ⛔ **如果任何核心檔案不存在，重新執行 Step 1**

### Step 3: 驗證自動化腳本存在 (BLOCKING)

```bash
# 必須驗證所有腳本存在
ls -la ./04-ui-flow/scripts/convert-to-iphone.sh        # iPad→iPhone 轉換
ls -la ./04-ui-flow/scripts/update-index-counts.sh      # 統計更新
ls -la ./04-ui-flow/scripts/add-responsive-structure.sh # 響應式結構
```

### Step 4: 建立模組目錄結構

```bash
cd ./04-ui-flow

# 標準模組目錄（所有 App 類型通用）
mkdir -p auth       # 認證模組
mkdir -p onboard    # 引導模組
mkdir -p home       # 首頁模組
mkdir -p dash       # 儀表板模組
mkdir -p feature    # 功能模組（通用）
mkdir -p profile    # 個人資料模組
mkdir -p setting    # 設定模組
mkdir -p report     # 報告模組

# 擴展模組目錄（依專案類型選用）
mkdir -p vocab      # 字庫模組（教育類）
mkdir -p train      # 訓練模組（教育類）
mkdir -p progress   # 進度模組（教育類）
mkdir -p parent     # 家長模組（教育類）
mkdir -p cart       # 購物車模組（電商類）
mkdir -p product    # 商品模組（電商類）
mkdir -p social     # 社群模組（社群類）

# 其他目錄
mkdir -p iphone
mkdir -p screenshots/{ipad,iphone}
mkdir -p workspace/{context,state}
```

### Step 5: 執行初始化腳本 - 變數替換 (MANDATORY)

> ⚠️ **必須執行此腳本來替換模板變數**

```bash
cd ./04-ui-flow

# 執行初始化（替換所有 {{VARIABLE}} 模板變數）
bash ~/.claude/skills/app-uiux-designer.skill/process/00-init/templates/init-project.sh \
  "專案名稱" \
  "📚" \
  "40" \
  "專案描述（可選）"
```

**參數說明：**

| 參數 | 說明 | 範例 |
|------|------|------|
| $1 | 專案名稱 | "單字小達人" |
| $2 | 專案圖示 emoji | "📚" |
| $3 | 預估畫面總數 | "40" |
| $4 | 專案描述（可選） | "兒童英語學習 App" |

### Step 6: 驗證變數替換 (BLOCKING)

```bash
# 檢查是否還有未替換的變數
grep -c '{{PROJECT_NAME}}' ./04-ui-flow/index.html
grep -c '{{PROJECT_NAME}}' ./04-ui-flow/device-preview.html
grep -c '{{PROJECT_NAME}}' ./04-ui-flow/docs/ui-flow-diagram.html
# 所有結果應該是 0
```

> ⛔ **如果上述檢查結果 > 0，表示變數未替換，必須重新執行 Step 5**

### Step 7: 初始化 workspace 狀態 (MANDATORY)

> ⚠️ workspace 必須在 **專案目錄** `{PROJECT}/04-ui-flow/workspace/`

Claude 必須建立 `04-ui-flow/workspace/current-process.json`：

```json
{
  "skill": "app-uiux-designer",
  "version": "2.0-cor",
  "architecture": "chain-of-repository",
  "current_process": "00-init",
  "started_at": "2026-01-13T00:00:00Z",
  "updated_at": "2026-01-13T00:00:00Z",
  "project": {
    "name": "專案名稱",
    "path": "/path/to/project",
    "ui_flow_path": "/path/to/project/04-ui-flow"
  },
  "progress": {
    "00-init": "completed",
    "01-discovery": "pending",
    "02-planning": "pending",
    "03-generation": "pending",
    "04-validation": "pending",
    "05-diagram": "pending",
    "06-screenshot": "pending",
    "07-feedback": "pending",
    "08-finalize": "pending"
  },
  "context": {
    "loaded_files": [],
    "screens_completed": 0,
    "screens_total": 0,
    "last_action": "Initialized workspace with complete template copy"
  },
  "modules": {},
  "notes": ""
}
```

---

## 退出條件 (EXIT CRITERIA)

必須滿足 **全部** 條件才能進入下一節點：

| 條件 | 驗證方式 | 必須結果 |
|------|----------|----------|
| index.html 存在 | `wc -l ./04-ui-flow/index.html` | >= 500 |
| device-preview 存在 | `wc -l ./04-ui-flow/device-preview.html` | >= 600 |
| ui-flow-diagram 存在 | `wc -l ./04-ui-flow/docs/ui-flow-diagram.html` | >= 300 |
| capture-screenshots.js 存在 | `test -f ./04-ui-flow/capture-screenshots.js` | 成功 |
| validate-navigation.js 存在 | `test -f ./04-ui-flow/validate-navigation.js` | 成功 |
| project-theme.css 存在 | `test -f ./04-ui-flow/shared/project-theme.css` | 成功 |
| notify-parent.js 存在 | `test -f ./04-ui-flow/shared/notify-parent.js` | 成功 |
| 變數已替換 | `grep -c '{{PROJECT_NAME}}' ./04-ui-flow/device-preview.html` | = 0 |
| ipad-frame 存在 | `grep -c 'ipad-frame' ./04-ui-flow/device-preview.html` | > 0 |
| workspace 存在 | `test -f ./04-ui-flow/workspace/current-process.json` | 成功 |
| scripts 存在 | `ls ./04-ui-flow/scripts/*.sh \| wc -l` | >= 3 |

---

## 阻斷條件 (BLOCKING)

> ⛔ **以下任一情況發生時，禁止進入下一節點**

1. `grep '{{' ./04-ui-flow/device-preview.html` 有任何輸出
2. `device-preview.html` 少於 600 行
3. `capture-screenshots.js` 不存在
4. `validate-navigation.js` 不存在
5. `workspace/current-process.json` 不存在
6. `scripts/` 目錄中 .sh 檔案少於 3 個

---

## 模板變數清單

| 變數 | 說明 | 範例值 |
|------|------|--------|
| `{{PROJECT_NAME}}` | 專案顯示名稱 | 單字小達人 |
| `{{PROJECT_ID}}` | 專案 ID（小寫，無空格） | vocabkids |
| `{{PROJECT_ICON}}` | 專案圖示 emoji | 📚 |
| `{{PROJECT_DESCRIPTION}}` | 專案描述 | 兒童英語學習 App |
| `{{TOTAL_SCREENS}}` | 預估畫面總數 | 40 |
| `{{COVERAGE}}` | 導航覆蓋率（初始） | 0% |
| `{{MODULE_COUNT}}` | 模組數量（初始） | 0 |
| `{{IPAD_COUNT}}` | iPad 畫面數（初始） | 0 |
| `{{IPHONE_COUNT}}` | iPhone 畫面數（初始） | 0 |
| `{{GENERATED_DATE}}` | 產生日期 | 2026-01-13 |

---

## 重要提醒

### ⚠️ 關於畫面清單 (Screen List)

**index.html**、**device-preview.html** 和 **docs/ui-flow-diagram.html** 中的畫面清單會在後續步驟填入：

- **03-generation**: 產生畫面時，同步更新 index.html 和 device-preview.html 的畫面清單
- **05-diagram**: 產生流程圖時，填入 ui-flow-diagram.html 的 screen cards 和 arrows

因此，**00-init 只負責模板複製、變數替換和目錄建立**，不需要手動填入畫面清單。

### ⚠️ 關於 iPhone 版本

iPhone 版本的畫面會在 **03-generation** 或 **06-screenshot** 階段處理：

1. 使用 `scripts/convert-to-iphone.sh` 批量轉換
2. device-preview.html 支援 iPad/iPhone 雙模式預覽

### ⚠️ 關於截圖功能

截圖功能已內建於模板：

1. `capture-screenshots.js` - Puppeteer 截圖腳本
2. 使用方式：`node capture-screenshots.js`
3. 輸出目錄：`screenshots/ipad/` 和 `screenshots/iphone/`

---

## 相關檔案

| 檔案 | 說明 |
|------|------|
| `templates/init-project.sh` | 自動化初始化腳本 |
| `../../templates/ui-flow/*` | 模板來源（完整複製） |

---

## 下一節點

→ `process/03-generation/README.md` (HTML 畫面生成)

> ⚠️ **注意**: 01-discovery 和 02-planning 已由 `app-requirements-skill` 完成，本 Skill 直接從 00-init 進入 03-generation。
