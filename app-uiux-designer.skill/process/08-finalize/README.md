# 08-finalize: Final Verification

## 進入條件
- 07-feedback 已完成
- SDD/SRS 已更新

## 退出條件
- 所有驗證通過
- 流程完成報告已產生

## 步驟

### Step 1: 追溯驗證

```bash
node ~/.claude/skills/app-requirements-skill/scripts/verify-traceability.js [project-dir]
```

驗證項目：
- [ ] SRS → SDD 追溯 100%
- [ ] SRS → SCR 追溯 100%
- [ ] 所有需求都有對應畫面

### Step 2: 合規檢查

```bash
node ~/.claude/skills/app-requirements-skill/scripts/compliance-checker.js [project-dir]
```

檢查項目：
- [ ] TRACE-100: 追溯覆蓋率 100%
- [ ] DOC-SYNC: 文件同步 (MD/DOCX)
- [ ] UI-IMAGES: SDD 嵌入 UI 圖片
- [ ] MERMAID: 圖表使用 Mermaid
- [ ] UI-FLOW: UI Flow 已產出
- [ ] CLICK-COVER: 可點擊元素覆蓋 100%

### Step 3: UI Flow 最終驗證

```bash
cd 04-ui-flow
node validate-navigation.js
```

確認：
- [ ] 覆蓋率 = 100%
- [ ] 無無效元素
- [ ] 所有導航正確

### Step 4: 產生完成報告

建立 `ui-flow-completion-report.md`：

```markdown
# UI Flow Completion Report

## Project: {PROJECT_NAME}
## Date: YYYY-MM-DD

## Summary

| Metric | Value |
|--------|-------|
| Total Screens | XX |
| Navigation Coverage | 100% |
| Templates Used | XX |
| Screenshots Generated | XX |

## Deliverables

### UI Flow HTML (04-ui-flow/)
- [ ] index.html - Navigation index
- [ ] ui-flow-diagram.html - Flow diagram
- [ ] {module}/*.html - Screen prototypes
- [ ] images/ - Screenshots

### Updated Documents
- [ ] SDD with UI prototype references
- [ ] SRS with Screen References
- [ ] SRS with Inferred Requirements

## Verification Results

### Navigation Validation: ✅ PASSED
### Traceability: ✅ 100%
### Compliance: ✅ PASSED

## Notes

{Any additional notes or issues encountered}
```

### Step 5: 更新 current-process.json

```json
{
  "current_process": null,
  "progress": {
    "00-init": "completed",
    "01-discovery": "completed",
    "02-planning": "completed",
    "03-generation": "completed",
    "04-validation": "completed",
    "05-diagram": "completed",
    "06-screenshot": "completed",
    "07-feedback": "completed",
    "08-finalize": "completed"
  },
  "notes": "UI Flow generation completed successfully."
}
```

## 完成標誌

當以下所有條件滿足時，UI Flow 生成流程完成：

1. ✅ 所有畫面 HTML 已產生
2. ✅ 導航覆蓋率 100%
3. ✅ ui-flow-diagram.html 已產生
4. ✅ 所有截圖已產生
5. ✅ SDD/SRS 已更新並重新產生 DOCX
6. ✅ 追溯和合規檢查通過
7. ✅ 完成報告已產生

## 後續步驟

UI Flow 完成後，可進行：

1. **使用者測試** - 使用 HTML 原型進行可用性測試
2. **開發交接** - 將設計規格交付開發團隊
3. **迭代更新** - 根據反饋更新 UI Flow
