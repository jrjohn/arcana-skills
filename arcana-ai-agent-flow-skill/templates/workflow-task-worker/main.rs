//! Arcana workflow task-worker — Rust port of worker.py (2026-06-04), with
//! task-level concurrency. Behavior parity with the Python original:
//!
//!   Triage  (ai)      -> agent-task-node /task/diagnose on the failed build
//!   Build   (jenkins) -> trigger a rebuild and WAIT for its result
//!   Fix     (ai)      -> agent-task-node /task/fix (checkout, fix, verify, PR)
//!   Decide  (ai)      -> agent-task-node /task/decide (merge / escalate)
//!   <other> (ai)      -> decide;  <other> (jenkins) -> rebuild
//!
//! Concurrency model (the Python original was single-threaded — one slow
//! 15-min Build poll blocked every other instance's AI task):
//!   - each ready task runs in its own tokio task
//!   - semaphores cap concurrency per kind: fix=1 (local build verification is
//!     heavy on the shared 24G host), other ai=2, jenkins rebuild waits=3
//!   - an in-flight set prevents re-dispatching a task the poller sees again
//!     while it is still being processed (tasks stay Ready until completed)
//!
//! Retry/abort semantics are identical: MAX_RETRIES failures -> abort the
//! instance once (ACTIVE -> ABORTED -> dashboard shows FAILED), never hang.
//! Modes: MODE=auto synthesizes results (Mac-first dev); MODE=real calls out;
//! MODE=reconcile-only runs only the reconciler (no task dispatch).
//!
//! 2026-06-05 hardening (after the kafka-outage incident where Data Index froze
//! and the worker aborted live instances off stale work-item ids):
//!   - complete() failures are re-checked against the ENGINE (the synchronous
//!     source of truth): instance gone / task gone -> drop silently; same task
//!     renewed under a new work-item id -> retry once with the fresh id; only
//!     engine-confirmed same-id failures count toward MAX_RETRIES/abort.
//!   - a reconciler loop (RECONCILE_SECS, DATAINDEX_PG) repairs Data Index
//!     drift both ways: DI-ACTIVE instances the engine no longer has are marked
//!     ABORTED (+ their Ready tasks), and engine-live instances/tasks missing
//!     from DI are inserted — so the monitor stays truthful and the worker can
//!     keep dispatching even while the kafka event chain is down. Late events
//!     simply overwrite the repairs (events win; the reconciler only touches
//!     rows that stay drifted).

use std::collections::{HashMap, HashSet};
use std::io::Write;
use std::sync::{Arc, Mutex};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use serde_json::{json, Value};
use tokio::sync::Semaphore;

fn env_or(k: &str, d: &str) -> String {
    std::env::var(k).unwrap_or_else(|_| d.to_string())
}

struct Cfg {
    engine: String,
    data_index: String,
    mode: String,
    poll_secs: f64,
    max_retries: u32,
    agent: String,
    jenkins_url: String,
    jenkins_user: String,
    jenkins_token: String,
    usage_dir: String,
    // reconciler (empty DATAINDEX_PG or RECONCILE_SECS=0 disables it)
    dataindex_pg: String,
    reconcile_secs: u64,
    reconcile_pids: Vec<String>,
    reconcile_groups: Vec<String>,
}

impl Cfg {
    fn from_env() -> Self {
        let trim = |s: String| s.trim_end_matches('/').to_string();
        Cfg {
            engine: trim(env_or("ENGINE_URL", "http://localhost:8081")),
            data_index: trim(env_or("DATA_INDEX_URL", "http://localhost:8180")),
            mode: env_or("MODE", "auto").to_lowercase(),
            poll_secs: env_or("POLL_SECS", "5").parse().unwrap_or(5.0),
            max_retries: env_or("MAX_RETRIES", "3").parse().unwrap_or(3),
            agent: trim(env_or("AGENT_TASK_URL", "")),
            jenkins_url: trim(env_or("JENKINS_URL", "")),
            jenkins_user: env_or("JENKINS_USER", ""),
            jenkins_token: env_or("JENKINS_TOKEN", ""),
            usage_dir: env_or("USAGE_DIR", ""),
            dataindex_pg: env_or("DATAINDEX_PG", ""),
            reconcile_secs: env_or("RECONCILE_SECS", "300").parse().unwrap_or(300),
            reconcile_pids: env_or("RECONCILE_PROCESS_IDS", "ci-flow")
                .split(',').map(|s| s.trim().to_string()).filter(|s| !s.is_empty()).collect(),
            reconcile_groups: env_or("RECONCILE_GROUPS", "ai,jenkins")
                .split(',').map(|s| s.trim().to_string()).filter(|s| !s.is_empty()).collect(),
        }
    }
}

struct State {
    cfg: Cfg,
    http: reqwest::Client,
    failures: Mutex<HashMap<String, u32>>,
    given_up: Mutex<HashSet<String>>,
    in_flight: Mutex<HashSet<String>>,
    // human-handoff tasks we've already logged the resume hint for (notify-once)
    notified: Mutex<HashSet<String>>,
    sem_ai: Semaphore,
    sem_fix: Semaphore,
    sem_jenkins: Semaphore,
}

#[derive(Clone)]
struct Task {
    id: String,
    name: String,
    group: Option<String>,
    process_id: String,
    instance_id: String,
}

fn log(line: String) {
    // line-buffered stdout flushes per newline; force-flush anyway for docker logs
    let mut out = std::io::stdout();
    let _ = writeln!(out, "{line}");
    let _ = out.flush();
}

// ---- HTTP helpers ---------------------------------------------------------

async fn req_json(
    st: &State,
    method: reqwest::Method,
    url: &str,
    payload: Option<&Value>,
    timeout: Duration,
    auth: Option<(&str, &str)>,
) -> Result<(u16, String), String> {
    let mut r = st.http.request(method, url).timeout(timeout);
    if let Some(p) = payload {
        r = r.json(p);
    }
    if let Some((u, t)) = auth {
        r = r.basic_auth(u, Some(t));
    }
    let resp = r.send().await.map_err(|e| format!("{e}"))?;
    let status = resp.status().as_u16();
    let body = resp.text().await.map_err(|e| format!("{e}"))?;
    if status >= 400 {
        return Err(format!("HTTP {status}: {}", &body[..body.len().min(200)]));
    }
    Ok((status, body))
}

// ---- engine / data-index --------------------------------------------------

async fn ready_tasks(st: &State) -> Result<Vec<Task>, String> {
    let q = json!({"query":
        "{ UserTaskInstances(where: {state: {equal: \"Ready\"}}) \
           { id name potentialGroups processId processInstanceId } }"});
    let (_, body) = req_json(st, reqwest::Method::POST, &format!("{}/graphql", st.cfg.data_index),
                             Some(&q), Duration::from_secs(60), None).await?;
    let v: Value = serde_json::from_str(&body).map_err(|e| format!("{e}"))?;
    let arr = v["data"]["UserTaskInstances"].as_array().cloned().unwrap_or_default();
    Ok(arr.iter().filter_map(|t| {
        Some(Task {
            id: t["id"].as_str()?.to_string(),
            name: t["name"].as_str().unwrap_or("").to_string(),
            group: t["potentialGroups"].as_array()
                .and_then(|g| g.first()).and_then(|g| g.as_str()).map(String::from),
            process_id: t["processId"].as_str()?.to_string(),
            instance_id: t["processInstanceId"].as_str()?.to_string(),
        })
    }).collect())
}

async fn instance_vars(st: &State, pid: &str, iid: &str) -> Value {
    match req_json(st, reqwest::Method::GET, &format!("{}/{}/{}", st.cfg.engine, pid, iid),
                   None, Duration::from_secs(30), None).await {
        Ok((_, body)) => serde_json::from_str(&body).unwrap_or_else(|_| json!({})),
        Err(_) => json!({}),
    }
}

async fn complete(st: &State, t: &Task, group: &str, result: &str, sid: Option<&str>) -> Result<u16, String> {
    let url = format!("{}/{}/{}/{}/{}?phase=complete&group={}",
                      st.cfg.engine, t.process_id, t.instance_id, t.name, t.id, group);
    // `out` maps to the task's `out` dataOutput; `sid` (when the ai task declares a
    // sid dataOutput) persists the Claude session id on the instance so the next ai
    // task resumes the same conversation and a human can re-attach to it.
    let mut body = json!({"out": result});
    if let Some(sid) = sid {
        if !sid.is_empty() {
            body["sid"] = json!(sid);
        }
    }
    let (status, _) = req_json(st, reqwest::Method::POST, &url,
                               Some(&body), Duration::from_secs(900), None).await?;
    Ok(status)
}

async fn abort_instance(st: &State, pid: &str, iid: &str) -> String {
    match req_json(st, reqwest::Method::DELETE, &format!("{}/{}/{}", st.cfg.engine, pid, iid),
                   None, Duration::from_secs(30), None).await {
        Ok((s, _)) => s.to_string(),
        Err(e) => e,
    }
}

/// What the ENGINE says about a task we failed to complete (the data-index can
/// lag or freeze — e.g. kafka outage — so its work-item ids go stale).
enum EngineCheck {
    InstanceGone,        // instance finished/aborted elsewhere — drop, don't abort
    TaskGone,            // node moved past this task — drop
    Renewed(String),     // same node re-entered under a new work-item id — retry with it
    SameId,              // engine still has our exact task — genuine transient failure
    Unknown(String),     // engine unreachable — treat as transient
}

async fn engine_check(st: &State, t: &Task, group: &str) -> EngineCheck {
    let url = format!("{}/{}/{}/tasks?group={}", st.cfg.engine, t.process_id, t.instance_id, group);
    match req_json(st, reqwest::Method::GET, &url, None, Duration::from_secs(30), None).await {
        Err(e) if e.starts_with("HTTP 404") => EngineCheck::InstanceGone,
        Err(e) => EngineCheck::Unknown(e),
        Ok((_, body)) => {
            let v: Value = serde_json::from_str(&body).unwrap_or(Value::Null);
            let Some(arr) = v.as_array() else { return EngineCheck::Unknown("bad task list".into()) };
            let ready = arr.iter().filter(|e| {
                e["name"].as_str() == Some(t.name.as_str())
                    && e["phaseStatus"].as_str() == Some("Ready")
            }).filter_map(|e| e["id"].as_str()).collect::<Vec<_>>();
            match ready.iter().find(|id| **id == t.id) {
                Some(_) => EngineCheck::SameId,
                None => match ready.first() {
                    Some(id) => EngineCheck::Renewed(id.to_string()),
                    None => EngineCheck::TaskGone,
                },
            }
        }
    }
}

// ---- node handlers ----------------------------------------------------------

fn s(v: &Value, k: &str) -> String {
    v.get(k).and_then(Value::as_str).unwrap_or("").to_string()
}

/// The Claude session id the agent handed back (`_sid`), if any.
fn pick_sid(d: &Value) -> Option<String> {
    d.get("_sid").and_then(Value::as_str).filter(|s| !s.is_empty()).map(String::from)
}

/// Thread the current instance's `sid` into an agent payload so the agent
/// resumes the same session instead of starting amnesiac. No-op when unset.
fn with_sid(mut payload: Value, vars: &Value) -> Value {
    let sid = s(vars, "sid");
    if !sid.is_empty() {
        if let Some(o) = payload.as_object_mut() {
            o.insert("sid".to_string(), json!(sid));
        }
    }
    payload
}

fn console_fields(t: &Task) -> Value {
    json!({"_piid": t.instance_id, "_node": t.name})
}

fn merge(mut base: Value, extra: &Value) -> Value {
    if let (Some(b), Some(e)) = (base.as_object_mut(), extra.as_object()) {
        for (k, v) in e {
            b.insert(k.clone(), v.clone());
        }
    }
    base
}

fn truncate(s: &str, n: usize) -> String {
    // char-safe truncation (Claude output may contain multibyte UTF-8)
    s.char_indices().nth(n).map(|(i, _)| s[..i].to_string()).unwrap_or_else(|| s.to_string())
}

/// Triage(ai): diagnose only — fixing is the Fix node's job.
async fn diagnose(st: &State, t: &Task, vars: &Value) -> Result<(String, Option<Value>, Option<String>), String> {
    if st.cfg.mode == "real" && !st.cfg.agent.is_empty() {
        let payload = with_sid(merge(json!({"job": s(vars, "job"), "buildUrl": s(vars, "buildUrl"),
                                   "result": s(vars, "result")}), &console_fields(t)), vars);
        let (_, body) = req_json(st, reqwest::Method::POST, &format!("{}/task/diagnose", st.cfg.agent),
                                 Some(&payload), Duration::from_secs(900), None).await?;
        return Ok(match serde_json::from_str::<Value>(&body) {
            Ok(d) => (json!({"cause": d.get("cause").cloned().unwrap_or(json!("")),
                             "category": d.get("category").cloned().unwrap_or(json!("")),
                             "fixable": d.get("fixable").cloned().unwrap_or(json!(false))}).to_string(),
                      d.get("_usage").cloned(), pick_sid(&d)),
            Err(_) => ("diagnose: done".to_string(), None, None),
        });
    }
    Ok((format!("ai auto-diagnose: {}", s(vars, "job")), None, None))
}

fn job_url(vars: &Value) -> String {
    // buildUrl = http://jenkins:8080/jenkins/job/.../<num>/ -> drop the run number
    let b = s(vars, "buildUrl");
    let b = b.trim_end_matches('/');
    match b.rfind('/') {
        Some(i) if !b.is_empty() => b[..i].to_string(),
        _ => String::new(),
    }
}

async fn jenkins_last(st: &State, job: &str, auth: Option<(&str, &str)>) -> (Option<i64>, Option<bool>, Option<String>) {
    match req_json(st, reqwest::Method::GET,
                   &format!("{job}/lastBuild/api/json?tree=number,building,result"),
                   None, Duration::from_secs(20), auth).await {
        Ok((_, b)) => match serde_json::from_str::<Value>(&b) {
            Ok(d) => (d["number"].as_i64(), d["building"].as_bool(),
                      d["result"].as_str().map(String::from)),
            Err(_) => (None, None, None),
        },
        Err(_) => (None, None, None),
    }
}

/// Build(jenkins): trigger a rebuild and WAIT for its result.
async fn rebuild(st: &State, vars: &Value) -> Result<(String, Option<Value>, Option<String>), String> {
    if st.cfg.mode == "real" && !st.cfg.jenkins_url.is_empty() {
        let job = job_url(vars);
        if job.is_empty() {
            return Err("no buildUrl on instance; cannot rebuild".to_string());
        }
        let auth = (!st.cfg.jenkins_user.is_empty())
            .then(|| (st.cfg.jenkins_user.as_str(), st.cfg.jenkins_token.as_str()));
        let (base, _, _) = jenkins_last(st, &job, auth).await;
        let base = base.unwrap_or(0);
        req_json(st, reqwest::Method::POST, &format!("{job}/build"),
                 None, Duration::from_secs(30), auth).await?;
        for _ in 0..180 {
            tokio::time::sleep(Duration::from_secs(5)).await;
            let (n, building, result) = jenkins_last(st, &job, auth).await;
            if let (Some(n), Some(false), Some(r)) = (n, building, result) {
                if n > base {
                    return Ok((r, None, None));
                }
            }
        }
        return Ok(("UNKNOWN".to_string(), None, None));
    }
    Ok(("SUCCESS".to_string(), None, None)) // auto mode: assume green
}

/// Fix(ai): checkout, fix, verify locally, PR. Then the flow loops back to Build.
async fn fix(st: &State, t: &Task, vars: &Value) -> Result<(String, Option<Value>, Option<String>), String> {
    if st.cfg.mode == "real" && !st.cfg.agent.is_empty() {
        let cause = match vars.get("triage") {
            Some(Value::Object(o)) => o.get("cause").and_then(Value::as_str).unwrap_or("").to_string(),
            Some(Value::String(raw)) => match serde_json::from_str::<Value>(raw) {
                Ok(p) => p.get("cause").and_then(Value::as_str).unwrap_or("").to_string(),
                Err(_) => raw.clone(),
            },
            _ => String::new(),
        };
        let payload = with_sid(merge(json!({"job": s(vars, "job"), "cause": cause,
                                   "buildUrl": s(vars, "buildUrl"),
                                   "buildResult": s(vars, "buildResult")}), &console_fields(t)), vars);
        let (_, body) = req_json(st, reqwest::Method::POST, &format!("{}/task/fix", st.cfg.agent),
                                 Some(&payload), Duration::from_secs(1800), None).await?;
        let parsed = serde_json::from_str::<Value>(&body).ok();
        let usage = parsed.as_ref().and_then(|d| d.get("_usage").cloned());
        let sid = parsed.as_ref().and_then(pick_sid);
        return Ok((format!("fix: {}", truncate(&body, 400)), usage, sid));
    }
    Ok(("fix (auto)".to_string(), None, None))
}

/// Decide(ai): real Claude judgment; heuristic fallback when agent unreachable.
/// Analyze(ai): CI-health analysis for ci-maintenance. Feeds the scan JSON to
/// agent-task-node /task/analyze, returns "severity: recommendation".
async fn analyze(st: &State, t: &Task, vars: &Value) -> Result<(String, Option<Value>, Option<String>), String> {
    if st.cfg.mode == "real" && !st.cfg.agent.is_empty() {
        let payload = with_sid(merge(json!({"scan": s(vars, "scan")}), &console_fields(t)), vars);
        if let Ok((_, body)) = req_json(st, reqwest::Method::POST, &format!("{}/task/analyze", st.cfg.agent),
                                        Some(&payload), Duration::from_secs(900), None).await {
            if let Ok(d) = serde_json::from_str::<Value>(&body) {
                let out = format!("{}: {}", s(&d, "severity"), s(&d, "recommendation"));
                return Ok((truncate(&out, 400), d.get("_usage").cloned(), pick_sid(&d)));
            }
        }
    }
    Ok(("analysis: ok (auto)".to_string(), None, None))
}

async fn decide(st: &State, t: &Task, vars: &Value) -> Result<(String, Option<Value>, Option<String>), String> {
    if st.cfg.mode == "real" && !st.cfg.agent.is_empty() {
        let payload = with_sid(merge(json!({"job": s(vars, "job"),
                                   "buildResult": s(vars, "buildResult"),
                                   "attempts": vars.get("attempts").cloned().unwrap_or(Value::Null),
                                   "triage": vars.get("triage").cloned().unwrap_or(Value::Null),
                                   "fix": s(vars, "fix")}), &console_fields(t)), vars);
        if let Ok((_, body)) = req_json(st, reqwest::Method::POST, &format!("{}/task/decide", st.cfg.agent),
                                        Some(&payload), Duration::from_secs(900), None).await {
            if let Ok(d) = serde_json::from_str::<Value>(&body) {
                let out = format!("{}: {}", s(&d, "action"), s(&d, "reason"));
                return Ok((truncate(&out, 400), d.get("_usage").cloned(), pick_sid(&d)));
            }
        }
        // agent down / no /task/decide -> heuristic below (parity with Python)
    }
    if s(vars, "buildResult") == "SUCCESS" {
        return Ok(("build green after fix — merge via automerge safety net".to_string(), None, None));
    }
    Ok(("fix retries exhausted — escalate to human".to_string(), None, None))
}

/// Merge(ai): autonomous squash-merge of a verified-green PR via
/// agent-task-node /task/merge. The agent re-checks gh pr state (open + all
/// checks green + no conflicts) before merging, so this is safe to re-run.
/// Always returns Ok so the merge-flow instance completes — an unreachable
/// agent defers the merge (a later green build re-triggers) rather than
/// looping the work-item forever.
async fn do_merge(st: &State, t: &Task, vars: &Value) -> Result<(String, Option<Value>, Option<String>), String> {
    if st.cfg.mode == "real" && !st.cfg.agent.is_empty() {
        let payload = merge(json!({"job": s(vars, "job"), "prUrl": s(vars, "prUrl")}),
                            &console_fields(t));
        if let Ok((_, body)) = req_json(st, reqwest::Method::POST, &format!("{}/task/merge", st.cfg.agent),
                                        Some(&payload), Duration::from_secs(900), None).await {
            if let Ok(d) = serde_json::from_str::<Value>(&body) {
                let merged = d.get("merged").and_then(Value::as_bool).unwrap_or(false);
                let out = format!("merged={}: {}", merged, s(&d, "reason"));
                // merge-flow declares no sid output — leave it None so completion stays {"out":..}
                return Ok((truncate(&out, 400), d.get("_usage").cloned(), None));
            }
        }
        return Ok(("merge deferred — agent /task/merge unavailable".to_string(), None, None));
    }
    Ok(("merge skipped (worker not in real mode)".to_string(), None, None))
}

/// Release(ai): run release-please for the merged PR repo via
/// agent-task-node /task/release (deterministic -- github-release then
/// release-pr, no AI). Skips repos with no release-please-config. Always
/// returns Ok so the merge-flow instance completes even if the agent is
/// briefly unavailable (a later merge re-runs release-please idempotently).
async fn do_release(st: &State, t: &Task, vars: &Value) -> Result<(String, Option<Value>, Option<String>), String> {
    if st.cfg.mode == "real" && !st.cfg.agent.is_empty() {
        let payload = merge(json!({"prUrl": s(vars, "prUrl")}), &console_fields(t));
        if let Ok((_, body)) = req_json(st, reqwest::Method::POST, &format!("{}/task/release", st.cfg.agent),
                                        Some(&payload), Duration::from_secs(600), None).await {
            if let Ok(d) = serde_json::from_str::<Value>(&body) {
                let released = d.get("released").and_then(Value::as_bool).unwrap_or(false);
                let out = format!("released={}: {}", released, s(&d, "reason"));
                return Ok((truncate(&out, 400), d.get("_usage").cloned(), None));
            }
        }
        return Ok(("release deferred -- agent /task/release unavailable".to_string(), None, None));
    }
    Ok(("release skipped (worker not in real mode)".to_string(), None, None))
}

/// Returns Ok(None) when there is no handler for this task (skip it).
async fn dispatch(st: &State, t: &Task, vars: &Value)
    -> Result<Option<(String, String, Option<Value>, Option<String>)>, String> {
    let group = t.group.clone();
    let run = |g: Option<String>, r: Result<(String, Option<Value>, Option<String>), String>| {
        r.map(|(result, usage, sid)| g.map(|g| (g, result, usage, sid)))
    };
    match t.name.to_lowercase().as_str() {
        "triage" => run(group, diagnose(st, t, vars).await),
        "build" => run(group, rebuild(st, vars).await),
        "fix" => run(group, fix(st, t, vars).await),
        "decide" => run(group, decide(st, t, vars).await),
        "analyze" => run(group, analyze(st, t, vars).await),
        "merge" => run(group, do_merge(st, t, vars).await),
        "release" => run(group, do_release(st, t, vars).await),
        _ => match group.as_deref() {
            Some("ai") => run(group.clone(), decide(st, t, vars).await),
            Some("jenkins") => run(group.clone(), rebuild(st, vars).await),
            _ => Ok(None),
        },
    }
}

fn record_usage(st: &State, iid: &str, node: &str, usage: &Option<Value>) {
    let (Some(u), false) = (usage.as_ref(), st.cfg.usage_dir.is_empty()) else { return };
    let ts = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs_f64()).unwrap_or(0.0);
    let rec = json!({"node": node, "model": u.get("model").cloned().unwrap_or(Value::Null),
                     "input": u.get("input").and_then(Value::as_i64).unwrap_or(0),
                     "output": u.get("output").and_then(Value::as_i64).unwrap_or(0),
                     "ts": ts});
    let _ = std::fs::create_dir_all(&st.cfg.usage_dir);
    if let Ok(mut f) = std::fs::OpenOptions::new().create(true).append(true)
        .open(format!("{}/{}.jsonl", st.cfg.usage_dir, iid)) {
        let _ = writeln!(f, "{rec}");
    }
}

// ---- per-task processing (runs in its own tokio task) ----------------------

async fn process_task(st: Arc<State>, t: Task) {
    // concurrency cap by kind: fix is heavy (local build verification);
    // jenkins rebuilds are cheap waits; other ai calls are medium.
    let sem = match t.name.to_lowercase().as_str() {
        "fix" => &st.sem_fix,
        "build" => &st.sem_jenkins,
        _ => match t.group.as_deref() {
            Some("jenkins") => &st.sem_jenkins,
            _ => &st.sem_ai,
        },
    };
    let _permit = sem.acquire().await.expect("semaphore closed");

    let vars = instance_vars(&st, &t.process_id, &t.instance_id).await;
    let outcome = dispatch(&st, &t, &vars).await;
    match outcome {
        Ok(None) => {} // no handler — leave for someone else
        Ok(Some((group, result, usage, sid))) => match complete(&st, &t, &group, &result, sid.as_deref()).await {
            Ok(200) | Ok(201) => {
                log(format!("  ✓ {:8} [{}] {} -> {}", t.name, group, &t.instance_id[..8], result));
                record_usage(&st, &t.instance_id, &t.name, &usage);
                st.failures.lock().unwrap().remove(&t.id);
            }
            // complete failed: ask the ENGINE before counting it as a failure —
            // a stale data-index hands us dead work-item ids, and blind retries
            // here once aborted four live instances (2026-06-04 kafka outage).
            fail => {
                let err = match fail { Ok(code) => format!("HTTP {code}"), Err(e) => e };
                match engine_check(&st, &t, &group).await {
                    EngineCheck::InstanceGone => {
                        log(format!("  ~ {:8} {} instance gone on engine — dropping ({err})",
                                    t.name, &t.instance_id[..8]));
                        st.failures.lock().unwrap().remove(&t.id);
                    }
                    EngineCheck::TaskGone => {
                        log(format!("  ~ {:8} {} task no longer on engine — dropping ({err})",
                                    t.name, &t.instance_id[..8]));
                        st.failures.lock().unwrap().remove(&t.id);
                    }
                    EngineCheck::Renewed(fresh_id) => {
                        let t2 = Task { id: fresh_id.clone(), ..t.clone() };
                        match complete(&st, &t2, &group, &result, sid.as_deref()).await {
                            Ok(200) | Ok(201) => {
                                log(format!("  ✓ {:8} [{}] {} -> {} (work-item id refreshed)",
                                            t.name, group, &t.instance_id[..8], result));
                                record_usage(&st, &t.instance_id, &t.name, &usage);
                                st.failures.lock().unwrap().remove(&t.id);
                            }
                            e2 => {
                                let n = bump(&st, &t.id);
                                log(format!("  ! {} complete error after id refresh: {:?} (retry {n})",
                                            t.name, e2));
                            }
                        }
                    }
                    EngineCheck::SameId => {
                        let n = bump(&st, &t.id);
                        log(format!("  ! {} complete error (engine-confirmed): {err} (retry {n})", t.name));
                    }
                    EngineCheck::Unknown(ce) => {
                        let n = bump(&st, &t.id);
                        log(format!("  ! {} complete error: {err}; engine check failed: {ce} (retry {n})",
                                    t.name));
                    }
                }
            }
        },
        Err(e) => {
            let n = bump(&st, &t.id);
            log(format!("  ! {} error: {e} (retry {n})", t.name));
        }
    }
    st.in_flight.lock().unwrap().remove(&t.id);
}

fn bump(st: &State, tid: &str) -> u32 {
    let mut f = st.failures.lock().unwrap();
    let n = f.entry(tid.to_string()).or_insert(0);
    *n += 1;
    *n
}

// ---- data-index reconciler ---------------------------------------------------
//
// The data-index is a projection built from kafka events; lost events (broker
// outage, disk-full) leave it drifted FOREVER — zombie RUNNING rows on the
// monitor, phantom Ready tasks, and invisible live instances. The engine's
// REST API reads its own PG synchronously, so it is the ground truth. Every
// RECONCILE_SECS we diff the two and repair the data-index directly in its PG.
// Late kafka events overwrite the repairs (events win); the reconciler only
// touches rows that STAY drifted.

/// Engine-side Ready tasks of one instance, across the configured groups.
/// Ok(None) = instance no longer exists on the engine.
async fn engine_ready_tasks(st: &State, pid: &str, iid: &str)
    -> Result<Option<Vec<(String, String, String)>>, String> { // (task_id, name, group)
    let mut out = Vec::new();
    for g in &st.cfg.reconcile_groups {
        let url = format!("{}/{}/{}/tasks?group={}", st.cfg.engine, pid, iid, g);
        match req_json(st, reqwest::Method::GET, &url, None, Duration::from_secs(30), None).await {
            Err(e) if e.starts_with("HTTP 404") => return Ok(None),
            Err(e) => return Err(e),
            Ok((_, body)) => {
                let v: Value = serde_json::from_str(&body).unwrap_or(Value::Null);
                for e in v.as_array().map(|a| a.as_slice()).unwrap_or(&[]) {
                    if e["phaseStatus"].as_str() == Some("Ready") {
                        if let (Some(id), Some(name)) = (e["id"].as_str(), e["name"].as_str()) {
                            if !out.iter().any(|(i, _, _): &(String, String, String)| i.as_str() == id) {
                                out.push((id.to_string(), name.to_string(), g.clone()));
                            }
                        }
                    }
                }
            }
        }
    }
    Ok(Some(out))
}

async fn reconcile_once(st: &State, pg: &tokio_postgres::Client) -> Result<(), String> {
    for pid in &st.cfg.reconcile_pids {
        // 1. engine truth: live instances of this process
        let (_, body) = req_json(st, reqwest::Method::GET, &format!("{}/{}", st.cfg.engine, pid),
                                 None, Duration::from_secs(30), None).await?;
        let v: Value = serde_json::from_str(&body).map_err(|e| format!("{e}"))?;
        let live: HashSet<String> = v.as_array().map(|a| a.as_slice()).unwrap_or(&[]).iter()
            .filter_map(|e| e["id"].as_str().map(String::from)).collect();

        // 2. data-index view: ACTIVE instances of this process
        let q = json!({"query": format!(
            "{{ ProcessInstances(where: {{processId: {{equal: \"{pid}\"}}, state: {{equal: ACTIVE}}}}) {{ id }} }}")});
        let (_, body) = req_json(st, reqwest::Method::POST, &format!("{}/graphql", st.cfg.data_index),
                                 Some(&q), Duration::from_secs(60), None).await?;
        let v: Value = serde_json::from_str(&body).map_err(|e| format!("{e}"))?;
        let dix: HashSet<String> = v["data"]["ProcessInstances"].as_array()
            .map(|a| a.as_slice()).unwrap_or(&[]).iter()
            .filter_map(|e| e["id"].as_str().map(String::from)).collect();

        // 3. zombie drift: DI says ACTIVE, engine no longer has it
        for id in dix.difference(&live) {
            let n = pg.execute(
                "UPDATE processes SET state = 3, end_time = now(), last_update_time = now() \
                 WHERE id = $1 AND state = 1", &[id]).await.map_err(|e| format!("{e}"))?;
            pg.execute(
                "UPDATE tasks SET state = 'Aborted', last_update = now() \
                 WHERE process_instance_id = $1 AND state IN ('Ready', 'Reserved')", &[id])
                .await.map_err(|e| format!("{e}"))?;
            if n > 0 {
                log(format!("  ⟳ reconcile: {pid} {} gone on engine → marked ABORTED in data-index",
                            &id[..8]));
            }
        }

        // 4. invisible drift: engine-live instance the DI never saw — insert a
        //    minimal row so the monitor shows it (events later fill in detail)
        for id in live.difference(&dix) {
            let n = pg.execute(
                "INSERT INTO processes (id, process_id, process_name, state, start_time, \
                                        last_update_time, endpoint) \
                 VALUES ($1, $2, $2, 1, now(), now(), $3) ON CONFLICT (id) DO NOTHING",
                &[id, pid, &format!("{}/{}", st.cfg.engine, pid)]).await
                .map_err(|e| format!("{e}"))?;
            if n > 0 {
                log(format!("  ⟳ reconcile: {pid} {} live on engine but missing in data-index → inserted",
                            &id[..8]));
            }
        }

        // 5. task-level drift on live instances: phantom Ready rows (work item
        //    gone — today's stale-id trap) and missing Ready rows (event lost;
        //    inserting them keeps THIS worker dispatching during an outage)
        for iid in &live {
            let Some(etasks) = engine_ready_tasks(st, pid, iid).await? else { continue };
            let rows = pg.query(
                "SELECT id FROM tasks WHERE process_instance_id = $1 AND state = 'Ready'", &[iid])
                .await.map_err(|e| format!("{e}"))?;
            let ditasks: HashSet<String> = rows.iter().map(|r| r.get::<_, String>(0)).collect();
            for tid in ditasks.iter().filter(|t| !etasks.iter().any(|(id, _, _)| id == *t)) {
                pg.execute("UPDATE tasks SET state = 'Aborted', last_update = now() WHERE id = $1",
                           &[tid]).await.map_err(|e| format!("{e}"))?;
                log(format!("  ⟳ reconcile: phantom Ready task {} on {} → Aborted", &tid[..8], &iid[..8]));
            }
            for (tid, name, group) in etasks.iter().filter(|(id, _, _)| !ditasks.contains(id)) {
                pg.execute(
                    "INSERT INTO tasks (id, name, state, process_id, process_instance_id, \
                                        started, last_update) \
                     VALUES ($1, $2, 'Ready', $3, $4, now(), now()) ON CONFLICT (id) DO NOTHING",
                    &[tid, name, pid, iid]).await.map_err(|e| format!("{e}"))?;
                pg.execute(
                    "INSERT INTO tasks_potential_groups (task_id, group_id) VALUES ($1, $2) \
                     ON CONFLICT (task_id, group_id) DO NOTHING",
                    &[tid, group]).await.map_err(|e| format!("{e}"))?;
                log(format!("  ⟳ reconcile: Ready task {name} ({}) on {} missing in data-index → inserted",
                            &tid[..8], &iid[..8]));
            }
        }
    }
    Ok(())
}

async fn reconcile_loop(st: Arc<State>) {
    log(format!("reconciler: every {}s, processes={:?}, groups={:?}",
                st.cfg.reconcile_secs, st.cfg.reconcile_pids, st.cfg.reconcile_groups));
    loop {
        tokio::time::sleep(Duration::from_secs(st.cfg.reconcile_secs)).await;
        // fresh connection per cycle: trivial at this cadence, no stale-conn handling
        match tokio_postgres::connect(&st.cfg.dataindex_pg, tokio_postgres::NoTls).await {
            Ok((pg, conn)) => {
                let h = tokio::spawn(conn);
                if let Err(e) = reconcile_once(&st, &pg).await {
                    log(format!("  ⟳ reconcile error: {e}"));
                }
                h.abort();
            }
            Err(e) => log(format!("  ⟳ reconcile: pg connect failed: {e}")),
        }
    }
}

// ---- main poll loop ---------------------------------------------------------

#[tokio::main]
async fn main() {
    let cfg = Cfg::from_env();
    let conc_ai: usize = env_or("CONC_AI", "2").parse().unwrap_or(2);
    let conc_fix: usize = env_or("CONC_FIX", "1").parse().unwrap_or(1);
    let conc_jenkins: usize = env_or("CONC_JENKINS", "3").parse().unwrap_or(3);
    log(format!(
        "workflow-task-worker (rust) MODE={} engine={} data-index={} poll={}s conc(ai={},fix={},jenkins={})",
        cfg.mode, cfg.engine, cfg.data_index, cfg.poll_secs, conc_ai, conc_fix, conc_jenkins));

    let st = Arc::new(State {
        http: reqwest::Client::new(),
        failures: Mutex::new(HashMap::new()),
        given_up: Mutex::new(HashSet::new()),
        in_flight: Mutex::new(HashSet::new()),
        notified: Mutex::new(HashSet::new()),
        sem_ai: Semaphore::new(conc_ai),
        sem_fix: Semaphore::new(conc_fix),
        sem_jenkins: Semaphore::new(conc_jenkins),
        cfg,
    });

    if !st.cfg.dataindex_pg.is_empty() && st.cfg.reconcile_secs > 0 {
        tokio::spawn(reconcile_loop(st.clone()));
    }
    if st.cfg.mode == "reconcile-only" {
        // repair-only deployment (ops/testing): no task dispatch at all
        loop { tokio::time::sleep(Duration::from_secs(3600)).await; }
    }

    loop {
        match ready_tasks(&st).await {
            Ok(tasks) => {
                let total = tasks.len();
                let mut dispatched = 0;
                for t in tasks {
                    // human-handoff tasks: NEVER auto-complete — park (stay Ready)
                    // until a person releases them (out=verify|giveup). Notify once
                    // with how to take over; the dashboard shows the `sid` + attach cmd.
                    if t.group.as_deref() == Some("human") {
                        if st.notified.lock().unwrap().insert(t.id.clone()) {
                            log(format!("  ⏸ {:8} {} PARKED for human handoff (group=human) — \
                                         attach to the agent session via the dashboard resume command",
                                        t.name, &t.instance_id[..8]));
                        }
                        continue;
                    }
                    // skip tasks already being processed by a live tokio task
                    if st.in_flight.lock().unwrap().contains(&t.id) {
                        continue;
                    }
                    // retries exhausted -> abort the instance once -> FAILED
                    let failed = *st.failures.lock().unwrap().get(&t.id).unwrap_or(&0);
                    if failed >= st.cfg.max_retries {
                        let fresh = st.given_up.lock().unwrap().insert(t.instance_id.clone());
                        if fresh {
                            let code = abort_instance(&st, &t.process_id, &t.instance_id).await;
                            log(format!("  ✗ {:8} {} gave up after {} retries → FAILED (abort {})",
                                        t.name, &t.instance_id[..8], st.cfg.max_retries, code));
                        }
                        continue;
                    }
                    st.in_flight.lock().unwrap().insert(t.id.clone());
                    dispatched += 1;
                    tokio::spawn(process_task(st.clone(), t));
                }
                if total > 0 {
                    log(format!("cycle: {total} ready, {dispatched} dispatched, {} in flight",
                                st.in_flight.lock().unwrap().len()));
                }
            }
            Err(e) => log(format!("cycle error: {e}")),
        }
        tokio::time::sleep(Duration::from_secs_f64(st.cfg.poll_secs)).await;
    }
}
