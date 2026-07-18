---
name: arcana-journey-test-skill
description: |
  以人為本的旅程測試 skill — 為 sdlc-code-flow 的 test 節點產生「persona 工作鏈」
  旅程(跨功能、以終點狀態驗收),取代單畫面控件可達性檢查的視角。
  Used by _gen_journeys (journey generation) in the agent test verb.
---

# 以人為本旅程測試(Persona Journey Chains)

你在為 journey-walk gate 產生旅程。最高原則(John 2026-07-18 定):**測「使用者的
一天能不能過」,不是「這個畫面能不能渲染」。**

## 核心觀念

- 一條旅程 = 一個 persona 完成一件**真實工作**,可跨多個畫面/功能(工作鏈)。
- goal 文字就是 runner 的劇本:runner 逐步 observe→decide→act 直到 REACHED/BLOCKED。
  把鏈寫成編號步驟放進 goal,runner 就會走完整條鏈。
- 驗收看**終點狀態**(清單多了一筆/狀態變了/成功訊息出現),不是「按鈕存在」。

## 產品主鏈庫(依 PR 綁定裁剪,選 1-2 條最相關的;可改編步驟)

1. **設計師鏈(產品自己的 AI 能力)**:開表單設計師 → 用 AI chat 產一張表單(輸入
   描述、等提議、套用)→ 存新版 → 開流程設計師 → 綁定該表單於節點 → (若允許變異)
   發佈;驗收=目錄出現新版本。
2. **員工鏈**:登入 → 待辦事項 → 開一張待填/草稿 → 填表 →(變異時)送出 → 追蹤
   清單出現該筆且狀態正確。
3. **審核鏈**:審核中心 → 開一件待簽 →(變異時)核准 → 該件從收件匣消失、歷史可見。
4. **模擬鏈(設計師)**:模擬頁 → 選/生情境 → 執行 → 報告出現且覆蓋率非零。

## 變異規則(嚴格)

- 預設 **NON-MUTATING**:每條 goal 以「確認〈動作控件〉存在且可達(不要真的按下)」
  收尾 — 除非環境明示 `JOURNEY_MUTATE=1`。
- **只有** `JOURNEY_MUTATE=1`(代表 API_TARGET 是隔離 stack,不是真後端)時才產
  「真的按下去+驗終點狀態」版 goal。preview 的 /api 預設代理到真後端 — 對真後端
  變異會污染資料,絕不允許。
- 變異版 goal 必含明確終點斷言:「送出後應看到〈成功訊息/清單新增一筆/狀態=X〉,
  看不到即 BLOCKED」。

## 以人為本觀察(每條旅程都要)

goal 末尾加一句:「過程中若遇到系統詞彙(使用者聽不懂的詞)、假資料、死按鈕、或
錯誤訊息不是人話,記為 finding(不算 BLOCKED,但要回報)」。runner 會把這些帶進
journeyFindings 給 PM 的以人為本 rubric 用。

## 輸出

嚴格 JSON `{"journeys":[{"persona","goal","start"}]}`:persona 用產品的真 persona
(員工/審核者/設計師/管理者);goal = zh 編號步驟工作鏈 + 驗收句 + 以人為本觀察句;
start = 鏈的起點路由。最多 3 條;單 PR 特化檢查交給 testcases,不必重複。
