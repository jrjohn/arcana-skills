---
name: app-uiux-designer
description: |
  Enterprise UI/UX design expert. SRS/SDD → HTML UI Flow + Coverage Validation. Features: App Theme Style Designer, Visual Style Extraction, Multi-platform Assets, Motion Design, Dark Mode, i18n. Platform: iOS HIG / Material Design 3 / WCAG.

  【心理學整合】
  本 Skill 整合專業設計心理學知識：
  • 格式塔心理學 (Gestalt) - 接近性、相似性、連續性、閉合性、圖地關係等 7 原則
  • 美學設計原則 - 黃金比例、視覺層級、對齊、對比、留白、視覺平衡
  • 情感設計 (Don Norman) - 本能層、行為層、反思層三層次設計
  • 認知心理學 - 認知負荷、Fitts' Law、Hick's Law、漸進式揭露
  • 色彩心理學 - 色彩情感對照、文化差異、60-30-10 配色法則
---

# UI/UX Designer Skill

Enterprise-grade App & Web UI/UX design guide.

**Core:** SRS/SDD → HTML UI Flow + 100% Coverage Validation
**Features:** App Theme Style Designer | Visual Style Extraction | Motion Design | Dark Mode | i18n
**Platforms:** iOS HIG | Android Material 3 | Web WCAG | Figma

---

## Quick Reference

### Default Platform
- **Device:** iPhone 14 Pro (390×844) / Android Medium (360×800)
- **Format:** HTML + Tailwind CSS
- **Dual Platform:** iPad (1194×834) + iPhone (393×852)

### Critical Rules

> **⚠️ MANDATORY AUTO-VALIDATION - 強制自動驗證**
>
> 每次產生或修改 UI Flow HTML 後，**必須立即執行**：
> ```bash
> node ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/validate-navigation.js --fix
> ```
> **覆蓋率必須 = 100% 才能繼續任何後續動作！**
>
> 此規則無例外，違反將導致 UI Flow 導航斷裂。

1. **App Theme Style → Ask Discovery Questions First**
   See: `references/app-theme-style-designer.md`

2. **After UI Flow Complete → Auto SRS/SDD Feedback**
   See: `references/sdd-feedback.md`

3. **UI Flow Request → Auto Generate HTML**
   Triggers: "UI Flow", "Screen", "Wireframe", "Prototype"

4. **Screenshot 取代 Wireframe → 刪除 ASCII Wireframe**
   - 有截圖後，必須刪除對應的 `**Wireframe：**` 區塊
   - 原因：ASCII 在 DOCX 轉換會產生行號 bug
   - See: `references/sdd-feedback.md#截圖取代-wireframe-規則`

5. **⚠️ 可點擊元素 100% 覆蓋 + 強制阻止 (Clickable Element Coverage)**
   - UI Flow 中每個可點擊元素（按鈕、連結、Tab、圖標）必須有對應的目標畫面
   - 按鈕的 onclick 必須導向實際存在的 SCR-* 畫面
   - 禁止出現「點擊後無目標」的懸空按鈕
   - **UI Flow 生成前必須執行驗證：**
     ```bash
     node capture-screenshots.js --validate-only
     ```
   - **驗證失敗時禁止生成 UI Flow Diagram**
   - See: `references/coverage-validation.md`

6. **導航完整性驗證 (Navigation Integrity)**
   - 每個畫面必須有返回路徑（除了首頁/登入頁）
   - Tab Bar 的每個 Tab 必須有對應畫面
   - Modal/Sheet 必須有關閉機制
   - 表單提交後必須有成功/失敗畫面

6.1 **⚠️ Sidebar 同步 (Device Preview Sidebar Sync)**
   - **問題**：iframe 內導航後，左側選單不會自動高亮
   - **解決方案**：每個畫面必須引入 `notify-parent.js`

   **畫面 HTML 必須包含：**
   ```html
   <!-- 在 </body> 之前 -->
   <script src="../shared/notify-parent.js"></script>
   ```

   **device-preview.html 必須包含：**
   ```javascript
   // Listen for postMessage from iframe
   window.addEventListener('message', function(event) {
     if (event.data && event.data.type === 'pageLoaded') {
       syncSidebarFromIframe(event.data.url || event.data.pathname);
     }
   });
   ```

7. **⚠️ 強制使用模板 (MANDATORY Template Usage)**
   - **禁止**從頭建立自訂 HTML UI Flow
   - **必須**複製 `templates/ui-flow/` 模板到專案目錄
   - **必須**替換模板中的 `{{VARIABLE}}` 變數
   - **必須**按照模板結構建立畫面目錄 (auth/, vocab/, iphone/ 等)
   - 詳見下方 Template Location 章節

8. **⚠️ 表單按鈕與社群登入按鈕 (Form & Social Login Buttons)**
   - **禁止** `type="submit"` 按鈕無 onclick：會導致點擊無導航
   - **必須** 將 `type="submit"` 改為 `type="button"` 並加上 onclick
   - **必須** 所有社群登入按鈕 (Apple/Google/Facebook) 有 onclick 導航
   - See: `references/screen-content-requirements.md#7-禁止事項`

   ```html
   <!-- ❌ 錯誤 -->
   <button type="submit">登入</button>
   <button class="social-btn">Apple</button>

   <!-- ✅ 正確 -->
   <button type="button" onclick="location.href='SCR-AUTH-004-role.html'">登入</button>
   <button type="button" onclick="location.href='SCR-AUTH-004-role.html'" class="social-btn">Apple</button>
   ```

9. **⚠️ UI Flow Diagram 裝置切換 (Device Switching)**
   - **禁止** iPhone 模式載入 iPad 畫面路徑
   - **必須** 根據 `?device=` 參數動態切換 iframe src
   - iPad 畫面路徑：`../auth/`, `../vocab/`, `../train/` 等
   - iPhone 畫面路徑：`../iphone/` (統一目錄)

   ```javascript
   // ui-flow-diagram.html 必須包含此邏輯
   function switchIframeSourcesToIPhone() {
     document.querySelectorAll('.screen-iframe').forEach(iframe => {
       const src = iframe.getAttribute('src');
       // ../auth/SCR-*.html → ../iphone/SCR-*.html
       const newSrc = src.replace(/\.\.\/(auth|vocab|train|home|report|setting)\//, '../iphone/');
       iframe.setAttribute('src', newSrc);
     });
   }
   ```

10. **⚠️ 強制自動掃描驗證 (Mandatory Auto-Scan Validation)**
    - **必須** 在產生導航驗證表後，自動執行 `validate-navigation.js` 掃描所有畫面
    - **必須** 覆蓋率達 100% 才能繼續
    - **禁止** 手動驗證後不修復問題就繼續進行
    - See: `references/coverage-validation.md#11-mandatory-auto-scan-validation`

11. **⚠️ 所有可點擊元素必須有功能 (All Clickable Elements Must Have Handlers)**
    - **每個視覺上可點擊的元素都必須有 onclick，無例外**
    - 當目標畫面存在：`onclick="location.href='SCR-*.html'"`
    - 當目標畫面不存在：`onclick="alert('功能說明')"`
    - **禁止完全省略 onclick** - 這比使用 alert 更糟糕！
    - See: `references/screen-content-requirements.md#7-禁止事項`

    **設定列表行範例：**
    ```html
    <!-- ✅ 正確：目標存在 -->
    <button onclick="location.href='SCR-SETTING-002-profile.html'" class="...">
      個人資料
    </button>

    <!-- ✅ 正確：目標不存在，使用 alert -->
    <button onclick="alert('個人資料設定：編輯您的個人資訊')" class="...">
      個人資料
    </button>

    <!-- ❌ 錯誤：完全沒有 onclick -->
    <button class="...">個人資料</button>
    ```

    **自動偵測機制：**
    - ✅ 關閉按鈕 (X) - SVG path `M6 18L18 6` 等
    - ✅ 設定列表行 - chevron SVG `M9 5l7 7-7 7`
    - ✅ 可點擊列 - `active:bg-*` 或 `hover:bg-*` 樣式
    - See: `references/coverage-validation.md#11-5-2-settings-row-detection`

    ```bash
    # 產生導航表後，立即執行：
    cd 04-ui-flow && node ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/validate-navigation.js --fix

    # 驗證通過 (100%) 後才能繼續
    ```

    **觸發時機：**
    | 事件 | 動作 |
    |------|------|
    | 產生任何畫面 HTML 後 | 執行單畫面驗證 |
    | 產生導航驗證表後 | **強制執行全畫面掃描** |
    | 準備生成 UI Flow Diagram 前 | 確認覆蓋率 = 100% |
    | SRS/SDD 回補前 | 確認覆蓋率 = 100% |

12. **⚠️ 設定畫面必須生成子畫面 (Settings Screens Must Generate Sub-screens)**
    - **生成設定主頁時，必須同時生成所有設定列對應的詳情畫面**
    - **禁止使用 `alert()` 作為設定列的點擊動作**
    - 每個帶有 chevron (>) 的設定列必須導航到實際畫面
    - See: `references/settings-screens-generation.md`

    **設定列標準子畫面：**
    | 設定列文字 | 目標畫面 |
    |-----------|---------|
    | 個人資料 | SCR-SETTING-002-profile.html |
    | 帳號安全 | SCR-SETTING-003-security.html |
    | 隱私設定 | SCR-SETTING-004-privacy.html |
    | 資料管理 | SCR-SETTING-005-data.html |
    | 通知設定 | SCR-SETTING-006-notification.html |
    | 主題外觀 | SCR-SETTING-007-appearance.html |
    | 語音設定 | SCR-SETTING-008-voice.html |
    | 服務條款 | SCR-SETTING-010-terms.html |
    | 版本資訊 | SCR-SETTING-012-about.html |

    ```html
    <!-- ❌ 禁止 -->
    <button onclick="alert('個人資料')">個人資料</button>

    <!-- ✅ 正確 -->
    <button onclick="location.href='SCR-SETTING-002-profile.html'">個人資料</button>
    ```

13. **⚠️ index.html Device-Aware Links (裝置感知連結)**
    - **禁止** 在 index.html 使用硬編碼的 `<a href="device-preview.html?screen=...">` 連結
    - **必須** 使用 `onclick="openScreen(ipadPath, iphonePath)"` 函數
    - 連結會根據當前選擇的裝置 (iPad/iPhone) 動態導向正確的畫面路徑
    - See: `references/ui-gen-html.md#index-html-device-aware-screen-links-強制規則`
    - See: `references/coverage-validation.md#17-device-aware-link-validation`

    ```html
    <!-- ❌ 禁止 - 硬編碼連結 -->
    <a href="device-preview.html?screen=auth/SCR-AUTH-001-login.html">登入頁</a>

    <!-- ✅ 正確 - Device-aware 連結 -->
    <div onclick="openScreen('auth/SCR-AUTH-001-login.html', 'iphone/SCR-AUTH-001-login.html')"
         class="screen-link cursor-pointer">登入頁</div>
    ```

    **必要的 JavaScript 函數 (index.html):**
    ```javascript
    function openScreen(ipadPath, iphonePath) {
      const screenPath = currentDevice === 'iphone' ? iphonePath : ipadPath;
      window.location.href = 'device-preview.html?screen=' + screenPath;
    }
    ```

    **驗證命令：**
    ```bash
    # 應回傳 0 (無硬編碼連結)
    grep -c 'href="device-preview.html?screen=' index.html
    ```

14. **⚠️ 強制 SRS/SDD 回補 (MANDATORY SRS/SDD Feedback) - BLOCKING STEP**

    > **這是阻斷步驟！UI Flow 完成後必須執行回補，否則視為未完成。**

    UI Flow 生成完成後，**必須**執行以下回補項目：

    **SDD 回補項目 (必須):**
    | 項目 | 說明 | 驗證方式 |
    |------|------|----------|
    | **截圖嵌入** | 每個 SCR-* 必須有對應截圖 | `ls 02-design/SDD/images/*.png` |
    | **Button Navigation** | 每個畫面的按鈕導航表格 | 檢查 SDD.md 各畫面章節 |
    | **Wireframe 移除** | 有截圖後刪除 ASCII Wireframe | 搜尋 `**Wireframe：**` |
    | **Mermaid 流程圖** | UI Flow 的畫面關係圖 | 檢查 SDD.md 流程圖章節 |

    **SRS 回補項目 (必須):**
    | 項目 | 說明 | 驗證方式 |
    |------|------|----------|
    | **Screen References** | 每個 REQ 對應的 SCR 畫面 | 檢查 SRS.md Screen References 章節 |
    | **Inferred Requirements** | 從導航推斷的新需求 (REQ-NAV-*) | 檢查 SRS.md Inferred Requirements 章節 |
    | **User Flows** | Mermaid 使用者流程圖 | 檢查 SRS.md User Flows 章節 |

    **RTM 回補項目 (必須):**
    | 項目 | 說明 | 驗證方式 |
    |------|------|----------|
    | **SRS ↔ SCR 對應** | 所有 REQ 必須對應到 SCR | RTM 覆蓋率 = 100% |

    **執行步驟：**
    ```bash
    # Step 1: 生成截圖
    cd 04-ui-flow && node capture-screenshots.js

    # Step 2: 複製截圖到 SDD 目錄
    mkdir -p ../02-design/SDD/images
    cp screenshots/**/*.png ../02-design/SDD/images/

    # Step 3: 更新 SDD.md (手動或腳本)
    # - 嵌入截圖: ![SCR-xxx](./images/SCR-xxx.png)
    # - 刪除 **Wireframe：** 區塊
    # - 新增 Button Navigation 表格

    # Step 4: 更新 SRS.md (手動或腳本)
    # - 新增 Screen References 章節
    # - 新增 Inferred Requirements 章節
    # - 新增 User Flows 章節

    # Step 5: 更新 RTM.md
    # - 補充 SCR 欄位

    # Step 6: 重新產生 DOCX
    bash ~/.claude/skills/medical-software-requirements-skill/remove-heading-numbers.sh ../01-requirements/SRS-*.md
    bash ~/.claude/skills/medical-software-requirements-skill/remove-heading-numbers.sh ../02-design/SDD-*.md
    node ~/.claude/skills/medical-software-requirements-skill/md-to-docx.js ../01-requirements/SRS-*.md
    node ~/.claude/skills/medical-software-requirements-skill/md-to-docx.js ../02-design/SDD-*.md
    ```

    **回補驗證清單：**
    - [ ] SDD 所有 SCR-* 畫面有截圖嵌入
    - [ ] SDD 無殘留的 `**Wireframe：**` 區塊
    - [ ] SDD 每個畫面有 Button Navigation 表格
    - [ ] SRS 有 Screen References 章節
    - [ ] SRS 有 Inferred Requirements 章節
    - [ ] SRS 有 User Flows 章節
    - [ ] RTM SRS→SCR 覆蓋率 = 100%
    - [ ] DOCX 已重新產生

    **See:** `references/sdd-feedback.md` (完整回補規則)

15. **⚠️ 強制使用 app-requirements-skill 的 SRS/SDD 模板格式 (MANDATORY Template Format)**

    > **SRS/SDD 文件必須符合 app-requirements-skill 的模板格式，否則 md-to-docx.js 轉換會失敗！**

    **模板格式要求：**
    ```markdown
    # Software Design Description
    ## For {{project name}}

    Version 0.1
    Prepared by {{author}}
    {{organization}}
    {{date}}

    ## Table of Contents
    <!-- TOC content -->

    ## Revision History
    | Name | Date | Reason For Changes | Version |
    |------|------|--------------------|---------|

    ## 1. Introduction
    <!-- Main content with numbered sections -->
    ```

    **禁止的格式：**
    ```markdown
    # SDD 軟體設計規格書
    ## 文件資訊
    ### 版本歷史          <!-- ❌ 三級標題 -->
    ## 使用案例設計        <!-- ❌ 非編號章節 -->
    ```

    **為什麼重要：**
    - md-to-docx.js 依賴特定的文件結構來分離封面、目錄、修訂歷史和主內容
    - 中文標題（如 `## 文件資訊`）會導致轉換器無法正確解析文件結構
    - 結果是 DOCX 只有封面頁和目錄，主要內容全部遺失

    **正確做法：**
    1. 使用 app-requirements-skill 的模板創建 SRS/SDD
    2. 初始化專案（跨平台）：
       ```bash
       node [SKILL_DIR]/scripts/init-project.js [PROJECT_DIR]
       ```
       其中 `[SKILL_DIR]` 是 app-requirements-skill 的安裝位置
    3. 回補 UI Flow 時，保持模板的章節結構不變

    **驗證命令：**
    ```bash
    # 檢查 SDD 是否有正確的標題結構
    grep -n "^## Table of Contents\|^## Revision History\|^## 1\." SDD-*.md

    # 預期輸出應包含這些標題，若無則格式錯誤
    ```

    **Skill 路徑查詢（跨平台）：**
    - macOS/Linux: `~/.claude/skills/app-requirements-skill/`
    - Windows: `%USERPROFILE%\.claude\skills\app-requirements-skill\`
    - 或在 Claude Code 中直接執行 init-project.js，它會自動定位

---

## Template Location

> **⚠️ MANDATORY - 強制使用模板**
>
> 所有 UI Flow 輸出**必須**使用 `templates/ui-flow/` 下的模板。
> **禁止**從頭建立自訂 HTML 檔案。

### 模板複製步驟 (必須執行)

```bash
# Step 1: 複製模板到專案
cp -r ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/* ./04-ui-flow/

# Step 2: 替換變數 (PROJECT_NAME, PROJECT_ID, etc.)
# 使用 sed 或手動替換 {{VARIABLE}} 格式的變數

# Step 3: 建立模組目錄並產出畫面
mkdir -p 04-ui-flow/{auth,vocab,train,report,setting,iphone}
```

### Directory Structure
```
generated-ui/
├── index.html              # Screen overview
├── device-preview.html     # Multi-device preview (iPad/Mini/iPhone)
├── docs/
│   └── ui-flow-diagram.html  # Flow diagram (onclick → device-preview)
├── shared/
│   ├── project-theme.css   # Design System
│   └── notify-parent.js    # iframe sync
├── screenshots/            # For SDD embedding
├── auth/, dash/, etc.      # iPad screens
└── iphone/                 # iPhone screens
```

### Key Pattern - UI Flow Click Behavior
```html
<!-- CORRECT: onclick opens device-preview -->
<div class="screen-card" onclick="openScreen('auth/SCR-AUTH-001.html')">
  <img src="../screenshots/auth/SCR-AUTH-001.png">
</div>

<script>
function openScreen(screen) {
  window.open('../device-preview.html?screen=' + screen, '_blank');
}
</script>
```

---

## Reference Documents

| Category | Document | Description |
|----------|----------|-------------|
| **Core** | `ui-generation.md` | HTML/React/Angular/SwiftUI generation |
| **Core** | `spec-driven-generation.md` | SRS/SDD → UI mapping |
| **Core** | `coverage-validation.md` | 100% RTM + Clickable Element Coverage |
| **Core** | `screen-content-requirements.md` | 畫面內容最小要求與模板 |
| **Core** | `ui-flow-generation-workflow.md` | UI Flow 強制生成流程 |
| **Theme** | `app-theme-style-designer.md` | Age-specific design, color psychology |
| **Theme** | `style-extraction.md` | Visual style extraction |
| **Theme** | `design-system.md` | Design tokens, components |
| **Assets** | `asset-extraction.md` | iOS/Android/Web assets |
| **Flow** | `flow-prediction.md` | User flow prediction |
| **Flow** | `sdd-feedback.md` | SRS/SDD feedback rules |
| **Platform** | `ios-guidelines.md` | Apple HIG |
| **Platform** | `android-guidelines.md` | Material Design 3 |
| **Platform** | `web-guidelines.md` | WCAG accessibility |
| **Platform** | `figma-guidelines.md` | Figma integration |
| **Advanced** | `motion-design.md` | Micro-interactions, Lottie |
| **Advanced** | `dark-mode.md` | Dark mode support |
| **Advanced** | `localization.md` | i18n, RTL |
| **Advanced** | `ux-writing.md` | Microcopy guidelines |
| **Advanced** | `data-visualization.md` | Charts, graphs |
| **QA** | `accessibility.md` | WCAG compliance |
| **QA** | `psychology-validation.md` | UX psychology validation |
| **QA** | `design-review.md` | Nielsen heuristics |
| **Psychology** | `gestalt-psychology.md` | 格式塔視覺心理學 (7 原則) |
| **Psychology** | `aesthetic-design.md` | 美學設計原則 (黃金比例、視覺層級) |
| **Psychology** | `emotional-design.md` | 情感設計理論 (Don Norman 三層次) |
| **Research** | `ux-research.md` | User research methods |
| **Templates** | `standard-app-screens.md` | 標準 App 畫面參考 (60+ 畫面) |
| **Templates** | `settings-screens-generation.md` | 設定畫面子畫面生成指南 |

---

## Screen ID Format

| Type | Format | Example |
|------|--------|---------|
| Screen | `SCR-{MODULE}-{NNN}-{name}` | `SCR-AUTH-001-login` |
| Requirement | `REQ-{MODULE}-{NNN}` | `REQ-AUTH-001` |

### Module Codes
AUTH, ONBOARD, DASH, VOCAB, TRAIN, REPORT, SETTING, DEVICE, REWARD

---

## Scripts

| Script | Description |
|--------|-------------|
| `scripts/generate-app-icons.sh` | Generate iOS/Android app icons |
| `scripts/generate-mermaid-flow.js` | Generate Mermaid flowcharts |
| `templates/ui-flow/capture-screenshots.js` | Puppeteer screenshot capture |
| `templates/ui-flow/validate-navigation.js` | **Navigation auto-scan validation (無需 puppeteer)** |

### Claude Code Hook (自動驗證)

已設定 PostToolUse Hook，每次 Write/Edit HTML 檔案後自動執行驗證：

```json
// ~/.claude/settings.json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/validate-ui-flow.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**Hook 行為：**
- 只驗證 `*ui-flow*` 或 `*04-ui-flow*` 目錄中的 `.html` 檔案
- 跳過 `template`, `shared`, `docs` 目錄
- 顯示驗證結果但不阻擋（設定 `exit 2` 可改為阻擋模式）

### validate-navigation.js Usage

```bash
# 基本驗證
node validate-navigation.js

# 顯示修復建議
node validate-navigation.js --fix

# 輸出 Markdown 報告
node validate-navigation.js --report
```

### Close Button Detection (關閉按鈕檢測)

腳本自動檢測以下類型的關閉按鈕，並標記為 **CRITICAL** 問題：

| 檢測方式 | 範例 |
|----------|------|
| SVG X 路徑 | `M6 18L18 6M6 6l12 12` |
| Class 名稱 | `close`, `dismiss`, `exit`, `cancel` |
| X 符號 | `×`, `✕`, `✖` |
| Aria Label | `aria-label="close"`, `aria-label="關閉"` |

**輸出範例：**
```
❌ Line 58: ⚠️ CRITICAL: Close/Exit button has no onclick handler (must navigate back)
```

---

## UI Flow Generation Workflow (強制流程)

### ⚠️ 必須遵循的生成順序

```
Step 1: 畫面規劃 (Screen Planning)
├── 從 SDD 提取所有 SCR-* 畫面清單
├── 為每個畫面定義可點擊元素及其目標
└── 輸出：畫面導航關係矩陣

Step 2: 畫面 HTML 生成 (Screen HTML Generation)
├── 為每個 SCR-* 生成完整 HTML 內容
├── 必須包含實際 UI 元件（非 placeholder）
├── 必須設定所有 onclick/href 導航
└── 使用 templates/screen-types/ 內容模板

Step 3: 可點擊元素驗證 (Clickable Element Validation) ⚠️ 強制自動掃描
├── 執行 validate-navigation.js (無需 puppeteer)
│   └── node ~/.claude/skills/app-uiux-designer.skill/templates/ui-flow/validate-navigation.js --fix
├── 覆蓋率必須 = 100%
├── 所有無效目標必須修正
├── 修復後重新執行驗證 (loop until 100%)
└── ⛔ 驗證失敗時禁止進入 Step 4

Step 4: UI Flow Diagram 生成 (Flow Diagram Generation)
├── ui-flow-diagram.html 使用 iframe 即時預覽
├── 確認所有畫面卡片都顯示實際內容
└── 驗證導航箭頭正確

Step 5: 截圖生成 (Screenshot Generation) ⚠️ 必須
├── 執行 node capture-screenshots.js
├── 複製截圖到 02-design/SDD/images/
└── 驗證所有 SCR-* 都有對應截圖

Step 6: SRS/SDD 回補 (Feedback) ⚠️ 阻斷步驟
├── ⛔ 未完成回補視為 UI Flow 未完成！
├── SDD 更新：
│   ├── 嵌入截圖 (必須)
│   ├── 刪除 Wireframe (必須)
│   ├── 新增 Button Navigation 表格 (必須)
│   └── 新增 Mermaid 流程圖 (必須)
├── SRS 更新：
│   ├── 新增 Screen References 章節 (必須)
│   ├── 新增 Inferred Requirements 章節 (必須)
│   └── 新增 User Flows 章節 (必須)
├── RTM 更新：
│   └── 補充 SRS → SCR 對應 (必須)
└── See: sdd-feedback.md

Step 7: 重新產生 DOCX (Regenerate DOCX)
├── 移除 MD 手動編號
├── 轉換 SRS.md → SRS.docx
└── 轉換 SDD.md → SDD.docx
```

### 禁止行為

| 禁止項目 | 原因 |
|----------|------|
| ❌ 跳過 Step 1-3 直接生成 UI Flow Diagram | 會導致空白預覽 |
| ❌ 使用 placeholder 圖片或圖標替代實際畫面 | 無法驗證 UI 正確性 |
| ❌ 存在無目標的可點擊元素 | 導航斷裂 |
| ❌ 在驗證失敗時強制生成 UI Flow | 違反 100% 覆蓋規則 |
| ❌ `type="submit"` 按鈕無 onclick | 點擊只會觸發表單送出，無導航 |
| ❌ `href="#"` 懸空連結 | 點擊無反應或跳到頁首 |
| ❌ 社群登入按鈕無 onclick | 點擊無反應 |
| ❌ UI Flow Diagram iPhone 模式載入 iPad 畫面 | 必須動態切換 iframe src |
| ❌ 設定列使用 `alert()` 作為點擊動作 | 必須導航到實際子畫面 |
| ❌ 跳過 SRS/SDD 回補步驟 | UI Flow 未完成前不能進行其他任務 |
| ❌ 不嵌入截圖到 SDD | IEC 62304 要求 UI 設計可追溯 |
| ❌ 不更新 SRS Screen References | 需求無法追溯到畫面 |
| ❌ 不重新產生 DOCX | MD 與 DOCX 不同步 |

### UI Flow 預覽方式

**使用 iframe 即時預覽（推薦）：**
- 無需生成截圖
- 即時反映 HTML 變更
- iframe 縮放比例：iPhone `scale(0.305)`, iPad `scale(0.168)`

See: `references/ui-flow-generation-workflow.md`, `references/screen-content-requirements.md`

---

## Workflow Summary

```
1. Receive UI/UX Request
   ↓
2. If Theme Design → Ask App Theme Discovery Questions
   ↓
3. Screen Planning (畫面規劃)
   - Extract SCR-* list from SDD
   - Define clickable elements and targets
   ↓
4. Generate Screen HTML (畫面 HTML 生成)
   - Use templates/screen-types/ content templates
   - Include all UI components (not placeholders)
   ↓
5. Validate Clickable Elements (可點擊元素驗證) ⚠️ 強制自動掃描
   - Run: node validate-navigation.js --fix
   - Must achieve 100% coverage
   - Fix all issues and re-run until 100%
   - ⛔ BLOCKED if validation fails
   ↓
6. Generate UI Flow Diagram (UI Flow 生成)
   - ui-flow-diagram.html with iframe preview
   ↓
7. Generate Screenshots (截圖生成) ⚠️ 必須
   - Run: node capture-screenshots.js
   - Copy to 02-design/SDD/images/
   ↓
8. SRS/SDD Feedback (回補) ⚠️ 阻斷步驟
   ⛔ 未完成回補視為 UI Flow 未完成！
   - SDD: 嵌入截圖、刪除 Wireframe、Button Navigation、Mermaid
   - SRS: Screen References、Inferred Requirements、User Flows
   - RTM: SRS → SCR 對應
   - See: Rule 14 and sdd-feedback.md
   ↓
9. Regenerate DOCX (重新產生 DOCX)
   - 移除 MD 手動編號
   - SRS.md → SRS.docx
   - SDD.md → SDD.docx
```

> **Detailed workflows in reference documents**
