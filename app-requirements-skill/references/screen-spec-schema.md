# Screen Specification Schema

本文件定義 SDD 中 SCR-* 區塊的結構化格式，讓 app-uiux-designer.skill 可直接套用 template 產出 UI Flow，無需預測。

---

## Quick Reference

### SDD SCR-* 區塊最小格式

```markdown
## SCR-{MODULE}-{NNN}-{name}: {中文名稱}

**Screen Type:** {screen_type}
**Template:** {template_path}
**Module:** {MODULE}
**Priority:** P{0-2}

### Navigation
| Source | Target | Trigger |
|--------|--------|---------|
| SCR-AUTH-001 | this | 點擊註冊連結 |
| this | SCR-DASH-001 | 註冊成功 |
| this | SCR-AUTH-001 | 點擊返回 |

### UI Elements
| ID | Type | Label | Action | Target |
|----|------|-------|--------|--------|
| email | TextField | 電子郵件 | - | - |
| password | SecureField | 密碼 | - | - |
| submit | Button.Primary | 註冊 | Submit | SCR-DASH-001 |
| back | Button.Text | 返回登入 | Navigate | SCR-AUTH-001 |
```

---

## Screen Types (畫面類型)

每個 Screen Type 對應到 app-uiux-designer.skill 的特定 template。

| Screen Type | Template Path | 說明 | 必要元素 |
|-------------|---------------|------|----------|
| `auth.login` | `screen-types/auth/login.html` | 登入頁 | email, password, submit, forgot, register |
| `auth.register` | `screen-types/auth/register.html` | 註冊頁 | name, email, password, confirm, terms, submit |
| `auth.forgot-password` | `screen-types/auth/forgot-password.html` | 忘記密碼 | email, submit, back |
| `auth.forgot-sent` | `screen-types/auth/forgot-sent.html` | 已發送確認 | icon, message, resend, back |
| `auth.reset-password` | `screen-types/auth/reset-password.html` | 重設密碼 | password, confirm, submit |
| `auth.verify-email` | `screen-types/auth/verify-email.html` | Email 驗證 | icon, message, resend, change |
| `auth.role-select` | `screen-types/auth/role-select.html` | 角色選擇 | roles[], submit |
| `dash.home` | `screen-types/dash/home.html` | 首頁 | header, content, tabbar |
| `dash.dashboard` | `screen-types/dash/dashboard.html` | 儀表板 | stats[], charts[], actions[] |
| `list.standard` | `screen-types/list/standard.html` | 標準列表 | header, items[], empty_state |
| `list.grid` | `screen-types/list/grid.html` | 網格列表 | header, items[], filter |
| `detail.standard` | `screen-types/detail/standard.html` | 詳情頁 | header, image, content, cta |
| `form.standard` | `screen-types/form/standard.html` | 標準表單 | header, fields[], submit |
| `form.multi-step` | `screen-types/form/multi-step.html` | 多步驟表單 | steps[], progress, nav |
| `setting.main` | `screen-types/setting/main.html` | 設定主頁 | sections[], items[], logout |
| `setting.toggle-list` | `screen-types/setting/toggle-list.html` | Toggle 列表 | items[] with toggles |
| `setting.radio-list` | `screen-types/setting/radio-list.html` | 單選列表 | items[] with radio |
| `profile.view` | `screen-types/profile/view.html` | 個人檔案檢視 | avatar, info, actions[] |
| `profile.edit` | `screen-types/profile/edit.html` | 個人檔案編輯 | avatar_upload, fields[] |
| `state.empty` | `screen-types/state/empty.html` | 空狀態 | icon, title, description, cta |
| `state.error` | `screen-types/state/error.html` | 錯誤狀態 | icon, title, description, retry |
| `state.loading` | `screen-types/state/loading.html` | 載入中 | spinner, message |
| `state.success` | `screen-types/state/success.html` | 成功狀態 | icon, title, description, cta |

---

## UI Element Types (UI 元素類型)

### Input Elements

| Type | HTML 對應 | 屬性 |
|------|----------|------|
| `TextField` | `<input type="text">` | placeholder, validation |
| `TextField.Email` | `<input type="email">` | placeholder, validation |
| `TextField.Phone` | `<input type="tel">` | placeholder, format |
| `SecureField` | `<input type="password">` | placeholder, showToggle |
| `TextArea` | `<textarea>` | placeholder, rows |
| `NumberField` | `<input type="number">` | min, max, step |
| `DatePicker` | Date picker | minDate, maxDate |
| `TimePicker` | Time picker | format |
| `Select` | `<select>` | options[] |
| `Checkbox` | `<input type="checkbox">` | label |
| `Radio` | `<input type="radio">` | options[] |
| `Toggle` | Toggle switch | - |
| `Slider` | Range slider | min, max, step |
| `SearchField` | Search input | placeholder |

### Button Elements

| Type | 樣式 | 用途 |
|------|------|------|
| `Button.Primary` | 主要按鈕 (填色) | 主要 CTA |
| `Button.Secondary` | 次要按鈕 (邊框) | 次要動作 |
| `Button.Text` | 文字按鈕 | 連結樣式 |
| `Button.Icon` | 圖示按鈕 | 工具列 |
| `Button.Floating` | FAB | 主要新增動作 |
| `Button.Social.Apple` | Apple 登入 | 社群登入 |
| `Button.Social.Google` | Google 登入 | 社群登入 |
| `Button.Social.Facebook` | Facebook 登入 | 社群登入 |

### Display Elements

| Type | 說明 |
|------|------|
| `Text.Title` | 大標題 |
| `Text.Subtitle` | 副標題 |
| `Text.Body` | 內文 |
| `Text.Caption` | 說明文字 |
| `Text.Link` | 可點擊連結 |
| `Image` | 圖片 |
| `Icon` | SF Symbol / Material Icon |
| `Avatar` | 圓形頭像 |
| `Badge` | 徽章/標籤 |
| `Divider` | 分隔線 |
| `Spacer` | 間距 |

### Container Elements

| Type | 說明 |
|------|------|
| `Card` | 卡片容器 |
| `Section` | 區塊 |
| `List` | 列表容器 |
| `ListItem` | 列表項目 |
| `Grid` | 網格容器 |
| `TabBar` | 底部 Tab |
| `Header` | 頂部導航列 |
| `BottomSheet` | 底部彈出 |
| `Modal` | 對話框 |

---

## Action Types (動作類型)

| Action | 說明 | 參數 |
|--------|------|------|
| `Navigate` | 導航到畫面 | Target: SCR-* |
| `Submit` | 提交表單 | Target: SCR-* (成功後) |
| `Back` | 返回上一頁 | - |
| `Dismiss` | 關閉 Modal/Sheet | - |
| `External` | 開啟外部連結 | URL |
| `Call` | 撥打電話 | PhoneNumber |
| `Email` | 發送郵件 | EmailAddress |
| `Share` | 分享 | - |
| `Copy` | 複製到剪貼簿 | - |
| `Refresh` | 重新載入 | - |
| `LoadMore` | 載入更多 | - |
| `Toggle` | 切換狀態 | - |
| `Select` | 選擇項目 | - |
| `Delete` | 刪除 | Confirm: true/false |
| `Logout` | 登出 | Target: SCR-AUTH-001 |

---

## Complete SDD Screen Spec Example

### 完整範例：登入畫面

```markdown
## SCR-AUTH-001-login: 登入畫面

**Screen Type:** auth.login
**Template:** screen-types/auth/login.html
**Module:** AUTH
**Priority:** P0
**Related Requirements:** REQ-AUTH-001, REQ-AUTH-002

### Description
使用者登入畫面，支援 Email/密碼登入與社群登入。

### Navigation

| Direction | Screen | Trigger | Condition |
|-----------|--------|---------|-----------|
| ← From | SCR-LAUNCH-001 | App 啟動 | 未登入 |
| → To | SCR-DASH-001 | 登入成功 | 驗證通過 |
| → To | SCR-AUTH-002 | 點擊註冊 | - |
| → To | SCR-AUTH-003 | 點擊忘記密碼 | - |
| ↔ State | Error | 登入失敗 | 驗證錯誤 |

### UI Elements

| ID | Type | Label | Placeholder | Validation | Action | Target |
|----|------|-------|-------------|------------|--------|--------|
| logo | Image | - | - | - | - | - |
| title | Text.Title | 歡迎回來 | - | - | - | - |
| email | TextField.Email | 電子郵件 | 請輸入 Email | email_format | - | - |
| password | SecureField | 密碼 | 請輸入密碼 | min_length:8 | - | - |
| remember | Checkbox | 記住我 | - | - | - | - |
| submit | Button.Primary | 登入 | - | - | Submit | SCR-DASH-001 |
| forgot | Button.Text | 忘記密碼？ | - | - | Navigate | SCR-AUTH-003 |
| divider | Divider | 或使用以下方式登入 | - | - | - | - |
| apple | Button.Social.Apple | 使用 Apple 登入 | - | - | Submit | SCR-DASH-001 |
| google | Button.Social.Google | 使用 Google 登入 | - | - | Submit | SCR-DASH-001 |
| register | Button.Text | 還沒有帳號？註冊 | - | - | Navigate | SCR-AUTH-002 |

### Layout Structure

```
┌─────────────────────────────────────────┐
│                 HEADER                   │ (Logo + Title)
├─────────────────────────────────────────┤
│                                          │
│  ┌────────────────────────────────────┐ │
│  │ email                               │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ password                     [👁]  │ │
│  └────────────────────────────────────┘ │
│                                          │
│  [remember]              [forgot →]     │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │           登入 (submit)            │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ──────────── 或 ────────────           │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │ 🍎 使用 Apple 登入                 │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ G  使用 Google 登入                │ │
│  └────────────────────────────────────┘ │
│                                          │
│          還沒有帳號？註冊               │
│                                          │
└─────────────────────────────────────────┘
```

### States

| State | Trigger | UI Changes |
|-------|---------|------------|
| Default | 初始載入 | 所有欄位空白 |
| Loading | 點擊登入 | submit 按鈕 disabled + spinner |
| Error | 驗證失敗 | 顯示錯誤訊息、email/password 紅框 |
| Success | 驗證成功 | 導航至 SCR-DASH-001 |

### Error Messages

| Error | Message |
|-------|---------|
| INVALID_EMAIL | 請輸入有效的 Email 地址 |
| WRONG_PASSWORD | 密碼錯誤，請重試 |
| USER_NOT_FOUND | 此帳號尚未註冊 |
| ACCOUNT_LOCKED | 帳號已鎖定，請稍後再試 |
| NETWORK_ERROR | 網路連線失敗，請檢查網路設定 |
```

---

## Integration Workflow

### app-requirements-skill 產出 SDD 時

1. **識別畫面類型** → 從 Screen Types 表選擇
2. **指定 Template** → 對應的 template 路徑
3. **定義 Navigation** → 來源/目標畫面
4. **列出 UI Elements** → 使用標準 Type
5. **指定 Actions** → 使用標準 Action Types
6. **描述 States** → Loading/Error/Success

### app-uiux-designer.skill 產出 UI Flow 時

1. **讀取 Screen Type** → 載入對應 template
2. **套用 UI Elements** → 替換 template 變數
3. **設定 Navigation** → 產生 onclick/href
4. **產生 States** → 產生各狀態變體
5. **套用 Theme** → 使用專案 Design Token

```
app-requirements-skill                app-uiux-designer.skill
┌────────────────────┐               ┌────────────────────┐
│ SDD with           │               │                    │
│ Screen Spec Schema │ ─────────────▶│ Load Template      │
│                    │               │ ↓                  │
│ Screen Type: X     │               │ Replace Variables  │
│ Template: path     │               │ ↓                  │
│ UI Elements: [...]  │               │ Set Navigation     │
│ Navigation: [...]   │               │ ↓                  │
│ States: [...]       │               │ Generate HTML      │
└────────────────────┘               └────────────────────┘
                                              ↓
                                     ┌────────────────────┐
                                     │ 04-ui-flow/        │
                                     │ ├ auth/            │
                                     │ │ └ SCR-AUTH-001.html│
                                     │ └ iphone/          │
                                     │   └ SCR-AUTH-001.html│
                                     └────────────────────┘
```

---

## Validation Checklist

app-requirements-skill 產出 SDD 前驗證：

```
☐ 每個 SCR-* 區塊都有 Screen Type
☐ 每個 SCR-* 區塊都有 Template 路徑
☐ 每個 UI Element 都使用標準 Type
☐ 每個 Action 都使用標準 Action Type
☐ 每個 Navigate Action 都有有效的 Target SCR-*
☐ Navigation 表格覆蓋所有進出畫面
☐ States 包含 Default/Loading/Error (如適用)
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-12 | 初版 - Screen Spec Schema 定義 |
