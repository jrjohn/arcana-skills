# UI 圖片嵌入 SDD 規範

本文件定義如何將 UI/UX 設計圖片嵌入 SDD (軟體設計規格書) 文件中。

## 為什麼要嵌入圖片？

| 方式 | 優點 | 缺點 |
|-----|------|------|
| **外部連結 (URL)** | 檔案小、即時更新 | 連結失效、需網路、無法離線檢視 |
| **直接嵌入圖片** | 文件獨立完整、可離線、法規送審友好 | 檔案較大 |

**IEC 62304 合規考量：** 法規送審時，文件必須獨立完整，不應依賴外部連結。因此建議將 UI 設計圖片直接嵌入 SDD 文件。

---

## 圖片規範

### 格式要求

| 屬性 | 建議值 | 說明 |
|-----|-------|------|
| **格式** | PNG (推薦) | 支援透明背景，無損壓縮 |
| | JPG | 適合照片類圖片 |
| **解析度** | @2x (推薦) | 確保 DOCX 輸出清晰 |
| | @1x | 僅供草稿或低解析度需求 |
| | @3x | 高解析度需求 |
| **色彩模式** | sRGB | 確保跨平台顯示一致 |
| **最大尺寸** | 2MB/圖片 | 避免文件過大 |

### 命名規範

```
SCR-{模組}-{序號}-{描述}.png
```

**範例：**
- `SCR-AUTH-001-login.png` - 登入畫面
- `SCR-AUTH-002-signup.png` - 註冊畫面
- `SCR-HOME-001-dashboard.png` - 首頁儀表板
- `SCR-TRAIN-001-game-selection.png` - 遊戲選擇畫面
- `SCR-REPORT-001-daily.png` - 每日報告畫面

### 目錄結構

```
{project}/
├── 02-design/
│   └── SDD/
│       ├── SDD-{project}-{version}.md
│       └── images/                    ← UI 圖片存放位置
│           ├── SCR-AUTH-001-login.png
│           ├── SCR-AUTH-002-signup.png
│           ├── SCR-HOME-001-dashboard.png
│           └── ...
│
└── 03-assets/
    └── ui-screens/                    ← 備用位置 (原始檔)
        ├── @1x/
        ├── @2x/
        └── @3x/
```

---

## Markdown 嵌入語法

### 基本語法

```markdown
![{圖片描述}](./images/{檔名}.png)
```

### 範例

```markdown
### 6.1 認證模組畫面設計

#### SCR-AUTH-001 登入畫面

![SCR-AUTH-001 登入畫面](./images/SCR-AUTH-001-login.png)

**畫面說明：**
- 頂部：App Logo
- 中部：電子郵件與密碼輸入欄位
- 底部：登入按鈕、忘記密碼連結、社群登入選項

**對應需求：** SRS-AUTH-001, SRS-AUTH-002
```

### 多狀態畫面

```markdown
#### SCR-AUTH-001 登入畫面

**預設狀態：**
![SCR-AUTH-001 登入畫面 - 預設](./images/SCR-AUTH-001-login-default.png)

**輸入中狀態：**
![SCR-AUTH-001 登入畫面 - 輸入中](./images/SCR-AUTH-001-login-input.png)

**錯誤狀態：**
![SCR-AUTH-001 登入畫面 - 錯誤](./images/SCR-AUTH-001-login-error.png)
```

---

## 從設計工具匯出

### Figma

1. 選擇要匯出的 Frame
2. 右側面板 → Export
3. 設定：
   - Format: PNG
   - Scale: 2x
   - Include "id" attribute: 取消勾選
4. 點擊 Export

### Sketch

1. 選擇 Artboard
2. File → Export → Export Selected...
3. 設定：
   - Format: PNG
   - Scale: 2x
4. Export

### Adobe XD

1. 選擇 Artboard
2. File → Export → Selected...
3. 設定：
   - Format: PNG
   - Export for: Design (2x)
4. Export

### Penpot

1. 選擇 Frame
2. 右鍵 → Export selection
3. 設定：
   - Type: PNG
   - Scale: 2
4. Export

---

## DOCX 轉換支援

`md-to-docx-converter.md` 中的轉換器已支援自動嵌入圖片。

### 轉換流程

```
1. 讀取 Markdown 檔案
2. 解析圖片語法 ![alt](path)
3. 讀取對應圖片檔案
4. 將圖片嵌入 DOCX
5. 輸出完整 DOCX 文件
```

### 支援的圖片路徑

| 路徑類型 | 範例 | 支援 |
|---------|------|------|
| 相對路徑 | `./images/xxx.png` | ✓ |
| 相對路徑 (無 ./) | `images/xxx.png` | ✓ |
| 絕對路徑 | `/path/to/xxx.png` | ✓ |
| URL | `https://...` | ✗ (不建議) |

---

## 最佳實踐

### Do's ✓

- 使用 @2x 解析度確保清晰度
- 使用 PNG 格式保持品質
- 遵循命名規範 `SCR-{模組}-{序號}-{描述}.png`
- 將圖片放在 `02-design/SDD/images/` 目錄
- 每張圖片加上文字說明
- 標註對應的 SRS 需求編號

### Don'ts ✗

- 不要使用外部 URL 連結
- 不要使用過大的圖片 (>2MB)
- 不要在圖片中包含敏感資訊
- 不要使用中文或空格作為檔名
- 不要遺漏圖片的 alt 描述

---

## 檢查清單

在完成 SDD UI 章節時，確認以下項目：

- [ ] 所有畫面都有對應的圖片
- [ ] 圖片命名符合規範
- [ ] 圖片解析度為 @2x
- [ ] 圖片格式為 PNG
- [ ] 圖片已放入 `images/` 目錄
- [ ] Markdown 中正確嵌入圖片
- [ ] 每張圖片都有文字說明
- [ ] 標註對應的 SRS 需求編號
- [ ] DOCX 轉換後圖片正常顯示
