# Process 01: UI 需求探索 (UI Discovery)

## 設計理念

> **在動手設計前，先完整理解 UI 需求！**
>
> 此階段收集所有影響 UI 設計的關鍵資訊，確保後續 Phase 能產生符合需求的 UI Flow。

---

## 進入條件

- [ ] 00-init 已完成（模板已複製、workspace 已初始化）
- [ ] SRS 文件可讀取（了解功能需求）
- [ ] SDD 文件可讀取（了解畫面定義）

---

## 執行步驟

### Step 1: 讀取現有文件

從 SRS/SDD 提取已定義的 UI 相關資訊：

```bash
# 搜尋 SRS 中的 UI 相關需求
grep -E 'UI|介面|畫面|顯示|操作' 01-requirements/SRS-*.md

# 搜尋 SDD 中的 SCR-* 定義
grep -E 'SCR-[A-Z]+-[0-9]+' 02-design/SDD-*.md | head -20
```

### Step 2: UI 需求訪談

> **MANDATORY**: 必須向使用者確認以下所有項目！

#### 2.1 平台與裝置

| 問題 | 選項 | 預設 |
|------|------|------|
| 目標平台 | iOS / Android / Web / 跨平台 | iOS |
| 主要裝置 | iPad / iPhone / 兩者皆支援 | 兩者皆支援 |
| iPad 方向 | 橫向 / 直向 / 兩者 | 橫向 (Landscape) |
| iPhone 方向 | 直向 / 橫向 / 兩者 | 直向 (Portrait) |

#### 2.2 設計風格

| 問題 | 選項 | 預設 |
|------|------|------|
| 設計語言 | iOS HIG / Material Design 3 / 自訂 | iOS HIG |
| 整體風格 | 現代簡約 / 活潑童趣 / 專業商務 / 科技感 | 依 App 類型 |
| 圓角程度 | 無 / 小 (4-8px) / 中 (12-16px) / 大 (20-24px) | 中 |
| 陰影使用 | 無 / 輕微 / 明顯 | 輕微 |

#### 2.3 色彩方案

| 問題 | 說明 | 範例 |
|------|------|------|
| 主色 (Primary) | 品牌主色、主要按鈕 | #6366F1 (Indigo) |
| 次色 (Secondary) | 輔助強調色 | #10B981 (Emerald) |
| 強調色 (Accent) | CTA、重要提示 | #F59E0B (Amber) |
| 背景色 | 主要背景 | #F8FAFC (Slate-50) |
| 文字色 | 主要文字 | #1E293B (Slate-800) |

#### 2.4 深色模式

| 問題 | 選項 | 預設 |
|------|------|------|
| 支援深色模式 | 是 / 否 / 未來考慮 | 否 |
| 切換方式 | 跟隨系統 / 手動切換 / 兩者 | 跟隨系統 |

#### 2.5 字體與排版

| 問題 | 選項 | 預設 |
|------|------|------|
| 中文字體 | 系統預設 / Noto Sans TC / 思源黑體 | 系統預設 |
| 英文字體 | SF Pro / Inter / Roboto | SF Pro (iOS) |
| 標題大小 | 大 (28-32px) / 中 (24px) / 小 (20px) | 中 |

#### 2.6 特殊需求

| 問題 | 說明 |
|------|------|
| 無障礙需求 | WCAG 等級、最小觸控區域 |
| 動畫偏好 | 豐富動畫 / 簡約動畫 / 無動畫 |
| 多語言支援 | 需支援的語言清單 |
| 特殊元件 | 自訂元件需求 |

### Step 3: 分析 App 類型

根據 SRS 內容判斷 App 類型，載入對應的標準畫面清單：

| App 類型 | 識別關鍵字 | 參考檔案 |
|----------|-----------|----------|
| 教育類 | 學習、課程、測驗、進度 | `references/standard-app-screens.md` |
| 電商類 | 商品、購物車、結帳、訂單 | `references/standard-app-screens.md` |
| 社群類 | 貼文、好友、聊天、通知 | `references/standard-app-screens.md` |
| 工具類 | 設定、匯出、歷史記錄 | `references/standard-app-screens.md` |
| 醫療類 | 患者、處方、預約、健康 | `references/standard-app-screens.md` |

### Step 4: 產生 UI 需求文件

建立 `workspace/ui-requirements.json`：

```json
{
  "version": "1.0",
  "created_at": "2026-01-21T00:00:00Z",
  "project": {
    "name": "專案名稱",
    "type": "education|ecommerce|social|tool|healthcare",
    "description": "專案描述"
  },
  "platform": {
    "target": "iOS",
    "devices": ["iPad", "iPhone"],
    "ipad_orientation": "landscape",
    "iphone_orientation": "portrait"
  },
  "design": {
    "language": "iOS HIG",
    "style": "modern-minimal|playful|professional|tech",
    "border_radius": "medium",
    "shadow": "subtle"
  },
  "colors": {
    "primary": "#6366F1",
    "secondary": "#10B981",
    "accent": "#F59E0B",
    "background": "#F8FAFC",
    "text": "#1E293B",
    "dark_mode": false
  },
  "typography": {
    "chinese_font": "system",
    "english_font": "SF Pro",
    "heading_size": "medium"
  },
  "accessibility": {
    "wcag_level": "AA",
    "min_touch_target": "44px"
  },
  "special_requirements": {
    "animations": "subtle",
    "languages": ["zh-TW"],
    "custom_components": []
  },
  "inferred_screens": {
    "from_sdd": 0,
    "predicted": 0,
    "total": 0
  }
}
```

### Step 5: 更新 Design Token

根據收集的需求，更新 `shared/project-theme.css`：

```css
:root {
  /* Colors */
  --color-primary: #6366F1;
  --color-secondary: #10B981;
  --color-accent: #F59E0B;
  --color-background: #F8FAFC;
  --color-text: #1E293B;

  /* Typography */
  --font-family-zh: -apple-system, "PingFang TC", "Noto Sans TC", sans-serif;
  --font-family-en: "SF Pro Display", -apple-system, sans-serif;

  /* Spacing */
  --border-radius-sm: 4px;
  --border-radius-md: 12px;
  --border-radius-lg: 20px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
}
```

### Step 6: 更新 workspace 狀態

```json
{
  "current_process": "01-discovery",
  "progress": {
    "00-init": "completed",
    "01-discovery": "completed"
  },
  "context": {
    "ui_requirements_collected": true,
    "app_type": "education",
    "platform": "iOS",
    "devices": ["iPad", "iPhone"],
    "dark_mode": false,
    "last_action": "UI requirements collected and saved to workspace/ui-requirements.json"
  }
}
```

---

## 退出條件 (EXIT CRITERIA)

必須滿足 **全部** 條件才能進入下一節點：

| 條件 | 驗證方式 |
|------|----------|
| ui-requirements.json 存在 | `test -f workspace/ui-requirements.json` |
| 平台已確認 | `jq '.platform.target' workspace/ui-requirements.json` |
| 裝置已確認 | `jq '.platform.devices' workspace/ui-requirements.json` |
| 色彩已定義 | `jq '.colors.primary' workspace/ui-requirements.json` |
| project-theme.css 已更新 | `grep 'color-primary' shared/project-theme.css` |

---

## 阻斷條件 (BLOCKING)

> **以下任一情況發生時，禁止進入下一節點**

1. `workspace/ui-requirements.json` 不存在
2. 平台或裝置未確認
3. 色彩方案未定義
4. 使用者未確認需求

---

## 快速路徑

若 SDD 已包含完整 UI 需求（例如從 app-requirements-skill Phase 2 產生），可跳過訪談：

```bash
# 檢查 SDD 是否有 UI 需求章節
grep -q "UI/UX 需求\|UI Requirements" 02-design/SDD-*.md && echo "可使用快速路徑"
```

**快速路徑步驟**：
1. 從 SDD 提取 UI 需求
2. 自動產生 `ui-requirements.json`
3. 跳至 Step 5 更新 Design Token

---

## AFP (Anti Forgetting Protocol) 整合

### Phase 轉換前檢查清單

```
[ ] ui-requirements.json 已產生
[ ] project-theme.css 已更新
[ ] current-process.json 已更新
[ ] 使用者已確認所有需求
```

### Compact 保留重點

```
/compact 保留：
1. 專案名稱與路徑
2. App 類型：{type}
3. 平台：{platform}，裝置：{devices}
4. 主色：{primary}，次色：{secondary}
5. 深色模式：{dark_mode}
6. 預估畫面數：{total_screens}
```

### Phase Summary 範本

```markdown
## Last Completed: 01-discovery
- App 類型: education
- 平台: iOS (iPad + iPhone)
- 風格: iOS HIG, 現代簡約
- 主色: #6366F1
- 深色模式: 否

## Next Phase: 02-planning
- 待辦: 建立 SCR-* 畫面清單
- 預估畫面數: 40
```

---

## 相關檔案

| 檔案 | 說明 |
|------|------|
| `references/ios-guidelines.md` | iOS HIG 參考 |
| `references/android-guidelines.md` | Material Design 3 參考 |
| `references/design-system.md` | Design System 建立指南 |
| `references/dark-mode.md` | 深色模式實作指南 |
| `references/accessibility.md` | 無障礙設計指南 |
| `references/standard-app-screens.md` | 各類型 App 標準畫面 |

---

## 下一節點

→ `process/02-planning/README.md` (智慧畫面規劃)

**注意**: 只有在 UI 需求完整收集後才能進入下一節點！
