# 07-feedback: Document Feedback (SDD/SRS 回補)

## 進入條件
- 06-screenshot 已完成
- 所有截圖已產生

## 退出條件
- SDD 已更新（UI 原型參考）
- SRS 已更新（Screen References, Inferred Requirements）
- DOCX 已重新產生

## 步驟

### Step 1: 更新 SDD

在 SDD 的每個 SCR-* 區塊中加入：

> ⚠️ **格式規範 (MANDATORY)**
> - **不使用表格**，直接嵌入圖片
> - **不保留 HTML 連結**
> - 圖片必須是真實嵌入，不能只是路徑文字

```markdown
##### UI 原型參考

**iPad 版本：**

![](images/ipad/SCR-AUTH-001-login.png)

**iPhone 版本：**

![](images/iphone/SCR-AUTH-001-login.png)
```

> **正確範例 vs 錯誤範例**
>
> ❌ 錯誤：使用表格
> ```markdown
> | Platform | Screenshot |
> |----------|------------|
> | iPad | ![](images/ipad/SCR-*.png) |
> ```
>
> ❌ 錯誤：保留 HTML 連結
> ```markdown
> | iPad | ![](images/ipad/SCR-*.png) | [連結](../04-ui-flow/...) |
> ```
>
> ✅ 正確：直接嵌入圖片
> ```markdown
> **iPad 版本：**
>
> ![](images/ipad/SCR-*.png)
> ```

### Step 2: 更新 SRS

#### 2a. Screen References 章節

```markdown
## Screen References

| Requirement | Screen(s) |
|-------------|-----------|
| REQ-AUTH-001 | SCR-AUTH-001-login |
| REQ-AUTH-002 | SCR-AUTH-002-register |
| ... | ... |
```

#### 2b. Inferred Requirements 章節

從 UI Flow 推導的導航需求：

```markdown
## Inferred Requirements (from UI Flow)

### REQ-NAV-001: Login Navigation
- **Source**: SCR-AUTH-001 Button Navigation
- **Description**: 登入成功後導航至角色選擇畫面
- **Acceptance Criteria**: 點擊登入按鈕後顯示 SCR-AUTH-004
- **Traceability**: SCR-AUTH-001 → SCR-AUTH-004
```

#### 2c. User Flows 章節

使用 Mermaid flowchart 更新：

```markdown
## User Flows

### 認證流程

\`\`\`mermaid
flowchart LR
    SCR-AUTH-001[登入] --> SCR-AUTH-004[角色選擇]
    SCR-AUTH-004 --> SCR-DASH-001[學童首頁]
    SCR-AUTH-004 --> SCR-DASH-002[家長首頁]
\`\`\`
```

### Step 3: 更新 Revision History

在 SDD 和 SRS 的 Revision History 中新增：

```markdown
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.1 | YYYY-MM-DD | Claude | Added UI prototype references from UI Flow |
```

### Step 4: 重新產生 DOCX

> ⚠️ **Markdown 格式規則**：轉換前確認 SDD/SRS 符合格式規範
> - Code Block（```）僅用於程式碼和 Mermaid 圖表
> - Use Case 禁止使用 Code Block，應使用粗體標籤 + 編號清單
> - 詳見：`~/.claude/skills/app-requirements-skill/references/sdd-standards.md`

```bash
# 安裝依賴（如未安裝）
cd ~/.claude/skills/app-requirements-skill && npm install docx

# 轉換 SDD
node ~/.claude/skills/app-requirements-skill/md-to-docx.js /path/to/SDD-*.md

# 轉換 SRS
node ~/.claude/skills/app-requirements-skill/md-to-docx.js /path/to/SRS-*.md
```

### Step 5: 驗證清單

- [ ] SDD 所有 SCR-* 區塊已更新
- [ ] SRS Screen References 章節已新增
- [ ] SRS Inferred Requirements 已新增
- [ ] SRS User Flows 已更新
- [ ] SDD 和 SRS Revision History 都已更新
- [ ] SDD.docx 和 SRS.docx 都已重新產生

### Step 6: UI 原型參考驗證 (BLOCKING)

> ⚠️ **必須通過以下驗證才能標記 07-feedback 為 completed**

```bash
#!/bin/bash
# UI 原型參考完整性驗證
cd {PROJECT}/02-design
SDD_FILE=$(ls SDD-*.md | head -1)

echo "🔍 驗證 UI 原型參考完整性..."

# 1. 統計 SDD 本文畫面數
SCREEN_COUNT=$(grep -c "^#### SCR-" "$SDD_FILE")

# 2. 統計有圖片參考的畫面數
IMAGE_REF_COUNT=$(grep -c "images/ipad/SCR-.*\.png" "$SDD_FILE")

# 3. 找出缺少圖片參考的畫面
echo ""
echo "📊 統計結果:"
echo "   SDD 畫面數: $SCREEN_COUNT"
echo "   有圖片參考: $IMAGE_REF_COUNT"

if [ "$SCREEN_COUNT" != "$IMAGE_REF_COUNT" ]; then
  echo ""
  echo "❌ 驗證失敗: 有 $(($SCREEN_COUNT - $IMAGE_REF_COUNT)) 個畫面缺少圖片參考"
  echo ""
  echo "缺少圖片參考的畫面:"
  grep "^#### SCR-" "$SDD_FILE" | sed 's/#### //' | sed 's/:.*//' | while read screen; do
    if ! grep -q "images/ipad/$screen.png" "$SDD_FILE"; then
      echo "  - $screen"
    fi
  done
  exit 1
fi

echo ""
echo "✅ 驗證通過: 所有 $SCREEN_COUNT 個畫面都有 UI 原型參考"
```

**驗證項目：**
- [ ] 每個 `#### SCR-*` 區塊都有 `##### UI 原型參考` 子區塊
- [ ] iPad 圖片路徑: `images/ipad/SCR-*.png`
- [ ] iPhone 圖片路徑: `images/iphone/SCR-*.png`
- [ ] 圖片檔案實際存在
- [ ] ⚠️ **格式檢查：不使用表格，不保留 HTML 連結**

## 輸出檔案

```
01-requirements/
└── SRS-{Project}-1.x.md    # 更新版
└── SRS-{Project}-1.x.docx  # 重新產生

02-design/
└── SDD-{Project}-1.x.md    # 更新版
└── SDD-{Project}-1.x.docx  # 重新產生
└── images/
    ├── ipad/               # 截圖（複製或連結）
    └── iphone/
```

## 注意事項

1. **圖片路徑** - 確保相對路徑正確
2. **DOCX 圖片嵌入** - md-to-docx.js 會自動嵌入圖片
3. **追溯完整性** - 確保所有 REQ 都有對應 SCR
