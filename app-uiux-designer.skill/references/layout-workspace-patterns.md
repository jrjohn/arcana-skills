# Layout & Workspace Patterns — 版面機制與 Column Budget

> 補足本 skill 的最後一哩:`ux-audit-rubric.md` 給**原則**(視覺層次、漸進揭露)、`design-system.md` 給 **token 方法論**,但兩者都沒講「**一個實際頁面到底能排幾欄、設定/次要內容該去哪**」的**版面機制**。缺這一層,才會出現「技術上有畫面、實際被切成 5 格沒法用」。本檔把原則落到**可執行的版面法則 + 可量測門檻**,設計(uiux 節點)與稽核(PM 節點)、自動 gate 共用。
>
> 依據:Refactoring UI(視覺層次:3–4 層即足、去強調 section 標題)、NN/g Progressive Disclosure(把進階/次要功能延到次級畫面/抽屜,降認知負荷 up to 55%、掃描 Z-pattern、摺線上競爭元素 ≤7)、4/8-pt 間距系統、型階 ≥1.25。

---

## 0. 一句話心法

**畫面的水平寬度是稀缺資源,不是拿來平均切割的。** 一頁只該有**一個主導工作區**;其餘一切(設定、次要工具、輔助資訊)要嘛壓成一列工具列、要嘛收進漸進揭露的抽屜,**不准各自佔一個常駐欄跟主區搶寬**。

---

## 1. Column Budget（欄位預算)— 最重要的一條

把「同一垂直切面上、同時可見的欄」當**預算**來管,不是想加就加。

- **App shell 已先花掉 1 欄**:固定左側導覽列(nav)。feature 內容區是在**剩下的寬**裡排版。
- **一個 feature 內容區,桌機同時最多 2–3 欄**。超過就是認知過載(對應 rubric「等權重 N 等分堆疊」)。
- **🔴 自帶多欄的嵌入式編輯器,算它自己的 3 欄。** `@bpmn-io/form-js`、`bpmn-js`、任何「palette | 畫布 | 屬性」三件式編輯器,**掛上去的當下就已用掉 3 欄預算**。
  - ⟹ **推論(硬規則)**:一個 host 這種編輯器的頁面,**不得在它旁邊再放任何常駐欄**(設定欄、清單欄都不行)。編輯器要**吃滿整個內容區寬**。
- **算法**:`nav(1) + 你自己排的欄 + 嵌入編輯器的內部欄`。**> 3 就違規。**
  - form-designer 舊版 = `nav(1) + 設定欄(1) + form-js(3)` = **5** ❌ → 這就是使用者看到的「5 格」。

---

## 2. 四種版面原型（Archetype)— 每頁先歸類再排版

每個 feature 頁**先選一種原型**,照它的欄數與「設定/次要去哪」排,不要每頁重想。

### A. List–Detail（清單–詳情)
- 版面:`清單欄(minmax(260,340)) | 詳情(1fr)`,**2 欄**。
- 選清單一列 → 右側詳情換內容,**版面不 reflow**。
- 用於:approvals(收件匣)、users、instance-history。

### B. Builder（建構器)★ 本案重點
- 版面:**頂部 Toolbar(一列) + 全寬主畫布**。**內容區 0 個自排常駐欄**(把預算全給編輯器)。
- 設定(目標、引擎、載入/儲存)→ **頂部水平 toolbar**。
- 次要(AI 生成、範本目錄、上傳、匯入)→ **漸進揭露 drawer/offcanvas**,按鈕開。
- 用於:form-designer、process designer(bpmn-js)、任何嵌入式視覺編輯器。
- **關鍵**:主編輯器全寬時,它自帶的 palette|畫布|屬性 三欄才有正常寬;一旦旁邊塞常駐欄,畫布就餓死。

### C. Dashboard（儀表板)
- 版面:**KPI 摘要列(卡片) + 其下最多 2 個內容欄**(圖/表)。
- 先摘要後細節(summary-before-detail);細節可點 KPI 卡展開(漸進揭露)。
- 用於:home、evaluation、simulation、evolution。

### D. Form / Settings（表單/設定)
- 版面:**單一置中欄**(`max-width ~720px`),卡片垂直堆疊。
- 別為了填滿寬度硬拉兩欄 —— 長表單單欄最好讀(眼睛不用左右跳)。
- 用於:profile、settings、governance。

> 選型速查:**有嵌入式編輯器 → Builder**;**一主體 + 逐項詳情 → List-Detail**;**先看數字再鑽 → Dashboard**;**填欄位/調設定 → Form**。

---

## 3. 漸進揭露機制表（次要內容該用哪個容器)

| 內容性質 | 容器 | 例 |
|---|---|---|
| 次要但常用(隨時想開) | **Drawer / Offcanvas**(側滑,覆蓋不佔欄) | form-designer 的 AI 生成 + 範本目錄 |
| 進階/少用選項 | **Collapsible / Accordion**(「更多設定」) | 篩選器進階條件 |
| 稀用、單次動作 | **Modal**(對話框) | 發佈確認、刪除確認 |
| 情境編輯(選了才需要) | **一個**情境側板(選取才出現,如 org 屬性欄) | org designer 選節點 |

**鐵律**:同一頁**最多一個**常駐/情境側板;要更多就改 drawer(覆蓋式,不佔版面寬)。**重用平台既有 `right-panel` 的 off-canvas 模式**(它是 toggled overlay、不佔欄),不要每頁重造抽屜。

---

## 4. 反樣式案例庫（Worked Examples)

### 案例 1:form-designer「5 格」(本案主因)
- **前**:`row` = `col-lg-4 設定欄`(目標節點+AI+目錄)`| col-lg-8 編輯器`;右欄 host 的 form-js 自帶 3 欄 → `nav(1)+設定(1)+form-js(3)=5`。畫布("Build your form")被擠到極窄。
- **後(Builder 原型)**:
  ```
  ┌ Toolbar: 流程ID  節點ID  引擎▾   [載入][儲存]        [＋AI/範本 ▸] ┐
  ├──────────────────────────────────────────────────────────────────┤
  │  form-js 全寬:  [ palette | ───── 畫布 ───── | 屬性 ]              │
  └──────────────────────────────────────────────────────────────────┘
     (AI 生成 / 上傳 / 既有表單目錄 → 右側 drawer,按鈕開)
  ```
  欄數 = `nav(1)+form-js(3)=4`,且**編輯器全寬**,畫布正常。
- **對應原則**:rubric「等權重 N 等分堆疊」+ Column Budget + Builder 原型 + 漸進揭露。

### 案例 2:org designer 情境側板
- ✅ 已做對:屬性欄**選取節點才出現**(`.has-selection` 才 3 欄),平時 2 欄不留空欄。這是「情境側板 ≤1」的正解,可當正面教材。

---

## 5. Design Token 綁定（不准 hardcode)

版面與樣式一律走 token,不寫死 hex/px:
- **本專案 token 表**:`dashboard/src/app/shared/styles/_tokens.scss`(`:root` CSS 變數)。間距用 4/8-pt scale、型階 ≥1.25、顏色走語意角色(surface/border/text/brand/semantic)。方法論見 `design-system.md`。
- **對齊 Bootstrap**:優先復用 `--bs-*`(`--bs-body-color`/`--bs-border-color`/`--bs-tertiary-bg`…),新 token 疊在其上,**避免雙套色**。
- ❌ 禁止:component SCSS 出現裸 hex(`#0d6efd`/`#6c757d`/`#f8f9fa`…)或裸 px 間距;一律 `var(--…)`。

---

## 6. 可量測門檻（給 uiux-review gate 用)

以下可被 `dashboard/e2e/uiux-review.mjs` 自動量(Playwright 量 DOM 幾何),違反即記:

| 檢查 | 門檻 | 嚴重度 |
|---|---|---|
| 橫向溢出 | `body/主容器 scrollWidth ≤ clientWidth` | **FAIL** |
| Column budget | 同一垂直切面同時可見內容欄 ≤ 3(含嵌入編輯器內部欄) | **FAIL** |
| Panel 過窄 | 任一並排 panel 可用寬 ≥ ~320px(或該裝置斷點下自動收合) | WARN |
| 空帶(empty band) | 主區下方無 > ~30% viewport 高的空白 | WARN |
| 觸控目標 | 主要動作 ≥ 44×44px | WARN |

**推進策略**:先 **advisory**(WARN 不擋),讓既有頁逐頁遷移;主要頁都過後轉**硬 gate**(FAIL 擋 merge,同 coverage/arch-qube)。

---

## 7. 設計/稽核自檢清單（uiux 節點產、PM 節點驗)

- [ ] 本頁歸了哪個原型?欄數符合該原型上限?
- [ ] `nav + 自排欄 + 嵌入編輯器內部欄 ≤ 3`?有嵌入編輯器 → 它全寬、旁邊 0 常駐欄?
- [ ] 次要/進階/稀用內容都進了 toolbar 或漸進揭露容器,沒各佔一欄?
- [ ] 常駐/情境側板 ≤ 1?更多用 drawer?
- [ ] 有明確主導區(視覺層次 3–4 層),不是等權重平分?
- [ ] 全走 token,無裸 hex/px?
- [ ] 空/載入/錯誤狀態齊(見 rubric §7)?
