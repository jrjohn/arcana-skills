# 動效設計指南 (Motion Design)

## 動效原則

### 核心原則
| 原則 | 說明 | 範例 |
|------|------|------|
| **有意義** | 動效服務於功能 | 指引視線、確認操作 |
| **自然** | 符合物理直覺 | 慣性、重力、彈性 |
| **快速** | 不阻礙使用者 | 200-500ms 為主 |
| **一致** | 全 App 統一語言 | 相同元素相同動效 |

### 動效用途
```
功能性動效:
├── 導航轉場 (頁面切換)
├── 狀態變化 (Loading → Success)
├── 視覺回饋 (點擊、Hover)
└── 引導注意 (新功能提示)

裝飾性動效:
├── 品牌表達 (Logo 動畫)
├── 情感連結 (空狀態插圖)
└── 愉悅感 (成就慶祝)
```

---

## 時間與緩動

### 時間標準
| Token | 時長 | 用途 |
|-------|------|------|
| `duration.instant` | 100ms | 顏色、透明度 |
| `duration.fast` | 200ms | 小元素、Hover |
| `duration.normal` | 300ms | 大部分互動 |
| `duration.slow` | 400ms | 大型元素、Modal |
| `duration.slower` | 500ms | 頁面轉場 |

### 緩動函數 (Easing)
```css
/* 標準緩動 */
--ease-out: cubic-bezier(0, 0, 0.2, 1);      /* 進入 */
--ease-in: cubic-bezier(0.4, 0, 1, 1);       /* 離開 */
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1); /* 移動 */

/* 彈性緩動 */
--ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
--ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);

/* 強調緩動 */
--ease-expressive: cubic-bezier(0.2, 0, 0, 1);
```

### 選擇緩動
| 場景 | 緩動 | 原因 |
|------|------|------|
| 元素進入 | ease-out | 快進慢出，感覺迎接 |
| 元素離開 | ease-in | 慢進快出，不留戀 |
| 位置移動 | ease-in-out | 自然加減速 |
| 強調/慶祝 | bounce/spring | 活潑有彈性 |

---

## 轉場模式

### 頁面轉場
```
共享元素轉場 (Shared Element):
┌────────┐     ┌────────────────┐
│ [img]  │ →→→ │    [img]       │
│ title  │     │    title       │
│ desc   │     │    content...  │
└────────┘     └────────────────┘
列表項          詳情頁
```

### 轉場類型
| 類型 | 動畫 | 使用場景 |
|------|------|----------|
| **Push** | 水平滑入 | 前進導航 |
| **Pop** | 水平滑出 | 返回導航 |
| **Modal** | 底部滑入 | 彈窗、Sheet |
| **Fade** | 淡入淡出 | Tab 切換 |
| **Shared** | 元素過渡 | 列表→詳情 |
| **Expand** | 從原點展開 | FAB→全屏 |

### 平台轉場規範
| 平台 | 前進 | 返回 | Modal |
|------|------|------|-------|
| iOS | 右滑入 | 左滑出 | 底部滑入 |
| Android | 淡入+縮放 | 淡出 | 底部滑入 |
| Web | 淡入 | 淡入 | 淡入+縮放 |

---

## Micro-interactions

### 按鈕互動
```
Default → Hover → Press → Release
  │         │        │        │
  │     scale:1.02   │    scale:1
  │     shadow↑   scale:0.98   │
  │                shadow↓     │
  └──────────────────────────────
         200ms      100ms
```

### 常見 Micro-interactions
| 元件 | 互動 | 動效 |
|------|------|------|
| Button | Hover | 放大 1.02x, 陰影加深 |
| Button | Press | 縮小 0.98x |
| Switch | Toggle | 圓點滑動 + 背景變色 |
| Checkbox | Check | 打勾路徑動畫 |
| Input | Focus | 邊框變色 + Label 上移 |
| Card | Hover | 浮起 (translateY -4px) |
| Like | Tap | 心跳縮放 + 粒子效果 |

### 載入狀態
```
Skeleton Loading:
┌─────────────────┐
│ ░░░░░░░░░░░░░░░ │ ← shimmer 動畫
│ ░░░░░░░░        │   從左到右掃過
│ ░░░░░░░░░░░     │
└─────────────────┘

Spinner: 旋轉 (1s linear infinite)
Progress: 進度條填充
Pulse: 透明度脈動 (0.5 ↔ 1)
```

---

## 動效程式碼

### CSS 動畫
```css
/* 進入動畫 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.element-enter {
  animation: fadeInUp 300ms var(--ease-out) forwards;
}

/* Skeleton shimmer */
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
```

### SwiftUI 動畫
```swift
// 基本動畫
withAnimation(.easeOut(duration: 0.3)) {
    isExpanded.toggle()
}

// 彈性動畫
withAnimation(.spring(response: 0.4, dampingFraction: 0.6)) {
    scale = 1.0
}

// 轉場
.transition(.asymmetric(
    insertion: .move(edge: .trailing),
    removal: .move(edge: .leading)
))
```

### Jetpack Compose 動畫
```kotlin
// 狀態動畫
val size by animateDpAsState(
    targetValue = if (expanded) 200.dp else 100.dp,
    animationSpec = spring(dampingRatio = 0.6f)
)

// 進入/離開動畫
AnimatedVisibility(
    visible = isVisible,
    enter = fadeIn() + slideInVertically(),
    exit = fadeOut() + slideOutVertically()
)
```

---

## Lottie/Rive 輸出

### 動畫資源規格
| 格式 | 用途 | 大小建議 |
|------|------|----------|
| Lottie (.json) | 複雜向量動畫 | < 50KB |
| Rive (.riv) | 互動式動畫 | < 100KB |
| APNG | 簡單循環 | < 200KB |
| GIF | 相容性優先 | < 500KB |

### 輸出清單
```
📁 animations/
├── 📁 loading/
│   ├── spinner.json
│   └── skeleton.json
├── 📁 feedback/
│   ├── success.json
│   ├── error.json
│   └── celebration.json
├── 📁 onboarding/
│   └── intro-animation.json
└── 📁 empty-states/
    ├── no-data.json
    └── no-connection.json
```

---

## 無障礙考量

### Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

### 動效無障礙規則
```
✅ 提供 reduced-motion 替代方案
✅ 避免閃爍 (< 3次/秒)
✅ 動畫可暫停/停止
✅ 不依賴動畫傳達資訊
❌ 自動播放超過 5 秒的動畫
```

---

## 動效 Token 輸出

### JSON Token
```json
{
  "motion": {
    "duration": {
      "instant": "100ms",
      "fast": "200ms",
      "normal": "300ms",
      "slow": "400ms"
    },
    "easing": {
      "standard": "cubic-bezier(0.4, 0, 0.2, 1)",
      "enter": "cubic-bezier(0, 0, 0.2, 1)",
      "exit": "cubic-bezier(0.4, 0, 1, 1)",
      "spring": "cubic-bezier(0.175, 0.885, 0.32, 1.275)"
    }
  }
}
```
