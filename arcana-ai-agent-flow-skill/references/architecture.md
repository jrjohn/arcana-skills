# Arcana AI Agent Flow — 設計文件

> 通用工作流平台 + 即時監控：**單一 Kogito BPMN 引擎**（SonataFlow 已於 2026-06-09 退役）、
> 角色治理（ai / jenkins / human）、自助式可觀測 dashboard、AI↔human 無縫交接。
> 狀態：production（bluesea / workflow.arcana.boo）。開發策略 = **Mac-first**。

---

## 1. 願景 / 為什麼

打造一套**通用工作流平台**：流程定義（每節點配角色）→ 任務實例 → 即時監控 dashboard：
1. **任務/流程實例清單**（task list）。
2. **動態流程圖**（bpmn-js 標準 BPMN 圖，目前/已走節點即時高亮）。

角色：**AI（Claude CLI）**、**CI/CD（Jenkins）**、**human（交接）**；角色之上可長出組織 / RBAC。

平台承擔 Arcana CI 的三件自動化大事：紅 build 修復、綠 PR 自動合併 + 自動 release、
每小時健康治理 —— 全部以「可見、可審計的 BPMN 流程」呈現，取代不透明 inline 邏輯。

---

## 2. 設計精神（對齊 Cannerflow）

1. **流程三要素先行**：每個流程定義明確 (a) **目標**、(b) **流程設計**（節點+轉換）、
   (c) **角色**（每節點誰負責）。角色是一等公民。
2. **分層解耦**：引擎 → 統一 store（Data Index/PG）→ **語意/抽象層（rust read-API）** → UI（Angular）。
   每層可獨立替換；使用者**不直接碰** BPMN XML / 引擎內部。
3. **自助 + 抽象化**：dashboard 用「目標/流程/角色」語彙呈現；引擎內部（persistence blob、
   protobuf、kafka）由語意層隱藏。
4. **Cloud-Native / 彈性**：全容器化、宣告式流程定義（BPMN 檔即設計）。
5. **資料驅動 + 自動化省 toil**：process/task 是一等可查模型；AI/Jenkins 自動完成任務，
   AI 修不動時**交棒給人**而不是死路。

---

## 3. 核心決策

### 3.1 單引擎（2026-06-09 拍板，原雙引擎退役）

原設計為雙引擎（BPMN 人工決策 / SonataFlow 全自動）。退掉 SWF 的理由（逐條）：
- ci-maintenance 的 `.sw.yaml` 只是 3 個 `type: inject` 空殼 state —— 純 heartbeat，什麼都不做。
- **BPMN 是 SWF 的 superset**：SWF 的 ActionNode = BPMN ServiceTask/ScriptTask；BPMN 還多
  UserTask / gateway / 角色（ci-flow 全靠這些）。
- 「雲原生」不是 SWF 專利 —— Kogito BPMN 同為 Quarkus、可 k8s、可 kafka event。SWF 唯一
  真優勢（Knative scale-to-zero）在本平台兩引擎都常駐 container 的部署下完全沒用到。

結果：**一個 Kogito BPMN 引擎跑全部三個 process**，省 1 container + 185MB image + 一套 build。

### 3.2 其他拍板

| # | 決策 |
|---|---|
| 引擎 | **單一 Kogito BPMN**（ci-flow + merge-flow + ci-maintenance） |
| read-API | **arcana-cloud-rust**（Axum+SQLx），engine-agnostic，**只讀**，不驅動引擎 |
| 查詢層 | **單一 Kogito Data Index**（kafka events → PG，GraphQL） |
| 即時 | polling ~3-5s |
| 任務驅動 | **Rust task-worker**（task name dispatch；group=human 永不自動完成） |
| AI 執行 | agent-task-node（Claude CLI，**session persistence**，`sid` 貫穿整流程） |
| 治理執行面 | ci-maint-endpoint **唯讀**（零 docker socket）；真 prune/GC 留 host cron |
| 角色 | `ai`（Claude）、`jenkins`（CI/CD）、`human`（交接）；組織/RBAC 為未來 |

---

## 4. 架構（端到端）

```
Jenkins RunListener v7                          ci-scheduler（每 3600s）
  紅 build → POST /ci-flow（6h cooldown）          POST /ci-maintenance
  綠 PR build（fleet-wide）→ POST /merge-flow            │
                      │                                  │
                      ▼                                  ▼
        Kogito BPMN 引擎（Quarkus + persistence-jdbc + events addon）
          ci-flow / merge-flow / ci-maintenance（節點 GroupId=ai|jenkins|human）
                      │ process/task 事件（kafka）
                      ▼
        Kogito Data Index (postgresql)   ← 統一可查詢層（GraphQL）
                      ▼
   arcana-cloud-rust  /api/v1/workflows/*（Axum read-API，語意/抽象層）
     ├─ GET /processes                 實例清單（status/role 過濾）
     ├─ GET /processes/{id}            單一實例 + 目前狀態
     ├─ GET /processes/{id}/timeline   狀態時間軸
     ├─ GET /definitions/{id}/graph    流程圖（節點+邊+角色）
     └─ GET /definitions/{id}/bpmn     BPMN XML（BPMN_DIR）→ 前端 bpmn-js 畫標準圖
                      ▼ REST/JSON (+ polling)
   Angular dashboard（nginx 容器，單一 origin）
     ├─ Task List（實例表 + 角色 badge + status 過濾）
     ├─ bpmn-js 流程圖（visited/current/error 高亮；無 XML 才 fallback 自訂 SVG）
     └─ Handoff banner（parked human task → sid + claude --resume 指令可複製）

   workflow-task-worker（Rust，驅動流程）
     依 task name dispatch：triage/build/fix/decide/analyze/merge/release
       ai      → agent-task-node（claude，sid 續會話）
       jenkins → Jenkins build（觸發 + 等結果）
       human   → 永不自動完成 —— PARK（保持 Ready，等人）
     + reconciler（每 300s，引擎為真相源，雙向修 Data Index 漂移）
```

**為何不靠引擎原生 persistence 直查**：Kogito 原生 persistence 是 protobuf BYTEA blob、
completed 實例預設刪除 → 不可查。**Data Index 是標準可查詢層**。

---

## 5. 三個 Process

### 5.1 ci-flow — 紅 build 修復（含 human handoff）

`Triage(ai) → Build(jenkins) → [fixable? Fix(ai) → Build ⟲ 最多 3 次] → Decide(ai) → endGate`

- endGate：build 綠 **或** AI Decide 判定已解（`decision.startsWith("merge")`）→ End；
  否則 → **`humanFixTask`（group=human）** —— worker park 住（Ready 不動），dashboard 顯示
  交接 banner。人用 `docker exec -it agent-task-node claude --resume <sid>` 接手**同一個
  Claude 會話**，修好後 complete task `out=verify`（回 Build 驗證）或 `out=giveup`（→ failEnd）。
- `sid` 是 process var：triage/fix/decide 共用一個 Claude conversation（agent-task-node
  開 session persistence，`_sid` 回傳、worker `with_sid()` 線穿），dashboard variables 可見。
- endGate 條件注意：必須同時看 `buildResult` **和** `decision`，否則「main 上已解但本
  branch 沒重跑綠」會誤 park 人（2026-06-09 修過的真實 bug）。

### 5.2 merge-flow — 綠 PR 自動合併 + 自動 release

`Start → Merge(ai) → Release(ai) → End`

- **Merge**：agent `/task/merge` —— Claude 以 `gh pr view/checks` 驗證（open + 全綠 + 無
  conflict）→ `gh pr merge --squash --delete-branch`。agent 不可達時 defer（之後綠 build
  會再觸發），流程仍 complete。
- **Release**：agent `/task/release` —— **deterministic，不經 Claude**（release-please 是
  工具，無 AI/token）。由 prUrl 推 repo；無 release-please-config 的 repo skip；否則
  `npx release-please@16 github-release` 再 `release-pr`（API-only，免 clone）。
- **全自動閉環**：release-please 兩階段、每次 merge 冪等跑 —— release PR 本身綠 → 走同
  一條 automerge → merge-flow → Release node 切 tag+GitHub Release+changelog。終止條件：
  release/snapshot bump commit 是 `chore:`（non-releasable）。
- **前提**：conventional commits（Renovate 的 `chore(deps)`/`fix(deps)` 合格，會切 release；
  隨手 `Add X` 不會）。maven release-type repo 會週期性開 `X.Y.Z-SNAPSHOT` PR（正常）。

### 5.3 ci-maintenance — 每小時健康治理（唯讀）

`Scan → Analyze(ai) → Remediate → Verify`

- Scan/Remediate/Verify 是 scriptTask → `boo.arcana.MaintHttp`（engine 內建 Java helper）
  → **ci-maint-endpoint**（Rust Axum，掛 `/data:ro` + `/var/log:ro` + Jenkins env，
  **零 docker socket**）：`/scan` = disk% + Jenkins health + 各 host cron 上次結果；
  `/remediate` = 只透過 Jenkins API 把 offline node 上線（磁碟壓力僅標 needsAttention）；
  `/verify`。真 prune/GC 仍歸 host cron —— **執行歸 host，BPMN 只做巡檢+編排+記錄+AI**。
- Analyze = ai UserTask → worker → agent `/task/analyze`：Claude 分析健康趨勢，輸出
  severity + recommendation。4 個 step 輸出全寫 process var → Data Index → KPI/audit 可見。
- 成本：每小時一次 Claude 分析（token 量小）。

---

## 6. 元件

| 元件 | 說明 | base / 技術 |
|---|---|---|
| **kogito-bpmn** | 唯一引擎，跑三個 process | Quarkus 3.8.4 + `jbpm-with-drools-quarkus` + `kie-addons-quarkus-persistence-jdbc` + `quarkus-jdbc-postgresql` + events addon + kafka connector |
| **kogito-data-index** | 統一可查詢層（process/task/timeline + GraphQL） | `kogito-data-index-postgresql`（CQRS，kafka 事件投影） |
| **kogito-pg** | 工作流專用 PG（workflow / dataindex / arcana 三 DB） | postgres:17-alpine |
| **arcana-cloud-rust** | engine-agnostic 唯讀 read-API + `/definitions/{id}/bpmn`（bpmn-js 用） | Axum + SQLx；`BPMN_DIR=/app/bpmn` |
| **workflow-task-worker** | **Rust** poller：task name dispatch（triage/build/fix/decide/analyze/merge/release）；human 永不自動完成；reconciler 每 300s 以引擎為真相源修 DI | tokio + reqwest + tokio-postgres；image `arcana/task-worker:1.3.0` |
| **agent-task-node** | Claude CLI 任務節點：`/task/diagnose|fix|decide|merge|analyze`（Claude，session persistence + sid）+ `/task/release`（deterministic，繞過 Claude） | `claude -p --output-format json`；`/root/.claude` host bind mount（session 永續） |
| **ci-maint-endpoint** | 唯讀 CI 健康 probe（`/scan` `/remediate` `/verify`），零 docker socket | Rust Axum；image `arcana/ci-maint-endpoint:1.0.0` |
| **dashboard-web** | Angular 即時監控：實例表 + **bpmn-js** 流程圖 + handoff banner（sid + resume 指令） | standalone + signals；nginx `/api` proxy |
| **ci-bpmn-trigger.groovy** | Jenkins RunListener **v7**：紅 build→/ci-flow（6h cooldown）；綠 PR build（fleet-wide）→/merge-flow | init.groovy.d + scriptText 熱套用 |
| **ci-scheduler** | 每 3600s POST /ci-maintenance | curlimages/curl loop |

---

## 7. 領域模型 / PG schema

**Kogito persistence + Data Index 自建表**（process_instances / user task / variables）。

**arcana-cloud-rust read-model / 定義表**：
- `workflow_definition(id, name, version, bpmn_xml, nodes jsonb, engine, created_at)`
- `role(id, key, label, kind)` — seed `ai`/`jenkins`（`human` 由 BPMN GroupId 帶入）
- `process_node_role(workflow_id, node_id, role_key)`
- `eform_definition(...)` — 表單定義（只建表）
- process/task **實例**優先讀 Data Index

---

## 8. 開發策略 — Mac-first

- 專案：`/Users/jrjohn/Documents/projects/arcana-ai-agent-flow`（Mac 為 full source；
  bluesea `/data/projects/arcana-ai-agent-flow` 是 deploy copy）。
- 先 Mac docker-compose 跑通端到端，綠了再導入 bluesea（devops_default、既有 kafka、
  Authelia）。worker 與 engine 也可直接在 bluesea build（worker 是 self-contained Rust；
  engine 用 maven-docker 出 jar 再 docker build）。

---

## 9. 驗證

- Data Index GraphQL 查到實例 + user task 的 group（ai/jenkins/human）。
- read-api `/processes` 回清單；`/definitions/{id}/graph` 回節點(含 role)+邊；
  `/definitions/{id}/bpmn` 回 XML（bpmn-js 渲染）。
- ci-flow：紅 build → 實例 → ai/jenkins 節點自動完成 → 綠則 End；修不動則 park 在
  HumanFix，dashboard 出現 resume banner，`claude --resume <sid>` 可接手。
- merge-flow：綠 PR build → Merge squash-merge → Release 跑 release-please
  （無 config 的 repo `released=false, skipped`）→ COMPLETED。
- ci-maintenance：每小時實例 Scan→Analyze→Remediate→Verify，4 個 var 齊全。

---

## 10. 風險 / 留意

- **DB 內容是引擎真相的投影**：kafka 斷時 Data Index 會漂 —— worker 的 reconciler 與
  engine-recheck 邏輯是為此而生，不要繞過它直接 abort 實例。
- **大改 BPMN 結構要 bump process version**，否則 Data Index `definitions_nodes` 新舊
  node 疊加、圖會畫歪（執行不受影響）。
- bluesea 資源 headroom：單引擎後省 1 container；24G RAM 下 Quarkus heap 可調。
- bluesea infra 動作受 classifier gating → 多半要 John 親手 `!` 授權。
- agent `/task/release` 需要 agent container 內有 **GH_TOKEN + node/npx**。
