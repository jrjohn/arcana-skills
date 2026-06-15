#!/usr/bin/env python3
"""
agent-task-node — Claude agent as a SonataFlow execution node.

Exposes scoped CI-maintenance tasks over HTTP. Each task runs a focused
`claude -p` invocation with a JSON Schema so the workflow engine gets a
validated, typed result back (no free-text parsing).

POST /task/diagnose  {"job":..,"buildUrl":..}      -> {cause,fixable,proposedAction,confidence}
POST /task/fix       {"job":..,"cause":..}          -> {action,prUrl,branch,summary,pushed}
POST /task/merge     {"prUrl":..}                   -> {merged,reason}
GET  /healthz                                       -> {"ok":true}

Design notes:
- Stateless; SonataFlow owns flow/state/retry. This node only does the
  intelligent step and returns typed JSON.
- `claude -p --json-schema <schema>` (CLI >= 2.1.x) validates output.
- Prompts are kept terse + per-task (decomposed from the old daily.md).
  They lean on the agent's memory (arch-qube / network-prune / disk traps).
- Auth: relies on the mounted claude-home (/root/.claude) credentials,
  same as the existing daily-ci-agent image this is built FROM.
"""
import json
import os
import shutil
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CLAUDE = shutil.which("claude") or "/usr/local/bin/claude"
MODEL = os.environ.get("AGENT_MODEL", "")  # empty => settings-driven default
TIMEOUT = int(os.environ.get("AGENT_TASK_TIMEOUT", "900"))  # 15 min per task
STUB = os.environ.get("AGENT_STUB", "") == "1"  # test mode: skip claude, return canned typed JSON
STUB_RESPONSES = {
    "diagnose": {"cause": "stub: simulated build failure", "category": "code",
                 "fixable": True, "proposedAction": "stub: minimal patch", "confidence": 0.9},
    "fix": {"action": "stub-pr", "prUrl": "https://github.com/jrjohn/stub/pull/1",
            "branch": "ci/stub-fix", "summary": "stub: applied minimal fix", "pushed": True},
    "merge": {"merged": True, "reason": "stub: green build, auto-merged"},
    "sweep": {"checked": 14, "red": [], "retriggered": 0, "summary": "stub: all repos green"},
}

# --- JSON Schemas: the typed contract SonataFlow switches/retries on ---
SCHEMAS = {
    "diagnose": {
        "type": "object",
        "properties": {
            "cause": {"type": "string"},
            "category": {"type": "string",
                         "enum": ["code", "test", "infra", "registry", "disk",
                                  "network", "flaky-transient", "unknown"]},
            "fixable": {"type": "boolean"},
            "proposedAction": {"type": "string"},
            "confidence": {"type": "number"},
        },
        "required": ["cause", "category", "fixable", "proposedAction"],
    },
    "fix": {
        "type": "object",
        "properties": {
            "action": {"type": "string"},
            "prUrl": {"type": "string"},
            "branch": {"type": "string"},
            "summary": {"type": "string"},
            "pushed": {"type": "boolean"},
        },
        "required": ["action", "summary", "pushed"],
    },
    "merge": {
        "type": "object",
        "properties": {
            "merged": {"type": "boolean"},
            "reason": {"type": "string"},
        },
        "required": ["merged"],
    },
    "sweep": {
        "type": "object",
        "properties": {
            "checked": {"type": "integer"},
            "red": {"type": "array", "items": {"type": "string"}},
            "retriggered": {"type": "integer"},
            "summary": {"type": "string"},
        },
        "required": ["checked", "red", "summary"],
    },
}

# --- Per-task prompts (decomposed from daily.md; terse, schema does the shape) ---
def prompt_diagnose(p):
    return (
        f"A Jenkins pipeline build failed. job={p.get('job')} buildUrl={p.get('buildUrl')}.\n"
        "Fetch the console log (curl the buildUrl + /consoleText via the jenkins service), "
        "find the FIRST failing stage and the actual error.\n"
        "Classify the root cause. Known recurring traps (check memory): arch-qube registry "
        "blob loss (short read EOF), docker network prune racing compose builds (network not "
        "found), disk-pressure flood watermark, testcontainer needing docker.sock, mysql "
        "container unhealthy (often flaky-transient). Decide if it is agent-fixable via a code/"
        "config change on a PR branch, vs infra needing host action (not your job), vs a "
        "transient that just needs a re-trigger. Return the diagnosis."
    )

def prompt_fix(p):
    return (
        f"Fix the diagnosed CI failure for job={p.get('job')}. Root cause: {p.get('cause')}.\n"
        "Make the minimal correct change on a NEW branch off the repo's default branch, push, "
        "open a PR. Do NOT touch main directly. If the cause is infra/host-level (not fixable "
        "by a repo change) or a transient, set action accordingly and pushed=false. "
        "Verify-before-push discipline: only push changes you can justify."
    )

def prompt_merge(p):
    return (
        f"PR {p.get('prUrl')} has a fully green verifying build (real gates passed). "
        "Per the autonomous-maintenance policy, merge it if it is a clean app/hardening/dep PR "
        "and its checks are green. Return whether you merged and why/why not."
    )

def prompt_sweep(p):
    return (
        "Safety-net sweep of ALL Arcana repos (the periodic maintenance pass that "
        "replaced the old cron daily-run). For each repo, check the latest main-branch "
        "Jenkins build status. List repos whose main is RED. For each RED main, re-trigger "
        "its Jenkins build so the maintenance workflow picks up the resulting build event. "
        "Also note repos with an open Renovate/dep PR that is green but unmerged. Return "
        "counts (checked, retriggered) + the red repo list + a short summary."
    )

PROMPTS = {"diagnose": prompt_diagnose, "fix": prompt_fix, "merge": prompt_merge, "sweep": prompt_sweep}


def run_claude(task, payload):
    if STUB:
        return STUB_RESPONSES[task]
    schema = json.dumps(SCHEMAS[task])
    prompt = PROMPTS[task](payload)
    cmd = [CLAUDE, "-p", prompt, "--json-schema", schema,
           "--no-session-persistence"]
    if MODEL:
        cmd += ["--model", MODEL]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
    if proc.returncode != 0:
        raise RuntimeError(f"claude exit {proc.returncode}: {proc.stderr[:500]}")
    out = proc.stdout.strip()
    # claude -p --json-schema emits the validated JSON object as stdout
    return json.loads(out)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/healthz":
            self._send(200, {"ok": True})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        task = self.path.rsplit("/", 1)[-1]
        if task not in PROMPTS:
            return self._send(404, {"error": f"unknown task {task}"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n) or b"{}")
        except Exception as e:
            return self._send(400, {"error": f"bad json: {e}"})
        try:
            result = run_claude(task, payload)
            self._send(200, result)
        except subprocess.TimeoutExpired:
            self._send(504, {"error": "task timeout"})
        except Exception as e:
            self._send(500, {"error": str(e)})

    def log_message(self, fmt, *args):
        print("[agent-task-node] " + (fmt % args), flush=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8090"))
    print(f"[agent-task-node] listening on :{port} (claude={CLAUDE})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
