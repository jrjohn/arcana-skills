# Arcana AI Agent Flow — 設計文件

> 通用工作流平台 + 即時監控:雙引擎(人工決策 BPMN / 全自動 SonataFlow)、角色治理、自助式可觀測 dashboard。
> 狀態:設計定稿(2026-06-02)。開發策略 = **Mac-first**(本地 docker 跑通驗證 → 再導入 bluesea)。

---

## 1. 願景 / 為什麼

打造一套**通用工作流平台**:流程定義(每節點配角色)→ 任務實例 →(未來)eForm 表單,搭配**即時監控 dashboard**:
1. **任務/流程實例清單**(task list)。
2. **動態流程圖**(節點依角色 lane 著色、目前/已走節點即時高亮)。

第一組角色:**AI(Claude CLI)**、**CI/CD(Jenkins)**;角色之上可長出組織 / RBAC。

同時補上 Arcana 兩軌 CI 架構的「可觀測性」缺口(現有 SonataFlow serverless + routine 模式照舊跑 CI)。

---

## 2. 設計精神(對齊 Cannerflow)

平台不是一次性監控工具,而是**自助式、分層解耦、角色治理**的工作流平台 —— 抽象化引擎複雜度,讓非專家也能看懂/操作:

1. **流程三要素先行**(Cannerflow 建置前要素):每個流程定義都明確 (a) **目標**、(b) **流程設計**(節點+轉換)、(c) **角色**(每節點誰負責)。角色是一等公民。
2. **分層解耦**:引擎 → 統一 store(Data Index/PG) → **語意/抽象層(rust read-API)** → UI(Angular)。每層可獨立替換;使用者**不直接碰** BPMN XML / 引擎內部。
3. **自助 + 抽象化**:dashboard 用「目標/流程/角色」語彙呈現(非 BPMN 術語);引擎內部(persistence blob、protobuf、kafka)由語意層隱藏。
4. **Cloud-Native / 彈性**:全容器化、可獨立擴縮、宣告式流程定義(BPMN/SWF 檔即設計)。
5. **資料驅動 + 自動化省 toil**:process/task 是一等可查模型;AI/Jenkins 自動完成任務取代人工 toil。

---

## 3. 核心決策

### 3.1 雙引擎(兩面向都支援)
- **Kogito BPMN(jBPM)** → 「**有人工/角色決策點**」的流程(UserTask + lane/role + 表單)。獨立 Quarkus 服務(base = `process-postgresql-persistence-quarkus`)。
- **SonataFlow(CNCF Serverless Workflow)** → 「**全自動、不需人工**」的流程(現有 CI 維護即此類)。
- **統一監控**:兩引擎皆 Kogito 家族 → process/task 事件都進**同一個 Kogito Data Index(PG)** → 一個 read-API → 一個 dashboard。

### 3.2 其他拍板
| # | 決策 |
|---|---|
| 引擎 | 雙引擎並存(BPMN 人工 / SonataFlow 自動) |
| read-API | **arcana-cloud-rust**(Axum+SQLx),engine-agnostic,**只讀**,不驅動引擎 |
| 查詢層 | **單一 Kogito Data Index**(雙引擎共用) |
| 即時 | **polling ~3-5s**(SSE 為後續) |
| 任務驅動 | **AI/Jenkins 任務完成整合納入**(task-worker → 流程實際推進) |
| SonataFlow | 現有**兩容器合併**成單一引擎後再整合 |
| 本輪範圍 | 定義層(節點配角色)+ 任務實例 + 監控 + 任務完成驅動;eForm 只建 DEFINITION schema;artifact INSTANCE 暫緩 |
| 角色 | `ai`(Claude CLI)、`jenkins`(CI/CD);→ 組織/RBAC 為未來 |

---

## 4. 架構(端到端,雙引擎統一監控)

```
[人工決策] Kogito BPMN 引擎               [全自動] SonataFlow 引擎
   ├─ BPMN(節點 GroupId=ai/jenkins)          ├─ SWF 流程(CI 維護等)
   │  + persistence-jdbc                      │  + events addon(rebuild)
   └─ process/task 事件 ──────┐    ┌────── process 事件
                              ▼    ▼
            Kogito Data Index (postgresql)   ← 統一可查詢層
            (BPMN + SWF 的 instances / user tasks 含 group/role / timeline + GraphQL)
                              │ (PG 表 or GraphQL,唯讀)
                              ▼
   arcana-cloud-rust  /api/v1/workflows/*   (Axum read-API,語意/抽象層)
     ├─ GET /processes            實例清單(依 status/role 過濾)
     ├─ GET /processes/{id}       單一實例 + 目前狀態
     ├─ GET /processes/{id}/timeline   狀態時間軸(高亮用)
     └─ GET /definitions/{id}/graph    流程圖(節點+邊+每節點角色)
                              │ REST/JSON (+ polling)
                              ▼
   Angular dashboard (nginx 容器,單一 origin → 免 CORS)
     ├─ Task List view    (實例表 + 角色 badge + status 過濾)
     └─ Live Flow Diagram (節點依 ai/jenkins lane 著色,current/visited/error 高亮,自動更新)

   ┌─ workflow-task-worker (驅動 BPMN 流程) ─┐
   │  輪詢 Kogito ready user tasks 依 group:  │
   │   group=ai     → agent-task-node(claude)完成 → 流程往下
   │   group=jenkins→ 觸發 Jenkins build,完成回填 → 流程往下
   └──────────────────────────────────────────┘
```

**為何不靠引擎原生 persistence 直查**:Kogito 原生 persistence 是 protobuf BYTEA blob、completed 實例預設刪除 → 不可查。**Data Index 是標準可查詢層**(專為此設計),且是 Kogito 家族(BPMN+SonataFlow)的統一索引。

---

## 5. 元件

| 元件 | 說明 | base / 技術 |
|---|---|---|
| **kogito-bpmn** | Kogito BPMN 引擎(人工/角色流程) | Quarkus 3.8.4 + `jbpm-with-drools-quarkus` + `kie-addons-quarkus-persistence-jdbc` + `quarkus-jdbc-postgresql` + Data Index addon。base = `process-postgresql-persistence-quarkus` |
| **kogito-data-index** | 統一可查詢層(process/task/timeline + GraphQL) | `kogito-data-index-postgresql` |
| **kogito-pg** | 工作流專用 PG(不重用 sonarqube-db / archive) | postgres:17-alpine, named volume, 不對外開 port |
| **arcana-cloud-rust** | engine-agnostic 唯讀 read-API | Axum + SQLx;新增 `workflow_controller`(仿 `jobs_controller.rs`)+ migrations + DAO(仿 `UserDao`) |
| **workflow-task-worker** | 驅動 BPMN(ai/jenkins 完成任務) | 輕量 poller(可獨立或在 agent-task-node 內);idempotent + bounded retry |
| **dashboard-web** | Angular 即時監控 | standalone + signals + typed HttpClient;流程圖 lib **cytoscape**(動態高亮+lane 著色佳);polling;→ nginx 容器(仿 `arcana-angular/Dockerfile.ci`,`/api/` proxy 到 rust) |

---

## 6. 領域模型 / PG schema

**Kogito persistence + Data Index 自建表**(process_instances / user task / variables,Flyway migrate-at-start)。

**arcana-cloud-rust read-model / 定義表**(migrations 仿現有 `20241226*.sql`):
- `workflow_definition(id, name, version, bpmn_xml|swf_json, nodes jsonb, engine, created_at)` — 流程設計 + 每節點角色(供流程圖);`engine` 區分 BPMN/SWF
- `role(id, key, label, kind)` — seed `ai`/`jenkins`;預留 `organization`/RBAC
- `process_node_role(workflow_id, node_id, role_key)` — 節點↔角色
- `eform_definition(id, node_id, schema jsonb, ...)` — 表單**定義**(本輪只建表)
- `artifact_instance(...)` — **設計但本輪不實作/不寫入**(尚未用到)
- process/task **實例**優先讀 Data Index;必要時建輕量 read view

---

## 7. 開發策略 — Mac-first

- **專案**:`/Users/jrjohn/Documents/projects/arcana-ai-agent-flow`。
- **先 Mac、後 bluesea**:整套(kogito-pg + kogito-bpmn + data-index + rust + task-worker + Angular)先用**本地 docker-compose 在 Mac 跑通 + 端到端驗證**,綠了**再導入 bluesea**。理由:迭代快、免 ssh 往返、免 bluesea infra 的 classifier gating。
- **產出 = 可攜 compose 專案**:`docker-compose.yml`(全 stack)+ 各服務原始碼 + 本設計 md;Mac 綠 → 同一份 compose/images 部署 bluesea(devops_default + localhost:5000)。

### 專案結構(初版)
```
arcana-ai-agent-flow/
├── docs/design.md                  # 本文件
├── docker-compose.yml              # 全 stack(Mac 本地)
├── kogito-bpmn/                    # Kogito BPMN 引擎(Quarkus) + 範例 .bpmn2
├── data-index/                     # Data Index 設定(或用官方 image)
├── read-api/                       # (指向 arcana-cloud-rust;或本地 clone 改)
├── task-worker/                    # ai/jenkins 任務完成 poller
└── dashboard-web/                  # Angular app
```

---

## 8. Build 順序(A→E 全在 Mac 本地跑通,F 才導入 bluesea)

- **0. 專案 + 設計 md**:骨架 + 本文件。✅(本次)
- **A. 資料地基(本地)**:compose 起 kogito-pg + Kogito BPMN(1 個含 ai/jenkins lane 範例 BPMN)+ persistence + Data Index → 起一個實例,確認資料進 Data Index 可查。
- **B. read-API**:rust 加 workflow_controller + migrations + DAO → `/api/v1/workflows/*` 回真資料,engine-agnostic。
- **C. task-worker**:ai 任務 agent-task-node 完成、jenkins 任務 Jenkins 完成 → 流程實際推進。驗:一個 BPMN 實例 start→end。
- **D. Angular dashboard**:task list + flow diagram(角色 lane + 高亮)+ polling → nginx 容器。瀏覽器看到清單 + 動態圖隨 task 完成前進。
- **E. 合併 SonataFlow + 整合自動化面向**:兩容器合併單一引擎 + events addon → 進同一 Data Index → dashboard 同顯 BPMN + SWF。
- **F. 導入 bluesea**:Mac 驗證綠 → 同份 compose/images 部署 bluesea,接真實 Jenkins/agent-task-node/SonataFlow。(bluesea infra 動作多半要 John 親手 `!` 授權。)

---

## 9. 驗證

- **A**:`curl` Data Index GraphQL/SQL 查到實例 + user task 的 group(ai/jenkins)。
- **B**:`curl read-api /api/v1/workflows/processes` 回清單;`/definitions/{id}/graph` 回節點(含 role)+邊。
- **C**:起 BPMN 實例 → task-worker 讓 ai/jenkins 節點依序自動完成 → start→end。
- **D**:dashboard task list 顯示實例+角色;flow diagram 依角色著色、current/visited 高亮;task 完成後 polling 自動前進。
- **E**:合併後單一 SonataFlow 引擎跑一個 CI 自動流程 → dashboard 同時顯示 SWF + BPMN 實例。

---

## 10. 風險 / 留意

- 平台級多元件建置 —— Mac-first 分階段,A 先證資料鏈通。
- Kogito BPMN 服務需 build image(BPMN+persistence+data-index deps);arm64 Maven build 較久。
- **資源 headroom**:bluesea 多了 kogito-bpmn + data-index + kogito-pg + rust + nginx + task-worker;24G RAM 先量再上(Quarkus 可 native 壓低,可調 heap)。
- **SonataFlow 合併(E)**:兩容器目前共用 consumer group 分割 partition,合併注意 in-flight 不丟、確認哪份 config(JDK21 vs JDK17 + AGENT_TASK_URL)為準。
- bluesea infra 動作受 classifier gating → 多半要 John 親手 `!` 授權(同 RunListener / 引擎部署模式)。
