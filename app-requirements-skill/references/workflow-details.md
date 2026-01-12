# 工作流程詳細說明

本文件包含 medical-software-requirements-skill 的詳細工作流程說明。

## 🧠 心理學自動套用流程

### Step 1: 讀取心理學指南

執行任何文件操作前，必須先讀取以下檔案：

```bash
# 1. 設計心理學
cat ~/.claude/skills/medical-software-requirements-skill/references/design-psychology.md

# 2. 認知心理學
cat ~/.claude/skills/medical-software-requirements-skill/references/cognitive-psychology.md

# 3. 文件編排心理學
cat ~/.claude/skills/medical-software-requirements-skill/references/document-layout-psychology.md
```

### Step 2: 根據任務類型套用心理學

| 任務類型 | 設計心理學 | 認知心理學 | 文件編排心理學 |
|---------|:----------:|:----------:|:--------------:|
| 產出/修改 SRS | ✅ | ✅ | ✅ |
| 產出/修改 SDD | ✅ | ✅ | ✅ |
| 產出/修改 SWD | - | ✅ | ✅ |
| 產出/修改 STP/STC | - | - | ✅ |
| 檢視/審查文件 | ✅ | ✅ | ✅ |
| 產生 DOCX | - | - | ✅ |

### Step 3: 輸出心理學檢視報告

```markdown
## 心理學符合度檢視

### 設計心理學 ✅/⚠️/❌
- 認知負荷：[評估]
- 漸進式揭露：[評估]
- Fitts' Law：[評估]

### 認知心理學 ✅/⚠️/❌
- 心智模型：[評估]
- 工作記憶：[評估]
- 錯誤預防：[評估]

### 文件編排心理學 ✅/⚠️/❌
- 讀者角色分析：[評估]
- F 型排版：[評估]
- 表格可讀性：[評估]
```

---

## 完整工作流程

```
┌────────────────────────────────────────────────────────────────┐
│                    醫療軟體開發文件工作流程                        │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  第一階段：需求收集                                               │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 1.1 專案願景訪談    → 產出：Project Vision Statement      │ │
│  │ 1.2 利害關係人分析   → 產出：Stakeholder Analysis         │ │
│  │ 1.3 功能需求收集    → 產出：Functional Requirements       │ │
│  │ 1.4 非功能需求分析   → 產出：Non-Functional Requirements  │ │
│  │ 1.5 軟體安全分類    → 產出：Safety Classification         │ │
│  └──────────────────────────────────────────────────────────┘ │
│                           ↓                                    │
│  第二階段：文件產出                                               │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 2.1 SRS 軟體需求規格書  (+ 設計心理學 + 認知心理學)         │ │
│  │ 2.2 SDD 軟體設計規格書  (+ UI/UX 整合 + AI 資產)          │ │
│  │ 2.3 SWD 軟體詳細設計書                                    │ │
│  │ 2.4 STP 軟體測試計畫                                      │ │
│  │ 2.5 STC 軟體測試案例                                      │ │
│  │ 2.6 SVV 軟體驗證確認報告                                  │ │
│  │ 2.7 RTM 需求追溯矩陣   (100% 覆蓋率驗證)                  │ │
│  └──────────────────────────────────────────────────────────┘ │
│                           ↓                                    │
│  第三階段：UI Flow 產生 (自動觸發)                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 3.1 啟用 app-uiux-designer.skill                         │ │
│  │ 3.2 產生 HTML 互動原型                                    │ │
│  │ 3.3 產生 UI 截圖 (Puppeteer)                             │ │
│  │ 3.4 回補 SDD (UI 原型 + 圖片)                            │ │
│  │ 3.5 回補 SRS (Screen References + Inferred Requirements) │ │
│  └──────────────────────────────────────────────────────────┘ │
│                           ↓                                    │
│  第四階段：DOCX 產生                                             │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 4.1 移除 MD 手動編號                                      │ │
│  │ 4.2 執行 md-to-docx.js 轉換                              │ │
│  │ 4.3 驗證圖片嵌入                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 階段 1.1：專案願景訪談

### 訪談問題範本

| 類別 | 問題 |
|------|------|
| 產品願景 | 這個產品要解決什麼問題？ |
| 目標用戶 | 主要使用者是誰？ |
| 成功指標 | 如何衡量產品成功？ |
| 技術限制 | 有哪些技術或法規限制？ |

---

## 階段 1.2：利害關係人分析

### 利害關係人矩陣

| 角色 | 關注點 | 影響力 | 溝通頻率 |
|------|--------|--------|---------|
| 產品負責人 | 功能優先順序 | 高 | 每日 |
| 法規專員 | IEC 62304 合規 | 高 | 每週 |
| 臨床專家 | 臨床使用情境 | 中 | 雙週 |
| IT 人員 | 系統整合 | 中 | 需求時 |

---

## 階段 1.5：軟體安全分類評估

### IEC 62304 軟體安全分類

| 分類 | 定義 | 文件要求 |
|------|------|---------|
| Class A | 不會造成傷害 | 基本文件 |
| Class B | 可能造成非嚴重傷害 | 完整文件 + 風險分析 |
| Class C | 可能造成死亡或嚴重傷害 | 完整文件 + 風險分析 + 詳細追溯 |

---

## ID 編號系統

### 文件 ID 格式

| 文件類型 | ID 格式 | 範例 |
|---------|--------|------|
| SRS 需求 | REQ-{MODULE}-{NNN} | REQ-AUTH-001 |
| SDD 設計 | SDD-{MODULE}-{NNN} | SDD-AUTH-001 |
| SDD 畫面 | SCR-{MODULE}-{NNN} | SCR-AUTH-001-login |
| SWD 元件 | SWD-{MODULE}-{NNN} | SWD-AUTH-001 |
| STC 測試 | STC-{REQ-ID} | STC-REQ-AUTH-001 |

### 模組代碼

| 代碼 | 模組名稱 |
|------|---------|
| AUTH | 認證模組 |
| DASH | Dashboard |
| TRAIN | 訓練模組 |
| REPORT | 報告模組 |
| SETTING | 設定模組 |
| DEVICE | 設備模組 |
| VOCAB | 字庫模組 |

---

## MD 轉 DOCX 同步產生

### 轉換器 (md-to-docx.js)

**位置：** `~/.claude/skills/medical-software-requirements-skill/md-to-docx.js`

```bash
# 安裝依賴 (首次使用)
cd ~/.claude/skills/medical-software-requirements-skill
npm install docx
npm install -g @mermaid-js/mermaid-cli  # 若需渲染 Mermaid 圖表

# 轉換文件
node ~/.claude/skills/medical-software-requirements-skill/md-to-docx.js <input.md>

# 範例
node ~/.claude/skills/medical-software-requirements-skill/md-to-docx.js SRS-VocabKids-1.0.md
node ~/.claude/skills/medical-software-requirements-skill/md-to-docx.js SDD-VocabKids-1.0.md
```

### 轉換器功能

- ✅ 自動解析 Markdown 文件結構（支援中英文標題）
- ✅ 自動渲染 Mermaid 圖表為 SVG
- ✅ SVG 圖片自動嵌入 DOCX 並置中顯示
- ✅ 支援表格、程式碼區塊、標題階層
- ✅ 自動產生封面、目錄、頁首頁尾
- ✅ 標題自動編號 (1., 1.1, 1.1.1 等)
- ✅ 程式碼區塊格式化：行號、斑馬紋背景
- ✅ 語法高亮：基於 VSCode Light+ 配色
- ✅ 本地圖片嵌入：支援 PNG/JPEG

---

## 專案目錄結構

```
📁 {project-name}/
├── 📁 01-requirements/
│   └── SRS-{ProjectName}-{Version}.md/.docx
├── 📁 02-design/
│   ├── SDD-{ProjectName}-{Version}.md/.docx
│   └── SDD/images/
│       ├── iphone/
│       └── ipad/
├── 📁 03-assets/
│   ├── app-icon/
│   ├── icons/
│   └── images/
├── 📁 04-ui-flow/
│   ├── generated-ui/
│   ├── capture-screenshots.js
│   └── package.json
├── 📁 05-development/
│   └── SWD-{ProjectName}-{Version}.md/.docx
├── 📁 06-testing/
│   ├── STP-{ProjectName}-{Version}.md/.docx
│   └── STC-{ProjectName}-{Version}.md/.docx
├── 📁 07-verification/
│   └── SVV-{ProjectName}-{Version}.md/.docx
└── 📁 08-traceability/
    └── RTM-{ProjectName}-{Version}.md/.docx
```
