#!/usr/bin/env python3
"""Arcana workflow task-worker.

Drives role-based BPMN flows to completion by polling the Kogito Data Index for
*ready* user tasks and dispatching each by node + role:

  Triage  (ai)      -> agent-task-node /task/diagnose on the failed build
  Build   (jenkins) -> trigger a rebuild of the original Jenkins job
  Decide  (ai)      -> decide outcome (merge / escalate) from the build result
  <other> (ai)      -> agent-task-node /task/decide  (generic)
  <other> (jenkins) -> trigger Jenkins job for the processId (generic)

This is the orchestration layer that, with the Jenkins "red build -> create
ci-flow instance" trigger, replaces the old inline routine: the BPMN flow + this
worker now own diagnose/build/decide.

Modes (MODE env):
  auto  (Mac-first): synthesize results, no agent-task-node / Jenkins needed.
  real  (bluesea):   call agent-task-node + Jenkins for real.

Per-node context (job, buildUrl, result) is read from the process instance
variables on the engine, so handlers act on the actual failed build.

Idempotent (completed tasks stop appearing); bounded retry (MAX_RETRIES).
Stdlib only — no pip install.
"""

import json
import os
import time
import urllib.error
import urllib.request
from base64 import b64encode
from collections import defaultdict

ENGINE_URL = os.environ.get("ENGINE_URL", "http://localhost:8081").rstrip("/")
DATA_INDEX_URL = os.environ.get("DATA_INDEX_URL", "http://localhost:8180").rstrip("/")
MODE = os.environ.get("MODE", "auto").lower()
POLL_SECS = float(os.environ.get("POLL_SECS", "5"))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))

AGENT_TASK_URL = os.environ.get("AGENT_TASK_URL", "").rstrip("/")
JENKINS_URL = os.environ.get("JENKINS_URL", "").rstrip("/")
JENKINS_USER = os.environ.get("JENKINS_USER", "")
JENKINS_TOKEN = os.environ.get("JENKINS_TOKEN", "")

_failures = defaultdict(int)


def _req(url, payload=None, method="POST", timeout=900, auth=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    if auth:
        req.add_header("Authorization", "Basic " + b64encode(auth.encode()).decode())
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode()


def ready_tasks():
    query = ("{ UserTaskInstances(where: {state: {equal: \"Ready\"}}) "
             "{ id name potentialGroups processId processInstanceId } }")
    _, body = _req(f"{DATA_INDEX_URL}/graphql", {"query": query}, timeout=60)
    return (json.loads(body).get("data") or {}).get("UserTaskInstances") or []


def instance_vars(process_id, instance_id):
    """Process instance variables from the engine (job, buildUrl, result, ...)."""
    try:
        _, body = _req(f"{ENGINE_URL}/{process_id}/{instance_id}", method="GET", timeout=30)
        return json.loads(body)
    except (urllib.error.URLError, json.JSONDecodeError):
        return {}


def complete(process_id, instance_id, task_name, task_id, group, result):
    url = (f"{ENGINE_URL}/{process_id}/{instance_id}/{task_name}/{task_id}"
           f"?phase=complete&group={group}")
    return _req(url, {"out": result})


# ---- node handlers -------------------------------------------------------

def diagnose(vars_):
    """Triage(ai): diagnose the failed build, and (mirroring the old routine
    guardrails) auto-fix only for red */main builds that are fixable code/deps/
    test. Uses the same agent-task-node endpoints the routine used."""
    if MODE == "real" and AGENT_TASK_URL:
        job = vars_.get("job", "")
        payload = {"job": job, "buildUrl": vars_.get("buildUrl", ""),
                   "result": vars_.get("result", "")}
        _, dbody = _req(f"{AGENT_TASK_URL}/task/diagnose", payload, timeout=900)
        try:
            d = json.loads(dbody)
        except json.JSONDecodeError:
            return "diagnose: done (unparseable)"
        cat = str(d.get("category", ""))
        fixable = bool(d.get("fixable", False))
        out = {"cause": d.get("cause", ""), "category": cat, "fixable": fixable, "fixed": False}
        # auto-fix only red */main + fixable + code/deps/test (routine guardrail)
        if job.endswith("/main") and fixable and cat in ("code", "deps", "test"):
            try:
                _, fbody = _req(f"{AGENT_TASK_URL}/task/fix",
                                {"job": job, "cause": d.get("cause", ""),
                                 "buildUrl": vars_.get("buildUrl", "")}, timeout=900)
                out["fixed"] = True
                out["fix"] = fbody[:500]
            except urllib.error.URLError as e:
                out["fix_error"] = str(e)
        return json.dumps(out)
    return f"ai auto-diagnose: {vars_.get('job', 'unknown')}"


def rebuild(vars_):
    """Build(jenkins): trigger a rebuild of the original Jenkins job."""
    if MODE == "real" and JENKINS_URL:
        build_url = vars_.get("buildUrl", "")
        # buildUrl = http://jenkins:8080/jenkins/job/.../<num>/  -> job url = drop the run number
        job_url = build_url.rstrip("/").rsplit("/", 1)[0] if build_url else ""
        if not job_url:
            raise RuntimeError("no buildUrl on instance; cannot rebuild")
        auth = f"{JENKINS_USER}:{JENKINS_TOKEN}" if JENKINS_USER else None
        code, _ = _req(f"{job_url}/build", payload=None, method="POST", timeout=30, auth=auth)
        return f"jenkins: rebuild triggered HTTP {code}"
    return "jenkins: rebuild (auto)"


def decide(vars_):
    """Decide(ai): outcome from triage + (re)build result. No external call —
    agent-task-node has no /task/decide; decide from available variables."""
    triage = str(vars_.get("triage", ""))
    fixed = '"fixed": true' in triage.lower() or '"fixed":true' in triage.lower()
    if fixed:
        return "fix PR opened; awaiting rebuild — merge via automerge safety net"
    if "fixable\": false" in triage.lower() or "fixable\":false" in triage.lower():
        return "not auto-fixable — escalate to human"
    return "rebuild triggered; awaiting result"


def dispatch(task, vars_):
    name = (task.get("name") or "").lower()
    groups = task.get("potentialGroups") or []
    group = groups[0] if groups else None
    if name == "triage":
        return group, diagnose(vars_)
    if name == "build":
        return group, rebuild(vars_)
    if name == "decide":
        return group, decide(vars_)
    # generic fallback by role
    if group == "ai":
        return group, decide(vars_)
    if group == "jenkins":
        return group, rebuild(vars_)
    return None, None


def cycle():
    tasks = ready_tasks()
    for t in tasks:
        tid = t["id"]
        if _failures[tid] >= MAX_RETRIES:
            continue
        vars_ = instance_vars(t["processId"], t["processInstanceId"])
        try:
            group, result = dispatch(t, vars_)
            if not group:
                continue
            status, _ = complete(t["processId"], t["processInstanceId"], t["name"], tid, group, result)
            if status in (200, 201):
                print(f"  ✓ {t['name']:8} [{group}] {t['processInstanceId'][:8]} -> {result}", flush=True)
                _failures.pop(tid, None)
            else:
                _failures[tid] += 1
                print(f"  ! {t['name']} HTTP {status} (retry {_failures[tid]})", flush=True)
        except (urllib.error.URLError, RuntimeError, KeyError) as e:
            _failures[tid] += 1
            print(f"  ! {t['name']} error: {e} (retry {_failures[tid]})", flush=True)
    return len(tasks)


def main():
    print(f"workflow-task-worker MODE={MODE} engine={ENGINE_URL} "
          f"data-index={DATA_INDEX_URL} poll={POLL_SECS}s", flush=True)
    while True:
        try:
            n = cycle()
            if n:
                print(f"cycle: {n} ready task(s) processed", flush=True)
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            print(f"cycle error: {e}", flush=True)
        time.sleep(POLL_SECS)


if __name__ == "__main__":
    main()
