# AI Prompt 範本庫

完整的 AI 圖像產生 Prompt 範本，適用於 Midjourney、DALL-E、Stable Diffusion 等工具。

## 目錄
1. [App Icon Prompts](#app-icon-prompts)
2. [UI 畫面 Prompts](#ui-畫面-prompts)
3. [插圖 Prompts](#插圖-prompts)
4. [背景圖 Prompts](#背景圖-prompts)
5. [Prompt 結構指南](#prompt-結構指南)

---

## App Icon Prompts

### 醫療健康類

```
Professional medical healthcare app icon,
minimalist heart with pulse line design,
inside a rounded shield shape,
primary color #2196F3 (blue),
secondary color #FFFFFF (white),
clean flat design style,
no text no letters,
1024x1024 resolution,
centered composition,
suitable for iOS and Android app stores
```

```
Modern healthcare app icon,
stethoscope forming a circular shape,
gradient from #1976D2 to #42A5F5,
white highlights,
subtle 3D effect,
medical professional aesthetic,
no text,
1024x1024
```

```
Telemedicine app icon design,
abstract person with medical cross,
teal #009688 and white color scheme,
minimalist geometric style,
rounded corners,
friendly and trustworthy,
no text,
1024x1024
```

### 健身運動類

```
Fitness tracking app icon,
dynamic running figure silhouette,
gradient orange #FF5722 to yellow #FFC107,
motion blur effect,
energetic and active,
no text,
1024x1024
```

### 金融商業類

```
Finance banking app icon,
abstract coin or currency symbol,
gradient from #1E88E5 to #42A5F5,
secure and professional appearance,
minimal geometric design,
no text,
1024x1024
```

### 教育學習類

```
Educational learning app icon,
open book with lightbulb above,
friendly blue #2196F3 color,
flat illustration style,
knowledge and wisdom concept,
no text,
1024x1024
```

---

## UI 畫面 Prompts

### 登入畫面

```
Mobile app login screen UI/UX design,
modern minimal style,
top: company logo placeholder,
center: email and password input fields,
primary action button "Sign In",
social login options (Google, Apple),
bottom: forgot password and sign up links,
blue #2196F3 accent color,
white background,
iPhone 14 Pro frame,
high fidelity mockup
```

### 儀表板 Dashboard

```
Mobile dashboard home screen design,
healthcare patient management app,
top: greeting "Good morning, Dr. Smith" with avatar,
stats cards row: patients, appointments, alerts,
upcoming appointments list section,
quick action buttons grid,
bottom navigation bar,
clean white and blue color scheme,
Material Design style,
realistic UI mockup
```

### 資料列表

```
Mobile list view screen design,
patient records list,
search bar at top,
filter chips below search,
list items with: avatar, name, ID, status badge,
pull to refresh indicator,
floating action button (FAB) bottom right,
white background with subtle dividers,
iOS style
```

### 詳細資料頁

```
Mobile detail screen UI design,
patient profile page,
top: large profile photo with name,
info section: age, gender, blood type, allergies,
tabs: Overview, History, Documents,
vital signs chart,
action buttons: Call, Message, Schedule,
modern healthcare app aesthetic
```

---

## 插圖 Prompts

### 空狀態插圖

```
Flat illustration for empty state,
character looking at empty clipboard or folder,
blue and gray muted colors,
friendly cartoon style,
subtle shadow,
"no data" or "no results" concept,
transparent or white background,
400x400 size
```

```
Minimal line illustration,
magnifying glass finding nothing,
light blue #64B5F6 single color,
simple stroke design,
empty search results concept,
vector style,
transparent background
```

### 成功狀態插圖

```
Celebration illustration,
checkmark inside circle with confetti,
green #4CAF50 primary color,
happy successful completion concept,
flat design with subtle gradients,
transparent background,
300x300 size
```

### 錯誤狀態插圖

```
Error state illustration,
confused character with warning sign,
red #F44336 accent color,
friendly not scary,
problem or issue concept,
flat illustration style,
transparent background,
400x400
```

### Onboarding 插圖

```
Mobile app onboarding illustration,
doctor using tablet device,
patient health monitoring concept,
blue and teal color scheme,
modern flat illustration style,
medical healthcare theme,
friendly and approachable,
600x400 size
```

```
Onboarding illustration slide 2,
connected devices concept,
smartphone, smartwatch, health sensors,
data flowing between devices,
gradient blue background,
tech-forward illustration style,
600x400
```

---

## 背景圖 Prompts

### 登入背景

```
Abstract gradient background for mobile app,
soft blue #E3F2FD to white gradient,
subtle geometric patterns,
medical healthcare theme,
professional and calming,
1080x1920 mobile resolution,
can have UI elements overlaid
```

### 儀表板背景

```
Subtle pattern background,
light gray #F5F5F5 base,
very subtle hexagon or grid pattern,
minimal and clean,
dashboard background texture,
tileable seamless pattern,
professional aesthetic
```

### 專業醫療背景

```
Healthcare medical background image,
blurred hospital corridor or clinic,
soft blue tint,
very subtle and muted,
bokeh light effects,
can overlay text and UI,
1920x1080 or larger
```

---

## Prompt 結構指南

### 基本結構

```
[主體描述], [風格描述], [顏色描述], [技術規格]
```

### 詳細結構

```
[What] 什麼東西
[Style] 什麼風格
[Color] 什麼顏色
[Mood] 什麼氛圍
[Technical] 技術規格
[Negative] 排除什麼
```

### 範例拆解

```
Professional medical healthcare app icon,     ← What
minimalist flat design style,                  ← Style
blue #2196F3 and white color scheme,          ← Color
clean and trustworthy appearance,              ← Mood
1024x1024 resolution,                          ← Technical
no text no letters no words                    ← Negative
```

---

## 工具特定語法

### Midjourney

```
/imagine prompt: [你的 prompt] --ar 1:1 --v 6 --style raw

參數說明:
--ar 1:1    長寬比 (1:1 正方形, 16:9 橫式)
--v 6       版本 6
--style raw 較少 AI 風格化
--no text   排除文字
--q 2       高品質
```

### DALL-E 3

```
直接描述即可，DALL-E 3 理解自然語言
建議加上:
- 明確的尺寸: "1024x1024"
- 排除項目: "no text, no watermarks"
- 風格指定: "flat design", "vector style"
```

### Stable Diffusion

```
Prompt: [正面描述]
Negative Prompt: text, letters, words, watermark, signature, blurry, low quality

建議參數:
- Steps: 30-50
- CFG Scale: 7-12
- Sampler: DPM++ 2M Karras
```

---

## 醫療專用 Prompt 庫

### 臨床圖標

```
Medical vital signs icon set,
heart rate, blood pressure, temperature, SpO2,
line icon style,
2px stroke weight,
single color [#2196F3 or #424242],
24x24 size each,
medical dashboard icons,
transparent background
```

### 科別圖標

```
Medical specialty icons set,
cardiology (heart), neurology (brain),
orthopedics (bone), pediatrics (child),
dermatology (skin), ophthalmology (eye),
filled icon style,
consistent rounded design,
medical blue color,
32x32 each
```

### 醫療裝置

```
Medical device illustration,
[血壓計/血糖機/體溫計/血氧機],
isometric 3D style,
soft shadows,
white background,
product illustration style,
300x300 size
```

---

## Prompt 最佳實踐

### DO ✓

1. **具體描述** - "heart with pulse line" 而非 "heart"
2. **指定顏色** - 使用 hex code "#2196F3"
3. **指定尺寸** - "1024x1024 resolution"
4. **指定風格** - "flat design", "Material Design"
5. **排除文字** - "no text, no letters"
6. **指定用途** - "for iOS and Android app stores"

### DON'T ✗

1. 模糊描述 - "a nice icon"
2. 過多元素 - 一次描述太多東西
3. 矛盾指令 - "minimal but detailed"
4. 忽略尺寸 - 讓 AI 自行決定
5. 要求文字 - App Icon 不應有文字

### 迭代優化

1. 先產生基礎版本
2. 觀察結果，調整 prompt
3. 增加/減少細節
4. 調整風格關鍵字
5. 嘗試不同工具比較結果
