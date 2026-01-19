# UI Flow Generation Workflow (UI Flow 強制生成流程)

本文件定義 UI Flow 生成的完整強制流程，確保所有可點擊元素都有對應的目標畫面。

---

## 1. 流程概覽

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        UI Flow Generation Workflow                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Step 1: 畫面規劃 (Screen Planning)                                          │
│  ├── 從 SDD 提取 SCR-* 清單                                                   │
│  ├── 定義可點擊元素及目標                                                      │
│  └── 輸出：畫面導航關係矩陣                                                    │
│           │                                                                  │
│           ▼                                                                  │
│  Step 2: 畫面 HTML 生成 (Screen HTML Generation)                             │
│  ├── 使用 templates/screen-types/ 模板                                        │
│  ├── 填入完整 UI 內容（非 placeholder）                                        │
│  └── 設定所有 onclick/href                                                    │
│           │                                                                  │
│           ▼                                                                  │
│  Step 3: 可點擊元素驗證 (Clickable Validation)                                │
│  ├── 執行: node capture-screenshots.js --validate-only                       │
│  ├── 檢查覆蓋率 = 100%                                                        │
│  └── ⛔ 失敗時阻止進入 Step 4                                                  │
│           │                                                                  │
│           ├─── ❌ 覆蓋率 < 100% ──→ 返回 Step 2 修正                          │
│           │                                                                  │
│           ▼ ✅ 覆蓋率 = 100%                                                  │
│  Step 4: UI Flow Diagram 生成                                                │
│  ├── ui-flow-diagram.html 使用 iframe 即時預覽                                │
│  └── 驗證所有畫面卡片顯示正確                                                  │
│           │                                                                  │
│           ▼                                                                  │
│  Step 5: SRS/SDD 回補                                                        │
│  └── 按照 sdd-feedback.md 執行                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Step 1: 畫面規劃

### 2.1 從 SDD 提取 SCR-* 清單

```markdown
## 畫面清單範例

| SCR ID | 畫面名稱 | 模組 | 說明 |
|--------|----------|------|------|
| SCR-AUTH-001 | Login | AUTH | 登入頁 |
| SCR-AUTH-002 | Register | AUTH | 註冊頁 |
| SCR-DASH-001 | Home | DASH | 首頁 |
| SCR-SETTING-001 | Settings | SETTING | 設定頁 |
```

### 2.2 定義可點擊元素及目標

為每個畫面列出所有可點擊元素：

```markdown
## SCR-AUTH-001 Login 可點擊元素

| 元素 | 類型 | 目標 | 條件 |
|------|------|------|------|
| 登入按鈕 | Button | SCR-DASH-001 | 驗證成功 |
| 登入按鈕 | Button | 顯示錯誤 | 驗證失敗 |
| 忘記密碼 | Link | SCR-AUTH-003 | - |
| 註冊 | Link | SCR-AUTH-002 | - |
| Google 登入 | Button | SCR-DASH-001 | OAuth 成功 |
| Apple 登入 | Button | SCR-DASH-001 | OAuth 成功 |
```

### 2.3 輸出：畫面導航關係矩陣

```markdown
## 導航關係矩陣

| 來源畫面 | 可點擊元素 | 目標畫面 | 驗證狀態 |
|----------|------------|----------|----------|
| SCR-AUTH-001 | 登入按鈕 | SCR-DASH-001 | ✅ |
| SCR-AUTH-001 | 忘記密碼 | SCR-AUTH-003 | ✅ |
| SCR-AUTH-001 | 註冊 | SCR-AUTH-002 | ✅ |
| SCR-AUTH-002 | 返回 | SCR-AUTH-001 | ✅ |
| SCR-AUTH-002 | 註冊按鈕 | SCR-ONBOARD-001 | ⚠️ 待建立 |
```

---

## 3. Step 2: 畫面 HTML 生成

### 3.1 使用內容模板

```bash
# 複製模板
cp ~/.claude/skills/app-uiux-designer.skill/templates/screen-types/auth/login.html \
   ./04-ui-flow/auth/SCR-AUTH-001-login.html

# 替換變數
sed -i 's/{{PROJECT_NAME}}/MyApp/g' ./04-ui-flow/auth/SCR-AUTH-001-login.html
sed -i 's/{{SCREEN_ID}}/SCR-AUTH-001/g' ./04-ui-flow/auth/SCR-AUTH-001-login.html
```

### 3.2 填入完整 UI 內容

**禁止：**
- 空的 div 或 placeholder
- `onclick=""` 或 `href="#"`
- 文字如「TODO」「待實作」

**必須：**
- 完整的表單元件
- 有效的 onclick/href
- 真實的文字內容

### 3.3 設定所有導航

```html
<!-- 登入按鈕 - 導航到首頁 -->
<button onclick="location.href='../dash/SCR-DASH-001-home.html'">
  登入
</button>

<!-- 忘記密碼連結 -->
<a href="../auth/SCR-AUTH-003-forgot-password.html">
  忘記密碼？
</a>

<!-- 返回按鈕 -->
<button onclick="history.back()">
  返回
</button>
```

---

## 4. Step 3: 可點擊元素驗證

### 4.1 執行驗證

```bash
cd ./04-ui-flow
node capture-screenshots.js --validate-only
```

### 4.2 預期輸出 (成功)

```
============================================================
{{PROJECT_NAME}} UI Flow Screenshot Capture & Validation
============================================================

=== CLICKABLE ELEMENT VALIDATION ===

   Total clickable elements: 45
   Valid targets: 45
   Invalid targets: 0
   Coverage: 100%

   Report saved: validation-report.json

=== NAVIGATION INTEGRITY VALIDATION ===

   Navigation issues found: 0
   ✅ All screens have proper navigation

============================================================
✅ COMPLETE - All validations passed
============================================================
```

### 4.3 預期輸出 (失敗)

```
============================================================
{{PROJECT_NAME}} UI Flow Screenshot Capture & Validation
============================================================

=== CLICKABLE ELEMENT VALIDATION ===

   Total clickable elements: 45
   Valid targets: 42
   Invalid targets: 3
   Coverage: 93%

   INVALID ELEMENTS:
   ❌ auth/SCR-AUTH-001-login.html
      onclick: "../onboard/SCR-ONBOARD-001.html" → target not found
   ❌ auth/SCR-AUTH-002-register.html
      href: "../verify/SCR-VERIFY-001.html" → target not found

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
❌ VALIDATION FAILED: Clickable element coverage < 100%
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

   All invalid targets must be fixed before proceeding.

   Missing screens:
   - ../onboard/SCR-ONBOARD-001.html (referenced from auth/SCR-AUTH-001-login.html)
   - ../verify/SCR-VERIFY-001.html (referenced from auth/SCR-AUTH-002-register.html)

⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔
⛔ UI FLOW GENERATION IS BLOCKED
⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔⛔

   Validation coverage: 93%
   Required coverage: 100%

   To proceed, you must:
   1. Create all missing target screens
   2. Fix all invalid onclick/href targets
   3. Re-run validation: node capture-screenshots.js --validate-only

   WARNING: Using --skip-validation is NOT recommended.
   It violates the 100% clickable element coverage rule.
```

### 4.4 修正缺失畫面

1. **建立缺失的畫面 HTML**
2. **更新導航目標（如果路徑錯誤）**
3. **重新執行驗證**

```bash
# 建立缺失畫面
cp templates/screen-types/common/form-page.html ./onboard/SCR-ONBOARD-001.html
cp templates/screen-types/states/success-state.html ./verify/SCR-VERIFY-001.html

# 重新驗證
node capture-screenshots.js --validate-only
```

---

## 5. Step 4: UI Flow Diagram 生成

### 5.1 使用 iframe 即時預覽

UI Flow Diagram 使用 iframe 顯示實際畫面內容：

```html
<!-- ui-flow-diagram.html 中的畫面卡片 -->
<div class="screen-card module-auth" onclick="openScreen('auth/SCR-AUTH-001-login.html')">
  <div class="ipad-frame">
    <div class="screen-id">AUTH-001</div>
    <iframe src="../auth/SCR-AUTH-001-login.html" loading="lazy"></iframe>
  </div>
  <div class="screen-label">SCR-AUTH-001 Login</div>
</div>
```

### 5.2 iframe 縮放比例

| 裝置 | 原始尺寸 | 卡片尺寸 | 縮放比例 |
|------|----------|----------|----------|
| iPad | 1194×834 | 200×140 | `scale(0.168)` |
| iPhone | 393×852 | 120×260 | `scale(0.305)` |

### 5.3 驗證畫面顯示

確認所有畫面卡片：
- [ ] 顯示實際 UI 內容（非空白）
- [ ] 縮放比例正確
- [ ] 點擊可開啟 device-preview

---

## 6. Step 5: SRS/SDD 回補

### 6.1 SDD 回補

- 更新 Button Navigation 表格
- 嵌入 UI 截圖（如果使用截圖模式）
- 更新 Mermaid 流程圖

### 6.2 SRS 回補

- 新增 Screen References 章節
- 新增 Inferred Requirements (REQ-NAV-*)
- 更新 User Flows (Mermaid)

### 6.3 重新產生 DOCX

```bash
# 規範化 MD
bash ~/.claude/skills/app-requirements-skill/remove-heading-numbers.sh docs/SDD.md
bash ~/.claude/skills/app-requirements-skill/remove-heading-numbers.sh docs/SRS.md

# 轉換 DOCX
node ~/.claude/skills/app-requirements-skill/md-to-docx.js docs/SDD.md docs/SDD.docx
node ~/.claude/skills/app-requirements-skill/md-to-docx.js docs/SRS.md docs/SRS.docx
```

---

## 7. 常見錯誤與修正

| 錯誤 | 原因 | 修正方法 |
|------|------|----------|
| UI Flow 顯示空白卡片 | 畫面 HTML 不存在 | 建立對應的 HTML 檔案 |
| iframe 顯示 404 | 路徑錯誤 | 檢查 src 路徑 |
| 驗證失敗 | onclick/href 目標不存在 | 建立目標畫面或修正路徑 |
| 無法點擊畫面卡片 | pointer-events 設定 | 確認 iframe 有 `pointer-events: none` |
| 縮放比例錯誤 | CSS transform 設定 | 檢查 CSS scale 值 |

---

## 8. 工具命令參考

| 命令 | 說明 |
|------|------|
| `node capture-screenshots.js --validate-only` | 僅執行驗證 |
| `node capture-screenshots.js` | 驗證 + 截圖 |
| `node capture-screenshots.js --skip-validation` | 跳過驗證（不建議） |

---

## 9. 檢查清單

### 生成前檢查

- [ ] SDD 中所有 SCR-* 都有對應的 HTML 檔案
- [ ] 每個 HTML 包含完整 UI 內容
- [ ] 所有 onclick/href 指向存在的畫面
- [ ] 執行 `--validate-only` 通過
- [ ] 覆蓋率 = 100%

### 生成後檢查

- [ ] UI Flow Diagram 所有卡片顯示正確
- [ ] 點擊卡片可開啟 device-preview
- [ ] 不同裝置模式 (iPad/iPhone) 正常
- [ ] SRS/SDD 已回補
- [ ] DOCX 已重新產生

---

> **See also:**
> - `screen-content-requirements.md` - 畫面內容要求
> - `coverage-validation.md` - 覆蓋驗證詳細規則
> - `sdd-feedback.md` - SRS/SDD 回補流程
