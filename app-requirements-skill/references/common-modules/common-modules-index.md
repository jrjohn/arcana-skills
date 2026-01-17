# 通用模組索引 (Common Modules Index)

所有 App 專案的**必要模組**定義。智慧預測時優先載入這些模組，確保基礎功能完整。

---

## 必要模組清單

| 模組 | 代碼 | 必要性 | 最少畫面數 | 說明 |
|------|------|--------|-----------|------|
| 認證模組 | AUTH | **必要** | 3 | 登入、註冊、忘記密碼 |
| 個人檔案模組 | PROFILE | **必要** | 2 | 查看、編輯個人資料 |
| 設定模組 | SETTING | **必要** | 4 | 主頁、帳戶、隱私、關於 |
| 共用狀態模組 | COMMON | **必要** | 4 | loading、empty、error、no-network |

---

## 模板檔案索引

| 模板檔案 | 說明 | 內容 |
|----------|------|------|
| `auth-module-template.md` | AUTH 模組 | 8 個標準畫面定義 |
| `profile-module-template.md` | PROFILE 模組 | 3 個標準畫面定義 |
| `setting-module-template.md` | SETTING 模組 | 18 個標準畫面定義 |
| `common-states-template.md` | COMMON 模組 | 5 個狀態畫面定義 |

---

## 智慧預測優先順序

```
1️⃣ 必要模組 (common-modules/)
   └── AUTH, PROFILE, SETTING, COMMON

2️⃣ App 類型需求 (按關鍵字自動載入)
   ├── education-requirements.md
   ├── ecommerce-requirements.md
   ├── social-requirements.md
   ├── healthcare-requirements.md
   └── productivity-requirements.md

3️⃣ Button Navigation 分析
   └── 導航缺口自動識別

4️⃣ 命名約定推測
   └── 詳情頁、編輯頁、確認頁
```

---

## 必要模組檢核腳本

```bash
#!/bin/bash
# === 必要模組檢核 (BLOCKING) ===
# 執行時機：Step 4 智慧預測完成後

REQUIRED_MODULES=("AUTH" "PROFILE" "SETTING" "COMMON")
SDD_FILE="02-design/SDD-*.md"

echo "🔍 檢核必要模組..."

ERRORS=0
for MODULE in "${REQUIRED_MODULES[@]}"; do
  COUNT=$(grep -c "^#### SCR-${MODULE}-" $SDD_FILE 2>/dev/null || echo "0")
  if [ "$COUNT" -eq 0 ]; then
    echo "❌ 缺少必要模組: $MODULE"
    ERRORS=$((ERRORS+1))
  else
    echo "✅ $MODULE: $COUNT 個畫面"
  fi
done

# COMMON 狀態畫面特別檢核
echo ""
echo "🔍 檢核 COMMON 狀態畫面..."
COMMON_STATES=("loading" "empty" "error" "no-network")
for STATE in "${COMMON_STATES[@]}"; do
  if grep -q "SCR-COMMON-.*-${STATE}" $SDD_FILE 2>/dev/null; then
    echo "✅ COMMON 狀態: $STATE"
  else
    echo "❌ 缺少 COMMON 狀態: $STATE"
    ERRORS=$((ERRORS+1))
  fi
done

echo ""
if [ $ERRORS -eq 0 ]; then
  echo "✅ 必要模組檢核通過"
else
  echo "❌ 必要模組檢核失敗 ($ERRORS 個錯誤)"
  echo "⚠️ 請參考 common-modules/ 模板補充缺少的模組"
  exit 1
fi
```

---

## 必要模組最低要求

### AUTH 模組最低要求（3 畫面）

| 必要 | 畫面 ID | 名稱 |
|------|---------|------|
| ✅ | SCR-AUTH-*-login | 登入 |
| ✅ | SCR-AUTH-*-register | 註冊 |
| ✅ | SCR-AUTH-*-forgot | 忘記密碼 |

### PROFILE 模組最低要求（2 畫面）

| 必要 | 畫面 ID | 名稱 |
|------|---------|------|
| ✅ | SCR-PROFILE-*-view | 個人檔案查看 |
| ✅ | SCR-PROFILE-*-edit | 個人檔案編輯 |

### SETTING 模組最低要求（4 畫面）

| 必要 | 畫面 ID | 名稱 |
|------|---------|------|
| ✅ | SCR-SETTING-*-main | 設定主頁 |
| ✅ | SCR-SETTING-*-account | 帳戶設定 |
| ✅ | SCR-SETTING-*-privacy | 隱私設定 |
| ✅ | SCR-SETTING-*-about | 關於 |

### COMMON 模組最低要求（4 畫面）

| 必要 | 畫面 ID | 名稱 |
|------|---------|------|
| ✅ | SCR-COMMON-*-loading | 載入中狀態 |
| ✅ | SCR-COMMON-*-empty | 空狀態 |
| ✅ | SCR-COMMON-*-error | 錯誤狀態 |
| ✅ | SCR-COMMON-*-no-network | 無網路狀態 |

---

## 使用方式

### 在 SDD 撰寫時

1. 先載入 `common-modules-index.md` 確認必要模組
2. 複製對應模組模板到 SDD
3. 根據專案需求調整畫面細節
4. 執行檢核腳本確認完整性

### 在 UI Flow 生成時

1. `app-uiux-designer.skill` 會自動複製 `templates/common-modules/` 的 HTML
2. 根據 SDD Button Navigation 調整導航
3. 執行 Template Compliance Gate 驗證
