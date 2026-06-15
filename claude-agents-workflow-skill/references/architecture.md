# Architecture — SonataFlow 編排 + Claude agent 執行節點（全 Docker）

## 工作流（CI 維護生命週期，reference deployment）

```
event: ci.build.completed {job,result,branch,number,buildUrl}
  │
  ▼ Triage (switch / DMN)
  ├─ green main      → refresh arch-rank → END
  ├─ PR build green  → Merge-eligibility → (Decide)
  └─ red main        → Diagnose
                          │
                          ▼ Diagnose  → agent-task-node POST /task/diagnose {job,buildUrl}
                          │              → {cause, fixable, proposedAction}
                          ▼ Fix       → agent-task-node POST /task/fix {job,cause}
                          │              → {prUrl, branch, summary}
                          ▼ Verify (event state, correlation key = job)
                          │   觸發 re-build → 等該 job 下一個 ci.build.completed
                          ▼ Decide (switch + retry policy + timer SLA)
                          │   ├─ verified green → Merge (/task/merge) → Report
                          │   ├─ red & retries 未盡 → 回 Diagnose
                          │   └─ SLA 逾時 / retries 盡 → Escalate (notify)
                          ▼ Report → SendGrid + /data/ci-reports
```

## 元件（皆容器）
| 容器 | 角色 | 來源 |
|---|---|---|
| `sonataflow` | 編排引擎 + 工作流定義 + HTTP CloudEvent 入口 | Phase1: `sonataflow-devmode:10.x`；Phase2+: builder 出的 Quarkus app image |
| `agent-task-node` | Claude 執行節點，HTTP `/task/{diagnose,fix,merge}` → `claude -p --json-schema` | Dockerfile FROM 既有 daily-ci-agent image |
| PostgreSQL（既有） | SonataFlow process store（Phase2+，db `sonataflow`） | 既有 `pg-archive-test` 或新 PG 容器 |
| Jenkins（既有） | 事件源，全域 RunListener 發 CloudEvent | 既有，加 `init.groovy.d/ci-cloudevent.groovy` |

全部掛 `devops_default` network；一份 `templates/docker-compose.sonataflow.yml` 起 `sonataflow`+`agent-task-node`，接既有 PG/Jenkins。

## 分工原則
- **SonataFlow**：被動執行流程、狀態機、retry/timer/SLA、event correlation、instance 可觀測。**不推理**。
- **Claude agent**：診斷/修/merge 的智能，`claude -p --json-schema` 回 typed JSON 供工作流做決策。
- **host 端地基修復**（arch-qube skopeo re-push、watchdog/GC、Jenkins job 管理）**不進工作流** —— 那是人/維運兜底（見 memory `reference_bluesea_archqube_registry.md`、`feedback-agent-autonomy`）。

## Phase 進度
| Phase | 內容 | 狀態 |
|---|---|---|
| 0 | pre-flight recon + skill scaffold | ✅ 完成（recon 見 sonataflow-setup.md）|
| 1 | MVP：event→triage→diagnose→fix→**report-only**；devmode 映像 | ⏳ next |
| 2 | Verify 迴路：re-build + event correlation + bounded retry；轉 builder+PG | |
| 3 | 自動 merge（verified green）+ SLA escalate | |
| 4 | timer sweep workflow 取代 OS cron；舊 cron+flock 退場 | |
| 5 | 封裝發佈 arcana-skills（install + 索引）| |

回退：Phase 1-3 期間**保留現有 cron+flock daily-ci-agent 平行跑**，SonataFlow 穩定後才退場（Phase 4）。
