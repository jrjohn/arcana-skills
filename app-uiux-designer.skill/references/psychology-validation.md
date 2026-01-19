# UI 心理學驗證指南

驗證 UI 設計是否符合設計心理學原則，與 `app-requirements-skill` 的心理學規範整合。

## 目錄
1. [驗證原則](#驗證原則)
2. [自動化驗證規則](#自動化驗證規則)
3. [驗證流程](#驗證流程)
4. [報告格式](#報告格式)

---

## 驗證原則

### 原則來源

驗證規則整合自 `app-requirements-skill` 的三份心理學文件：

| 文件 | 路徑 | 主要原則 |
|------|------|----------|
| 設計心理學 | `references/design-psychology.md` | 認知負荷、Fitts' Law、Hick's Law |
| 認知心理學 | `references/cognitive-psychology.md` | 心智模型、錯誤預防、回饋 |
| 文件編排心理學 | `references/document-layout-psychology.md` | F 型閱讀、視覺層級 |

---

## 自動化驗證規則

### 1. 認知負荷 (Cognitive Load)

**原則：** 避免資訊過載，降低使用者認知負擔

**驗證規則：**

```javascript
const cognitivLoadRules = {
  // 單頁主要按鈕數量
  maxPrimaryButtons: 3,

  // 單頁總互動元素數量
  maxInteractiveElements: 15,

  // 表單欄位數量 (單頁)
  maxFormFields: 7,

  // 選項數量 (Radio/Checkbox)
  maxOptions: 7,

  // Tab/Segment 數量
  maxTabs: 5
};

function validateCognitiveLoad(html) {
  const issues = [];

  // 計算按鈕數量
  const primaryButtons = html.querySelectorAll('button.primary, button[type="submit"], .btn-primary');
  if (primaryButtons.length > cognitivLoadRules.maxPrimaryButtons) {
    issues.push({
      rule: 'cognitive-load',
      severity: 'warning',
      message: `主要按鈕過多 (${primaryButtons.length} > ${cognitivLoadRules.maxPrimaryButtons})`,
      suggestion: '考慮減少主要按鈕或使用階層式選單'
    });
  }

  // 計算表單欄位
  const formFields = html.querySelectorAll('input, select, textarea');
  if (formFields.length > cognitivLoadRules.maxFormFields) {
    issues.push({
      rule: 'cognitive-load',
      severity: 'warning',
      message: `單頁表單欄位過多 (${formFields.length} > ${cognitivLoadRules.maxFormFields})`,
      suggestion: '考慮分步驟表單 (Multi-step Form)'
    });
  }

  return issues;
}
```

### 2. Fitts' Law

**原則：** 目標越大、越近，越容易點擊

**驗證規則：**

```javascript
const fittsLawRules = {
  // 最小觸控目標大小 (px)
  minTouchTarget: 44,

  // 主要按鈕最小寬度
  minPrimaryButtonWidth: 120,

  // 主要按鈕最小高度
  minPrimaryButtonHeight: 44,

  // 危險按鈕與主要按鈕的最小間距
  minDangerButtonDistance: 100
};

function validateFittsLaw(html, styles) {
  const issues = [];

  // 檢查按鈕大小
  const buttons = html.querySelectorAll('button, a.btn, [role="button"]');
  buttons.forEach(btn => {
    const rect = btn.getBoundingClientRect();
    const minDimension = Math.min(rect.width, rect.height);

    if (minDimension < fittsLawRules.minTouchTarget) {
      issues.push({
        rule: 'fitts-law',
        element: btn.id || btn.className,
        severity: 'error',
        message: `按鈕過小 (${minDimension}px < ${fittsLawRules.minTouchTarget}px)`,
        suggestion: '增加按鈕尺寸至最少 44x44px'
      });
    }
  });

  return issues;
}
```

### 3. Hick's Law

**原則：** 選項越多，決策時間越長

**驗證規則：**

```javascript
const hicksLawRules = {
  // 主選單項目最大數量
  maxMenuItems: 7,

  // 底部導航 Tab 最大數量
  maxBottomNavItems: 5,

  // 選項按鈕最大數量
  maxChoiceButtons: 4,

  // 下拉選單建議顯示數量
  recommendedDropdownVisible: 5
};

function validateHicksLaw(html) {
  const issues = [];

  // 檢查選項數量
  const radioGroups = html.querySelectorAll('[role="radiogroup"], .radio-group');
  radioGroups.forEach(group => {
    const options = group.querySelectorAll('input[type="radio"], .radio-option');
    if (options.length > hicksLawRules.maxMenuItems) {
      issues.push({
        rule: 'hicks-law',
        severity: 'warning',
        message: `選項過多 (${options.length} > ${hicksLawRules.maxMenuItems})`,
        suggestion: '考慮分類或使用搜尋功能'
      });
    }
  });

  // 檢查底部導航
  const bottomNav = html.querySelector('.bottom-nav, [role="tablist"]');
  if (bottomNav) {
    const tabs = bottomNav.querySelectorAll('a, button, [role="tab"]');
    if (tabs.length > hicksLawRules.maxBottomNavItems) {
      issues.push({
        rule: 'hicks-law',
        severity: 'warning',
        message: `底部導航項目過多 (${tabs.length} > ${hicksLawRules.maxBottomNavItems})`,
        suggestion: '考慮使用 "更多" 選單收納次要項目'
      });
    }
  }

  return issues;
}
```

### 4. 漸進式揭露 (Progressive Disclosure)

**原則：** 逐步呈現資訊，避免一次顯示過多

**驗證規則：**

```javascript
const progressiveDisclosureRules = {
  // 多步驟流程應有進度指示器
  requireProgressIndicator: true,

  // 折疊區塊應有展開/收合控制
  requireCollapseControl: true,

  // 長列表應有分頁或無限滾動
  maxListItemsWithoutPagination: 20
};

function validateProgressiveDisclosure(html, screenId) {
  const issues = [];

  // 檢查多步驟流程是否有進度指示器
  const isMultiStepScreen = /step|wizard|onboard/i.test(screenId);
  if (isMultiStepScreen) {
    const progressIndicator = html.querySelector('.progress, .stepper, [role="progressbar"]');
    if (!progressIndicator) {
      issues.push({
        rule: 'progressive-disclosure',
        severity: 'warning',
        message: '多步驟流程缺少進度指示器',
        suggestion: '新增 Stepper 或 Progress Bar 元件'
      });
    }
  }

  // 檢查長列表
  const lists = html.querySelectorAll('ul, ol, .list');
  lists.forEach(list => {
    const items = list.querySelectorAll('li, .list-item');
    if (items.length > progressiveDisclosureRules.maxListItemsWithoutPagination) {
      const hasPagination = html.querySelector('.pagination, .load-more');
      if (!hasPagination) {
        issues.push({
          rule: 'progressive-disclosure',
          severity: 'info',
          message: `長列表 (${items.length} 項) 無分頁`,
          suggestion: '考慮新增分頁或 "載入更多" 功能'
        });
      }
    }
  });

  return issues;
}
```

### 5. 前置條件 (Prerequisite Flow)

**原則：** 確保流程順序合理，使用者有足夠上下文

**驗證規則：**

```javascript
const prerequisiteRules = {
  // 必須先經過 Dashboard 才能進入訓練
  dashboardBeforeTraining: true,

  // 必須先配對裝置才能使用裝置功能
  devicePairingFirst: true,

  // Onboarding 必須在首次使用時完成
  onboardingFirst: true
};

function validatePrerequisiteFlow(navigations) {
  const issues = [];

  // 建立導航圖
  const navGraph = buildNavigationGraph(navigations);

  // 檢查訓練模組是否可從非 Dashboard 直接進入
  const trainingScreens = navigations.filter(n => n.target.includes('TRAIN'));
  for (const nav of trainingScreens) {
    if (!nav.source.includes('DASH') && !nav.source.includes('TRAIN')) {
      issues.push({
        rule: 'prerequisite',
        severity: 'warning',
        message: `${nav.target} 可從 ${nav.source} 直接進入，可能跳過 Dashboard`,
        suggestion: '確認使用者是否已具備足夠上下文'
      });
    }
  }

  return issues;
}
```

### 6. 錯誤預防 (Error Prevention)

**原則：** 預防勝於治療，危險操作需確認

**驗證規則：**

```javascript
const errorPreventionRules = {
  // 危險操作關鍵字
  dangerousActions: ['刪除', '移除', '重置', '登出', 'delete', 'remove', 'reset', 'logout'],

  // 需要確認的操作
  requireConfirmation: ['刪除', '移除', '重置', 'delete', 'remove', 'reset'],

  // 不可逆操作需要輸入確認
  requireInputConfirmation: ['刪除帳號', '清除資料']
};

function validateErrorPrevention(html) {
  const issues = [];

  // 找出危險按鈕
  const buttons = html.querySelectorAll('button, a.btn');
  buttons.forEach(btn => {
    const text = btn.textContent.toLowerCase();
    const isDangerous = errorPreventionRules.dangerousActions.some(d => text.includes(d.toLowerCase()));

    if (isDangerous) {
      // 檢查是否有 data-confirm 或 modal 觸發
      const hasConfirm = btn.hasAttribute('data-confirm') ||
                         btn.getAttribute('onclick')?.includes('confirm') ||
                         btn.getAttribute('data-bs-toggle') === 'modal';

      if (!hasConfirm) {
        issues.push({
          rule: 'error-prevention',
          element: btn.id || btn.textContent,
          severity: 'error',
          message: `危險操作「${btn.textContent.trim()}」缺少確認機制`,
          suggestion: '新增確認對話框或 data-confirm 屬性'
        });
      }
    }
  });

  return issues;
}
```

### 7. 回饋 (Feedback)

**原則：** 操作後立即給予使用者回饋

**驗證規則：**

```javascript
const feedbackRules = {
  // 表單提交應有 Loading 狀態
  formSubmitLoading: true,

  // 操作完成應有 Toast/Snackbar
  actionCompleteFeedback: true,

  // 錯誤應有明確訊息
  errorMessage: true
};

function validateFeedback(html, hasLoadingState) {
  const issues = [];

  // 檢查表單是否有 Loading 狀態
  const forms = html.querySelectorAll('form');
  forms.forEach(form => {
    const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
    if (submitBtn && !hasLoadingState) {
      const hasLoadingIndicator = form.querySelector('.loading, .spinner, [role="progressbar"]');
      if (!hasLoadingIndicator) {
        issues.push({
          rule: 'feedback',
          severity: 'info',
          message: '表單缺少 Loading 狀態',
          suggestion: '新增提交時的 Loading 指示器'
        });
      }
    }
  });

  return issues;
}
```

---

## 驗證流程

```
┌─────────────────────────────────────────────────────────────┐
│                     心理學驗證流程                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 掃描 generated-ui/ 目錄                                 │
│     │                                                       │
│     ▼                                                       │
│  2. 解析每個 HTML 檔案                                       │
│     ├── DOM 結構分析                                        │
│     ├── CSS 樣式提取                                        │
│     └── Button Navigation 解析                              │
│     │                                                       │
│     ▼                                                       │
│  3. 執行驗證規則                                            │
│     ├── 認知負荷驗證                                        │
│     ├── Fitts' Law 驗證                                     │
│     ├── Hick's Law 驗證                                     │
│     ├── 漸進式揭露驗證                                      │
│     ├── 前置條件驗證                                        │
│     ├── 錯誤預防驗證                                        │
│     └── 回饋驗證                                            │
│     │                                                       │
│     ▼                                                       │
│  4. 彙整問題                                                │
│     ├── 按嚴重度分類 (error/warning/info)                   │
│     └── 按畫面分類                                          │
│     │                                                       │
│     ▼                                                       │
│  5. 產生報告                                                │
│     ├── 摘要表格                                            │
│     ├── 詳細問題清單                                        │
│     └── 修正建議                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 報告格式

### 完整驗證報告

```markdown
# UI 心理學驗證報告

## 執行資訊
| 項目 | 值 |
|------|-----|
| 執行時間 | 2024-XX-XX HH:MM |
| 驗證目錄 | ./generated-ui/ |
| 畫面數量 | 51 |
| 規則數量 | 7 |

## 驗證摘要

| 原則 | 通過 | 警告 | 錯誤 | 狀態 |
|------|------|------|------|------|
| 認知負荷 | 48 | 3 | 0 | ⚠️ |
| Fitts' Law | 49 | 1 | 1 | ❌ |
| Hick's Law | 51 | 0 | 0 | ✅ |
| 漸進式揭露 | 47 | 4 | 0 | ⚠️ |
| 前置條件 | 51 | 0 | 0 | ✅ |
| 錯誤預防 | 50 | 0 | 1 | ❌ |
| 回饋 | 45 | 6 | 0 | ⚠️ |

**總體評分：** 85/100 (良好，需改善 2 個錯誤)

## 必須修正 (Error)

### 1. SCR-SETTING-003 - Fitts' Law 違規

**問題：** 「刪除帳號」按鈕過小
- 當前尺寸：32x32 px
- 最小要求：44x44 px

**建議修正：**
```css
.btn-delete-account {
  min-height: 44px;
  min-width: 120px;
}
```

### 2. SCR-DEVICE-002 - 錯誤預防違規

**問題：** 「重置裝置」按鈕缺少確認對話框

**建議修正：**
```html
<button onclick="showConfirmModal('確定要重置裝置嗎？此操作無法復原。')">
  重置裝置
</button>
```

## 建議改善 (Warning)

### 1. SCR-AUTH-002 - 認知負荷

**問題：** 註冊表單單頁有 9 個欄位 (> 7)

**建議：** 拆分為 2 步驟表單
- Step 1: 帳號資訊 (Email, 密碼)
- Step 2: 個人資料 (姓名, 生日, 電話等)

### 2. SCR-ONBOARD-003 - 漸進式揭露

**問題：** 多步驟流程缺少進度指示器

**建議：** 新增 Stepper 元件顯示當前步驟

## 資訊提示 (Info)

### 1. 多個畫面 - 回饋

以下畫面的表單缺少 Loading 狀態：
- SCR-AUTH-001 (登入)
- SCR-AUTH-002 (註冊)
- SCR-SETTING-002 (通知設定)

**建議：** 提交時顯示 Loading 指示器

---

## 後續動作

- [ ] 修正 2 個 Error 級別問題
- [ ] 評估 4 個 Warning 級別問題
- [ ] 重新執行驗證
- [ ] 更新 SDD 心理學符合度章節
```

---

## 與 app-requirements-skill 整合

### 自動觸發

當 `app-requirements-skill` 執行以下操作時，建議同時執行心理學驗證：

1. 產出 SDD UI/UX 章節
2. 審查 UI 設計
3. 準備 IEC 62304 稽核文件

### 心理學符合度更新

驗證完成後，自動更新 SDD 的心理學符合度章節：

```markdown
## 心理學符合度驗證

### 設計心理學 ✅
- [x] 認知負荷 - 所有畫面元素數量在合理範圍
- [x] Fitts' Law - 按鈕尺寸 ≥ 44px
- [x] Hick's Law - 主要選項數 ≤ 7

### 認知心理學 ✅
- [x] 錯誤預防 - 危險操作皆有確認機制
- [x] 回饋 - 操作後有明確回饋
- [x] 心智模型 - 符合平台設計規範

### 驗證記錄
- 驗證日期：2024-XX-XX
- 驗證工具：app-uiux-designer.skill
- 驗證結果：通過 (85/100)
```
