# Dark Mode 設計指南

## Dark Mode 原則

### 設計目標
| 目標 | 說明 |
|------|------|
| 降低眼睛疲勞 | 低光環境下減少亮度刺激 |
| 省電 | OLED 螢幕黑色像素不發光 |
| 美觀 | 現代感、專業感 |
| 無障礙 | 光敏感使用者需求 |

### 核心原則
```
✅ 不是簡單反轉顏色
✅ 保持視覺層次與深度
✅ 維持品牌識別度
✅ 對比度符合 WCAG
✅ 減少大面積純白
```

---

## 顏色系統

### 表面層級 (Elevation)
```
Dark Mode 用亮度表達層級:

Layer 0 (Background):  #121212  ████████
Layer 1 (Surface):     #1E1E1E  ████████
Layer 2 (Card):        #252525  ████████
Layer 3 (Modal):       #2C2C2C  ████████
Layer 4 (Popup):       #333333  ████████

↑ 越高層級越亮
```

### 調色盤對照
| Token | Light Mode | Dark Mode |
|-------|------------|-----------|
| `background` | #FFFFFF | #121212 |
| `surface` | #F5F5F5 | #1E1E1E |
| `primary` | #1976D2 | #90CAF9 |
| `on-primary` | #FFFFFF | #000000 |
| `text-primary` | #212121 | #E0E0E0 |
| `text-secondary` | #757575 | #9E9E9E |
| `border` | #E0E0E0 | #333333 |
| `error` | #D32F2F | #EF5350 |
| `success` | #388E3C | #66BB6A |

### 語義色調整
```
Primary 品牌色:
Light: 飽和度高，深色
Dark:  飽和度降低，淺色 (避免刺眼)

Error/Warning:
Light: 正常飽和度
Dark:  亮度提高，飽和度略降

Text:
Light: 近黑色 (#212121)
Dark:  非純白 (#E0E0E0, 87% opacity)
```

---

## 對比度規範

### WCAG 對比度
| 元素 | Light Mode | Dark Mode | 要求 |
|------|------------|-----------|------|
| 正文 | 12:1 | 9:1 | ≥4.5:1 AA |
| 標題 | 15:1 | 11:1 | ≥3:1 |
| 禁用文字 | 3:1 | 3:1 | 可辨識即可 |
| 圖標 | 4.5:1 | 4.5:1 | ≥3:1 |

### 文字透明度
```
Dark Mode 文字 (白底):
├── High emphasis:    87% → rgba(255,255,255,0.87)
├── Medium emphasis:  60% → rgba(255,255,255,0.60)
├── Disabled:         38% → rgba(255,255,255,0.38)
└── Hint:             38% → rgba(255,255,255,0.38)
```

---

## 元件適配

### 卡片與陰影
```css
/* Light Mode */
.card-light {
  background: #FFFFFF;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* Dark Mode - 用亮度代替陰影 */
.card-dark {
  background: #1E1E1E;
  box-shadow: none; /* 或極淡陰影 */
  border: 1px solid rgba(255,255,255,0.05);
}
```

### 圖片處理
```
照片類:
├── 降低亮度 (brightness: 0.9)
├── 或加深色疊加層

圖標/插畫:
├── SVG: 動態換色
├── PNG: 提供 Dark 版本
└── 或使用 CSS filter: invert(1)

Logo:
├── 彩色 Logo: 通常不變
├── 黑色 Logo: 提供白色版本
```

### 輸入元件
| 狀態 | Light | Dark |
|------|-------|------|
| Default | 灰框白底 | 淺灰框深底 |
| Focus | 品牌色框 | 品牌色框(亮) |
| Filled | 白底 | 深灰底 |
| Error | 紅框 | 亮紅框 |

---

## Design Tokens

### Token 結構 (支援主題)
```json
{
  "color": {
    "background": {
      "$value": "{color.gray.50}",
      "$dark": "{color.gray.900}"
    },
    "text-primary": {
      "$value": "{color.gray.900}",
      "$dark": "{color.gray.100}"
    },
    "primary": {
      "$value": "#1976D2",
      "$dark": "#90CAF9"
    }
  }
}
```

### CSS Variables
```css
:root {
  --color-bg: #FFFFFF;
  --color-surface: #F5F5F5;
  --color-text: #212121;
  --color-primary: #1976D2;
}

[data-theme="dark"] {
  --color-bg: #121212;
  --color-surface: #1E1E1E;
  --color-text: #E0E0E0;
  --color-primary: #90CAF9;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --color-bg: #121212;
    /* ... */
  }
}
```

---

## 平台實作

### iOS (SwiftUI)
```swift
// 自動適配系統主題
Color(.systemBackground)  // 自動 Light/Dark
Color(.label)             // 自動文字色

// 自訂主題色
extension Color {
    static let brandPrimary = Color("BrandPrimary") // Assets 定義
}

// 檢測當前模式
@Environment(\.colorScheme) var colorScheme

if colorScheme == .dark {
    // Dark mode specific
}
```

### Android (Compose)
```kotlin
// Material 3 自動主題
MaterialTheme(
    colorScheme = if (isSystemInDarkTheme())
        darkColorScheme() else lightColorScheme()
)

// 自訂調色盤
private val DarkColorScheme = darkColorScheme(
    primary = Color(0xFF90CAF9),
    background = Color(0xFF121212),
    surface = Color(0xFF1E1E1E)
)
```

### React/Web
```tsx
// CSS Variables + Context
const ThemeContext = createContext<'light' | 'dark'>('light');

function App() {
  const [theme, setTheme] = useState<'light' | 'dark'>(
    window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark' : 'light'
  );

  return (
    <div data-theme={theme}>
      <ThemeContext.Provider value={theme}>
        {children}
      </ThemeContext.Provider>
    </div>
  );
}
```

---

## 切換策略

### 三態切換
```
┌─────────────────────────────────┐
│  ☀️ Light │ 🌙 Dark │ ⚙️ System │
└─────────────────────────────────┘

System: 跟隨裝置設定
Light:  強制淺色
Dark:   強制深色
```

### 轉場動畫
```css
/* 平滑切換 */
* {
  transition: background-color 200ms ease, color 200ms ease;
}

/* 或全局淡入淡出 */
html.theme-transitioning {
  transition: opacity 150ms ease;
}
```

---

## 檢查清單

### 設計師
```
□ 建立 Dark Mode 調色盤
□ 所有元件有 Dark 版本
□ 對比度符合 WCAG AA
□ 圖片/圖標適配
□ 品牌色有 Dark 變體
□ 陰影改用層級亮度
```

### 開發者
```
□ 使用語義化 Token
□ 支援系統主題偵測
□ 提供三態切換
□ 主題偏好持久化
□ 切換有過渡動畫
□ 測試所有頁面
```
