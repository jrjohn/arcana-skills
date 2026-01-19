# 05-diagram: UI Flow Diagram Generation

## 進入條件

- [ ] 04-validation 已完成
- [ ] 導航覆蓋率 = 100%
- [ ] 所有畫面 HTML 已產生

## 退出條件

- [ ] `docs/ui-flow-diagram.html` (裝置選擇頁) 已建立
- [ ] `docs/ui-flow-diagram-ipad.html` 已產生所有 iPad 畫面卡片
- [ ] `docs/ui-flow-diagram-iphone.html` 已產生所有 iPhone 畫面卡片
- [ ] 所有畫面 iframe 可正常顯示
- [ ] 點擊卡片可開啟 device-preview.html
- [ ] **iPad/iPhone 箭頭位置正確對齊（BLOCKING）**

---

## ⚠️ 重要：iPad 和 iPhone 必須分開產生

> **MANDATORY**: 必須建立獨立的 iPad 和 iPhone 版本 HTML 檔案！
>
> - `docs/ui-flow-diagram.html` - 裝置選擇頁面
> - `docs/ui-flow-diagram-ipad.html` - iPad 專用版本
> - `docs/ui-flow-diagram-iphone.html` - iPhone 專用版本

**為何不能共用單一檔案？**

1. **卡片尺寸不同**：iPad 橫向 (200x140px) vs iPhone 直向 (120x260px)
2. **佈局間距不同**：iPad 卡片間距較大，iPhone 較緊湊
3. **箭頭座標不同**：箭頭必須根據卡片位置和中心點計算，無法共用
4. **iframe 縮放不同**：iPad (scale 0.168) vs iPhone (scale 0.305)

---

## 裝置規格對照表

| 參數 | iPad Pro 11" | iPhone 15 Pro |
|------|--------------|---------------|
| 原始尺寸 | 1194 x 834 | 393 x 852 |
| 卡片尺寸 | 200 x 140 px | 120 x 260 px |
| iframe 縮放 | scale(0.168) | scale(0.305) |
| 卡片間距 (X) | 260px | 160px |
| 行間距 (Y) | 280px | 340px |
| 方向 | 橫向 (Landscape) | 直向 (Portrait) |

---

## 步驟

### Step 1: 建立裝置選擇頁面

建立 `docs/ui-flow-diagram.html` 作為入口：

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <title>{{PROJECT_NAME}} - Screen Flow Diagram</title>
  <!-- ... styles ... -->
</head>
<body>
  <div class="selector-container">
    <div class="title">{{PROJECT_NAME}}</div>
    <div class="subtitle">選擇裝置檢視 UI Flow Diagram</div>

    <div class="device-cards">
      <a href="ui-flow-diagram-ipad.html" class="device-card ipad">
        <div class="device-name">iPad Pro 11"</div>
        <div class="device-spec">1194 x 834 (Landscape)</div>
        <div class="screens-count">{{TOTAL_SCREENS}} Screens</div>
      </a>

      <a href="ui-flow-diagram-iphone.html" class="device-card iphone">
        <div class="device-name">iPhone 15 Pro</div>
        <div class="device-spec">393 x 852 (Portrait)</div>
        <div class="screens-count">{{TOTAL_SCREENS}} Screens</div>
      </a>
    </div>
  </div>

  <script>
    // 支援 URL 參數自動跳轉
    const urlParams = new URLSearchParams(window.location.search);
    const device = urlParams.get('device');
    if (device === 'ipad') {
      window.location.href = 'ui-flow-diagram-ipad.html';
    } else if (device === 'iphone') {
      window.location.href = 'ui-flow-diagram-iphone.html';
    }
  </script>
</body>
</html>
```

### Step 2: 建立 iPad 版本 (ui-flow-diagram-ipad.html)

**iPad 佈局參數：**

```javascript
const layoutConfig = {
  cardWidth: 200,
  cardHeight: 140,
  cardSpacing: 260,   // 卡片水平間距
  rowHeight: 280,     // 行垂直間距
  startX: 60,
  startY: 200
};
```

**卡片 X 位置公式：**
```
X = startX + (column_index × cardSpacing)
// Col 0: 60, Col 1: 320, Col 2: 580, Col 3: 840, Col 4: 1100, Col 5: 1360, Col 6: 1620
```

**Row Y 位置公式：**
```
Y = startY + (row_index × rowHeight)
// Row 0: 200, Row 1: 480, Row 2: 760, Row 3: 1040, Row 4: 1320
```

**箭頭 Y 中心點：**
```
arrowY = cardTop + (cardHeight / 2)
// = cardTop + 70
```

**Card 模板 (iPad)：**

```html
<div class="screen-card module-{module}" style="left: {X}px; top: {Y}px;"
     onclick="openScreen('{folder}/SCR-{MODULE}-{NNN}-{name}.html')">
  <div class="ipad-frame">
    <div class="screen-id">{MODULE}-{NNN}</div>
    <div class="iframe-container">
      <iframe src="../{folder}/SCR-{MODULE}-{NNN}-{name}.html" loading="lazy"></iframe>
    </div>
  </div>
  <div class="screen-label">{畫面中文名稱}</div>
</div>
```

**iPad iframe CSS：**

```css
.screen-card .ipad-frame {
  width: 200px;
  height: 140px;
  border-radius: 14px;
  border: 3px solid #1a1a1a;
}

.screen-card .iframe-container iframe {
  width: 1194px;
  height: 834px;
  transform: scale(0.168);
  transform-origin: 0 0;
}
```

### Step 3: 建立 iPhone 版本 (ui-flow-diagram-iphone.html)

**iPhone 佈局參數：**

```javascript
const layoutConfig = {
  cardWidth: 120,
  cardHeight: 260,
  cardSpacing: 160,   // 卡片水平間距
  rowHeight: 340,     // 行垂直間距
  startX: 60,
  startY: 200
};
```

**卡片 X 位置公式：**
```
X = startX + (column_index × cardSpacing)
// Col 0: 60, Col 1: 220, Col 2: 380, Col 3: 540, Col 4: 700, Col 5: 860, Col 6: 1020
```

**Row Y 位置公式：**
```
Y = startY + (row_index × rowHeight)
// Row 0: 200, Row 1: 540, Row 2: 880, Row 3: 1220, Row 4: 1560
```

**箭頭 Y 中心點：**
```
arrowY = cardTop + (cardHeight / 2)
// = cardTop + 130
```

**Card 模板 (iPhone)：**

```html
<div class="screen-card module-{module}" style="left: {X}px; top: {Y}px;"
     onclick="openScreen('{folder}/SCR-{MODULE}-{NNN}-{name}.html')">
  <div class="iphone-frame">
    <div class="screen-id">{MODULE}-{NNN}</div>
    <div class="iframe-container">
      <iframe src="../{folder}/SCR-{MODULE}-{NNN}-{name}.html" loading="lazy"></iframe>
    </div>
  </div>
  <div class="screen-label">{畫面中文名稱}</div>
</div>
```

**iPhone iframe CSS：**

```css
.screen-card .iphone-frame {
  width: 120px;
  height: 260px;
  border-radius: 16px;
  border: 3px solid #1a1a1a;
}

.screen-card .iframe-container iframe {
  width: 393px;
  height: 852px;
  transform: scale(0.305);
  transform-origin: 0 0;
}
```

### Step 4: 計算並產生箭頭 (各版本獨立)

> ⚠️ **重要**：每個版本的箭頭座標必須獨立計算，不可共用！

**箭頭座標計算公式：**

```javascript
// 卡片右邊緣
const cardRightEdge = (col) => startX + (col * cardSpacing) + cardWidth;

// 卡片左邊緣
const cardLeftEdge = (col) => startX + (col * cardSpacing);

// 水平箭頭 (同一 row)
const horizontalArrow = (fromCol, toCol, rowY) => {
  const startX = cardRightEdge(fromCol) + 8;
  const endX = cardLeftEdge(toCol) - 8;
  const y = rowY + (cardHeight / 2);
  return `M ${startX} ${y} L ${endX} ${y}`;
};

// 垂直箭頭 (跨 row)
const verticalArrow = (col, fromRow, toRow) => {
  const x = startX + (col * cardSpacing) + (cardWidth / 2);
  const startY = startY + (fromRow * rowHeight) + cardHeight;
  const endY = startY + (toRow * rowHeight);
  return `M ${x} ${startY} L ${x} ${endY}`;
};

// 曲線箭頭 (跨模組)
const curvedArrow = (fromCol, fromRow, toCol, toRow) => {
  const sx = startX + (fromCol * cardSpacing) + (cardWidth / 2);
  const sy = startY + (fromRow * rowHeight) + cardHeight;
  const ex = startX + (toCol * cardSpacing) + (cardWidth / 2);
  const ey = startY + (toRow * rowHeight);
  const cy = (sy + ey) / 2;
  return `M ${sx} ${sy} Q ${sx} ${cy} ${ex} ${ey}`;
};
```

**iPad 箭頭範例 (AUTH 流程)：**

```html
<!-- Row 1 Y=200, 卡片中心 Y=270 -->
<!-- AUTH-001 (X=60, 右邊=260) → AUTH-002 (X=320, 左邊=320) -->
<path d="M 268 270 L 312 270" stroke="#6366F1" stroke-width="2.5" fill="none" marker-end="url(#arrow-auth)"/>

<!-- AUTH-002 (X=320, 右邊=520) → AUTH-003 (X=580, 左邊=580) -->
<path d="M 528 270 L 572 270" stroke="#6366F1" stroke-width="2.5" fill="none" marker-end="url(#arrow-auth)"/>
```

**iPhone 箭頭範例 (AUTH 流程)：**

```html
<!-- Row 1 Y=200, 卡片中心 Y=330 -->
<!-- AUTH-001 (X=60, 右邊=180) → AUTH-002 (X=220, 左邊=220) -->
<path d="M 188 330 L 212 330" stroke="#6366F1" stroke-width="2.5" fill="none" marker-end="url(#arrow-auth)"/>

<!-- AUTH-002 (X=220, 右邊=340) → AUTH-003 (X=380, 左邊=380) -->
<path d="M 348 330 L 372 330" stroke="#6366F1" stroke-width="2.5" fill="none" marker-end="url(#arrow-auth)"/>
```

### Step 5: 更新 index.html 裝置切換

`index.html` 的裝置切換需要連結到不同的 diagram 檔案：

```javascript
function switchDevice(device) {
  currentDevice = device;

  // 使用裝置專屬的 diagram 檔案
  const diagramFile = device === 'ipad'
    ? 'docs/ui-flow-diagram-ipad.html'
    : 'docs/ui-flow-diagram-iphone.html';

  // 更新 iframe src
  document.getElementById('flow-iframe').src = diagramFile;

  // 更新全螢幕連結
  document.getElementById('fullscreen-link').href = diagramFile;

  // 更新按鈕狀態
  document.getElementById('btn-iphone').classList.toggle('active', device === 'iphone');
  document.getElementById('btn-ipad').classList.toggle('active', device === 'ipad');
}
```

---

## 模組顏色對照表

| Module | CSS Class | 顏色 |
|--------|-----------|------|
| AUTH | `.module-auth` | #6366F1 (Indigo) |
| HOME | `.module-home` | #F59E0B (Amber) |
| VOCAB | `.module-vocab` | #10B981 (Emerald) |
| LEARN | `.module-learn` | #9C27B0 (Purple) |
| REPORT | `.module-report` | #06B6D4 (Cyan) |
| SETTING | `.module-setting` | #64748B (Slate) |
| PARENT | `.module-parent` | #EC4899 (Pink) |

---

## 阻斷條件 (BLOCKING)

> ⛔ **以下任一情況發生時，禁止進入下一節點**

1. 缺少 `ui-flow-diagram.html` (裝置選擇頁)
2. 缺少 `ui-flow-diagram-ipad.html`
3. 缺少 `ui-flow-diagram-iphone.html`
4. iPad 版本的 screen-card 數量 ≠ 實際畫面數
5. iPhone 版本的 screen-card 數量 ≠ 實際畫面數
6. iframe src 路徑錯誤（404）
7. **iPad 箭頭座標不正確（未對齊卡片）**
8. **iPhone 箭頭座標不正確（未對齊卡片）**
9. **箭頭數量 < 10**
10. **Row Labels 與畫面標籤重疊（視覺問題）**
11. **箭頭路徑有負數 X 座標（跑出畫面左側）**

**驗證指令：**

```bash
# 檢查三個檔案都存在
ls docs/ui-flow-diagram.html
ls docs/ui-flow-diagram-ipad.html
ls docs/ui-flow-diagram-iphone.html

# 檢查 iPad 版本 screen-card 數量
grep -c 'class="screen-card' docs/ui-flow-diagram-ipad.html

# 檢查 iPhone 版本 screen-card 數量
grep -c 'class="screen-card' docs/ui-flow-diagram-iphone.html

# 檢查 iPad 版本箭頭數量
IPAD_ARROWS=$(grep -c '<path.*marker-end' docs/ui-flow-diagram-ipad.html)
echo "iPad 箭頭數量: $IPAD_ARROWS"

# 檢查 iPhone 版本箭頭數量
IPHONE_ARROWS=$(grep -c '<path.*marker-end' docs/ui-flow-diagram-iphone.html)
echo "iPhone 箭頭數量: $IPHONE_ARROWS"

# 驗證箭頭數量
if [ "$IPAD_ARROWS" -lt 10 ] || [ "$IPHONE_ARROWS" -lt 10 ]; then
  echo "⛔ 錯誤：箭頭數量不足 (最少各 10 個)"
  exit 1
fi

# 檢查箭頭是否有負數 X 座標 (跑出畫面左側)
IPAD_NEG_X=$(grep -E 'Q -[0-9]+|L -[0-9]+|M -[0-9]+' docs/ui-flow-diagram-ipad.html 2>/dev/null | wc -l)
IPHONE_NEG_X=$(grep -E 'Q -[0-9]+|L -[0-9]+|M -[0-9]+' docs/ui-flow-diagram-iphone.html 2>/dev/null | wc -l)
if [ "$IPAD_NEG_X" -gt 0 ] || [ "$IPHONE_NEG_X" -gt 0 ]; then
  echo "⛔ 錯誤：箭頭路徑有負數 X 座標 (iPad: $IPAD_NEG_X, iPhone: $IPHONE_NEG_X)"
  exit 1
fi
```

---

## 檔案結構

```
docs/
├── ui-flow-diagram.html         # 裝置選擇頁 (入口)
├── ui-flow-diagram-ipad.html    # iPad 專用版本
└── ui-flow-diagram-iphone.html  # iPhone 專用版本
```

---

## 視覺對齊規則

### Row Label 位置規則

> ⚠️ Row Labels 必須位於當前 row 畫面卡片的「上方」，且不可與前一 row 的畫面標籤重疊。

**計算公式：**

```
Row Label Top = Row Cards Top - 80px (留出足夠間距)

例如：
- Row 0 畫面 Y = 200px → Row Label Top = 120px
- Row 1 畫面 Y = 480px (iPad) → Row Label Top = 440px (480 - 40)
- Row 1 畫面 Y = 540px (iPhone) → Row Label Top = 500px (540 - 40)
```

**驗證方式：**

```bash
# 檢查 row-label 位置是否合理
grep 'row-label.*top:' docs/ui-flow-diagram-*.html

# 確保 label top < 該 row 的畫面 top
# iPad:  Row 0 < 200, Row 1 < 480, Row 2 < 760
# iPhone: Row 0 < 200, Row 1 < 540, Row 2 < 880
```

### 箭頭邊界規則

> ⚠️ 所有箭頭路徑的 X 座標必須 >= 0，避免跑出畫面左側。

**禁止的路徑：**

```html
<!-- ❌ 錯誤：有負數 X 座標 -->
<path d="M 420 900 Q 420 1000 160 1000 Q -100 1000 -100 550" .../>

<!-- ✅ 正確：所有 X 座標 >= 0 -->
<path d="M 420 900 Q 420 950 240 950 Q 80 950 80 700" .../>
```

**驗證指令：**

```bash
# 應該回傳空白（無負數 X 座標）
grep -E 'Q -[0-9]+|L -[0-9]+|M -[0-9]+' docs/ui-flow-diagram-*.html
```

---

## ⚠️ Pre-Flight 驗證 (MANDATORY - 不可跳過)

在完成本節點前，**必須**執行以下驗證：

### 驗證腳本

```bash
#!/bin/bash
cd 04-ui-flow

echo "======================================"
echo "  05-diagram Pre-Flight 驗證"
echo "======================================"

ERRORS=0

# 1. 檢查三個檔案存在
echo ""
echo "📁 檔案存在檢查"
[ -f "docs/ui-flow-diagram.html" ] && echo "✅ ui-flow-diagram.html" || { echo "❌ 缺少 ui-flow-diagram.html"; ERRORS=$((ERRORS + 1)); }
[ -f "docs/ui-flow-diagram-ipad.html" ] && echo "✅ ui-flow-diagram-ipad.html" || { echo "❌ 缺少 ui-flow-diagram-ipad.html"; ERRORS=$((ERRORS + 1)); }
[ -f "docs/ui-flow-diagram-iphone.html" ] && echo "✅ ui-flow-diagram-iphone.html" || { echo "❌ 缺少 ui-flow-diagram-iphone.html"; ERRORS=$((ERRORS + 1)); }

# 2. 檢查無佔位符殘留
echo ""
echo "🔍 佔位符檢查"
PLACEHOLDERS_IPAD=$(grep -c 'PLACEHOLDER' docs/ui-flow-diagram-ipad.html 2>/dev/null || echo "0")
PLACEHOLDERS_IPHONE=$(grep -c 'PLACEHOLDER' docs/ui-flow-diagram-iphone.html 2>/dev/null || echo "0")
TEMPLATE_VARS_IPAD=$(grep -c '{{[^}]*}}' docs/ui-flow-diagram-ipad.html 2>/dev/null || echo "0")
TEMPLATE_VARS_IPHONE=$(grep -c '{{[^}]*}}' docs/ui-flow-diagram-iphone.html 2>/dev/null || echo "0")

[ "$PLACEHOLDERS_IPAD" -eq 0 ] && echo "✅ iPad 無 PLACEHOLDER" || { echo "❌ iPad 有 $PLACEHOLDERS_IPAD 個 PLACEHOLDER"; ERRORS=$((ERRORS + 1)); }
[ "$PLACEHOLDERS_IPHONE" -eq 0 ] && echo "✅ iPhone 無 PLACEHOLDER" || { echo "❌ iPhone 有 $PLACEHOLDERS_IPHONE 個 PLACEHOLDER"; ERRORS=$((ERRORS + 1)); }
[ "$TEMPLATE_VARS_IPAD" -eq 0 ] && echo "✅ iPad 無模板變數" || { echo "❌ iPad 有 $TEMPLATE_VARS_IPAD 個未替換模板變數"; ERRORS=$((ERRORS + 1)); }
[ "$TEMPLATE_VARS_IPHONE" -eq 0 ] && echo "✅ iPhone 無模板變數" || { echo "❌ iPhone 有 $TEMPLATE_VARS_IPHONE 個未替換模板變數"; ERRORS=$((ERRORS + 1)); }

# 3. 檢查 screen-card 數量
echo ""
echo "📱 畫面卡片數量"
IPAD_CARDS=$(grep -c 'class="screen-card' docs/ui-flow-diagram-ipad.html 2>/dev/null || echo "0")
IPHONE_CARDS=$(grep -c 'class="screen-card' docs/ui-flow-diagram-iphone.html 2>/dev/null || echo "0")
IPAD_COUNT=$(find . -name "SCR-*.html" -not -path "./iphone/*" 2>/dev/null | wc -l | tr -d ' ')
IPHONE_COUNT=$(find iphone -name "SCR-*.html" 2>/dev/null | wc -l | tr -d ' ')

echo "iPad diagram 卡片: $IPAD_CARDS / iPad 畫面: $IPAD_COUNT"
echo "iPhone diagram 卡片: $IPHONE_CARDS / iPhone 畫面: $IPHONE_COUNT"

[ "$IPAD_CARDS" -eq "$IPAD_COUNT" ] && echo "✅ iPad 卡片數量正確" || { echo "❌ iPad 卡片數量不符"; ERRORS=$((ERRORS + 1)); }
[ "$IPHONE_CARDS" -eq "$IPHONE_COUNT" ] && echo "✅ iPhone 卡片數量正確" || { echo "❌ iPhone 卡片數量不符"; ERRORS=$((ERRORS + 1)); }
[ "$IPAD_CARDS" -gt 0 ] && echo "✅ iPad 卡片 > 0" || { echo "❌ iPad 無畫面卡片 (空白 diagram!)"; ERRORS=$((ERRORS + 1)); }
[ "$IPHONE_CARDS" -gt 0 ] && echo "✅ iPhone 卡片 > 0" || { echo "❌ iPhone 無畫面卡片 (空白 diagram!)"; ERRORS=$((ERRORS + 1)); }

# 4. 檢查箭頭數量
echo ""
echo "➡️ 導航箭頭數量"
IPAD_ARROWS=$(grep -c '<path.*marker-end' docs/ui-flow-diagram-ipad.html 2>/dev/null || echo "0")
IPHONE_ARROWS=$(grep -c '<path.*marker-end' docs/ui-flow-diagram-iphone.html 2>/dev/null || echo "0")

echo "iPad 箭頭: $IPAD_ARROWS"
echo "iPhone 箭頭: $IPHONE_ARROWS"

[ "$IPAD_ARROWS" -ge 10 ] && echo "✅ iPad 箭頭 >= 10" || { echo "❌ iPad 箭頭不足 (需 >= 10)"; ERRORS=$((ERRORS + 1)); }
[ "$IPHONE_ARROWS" -ge 10 ] && echo "✅ iPhone 箭頭 >= 10" || { echo "❌ iPhone 箭頭不足 (需 >= 10)"; ERRORS=$((ERRORS + 1)); }

# 5. 檢查箭頭邊界 (無負數 X 座標)
echo ""
echo "📐 箭頭邊界檢查"
IPAD_NEG_X=$(grep -E 'Q -[0-9]+|L -[0-9]+|M -[0-9]+' docs/ui-flow-diagram-ipad.html 2>/dev/null | wc -l | tr -d ' ')
IPHONE_NEG_X=$(grep -E 'Q -[0-9]+|L -[0-9]+|M -[0-9]+' docs/ui-flow-diagram-iphone.html 2>/dev/null | wc -l | tr -d ' ')

[ "$IPAD_NEG_X" -eq 0 ] && echo "✅ iPad 無負數 X 座標" || { echo "❌ iPad 有 $IPAD_NEG_X 個箭頭跑出左側邊界"; ERRORS=$((ERRORS + 1)); }
[ "$IPHONE_NEG_X" -eq 0 ] && echo "✅ iPhone 無負數 X 座標" || { echo "❌ iPhone 有 $IPHONE_NEG_X 個箭頭跑出左側邊界"; ERRORS=$((ERRORS + 1)); }

# 6. 結果
echo ""
echo "======================================"
if [ "$ERRORS" -eq 0 ]; then
  echo "✅ 05-diagram 驗證通過"
  exit 0
else
  echo "❌ 05-diagram 驗證失敗 - 發現 $ERRORS 個問題"
  echo ""
  echo "必須修復所有問題才能進入 06-screenshot"
  exit 1
fi
```

### 常見錯誤與修復

| 錯誤 | 原因 | 修復方式 |
|------|------|----------|
| 卡片數量為 0 | 只複製了模板，未填入實際畫面 | 依照 Step 2-3 填入所有 screen-card HTML |
| 有 PLACEHOLDER | 模板佔位符未替換 | 用實際 HTML 替換所有 `<!-- *_PLACEHOLDER -->` |
| 有模板變數 | `{{VAR}}` 未替換 | 用實際值替換所有 `{{變數}}` |
| 箭頭不足 | 未繪製導航路徑 | 依照 SDD Button Navigation 加入箭頭 SVG |
| iPad/iPhone 數量不符 | iPhone 版本未同步產生 | 確保 iphone/ 目錄有完整畫面 |
| Row Label 與畫面標籤重疊 | Label 位置太靠近前一 row 的卡片 | 將 label top 調整為 row top - 40~80px |
| 箭頭跑出左側邊界 | 曲線路徑使用負數 X 座標 | 修改路徑確保所有 X >= 60 |

---

## 下一節點

→ `process/06-screenshot/README.md` (截圖產生)
