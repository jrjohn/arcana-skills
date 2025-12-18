# 規格文件驅動 UI 生成指南

本指南說明如何從 SRS (軟體需求規格書)、SDD (軟體設計文件) 或其他規格文件自動生成完整的 UI/UX 畫面系列。

## 目錄
1. [支援的文件格式](#支援的文件格式)
2. [規格文件解析流程](#規格文件解析流程)
3. [SRS 文件解析](#srs-文件解析)
4. [SDD 文件解析](#sdd-文件解析)
5. [需求到 UI 映射](#需求到-ui-映射)
6. [批次 UI 生成](#批次-ui-生成)
7. [輸出目錄結構](#輸出目錄結構)
8. [生成報告模板](#生成報告模板)

---

## 支援的文件格式

### 可解析的規格文件類型

```
📄 支援格式
├── Markdown (.md)
│   ├── SRS-*.md (軟體需求規格書)
│   ├── SDD-*.md (軟體設計文件)
│   ├── PRD-*.md (產品需求文件)
│   ├── FSD-*.md (功能規格文件)
│   └── *.md (其他規格文件)
│
├── Word 文件 (.docx)
│   ├── SRS-*.docx
│   ├── SDD-*.docx
│   ├── PRD-*.docx
│   └── *.docx
│
├── PDF (.pdf)
│   └── 各類規格文件
│
└── 其他
    ├── .txt (純文字)
    └── .json (結構化規格)
```

### 文件類型說明

| 文件類型 | 全名 | 主要內容 | UI 生成重點 |
|----------|------|----------|-------------|
| **SRS** | Software Requirements Specification | 功能需求、使用者故事、用例 | 功能畫面、流程 |
| **SDD** | Software Design Document | 系統架構、畫面規格、資料模型 | 詳細畫面設計 |
| **PRD** | Product Requirements Document | 產品願景、功能清單、優先級 | 功能範圍、MVP |
| **FSD** | Functional Specification Document | 詳細功能規格、業務規則 | 互動邏輯、驗證 |
| **Wireframe Doc** | 線框圖文件 | 畫面佈局、元件配置 | 視覺實現 |

---

## 規格文件解析流程

### 整體流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    規格驅動 UI 生成流程                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📄 輸入規格文件                                                 │
│  (SRS/SDD/PRD.md 或 .docx)                                      │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                           │
│  │   文件解析       │                                           │
│  │  ─────────────  │                                           │
│  │  • 結構識別      │                                           │
│  │  • 章節提取      │                                           │
│  │  • 需求萃取      │                                           │
│  └────────┬────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                           │
│  │   需求分析       │                                           │
│  │  ─────────────  │                                           │
│  │  • 功能清單      │                                           │
│  │  • 使用者角色    │                                           │
│  │  • 流程識別      │                                           │
│  │  • 畫面推導      │                                           │
│  └────────┬────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                           │
│  │   UI 規劃        │                                           │
│  │  ─────────────  │                                           │
│  │  • 畫面清單      │                                           │
│  │  • 流程圖        │                                           │
│  │  • 元件需求      │                                           │
│  │  • 風格確認      │                                           │
│  └────────┬────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                           │
│  │   批次生成       │                                           │
│  │  ─────────────  │                                           │
│  │  • 依序生成畫面  │                                           │
│  │  • 套用風格      │                                           │
│  │  • 多格式輸出    │                                           │
│  └────────┬────────┘                                           │
│           │                                                     │
│           ▼                                                     │
│  📁 輸出目錄                                                    │
│  └── generated-ui/                                              │
│      ├── html/                                                  │
│      ├── react/                                                 │
│      ├── swiftui/                                               │
│      ├── compose/                                               │
│      └── report.md                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 解析步驟

```
Step 1: 文件讀取
        ├── 識別文件格式 (.md/.docx/.pdf)
        ├── 讀取文件內容
        └── 轉換為統一格式

Step 2: 結構解析
        ├── 識別章節標題
        ├── 提取表格資料
        ├── 解析列表項目
        └── 識別圖片/流程圖

Step 3: 需求萃取
        ├── 提取功能需求 (FR)
        ├── 提取使用者故事 (User Story)
        ├── 提取用例 (Use Case)
        ├── 提取畫面規格 (Screen Spec)
        └── 提取業務規則 (Business Rule)

Step 4: UI 映射
        ├── 需求 → 畫面對應
        ├── 流程 → 導航結構
        ├── 資料 → 表單/列表
        └── 規則 → 驗證/狀態

Step 5: 批次生成
        ├── 建立輸出目錄
        ├── 依序生成各畫面
        ├── 產生導航/路由
        └── 輸出生成報告
```

---

## SRS 文件解析

### SRS 常見結構

```markdown
# SRS 典型章節結構

1. 簡介 (Introduction)
   1.1 目的
   1.2 範圍
   1.3 定義與縮寫

2. 整體描述 (Overall Description)
   2.1 產品觀點
   2.2 產品功能        ← 【重要】功能清單
   2.3 使用者類別      ← 【重要】使用者角色
   2.4 操作環境
   2.5 限制條件

3. 功能需求 (Functional Requirements) ← 【核心】
   3.1 使用者故事
   3.2 用例描述
   3.3 功能規格

4. 外部介面需求 (External Interface Requirements)
   4.1 使用者介面      ← 【重要】UI 規格
   4.2 硬體介面
   4.3 軟體介面
   4.4 通訊介面

5. 非功能需求 (Non-functional Requirements)
   5.1 效能需求
   5.2 安全需求
   5.3 可用性需求      ← 【參考】UX 要求
```

### SRS 解析重點

#### 1. 功能需求萃取

```markdown
## 從 SRS 萃取的內容

### 使用者故事格式
As a [使用者角色]
I want to [功能描述]
So that [價值/目的]

→ 萃取:
  - 使用者角色 → 決定畫面權限/入口
  - 功能描述 → 對應畫面/功能
  - 價值目的 → 決定 UX 重點

### 用例格式
用例名稱: UC-001 使用者登入
主要參與者: 一般使用者
前置條件: 使用者已註冊
主要流程:
  1. 使用者開啟 App
  2. 系統顯示登入畫面
  3. 使用者輸入帳號密碼
  4. 系統驗證
  5. 登入成功，跳轉首頁
替代流程:
  3a. 使用者選擇社群登入
  4a. 驗證失敗，顯示錯誤

→ 萃取:
  - 用例名稱 → 功能模組
  - 主要流程 → 畫面流程
  - 替代流程 → 分支/錯誤狀態
```

#### 2. 功能清單萃取

```markdown
## SRS 功能清單範例

| ID | 功能名稱 | 描述 | 優先級 |
|----|----------|------|--------|
| FR-001 | 使用者註冊 | 新使用者可透過 Email 註冊帳號 | Must |
| FR-002 | 使用者登入 | 使用者可透過 Email/密碼登入 | Must |
| FR-003 | 社群登入 | 支援 Google/Apple 登入 | Should |
| FR-004 | 忘記密碼 | 使用者可重設密碼 | Must |
| FR-005 | 瀏覽商品 | 使用者可瀏覽商品列表 | Must |
| FR-006 | 搜尋商品 | 使用者可搜尋商品 | Must |
| FR-007 | 商品詳情 | 使用者可查看商品詳情 | Must |
| FR-008 | 加入購物車 | 使用者可將商品加入購物車 | Must |
| FR-009 | 結帳 | 使用者可完成購買流程 | Must |
| FR-010 | 訂單查詢 | 使用者可查詢訂單狀態 | Should |

→ 自動推導畫面:
  - FR-001 → 註冊頁 (多步驟)
  - FR-002 → 登入頁
  - FR-003 → 社群登入按鈕 (整合至登入頁)
  - FR-004 → 忘記密碼流程 (3頁)
  - FR-005 → 商品列表頁
  - FR-006 → 搜尋頁/搜尋結果
  - FR-007 → 商品詳情頁
  - FR-008 → 購物車頁
  - FR-009 → 結帳流程 (多頁)
  - FR-010 → 訂單列表/訂單詳情
```

#### 3. 使用者角色萃取

```markdown
## 使用者類別範例

| 角色 | 描述 | 主要功能 |
|------|------|----------|
| 訪客 | 未登入使用者 | 瀏覽、搜尋 |
| 會員 | 已註冊使用者 | 購買、收藏、訂單 |
| VIP 會員 | 付費會員 | 專屬優惠、優先服務 |
| 管理員 | 後台管理者 | 商品管理、訂單管理 |

→ 自動推導:
  - 不同角色的導航結構
  - 權限控制畫面
  - 角色專屬功能頁
```

---

## SDD 文件解析

### SDD 常見結構

```markdown
# SDD 典型章節結構

1. 簡介
   1.1 目的
   1.2 範圍

2. 系統架構 (System Architecture)
   2.1 架構概覽
   2.2 模組設計

3. 資料設計 (Data Design)        ← 【重要】
   3.1 資料模型
   3.2 資料庫設計

4. 介面設計 (Interface Design)   ← 【核心】
   4.1 使用者介面設計
   4.2 畫面規格
   4.3 導航結構
   4.4 互動設計

5. 元件設計 (Component Design)
   5.1 元件規格
   5.2 API 設計
```

### SDD 解析重點

#### 1. 畫面規格萃取

```markdown
## SDD 畫面規格範例

### 4.2.1 登入畫面 (SCR-001)

**畫面名稱:** 登入畫面
**畫面 ID:** SCR-001
**存取權限:** 公開

**畫面元素:**
| 元素 | 類型 | 說明 | 驗證規則 |
|------|------|------|----------|
| Logo | Image | App Logo | - |
| 標題 | Text | "歡迎回來" | - |
| Email 輸入 | TextField | 使用者 Email | Email 格式 |
| 密碼輸入 | SecureField | 使用者密碼 | 最少 8 字 |
| 登入按鈕 | Button | 主要 CTA | - |
| 忘記密碼 | Link | 跳轉忘記密碼 | - |
| Google 登入 | Button | 社群登入 | - |
| Apple 登入 | Button | 社群登入 | - |
| 註冊連結 | Link | 跳轉註冊頁 | - |

**畫面狀態:**
- Default: 初始空白狀態
- Loading: 登入驗證中
- Error: 登入失敗 (顯示錯誤訊息)
- Success: 登入成功 (跳轉首頁)

**導航:**
- 來源: 啟動畫面、登出後
- 目標: 首頁 (成功)、註冊頁、忘記密碼頁

→ 直接生成畫面程式碼
```

#### 2. 導航結構萃取

```markdown
## SDD 導航結構範例

### 4.3 導航結構

```
App
├── 🔓 公開區域
│   ├── 啟動畫面 (Splash)
│   ├── 引導頁 (Onboarding)
│   ├── 登入 (Login)
│   ├── 註冊 (Register)
│   └── 忘記密碼 (ForgotPassword)
│
├── 🔐 會員區域 (需登入)
│   ├── 首頁 (Home)
│   │   ├── 推薦商品
│   │   └── 最新消息
│   │
│   ├── 探索 (Explore)
│   │   ├── 分類列表
│   │   ├── 商品列表
│   │   └── 搜尋結果
│   │
│   ├── 購物車 (Cart)
│   │   ├── 購物車列表
│   │   └── 結帳流程
│   │
│   └── 我的 (Profile)
│       ├── 個人資料
│       ├── 訂單記錄
│       ├── 收藏清單
│       └── 設定
│
└── 🔒 管理區域 (需管理權限)
    ├── 儀表板 (Dashboard)
    ├── 商品管理
    └── 訂單管理
```

→ 自動生成:
  - Tab Bar 導航
  - Navigation Stack
  - 路由配置
```

#### 3. 資料模型萃取

```markdown
## SDD 資料模型範例

### 3.1 資料模型

**User (使用者)**
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | UUID | 主鍵 |
| email | String | 電子郵件 |
| name | String | 姓名 |
| avatar | URL | 頭像 |
| createdAt | DateTime | 建立時間 |

**Product (商品)**
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | UUID | 主鍵 |
| name | String | 商品名稱 |
| description | String | 描述 |
| price | Decimal | 價格 |
| images | [URL] | 圖片列表 |
| category | Category | 分類 |

→ 自動推導:
  - 表單欄位配置
  - 列表顯示欄位
  - 詳情頁結構
```

---

## 需求到 UI 映射

### 自動映射規則

```
┌─────────────────────────────────────────────────────────────────┐
│                     需求 → UI 自動映射                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  需求類型              →    UI 畫面                             │
│  ─────────────────────────────────────────────────────────      │
│  使用者註冊            →    註冊流程 (1-3 頁)                    │
│  使用者登入            →    登入頁 + 社群登入                    │
│  密碼重設              →    忘記密碼流程 (3 頁)                  │
│  瀏覽列表              →    列表頁 + 篩選 + 排序                 │
│  搜尋功能              →    搜尋頁 + 搜尋結果                    │
│  查看詳情              →    詳情頁 + 相關推薦                    │
│  CRUD 操作             →    列表 + 新增 + 編輯 + 詳情            │
│  購物車功能            →    購物車頁 + 數量調整                  │
│  結帳流程              →    結帳多步驟 (3-5 頁)                  │
│  訂單管理              →    訂單列表 + 訂單詳情                  │
│  個人資料              →    個人檔案 + 編輯頁                    │
│  設定功能              →    設定列表 + 各項設定頁                │
│  通知功能              →    通知列表 + 通知詳情                  │
│  社群功能              →    動態牆 + 發布 + 互動                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 畫面狀態自動補齊

```
每個功能畫面自動產生:

列表頁狀態:
├── Default (有資料)
├── Empty (空狀態 + CTA)
├── Loading (載入中 + Skeleton)
├── Error (錯誤 + 重試)
├── Refreshing (下拉更新)
└── LoadMore (載入更多)

表單頁狀態:
├── Default (空白)
├── Filled (有資料)
├── Validating (驗證中)
├── ValidationError (驗證錯誤)
├── Submitting (提交中)
├── SubmitSuccess (成功)
└── SubmitError (失敗)

詳情頁狀態:
├── Default (成功)
├── Loading (載入中)
└── Error (資料不存在)
```

### 映射範例

```markdown
## 輸入: SRS 功能需求

FR-005: 瀏覽商品
- 使用者可瀏覽商品列表
- 支援分類篩選
- 支援價格排序
- 顯示商品圖片、名稱、價格

## 輸出: UI 畫面清單

### SCR-010 商品列表頁
- 頁面類型: 列表頁
- 元件:
  - 頂部: 搜尋欄 + 篩選按鈕
  - 篩選: 分類篩選 Sheet
  - 排序: 排序選單
  - 列表: 商品卡片網格 (2 欄)
  - 卡片: 圖片 + 名稱 + 價格 + 收藏
- 狀態: Default/Empty/Loading/Error/LoadMore
- 導航: Tab Bar → 首頁 Tab

### SCR-011 分類篩選 Sheet
- 頁面類型: Bottom Sheet
- 元件: 分類列表 (單選/多選)

### SCR-012 排序選單
- 頁面類型: Action Sheet
- 選項: 推薦/價格低到高/價格高到低/最新
```

---

## 批次 UI 生成

### 生成請求格式

```markdown
## 規格驅動 UI 生成請求

### 輸入文件
- 文件路徑: /path/to/SRS-ProjectName-1.0.md
- 文件類型: SRS (軟體需求規格書)

### 輸出設定
- 輸出目錄: /path/to/generated-ui/
- 輸出格式:
  - [x] HTML + Tailwind
  - [x] React
  - [ ] SwiftUI
  - [ ] Jetpack Compose
- 風格設定:
  - 主色: #6366F1
  - 風格: 現代簡約
  - 圓角: 12px

### 生成範圍
- [x] 全部功能
- [ ] 僅指定功能: [功能列表]

### 額外選項
- [x] 產生導航/路由配置
- [x] 產生元件庫
- [x] 產生生成報告
- [ ] 套用已萃取風格
```

### 批次生成流程

```
1. 解析規格文件
   ├── 讀取 SRS/SDD
   ├── 萃取功能需求
   └── 產生畫面清單

2. 確認生成範圍
   ├── 顯示畫面清單
   ├── 估計畫面數量
   └── 使用者確認

3. 依序生成畫面
   ├── 按模組分組
   ├── 依優先級排序
   ├── 逐一生成程式碼
   └── 顯示進度

4. 產生支援檔案
   ├── 路由配置
   ├── 共用元件
   ├── 主題設定
   └── 型別定義

5. 輸出報告
   ├── 生成摘要
   ├── 畫面清單
   ├── 檔案目錄
   └── 後續建議
```

---

## 輸出目錄結構

### 標準輸出目錄

```
📁 generated-ui/
│
├── 📄 README.md                    # 生成報告與使用說明
├── 📄 SCREENS.md                   # 畫面清單與規格
│
├── 📁 html/                        # HTML + Tailwind 輸出
│   ├── 📁 auth/                    # 認證模組
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── forgot-password.html
│   │   └── reset-password.html
│   │
│   ├── 📁 home/                    # 首頁模組
│   │   ├── home.html
│   │   └── dashboard.html
│   │
│   ├── 📁 product/                 # 商品模組
│   │   ├── product-list.html
│   │   ├── product-detail.html
│   │   └── product-search.html
│   │
│   ├── 📁 cart/                    # 購物車模組
│   │   ├── cart.html
│   │   ├── checkout.html
│   │   └── order-confirmation.html
│   │
│   ├── 📁 profile/                 # 個人檔案模組
│   │   ├── profile.html
│   │   ├── edit-profile.html
│   │   ├── orders.html
│   │   └── settings.html
│   │
│   ├── 📁 components/              # 共用元件
│   │   ├── navbar.html
│   │   ├── tabbar.html
│   │   ├── card.html
│   │   └── button.html
│   │
│   └── 📁 states/                  # 狀態頁面
│       ├── empty.html
│       ├── loading.html
│       └── error.html
│
├── 📁 react/                       # React 輸出
│   ├── 📁 src/
│   │   ├── 📁 components/
│   │   │   ├── 📁 ui/              # 基礎元件
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   └── index.ts
│   │   │   │
│   │   │   └── 📁 layout/          # 佈局元件
│   │   │       ├── Header.tsx
│   │   │       ├── TabBar.tsx
│   │   │       └── Container.tsx
│   │   │
│   │   ├── 📁 screens/             # 畫面元件
│   │   │   ├── 📁 auth/
│   │   │   │   ├── LoginScreen.tsx
│   │   │   │   ├── RegisterScreen.tsx
│   │   │   │   └── ForgotPasswordScreen.tsx
│   │   │   │
│   │   │   ├── 📁 home/
│   │   │   │   └── HomeScreen.tsx
│   │   │   │
│   │   │   ├── 📁 product/
│   │   │   │   ├── ProductListScreen.tsx
│   │   │   │   └── ProductDetailScreen.tsx
│   │   │   │
│   │   │   └── 📁 profile/
│   │   │       ├── ProfileScreen.tsx
│   │   │       └── SettingsScreen.tsx
│   │   │
│   │   ├── 📁 styles/
│   │   │   └── theme.ts            # 主題設定
│   │   │
│   │   ├── 📁 types/
│   │   │   └── index.ts            # 型別定義
│   │   │
│   │   └── 📁 routes/
│   │       └── index.tsx           # 路由配置
│   │
│   └── package.json
│
├── 📁 swiftui/                     # SwiftUI 輸出
│   ├── 📁 Sources/
│   │   ├── 📁 Views/
│   │   │   ├── 📁 Auth/
│   │   │   ├── 📁 Home/
│   │   │   ├── 📁 Product/
│   │   │   └── 📁 Profile/
│   │   │
│   │   ├── 📁 Components/
│   │   │   ├── AppButton.swift
│   │   │   ├── AppTextField.swift
│   │   │   └── AppCard.swift
│   │   │
│   │   └── 📁 Theme/
│   │       └── AppTheme.swift
│   │
│   └── Package.swift
│
├── 📁 compose/                     # Jetpack Compose 輸出
│   └── 📁 app/src/main/java/
│       └── 📁 com/example/app/
│           ├── 📁 ui/
│           │   ├── 📁 screens/
│           │   ├── 📁 components/
│           │   └── 📁 theme/
│           └── 📁 navigation/
│
├── 📁 assets/                      # 共用資源
│   ├── 📁 icons/
│   ├── 📁 images/
│   └── 📁 fonts/
│
└── 📁 figma/                       # Figma 匯出
    └── screens.json                # Figma 結構 JSON
```

### 按專案命名

```
📁 generated-ui-{ProjectName}/
│
├── 📄 README.md
├── 📄 SCREENS.md
├── 📄 CHANGELOG.md
│
├── 📁 v1.0/                        # 版本化輸出
│   ├── html/
│   ├── react/
│   └── ...
│
└── 📁 latest/                      # 最新版本
    └── (symlink to v1.0)
```

---

## 生成報告模板

### README.md 模板

```markdown
# {ProjectName} UI 生成報告

## 生成資訊

| 項目 | 內容 |
|------|------|
| 專案名稱 | {ProjectName} |
| 規格文件 | SRS-{ProjectName}-1.0.md |
| 生成時間 | {DateTime} |
| 生成版本 | v1.0 |

## 生成摘要

| 統計 | 數量 |
|------|------|
| 總畫面數 | {TotalScreens} |
| 模組數 | {TotalModules} |
| 元件數 | {TotalComponents} |

### 輸出格式

- [x] HTML + Tailwind ({ScreenCount} 頁)
- [x] React ({ScreenCount} 元件)
- [ ] SwiftUI
- [ ] Jetpack Compose

## 畫面清單

### 認證模組 (Auth)

| 畫面 | 檔案 | 狀態 |
|------|------|------|
| 登入 | auth/login.html | ✅ |
| 註冊 | auth/register.html | ✅ |
| 忘記密碼 | auth/forgot-password.html | ✅ |

### 首頁模組 (Home)

| 畫面 | 檔案 | 狀態 |
|------|------|------|
| 首頁 | home/home.html | ✅ |

### 商品模組 (Product)

| 畫面 | 檔案 | 狀態 |
|------|------|------|
| 商品列表 | product/list.html | ✅ |
| 商品詳情 | product/detail.html | ✅ |
| 搜尋結果 | product/search.html | ✅ |

... (更多模組)

## 風格設定

```
主色: #6366F1
次色: #EC4899
背景: #FFFFFF
圓角: 12px
字型: Inter / SF Pro
```

## 如何使用

### HTML 預覽
```bash
cd generated-ui/html
open login.html
```

### React 開發
```bash
cd generated-ui/react
npm install
npm run dev
```

## 後續建議

1. **功能完善**
   - [ ] 串接後端 API
   - [ ] 實作表單驗證邏輯
   - [ ] 加入狀態管理

2. **設計調整**
   - [ ] 根據品牌調整色彩
   - [ ] 替換 placeholder 圖片
   - [ ] 微調間距與字型

3. **測試**
   - [ ] 響應式測試
   - [ ] 無障礙測試
   - [ ] 瀏覽器相容性測試

## 檔案目錄

```
generated-ui/
├── html/           # {HTMLCount} 個檔案
├── react/          # {ReactCount} 個檔案
├── assets/         # 共用資源
└── README.md       # 本文件
```

---

*由 App UI/UX Designer Skill 自動生成*
*生成時間: {DateTime}*
```

### SCREENS.md 模板

```markdown
# {ProjectName} 畫面規格

## 畫面總覽

```
總畫面數: {Total}
├── 認證模組: {AuthCount} 頁
├── 首頁模組: {HomeCount} 頁
├── 商品模組: {ProductCount} 頁
├── 購物車模組: {CartCount} 頁
└── 個人檔案模組: {ProfileCount} 頁
```

---

## SCR-001 登入頁

**基本資訊**
| 項目 | 內容 |
|------|------|
| 畫面 ID | SCR-001 |
| 畫面名稱 | 登入頁 |
| 模組 | 認證 (Auth) |
| 存取權限 | 公開 |

**畫面元素**
| 元素 | 類型 | 必要 |
|------|------|------|
| Logo | Image | ✓ |
| 標題 | Text | ✓ |
| Email 輸入 | TextField | ✓ |
| 密碼輸入 | SecureField | ✓ |
| 登入按鈕 | Button | ✓ |
| 忘記密碼 | Link | ✓ |
| 社群登入 | ButtonGroup | ○ |
| 註冊連結 | Link | ✓ |

**畫面狀態**
- Default
- Loading
- Error

**導航**
- 來源: 啟動畫面
- 目標: 首頁、註冊頁、忘記密碼

**對應需求**
- FR-002: 使用者登入
- FR-003: 社群登入

---

## SCR-002 註冊頁

... (更多畫面規格)
```

---

## 快速開始指令

### 從 SRS 生成 UI

```
請讀取 /path/to/SRS-ProjectName-1.0.md
並生成完整的 UI 畫面

輸出設定:
- 目錄: ./generated-ui/
- 格式: HTML + React
- 風格: 現代簡約，主色 #6366F1
```

### 從 SDD 生成 UI

```
請讀取 /path/to/SDD-ProjectName-1.0.docx
根據畫面規格生成 UI

輸出設定:
- 目錄: ./generated-ui/
- 格式: SwiftUI
- 嚴格遵循 SDD 定義的畫面結構
```

### 從多份文件生成

```
請讀取以下文件:
1. /path/to/SRS-ProjectName-1.0.md (功能需求)
2. /path/to/SDD-ProjectName-1.0.md (畫面規格)

整合兩份文件，生成完整 UI

輸出設定:
- 目錄: ./generated-ui-ProjectName/
- 格式: 全平台 (HTML/React/SwiftUI/Compose)
```

---

## 生成檢查清單

```
文件解析
□ 文件格式識別正確
□ 章節結構解析完整
□ 功能需求萃取完整
□ 使用者角色識別
□ 畫面規格提取

UI 規劃
□ 畫面清單完整
□ 流程邏輯正確
□ 狀態覆蓋完整
□ 導航結構合理

生成品質
□ 程式碼可執行
□ 風格一致
□ 命名規範
□ 目錄結構清晰

輸出完整性
□ 所有畫面已生成
□ 共用元件已建立
□ 路由配置已產生
□ 生成報告已輸出
```
