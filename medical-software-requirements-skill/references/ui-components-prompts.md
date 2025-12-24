# UI 元件 AI Prompt 清單

本文件提供各類 UI 元件的 AI 產生 Prompt 範本。

## 目錄
1. [按鈕 (Buttons)](#按鈕-buttons)
2. [輸入框 (Inputs)](#輸入框-inputs)
3. [卡片 (Cards)](#卡片-cards)
4. [導航 (Navigation)](#導航-navigation)
5. [圖標 (Icons)](#圖標-icons)
6. [對話框 (Dialogs)](#對話框-dialogs)
7. [列表 (Lists)](#列表-lists)
8. [圖表 (Charts)](#圖表-charts)
9. [醫療專用元件](#醫療專用元件)

---

## 按鈕 (Buttons)

### Primary Button

```
UI design of a primary action button for mobile app,
rectangular with 8px rounded corners,
filled solid blue (#2196F3) background,
white text "Submit" centered,
height 48px width 200px,
showing normal state,
subtle shadow for depth,
Material Design style,
transparent background PNG,
high resolution
```

### Button States 組合

```
UI button component design showing 4 states in a row:
normal (blue #2196F3),
pressed (darker blue #1976D2),
disabled (gray #BDBDBD),
loading (with spinner),
each button 120px wide 48px tall,
8px rounded corners,
white text,
clean flat design,
transparent background
```

### Floating Action Button (FAB)

```
Floating action button (FAB) design,
circular 56px diameter,
blue (#2196F3) background,
white plus (+) icon centered,
Material Design elevation shadow,
Android style,
transparent background PNG
```

### Text Button

```
Text button UI component,
no background fill,
blue (#2196F3) text "Learn More",
subtle hover state indicator,
uppercase letters,
clean minimal design,
transparent background
```

---

## 輸入框 (Inputs)

### Text Field

```
Text input field UI design for mobile,
rectangular with 4px rounded corners,
outlined style with gray border,
placeholder text "Enter your name",
label "Name" floating above,
height 56px width 300px,
Material Design text field,
transparent background PNG
```

### Text Field States

```
Text input field showing 4 states vertically:
empty with placeholder,
focused with blue border (#2196F3),
filled with content,
error with red border (#F44336) and error message,
each field 280px wide,
clean Material Design style
```

### Search Bar

```
Search bar UI component,
pill shape with rounded ends,
light gray (#F5F5F5) background,
magnifying glass icon on left,
placeholder "Search patients...",
height 48px width 320px,
iOS or Material Design style,
transparent background
```

### Password Field

```
Password input field design,
outlined text field,
password dots (•••••••) as content,
eye icon on right for visibility toggle,
"Password" label,
height 56px,
Material Design style
```

---

## 卡片 (Cards)

### Basic Card

```
UI card component design,
white background,
8px rounded corners,
subtle shadow (elevation 2),
padding 16px,
width 320px height 180px,
placeholder for title and content areas,
clean minimal design
```

### Patient Info Card (醫療)

```
Medical patient information card UI,
white background with subtle shadow,
top section: patient avatar (circle), name, ID,
middle section: age, gender, blood type badges,
bottom section: last visit date, status indicator,
rounded corners 12px,
width 340px,
healthcare professional style
```

### Data Display Card

```
Dashboard data card UI design,
white background,
icon in top left (chart icon, blue),
large number "1,234" as main metric,
small label "Total Patients" below,
percentage change indicator "+12%",
12px rounded corners,
clean data visualization style
```

### Action Card

```
Action card with image UI,
top: placeholder image area (16:9 ratio),
bottom: white area with title and description,
right arrow icon for navigation,
12px rounded corners,
subtle shadow,
width 300px
```

---

## 導航 (Navigation)

### Bottom Navigation Bar

```
Mobile bottom navigation bar design,
5 items: Home, Search, Add, Notifications, Profile,
icons with labels below,
center item (Add) highlighted or elevated,
active item in blue (#2196F3),
inactive items in gray,
white background,
iOS or Android style,
full width bar
```

### Tab Bar

```
Tab bar UI component,
3 tabs: "Overview", "Details", "History",
active tab with blue underline indicator,
horizontal layout,
Material Design style,
white background,
width 360px
```

### App Header

```
Mobile app header bar design,
left: back arrow icon,
center: "Patient Details" title,
right: more options (three dots) icon,
height 56px,
white background or blue (#2196F3) background with white icons,
Android/iOS style
```

### Sidebar / Drawer

```
Mobile drawer menu design,
top: user avatar and name,
menu items with icons: Dashboard, Patients, Schedule, Settings,
active item highlighted,
bottom: logout button,
width 280px,
white background,
Material Design style
```

---

## 圖標 (Icons)

### System Icons Set

```
Set of 12 minimal line icons for medical app:
home, user, calendar, bell, settings, search,
heart, clipboard, pill, stethoscope, chart, message,
24x24 size each,
2px stroke weight,
single color (can be blue #2196F3 or black),
consistent style,
arranged in 4x3 grid,
transparent background
```

### Medical Icons Set

```
Medical healthcare icon set, 9 icons:
heart rate, blood pressure, temperature,
medication, syringe, bandage,
hospital bed, ambulance, medical cross,
filled style with rounded corners,
blue (#2196F3) color,
32x32 each,
arranged in 3x3 grid
```

### Navigation Icons

```
Navigation icon set for mobile app:
home (house), back arrow, forward arrow,
menu (hamburger), close (X), more (3 dots),
search (magnifying glass), share, bookmark,
24x24 each, 2px stroke,
outlined style,
black or gray color
```

---

## 對話框 (Dialogs)

### Alert Dialog

```
Mobile alert dialog UI design,
centered modal with white background,
top: warning icon (yellow triangle),
title: "Confirm Action",
message: "Are you sure you want to proceed?",
two buttons: "Cancel" (text) and "Confirm" (filled blue),
rounded corners 16px,
dim background overlay,
width 300px
```

### Bottom Sheet

```
Bottom sheet modal UI design,
white background with top handle bar,
rounded top corners 20px,
list of options with icons:
"Share", "Edit", "Delete",
each option 56px height,
subtle dividers between items,
Android Material Design style
```

### Snackbar / Toast

```
Snackbar notification UI,
dark gray (#323232) background,
white text "Item saved successfully",
optional action button "UNDO" in blue,
rounded corners 4px,
floating at bottom of screen,
width 344px height 48px
```

---

## 列表 (Lists)

### Simple List

```
List UI design with 4 items,
each item: left icon, title, subtitle, right chevron,
height 72px per item,
subtle dividers between items,
white background,
Material Design list style,
width 360px
```

### Patient List Item (醫療)

```
Patient list item UI for healthcare app,
left: circular avatar,
center: patient name (bold), patient ID below,
right: status badge (green "Active" or red "Critical"),
chevron for navigation,
height 80px width 360px,
subtle shadow or divider
```

### Chat List

```
Messaging list UI design,
3 conversation items,
each: avatar, sender name, message preview, timestamp,
unread indicator (blue dot) for first item,
height 72px per item,
modern messaging app style
```

---

## 圖表 (Charts)

### Line Chart

```
Simple line chart UI for health data,
X axis: days of week (Mon-Sun),
Y axis: values 0-100,
single blue line with data points,
grid lines subtle gray,
white background,
clean minimal style,
width 320px height 200px
```

### Bar Chart

```
Horizontal bar chart UI,
4 bars showing different metrics,
blue bars with values,
labels on left,
clean healthcare dashboard style,
width 300px height 240px
```

### Pie/Donut Chart

```
Donut chart UI design,
4 segments in different colors,
center shows total number,
legend below with color indicators,
clean data visualization style,
width 200px height 200px plus legend
```

---

## 醫療專用元件

### Vital Signs Display

```
Vital signs display card UI for medical app,
showing heart rate: 72 BPM with heart icon,
blood pressure: 120/80 mmHg,
temperature: 36.5°C,
SpO2: 98%,
each metric in its own section,
color coded (green normal, red critical),
medical monitor style,
dark or white background
```

### Medication Card

```
Medication information card UI,
pill icon with medication name,
dosage: "500mg",
frequency: "2 times daily",
time indicators: morning and evening icons,
"Take with food" instruction,
refill reminder indicator,
rounded corners,
healthcare professional style
```

### Patient Wristband

```
Patient ID wristband display UI,
horizontal band shape,
patient photo (small circle),
name, DOB, MRN number,
barcode at bottom,
allergy alert indicator (red),
hospital style wristband design
```

### Alert Banner

```
Clinical alert banner UI,
full width,
red (#F44336) background for critical,
white warning icon and text,
"Critical: Abnormal Lab Result",
dismiss X button on right,
height 56px
```

### Appointment Slot

```
Appointment time slot UI,
time: "09:00 - 09:30",
patient name and type of visit,
status indicator (confirmed/pending),
duration badge,
calendar style design,
height 72px width 320px
```

---

## Prompt 技巧總結

### 結構模板

```
[元件類型] UI design for [平台],
[形狀/尺寸描述],
[顏色/風格描述],
[內容/文字描述],
[狀態/互動描述],
[設計風格] style,
transparent background PNG,
high resolution
```

### 關鍵詞彙

**風格：**
- Material Design
- iOS style
- Flat design
- Minimal
- Modern

**狀態：**
- normal / default
- pressed / active
- disabled
- focused
- hover
- loading

**背景：**
- transparent background
- white background
- dark background

**品質：**
- high resolution
- clean design
- professional
- pixel perfect
