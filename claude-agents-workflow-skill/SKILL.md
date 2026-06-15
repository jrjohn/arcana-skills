---
skill_name: claude-agents-workflow-skill
skill_version: 0.1.0
created_date: 2026-05-29
skill_type: complex
status: scaffold (Phase 0)
protocols:
  - COR
  - AFP
  - NTP
allowed_tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
dependencies:
  - claude-session-archive-skill
---

# claude-agents-workflow-skill

> **AI agents 協同模式的「底層」** —— 用 Apache KIE **SonataFlow**(CNCF Serverless Workflow,事件驅動)當編排層,Claude agent 退居「執行節點」被工作流以 scoped task 呼叫。

## 分層定位

```
Layer 2+  完整 AI 落地實踐（往上建構）
Layer 1   ★ 本 skill — agents 協同 substrate（SonataFlow 編排 + agent-as-node）
Layer 0   claude-session-archive-skill — 記憶層（跨 session 召回）
```

## 何時用（觸發）

要把「多個 Claude agent / 多步驟自動化」做成**正式、可觀測、可重試、有 SLA** 的工作流時 —— 而不是「一個 agent 自己排程自己迴圈」的黑箱。第一個 reference deployment = bluesea / Arcana CI 自動維護(Jenkins build 事件驅動 → 診斷→修→驗證→merge→報告)。

觸發詞：agent 協同、agent orchestration、SonataFlow、serverless workflow、事件驅動工作流、AI 工作流編排、把 agent 變工作流節點、CI 自動維護工作流。

## 核心分工（不可混淆）

| 層 | 負責 | 工具 |
|---|---|---|
| 編排層 | 流程、狀態、重試、SLA、event 關聯、可觀測 | **SonataFlow**（被動執行，不推理） |
| 執行節點 | 智能：診斷 / 修 / merge 判斷 | **Claude agent**（`claude -p --json-schema` 回 structured JSON） |

## 狀態

Phase 0（scaffold）完成。實作進度見 references/architecture.md 的 phase 表 + plan `queue-buzzing-hennessy.md`。
完整架構、部署、agent-node 模式見 `references/`；可部署 artifacts 見 `templates/`（Phase 1+ 填入）。
