# 無障礙設計指南 (Accessibility)

本文件提供符合 WCAG 2.1 標準的無障礙設計原則與實作指南。

## 目錄
1. [無障礙概述](#無障礙概述)
2. [WCAG 原則](#wcag-原則)
3. [視覺無障礙](#視覺無障礙)
4. [聽覺無障礙](#聽覺無障礙)
5. [運動無障礙](#運動無障礙)
6. [認知無障礙](#認知無障礙)
7. [平台特定指南](#平台特定指南)
8. [測試與驗證](#測試與驗證)

---

## 無障礙概述

### 為什麼需要無障礙設計？

```
全球約 15% 人口有某種形式的障礙
無障礙設計受益者:
├── 永久性障礙: 視障、聽障、肢障
├── 暫時性障礙: 骨折、眼睛發炎
├── 情境性障礙: 強光下、吵雜環境、單手操作
└── 年長使用者: 視力退化、動作變慢
```

### 無障礙效益

| 面向 | 效益 |
|------|------|
| 使用者 | 更多人能使用您的產品 |
| 法規 | 符合無障礙法規要求 |
| SEO | 改善搜尋引擎優化 |
| 品質 | 整體使用體驗提升 |
| 品牌 | 展現社會責任 |

---

## WCAG 原則

### WCAG 2.1 四大原則 (POUR)

```
P - Perceivable (可感知)
    資訊必須能被使用者感知

O - Operable (可操作)
    介面元件必須能被操作

U - Understandable (可理解)
    資訊與操作必須能被理解

R - Robust (穩健)
    內容必須能被各種輔助技術詮釋
```

### 合規等級

| 等級 | 說明 | 要求 |
|------|------|------|
| A | 基本 | 最低門檻 |
| AA | 標準 | 一般網站/App 目標 |
| AAA | 最高 | 特定需求 |

---

## 視覺無障礙

### 顏色對比

**WCAG 對比度要求:**

| 等級 | 一般文字 | 大型文字 |
|------|----------|----------|
| AA | 4.5:1 | 3:1 |
| AAA | 7:1 | 4.5:1 |

**大型文字定義:**
```
≥ 18pt (24px) 一般字重
≥ 14pt (18.5px) 粗體
```

**對比度範例:**
```
✅ 良好: #000000 on #FFFFFF = 21:1
✅ 通過 AA: #595959 on #FFFFFF = 7:1
⚠️ 僅大字: #757575 on #FFFFFF = 4.48:1
❌ 失敗: #AAAAAA on #FFFFFF = 2.32:1
```

**工具推薦:**
- WebAIM Contrast Checker
- Stark (Figma 外掛)
- Color Contrast Analyzer

### 不只依賴顏色

```
❌ 錯誤: 僅用紅色標示錯誤
✅ 正確: 紅色 + 圖標 + 文字說明

❌ 錯誤: 連結僅用藍色區分
✅ 正確: 藍色 + 底線

❌ 錯誤: 圖表僅用顏色區分
✅ 正確: 顏色 + 圖案/標籤
```

### 文字大小與縮放

```
最小字級: 16px (內文)
支援 200% 縮放不破版
使用相對單位: rem, em
避免固定高度容器

CSS 範例:
html { font-size: 100%; }  /* 16px */
body { font-size: 1rem; }
h1 { font-size: 2rem; }    /* 32px */
```

### 焦點指示器

```
❌ 移除: outline: none;
✅ 自訂但保持可見:

:focus {
  outline: 2px solid #0066CC;
  outline-offset: 2px;
}

:focus-visible {
  /* 僅鍵盤導航時顯示 */
  outline: 2px solid #0066CC;
}
```

### 圖片替代文字

**alt 文字原則:**
```
資訊性圖片: 描述內容與目的
  <img alt="折線圖顯示銷售額從 1 月到 6 月成長 50%">

裝飾性圖片: 空 alt 或 CSS 背景
  <img alt="" role="presentation">

功能性圖片: 描述功能
  <img alt="搜尋">

複雜圖表: 提供長描述
  <img alt="2024 年銷售報告" aria-describedby="chart-desc">
  <p id="chart-desc">詳細說明...</p>
```

### 動畫安全

```css
/* 尊重使用者偏好 */
@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
  }
}

/* 避免閃爍 */
不得超過每秒 3 次閃爍
```

---

## 聽覺無障礙

### 影片字幕

**字幕類型:**
| 類型 | 說明 |
|------|------|
| 隱藏式字幕 (CC) | 可開關，包含音效描述 |
| 開放式字幕 | 永久顯示 |
| 語音轉文字 | 即時產生 |

**字幕規範:**
```
一次顯示: 1-2 行
字數: 每行最多 32 字元
顯示時間: 至少 1 秒
同步: 與音訊同步
位置: 不遮擋重要內容
```

### 音訊替代

```
提供:
- 影片逐字稿
- 音檔文字版本
- 口述影像 (視障者)
```

### 不自動播放

```
❌ 自動播放有聲音的影片
✅ 預設靜音或由使用者啟動
✅ 提供暫停/停止控制
```

---

## 運動無障礙

### 鍵盤導航

**可鍵盤操作的元素:**
```html
<!-- 原生可聚焦 -->
<button>按鈕</button>
<a href="#">連結</a>
<input type="text">
<select>...</select>
<textarea>...</textarea>

<!-- 自訂元素需加 tabindex -->
<div role="button" tabindex="0">自訂按鈕</div>
```

**鍵盤操作規範:**

| 按鍵 | 操作 |
|------|------|
| Tab | 移至下一個元素 |
| Shift + Tab | 移至上一個元素 |
| Enter / Space | 啟動按鈕/連結 |
| Arrow Keys | 在群組內移動 |
| Escape | 關閉 Modal/Dropdown |
| Home / End | 移至首/尾項目 |

**焦點順序:**
```
邏輯順序: 由左至右、由上至下
避免焦點陷阱
Modal 開啟時: 焦點移入 Modal
Modal 關閉時: 焦點回到觸發元素
```

### 觸控目標

```
最小觸控目標:
iOS: 44 × 44 pt
Android: 48 × 48 dp
Web: 44 × 44 px

間距: 相鄰目標間至少 8px
```

### 手勢替代

```
❌ 僅支援滑動手勢
✅ 提供按鈕替代

❌ 僅支援捏合縮放
✅ 提供 +/- 按鈕

❌ 需要精確拖曳
✅ 提供其他輸入方式
```

### 時間限制

```
❌ 限時操作無法延長
✅ 提供延長或關閉選項
✅ 自動儲存使用者進度
✅ 警告即將逾時
```

---

## 認知無障礙

### 清晰的結構

**標題層級:**
```html
<h1>頁面主標題</h1>        <!-- 每頁僅一個 -->
  <h2>章節標題</h2>
    <h3>子章節</h3>
    <h3>子章節</h3>
  <h2>章節標題</h2>

❌ 跳過層級: h1 → h3
❌ 僅用於樣式而非結構
```

**地標區域:**
```html
<header role="banner">
  <nav role="navigation">...</nav>
</header>

<main role="main">
  <article>...</article>
</main>

<aside role="complementary">...</aside>

<footer role="contentinfo">...</footer>
```

### 一致的導航

```
✅ 每頁相同位置的導航
✅ 一致的命名與圖示
✅ 提供多種導航方式 (選單、搜尋、網站地圖)
✅ 顯示當前位置 (Breadcrumb、高亮)
```

### 錯誤處理

**表單驗證:**
```html
<!-- 清楚的錯誤訊息 -->
<label for="email">Email</label>
<input
  id="email"
  type="email"
  aria-invalid="true"
  aria-describedby="email-error"
>
<span id="email-error" role="alert">
  請輸入有效的 Email 格式，例如: name@example.com
</span>

✅ 具體說明錯誤
✅ 提供修正建議
✅ 錯誤訊息在欄位附近
✅ 不只依賴顏色
```

### 簡單的語言

```
✅ 使用常見詞彙
✅ 短句子 (20 字以內)
✅ 主動語態
✅ 避免行話與縮寫
✅ 提供縮寫說明: <abbr title="World Wide Web">WWW</abbr>
```

---

## 平台特定指南

### iOS 無障礙

**VoiceOver 支援:**
```swift
// 設定無障礙標籤
button.accessibilityLabel = "新增項目"

// 設定提示
button.accessibilityHint = "點兩下以新增項目到清單"

// 設定特徵
button.accessibilityTraits = .button

// 群組元素
view.accessibilityElements = [label, textField, button]
```

**Dynamic Type:**
```swift
label.font = UIFont.preferredFont(forTextStyle: .body)
label.adjustsFontForContentSizeCategory = true
```

**減少動態效果:**
```swift
if UIAccessibility.isReduceMotionEnabled {
    // 使用簡單動畫或無動畫
}
```

### Android 無障礙

**TalkBack 支援:**
```kotlin
// 設定內容描述
button.contentDescription = "新增項目"

// 重要性
view.importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_YES

// 自訂操作
ViewCompat.setAccessibilityDelegate(view, object : AccessibilityDelegateCompat() {
    override fun onInitializeAccessibilityNodeInfo(
        host: View,
        info: AccessibilityNodeInfoCompat
    ) {
        super.onInitializeAccessibilityNodeInfo(host, info)
        info.addAction(
            AccessibilityNodeInfoCompat.AccessibilityActionCompat(
                AccessibilityNodeInfoCompat.ACTION_CLICK,
                "新增項目"
            )
        )
    }
})
```

**可縮放文字:**
```kotlin
textView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
```

### Web 無障礙 (WAI-ARIA)

**ARIA 角色:**
```html
<!-- 地標 -->
<div role="navigation">...</div>
<div role="main">...</div>
<div role="search">...</div>

<!-- 小工具 -->
<div role="tablist">
  <button role="tab" aria-selected="true">Tab 1</button>
  <button role="tab" aria-selected="false">Tab 2</button>
</div>

<!-- 即時區域 -->
<div role="alert">錯誤訊息</div>
<div role="status" aria-live="polite">載入中...</div>
```

**ARIA 屬性:**
```html
<!-- 狀態 -->
aria-expanded="true|false"
aria-selected="true|false"
aria-checked="true|false|mixed"
aria-disabled="true"
aria-hidden="true"

<!-- 關係 -->
aria-labelledby="id"
aria-describedby="id"
aria-controls="id"
aria-owns="id"

<!-- 即時區域 -->
aria-live="polite|assertive|off"
aria-atomic="true|false"
```

**範例：Accordion:**
```html
<div class="accordion">
  <h3>
    <button
      aria-expanded="false"
      aria-controls="panel-1"
    >
      Section 1
    </button>
  </h3>
  <div
    id="panel-1"
    role="region"
    aria-labelledby="btn-1"
    hidden
  >
    Content...
  </div>
</div>
```

**範例：Modal:**
```html
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
>
  <h2 id="modal-title">確認刪除</h2>
  <p>確定要刪除這個項目嗎？</p>
  <button>取消</button>
  <button>確認</button>
</div>
```

---

## 測試與驗證

### 自動化測試工具

| 工具 | 類型 | 說明 |
|------|------|------|
| axe | 瀏覽器擴充 | 自動檢測 WCAG 問題 |
| WAVE | 瀏覽器擴充 | 視覺化顯示問題 |
| Lighthouse | Chrome 內建 | 無障礙分數 |
| Pa11y | CLI | CI/CD 整合 |
| jest-axe | 測試庫 | 自動化測試 |

### 手動測試清單

**鍵盤測試:**
```
□ 所有功能可用鍵盤操作
□ 焦點順序合理
□ 焦點指示器可見
□ 無焦點陷阱
□ 快捷鍵不衝突
```

**螢幕閱讀器測試:**
```
□ 所有內容可被朗讀
□ 圖片有替代文字
□ 表單欄位有標籤
□ 錯誤訊息被宣告
□ 動態內容更新被宣告
```

**視覺測試:**
```
□ 對比度符合標準
□ 200% 縮放不破版
□ 不只依賴顏色
□ 動畫可關閉
□ 文字可調整大小
```

**認知測試:**
```
□ 標題結構正確
□ 連結文字清楚
□ 錯誤訊息明確
□ 說明文字足夠
□ 操作可復原
```

### 螢幕閱讀器測試

| 平台 | 螢幕閱讀器 |
|------|------------|
| macOS | VoiceOver (內建) |
| Windows | NVDA (免費), JAWS |
| iOS | VoiceOver (內建) |
| Android | TalkBack (內建) |

**VoiceOver 快捷鍵 (macOS):**
```
開啟/關閉: Cmd + F5
導航: VO + 左右箭頭
標題: VO + Cmd + H
連結: VO + Cmd + L
表單: VO + Cmd + J
```

### 無障礙聲明範本

```markdown
# 無障礙聲明

## 承諾
[公司名稱] 致力於確保我們的 [產品名稱] 對所有人都能使用，
包括身心障礙者。

## 合規狀態
本產品符合 WCAG 2.1 AA 等級標準。

## 已知限制
- [列出已知問題與預計修復時間]

## 回饋
如果您在使用過程中遇到任何無障礙問題，請聯繫我們：
- Email: accessibility@example.com
- 電話: 02-1234-5678

## 最後更新
2024 年 1 月 15 日
```

---

## 快速檢查清單

### 設計師檢查清單

```
視覺
□ 顏色對比度 ≥ 4.5:1
□ 不只依賴顏色傳達資訊
□ 最小字級 16px
□ 觸控目標 ≥ 44px
□ 焦點狀態明顯

互動
□ 所有功能可鍵盤操作
□ 焦點順序合理
□ 提供手勢替代方案
□ 錯誤訊息清楚

內容
□ 標題層級正確
□ 連結文字有意義
□ 圖片有替代文字
□ 表單有標籤
```

### 開發者檢查清單

```
HTML
□ 使用語義化標籤
□ 標題層級正確 (h1-h6)
□ 表單有關聯 label
□ 圖片有 alt
□ 表格有 caption 和 th

ARIA
□ 自訂元件有正確 role
□ 狀態用 aria-* 表示
□ 動態內容用 aria-live
□ Modal 有 aria-modal

鍵盤
□ 可 Tab 導航
□ 可 Enter/Space 啟動
□ 可 Escape 關閉
□ 焦點管理正確

測試
□ axe 檢測通過
□ 鍵盤測試通過
□ 螢幕閱讀器測試
□ 縮放測試通過
```
