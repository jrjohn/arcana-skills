# 通用模組 HTML 模板 (Common Modules HTML Templates)

供所有 App 專案使用的**必要模組** HTML 模板。

---

## 模板索引

### AUTH 模組 (認證)

| 檔案 | 畫面類型 | 必要性 |
|------|----------|--------|
| `auth/SCR-AUTH-login.html` | 登入 | **必要** |
| `auth/SCR-AUTH-register.html` | 註冊 | **必要** |
| `auth/SCR-AUTH-forgot.html` | 忘記密碼 | **必要** |

### PROFILE 模組 (個人檔案)

| 檔案 | 畫面類型 | 必要性 |
|------|----------|--------|
| `profile/SCR-PROFILE-view.html` | 個人檔案查看 | **必要** |
| `profile/SCR-PROFILE-edit.html` | 個人檔案編輯 | **必要** |

### SETTING 模組 (設定)

| 檔案 | 畫面類型 | 必要性 |
|------|----------|--------|
| `setting/SCR-SETTING-main.html` | 設定主頁 | **必要** |
| `setting/SCR-SETTING-account.html` | 帳戶設定 | **必要** |
| `setting/SCR-SETTING-privacy.html` | 隱私設定 | **必要** |
| `setting/SCR-SETTING-about.html` | 關於 | **必要** |

### COMMON 模組 (共用狀態)

| 檔案 | 畫面類型 | 必要性 |
|------|----------|--------|
| `common/SCR-COMMON-loading.html` | 載入中狀態 | **必要** |
| `common/SCR-COMMON-empty.html` | 空狀態 | **必要** |
| `common/SCR-COMMON-error.html` | 錯誤狀態 | **必要** |
| `common/SCR-COMMON-no-network.html` | 無網路狀態 | **必要** |

---

## 模板變數

所有模板使用 `{{VARIABLE_NAME}}` 格式的變數，在複製到專案時需替換。

### 通用變數

| 變數 | 說明 | 範例 |
|------|------|------|
| `{{PROJECT_NAME}}` | 專案名稱 | VocabMaster |
| `{{PRIMARY_COLOR}}` | 主色 (HEX) | #00BFA5 |
| `{{SECONDARY_COLOR}}` | 輔色 (HEX) | #4FC3F7 |
| `{{ACCENT_COLOR}}` | 強調色 (HEX) | #FFD54F |
| `{{APP_EMOJI}}` | App 圖示 Emoji | 📚 |

### 畫面編號變數

| 變數 | 說明 | 範例 |
|------|------|------|
| `{{NUM_LOGIN}}` | 登入畫面編號 | 002 |
| `{{NUM_REGISTER}}` | 註冊畫面編號 | 003 |
| `{{NUM_FORGOT}}` | 忘記密碼編號 | 004 |
| `{{NUM_MAIN}}` | 設定主頁編號 | 001 |
| ...等 | 依專案而定 | - |

---

## 使用方式

### 1. 初始化時複製

在 `00-init` 階段自動複製這些模板到專案：

```bash
# 複製必要模組模板
cp -r ~/.claude/skills/app-uiux-designer.skill/templates/common-modules/* \
      {PROJECT}/04-ui-flow/
```

### 2. 替換變數

根據專案設定替換所有 `{{VARIABLE}}` 變數：

```bash
# 範例：替換專案名稱
sed -i '' 's/{{PROJECT_NAME}}/VocabMaster/g' *.html
```

### 3. 調整畫面編號

根據 SDD 的 SCR 編號調整模板中的導航路徑。

---

## 驗證檢核

### 必要模組存在檢核

```bash
#!/bin/bash
# === 必要模組 HTML 檢核 ===

REQUIRED=(
  "auth/SCR-AUTH-*-login.html"
  "auth/SCR-AUTH-*-register.html"
  "auth/SCR-AUTH-*-forgot.html"
  "profile/SCR-PROFILE-*-view.html"
  "profile/SCR-PROFILE-*-edit.html"
  "setting/SCR-SETTING-*-main.html"
  "setting/SCR-SETTING-*-account.html"
  "setting/SCR-SETTING-*-privacy.html"
  "setting/SCR-SETTING-*-about.html"
  "common/SCR-COMMON-*-loading.html"
  "common/SCR-COMMON-*-empty.html"
  "common/SCR-COMMON-*-error.html"
  "common/SCR-COMMON-*-no-network.html"
)

ERRORS=0
for PATTERN in "${REQUIRED[@]}"; do
  COUNT=$(ls $PATTERN 2>/dev/null | wc -l)
  if [ "$COUNT" -eq 0 ]; then
    echo "❌ 缺少: $PATTERN"
    ERRORS=$((ERRORS+1))
  else
    echo "✅ 存在: $PATTERN"
  fi
done

[ $ERRORS -eq 0 ] && echo "✅ 必要模組 HTML 檢核通過" || echo "❌ 缺少 $ERRORS 個必要模組"
```

---

## 來源

本模板基於 VocabMaster 專案提取，符合 iOS Human Interface Guidelines 和 Material Design 3 規範。
