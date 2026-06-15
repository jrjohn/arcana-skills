# claude-agents-workflow-skill

**AI agents 協同模式的底層** — 用 Apache KIE **SonataFlow**（CNCF Serverless Workflow，事件驅動）當編排層，把 **Claude agent 變成被工作流呼叫的「執行節點」**。**全部以 Docker 封裝**：`docker compose up` 即起整套。

## 為什麼

把「多 agent / 多步驟自動化」從**黑箱**（一個 agent 自己排程自己迴圈、不可觀測、無重試、無 SLA）升級成**正式工作流**（顯式狀態、per-step 重試、SLA 逾時 escalate、event 關聯、可觀測）。Claude 只負責**智能判斷**；流程治理交給成熟的工作流引擎（KIE = jBPM 15+ 年 + Drools 血統）。

## 分層藍圖

```
Layer 2+  完整 AI 落地實踐（往上建構）
Layer 1   ★ 本 skill — agents 協同 substrate
Layer 0   claude-session-archive-skill — 記憶層（跨 session 召回）
```

## 架構（全 Docker）

```
Jenkins (container) ──build done──▶ RunListener 發 CloudEvent (HTTP POST)
                                          │
                                          ▼
   ┌──────────────────────── docker-compose（同一 network）────────────────────────┐
   │                                                                                │
   │   sonataflow (container)            agent-task-node (container)                │
   │   ├ SonataFlow / Quarkus            ├ FROM 既有 daily-ci-agent image           │
   │   ├ 工作流: triage→diagnose→        │   (claude CLI + gh + git + auth)         │
   │   │   fix→verify→decide→report      ├ HTTP server 包 scoped task:              │
   │   ├ 呼叫 agent-task-node 各 task ──▶│   /task/diagnose /fix /merge             │
   │   └ process store → PostgreSQL      │   每個 = claude -p --json-schema 回 JSON │
   │        (container, 既有)            └──────────────────────────────────────── │
   └────────────────────────────────────────────────────────────────────────────┘
```

**核心分工**：SonataFlow = 流程/狀態/重試/SLA/可觀測（不推理）；Claude agent = 診斷/修/merge 的智能（`claude -p --json-schema` 回 structured JSON）。

## 部署（Docker-first）

整套是一份 `templates/docker-compose.sonataflow.yml`：
- `sonataflow` 服務（Phase 1 用 `apache/incubator-kie-sonataflow-devmode`，Phase 2+ 換 builder 出的 Quarkus app image + PG 持久化）。
- `agent-task-node` 服務（Dockerfile FROM 既有 agent image + 一支 HTTP task server）。
- 接既有 PostgreSQL（process store）、既有 Jenkins（事件源）。

`scripts/install.sh` 一鍵把這份 compose 部署到目標主機（reference deployment = bluesea / Arcana CI）。

## 狀態
Phase 0（scaffold + recon）完成。逐 phase 進度見 `references/architecture.md`。
