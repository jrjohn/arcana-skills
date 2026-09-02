#!/usr/bin/env python3
"""稽核開單走產品 API,不繞引擎 —— 跑法:python3 audit_product_api_selftest.py

## 為什麼

2026-09-02:流程詳情每一關顯示「這個階段當時沒有記錄表單內容」,即使值就在
流程變數裡。真因是稽核**直接打引擎** `POST engine/sdlc-code-flow`,繞過
`flow_lifecycle_controller` 的「啟動時記一刻」(#285)—— 起點表單那一刻沒被寫進
artifact_instance_log,而抽屜讀的 by-flow 只回真的發生過的刻(reconcile-on-read
已於 2026-08-25 刻意移除),於是回 0 筆。

實測:同一份 payload 走引擎 → by-flow 0 筆;走產品 API → 1 筆(formData 帶
feature_request)。修法是讓稽核走產品 API,#285 的記錄邏輯就涵蓋它了 ——
單一漏斗,同一份測試同時管兩條路。

這支攔在 subprocess(curl 唯一的出口),驗**真的送出去的**是產品 API 的路徑與
Bearer,不是我以為送的。

注意:arcana-skills 沒有 CI,這支不會自動跑。這是實話,不是設計。
"""
import importlib.util, json, os, subprocess, sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
os.environ.setdefault("STUB", "")
spec = importlib.util.spec_from_file_location("atn", os.path.join(D, "server.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ok = fail = 0
def check(label, cond, extra=""):
    global ok, fail
    if cond: ok += 1; print("  ✓ %s" % label)
    else:    fail += 1; print("  ✗ %s  %s" % (label, str(extra)[:200]))

CALLS = []
class R:
    def __init__(self, out): self.returncode = 0; self.stdout = out; self.stderr = ""

def patched_run(cmd, *a, **k):
    CALLS.append(cmd)
    url = cmd[cmd.index("-X") + 2] if "-X" in cmd else ""
    if url.endswith("/auth/login"):
        return R(json.dumps({"data": {"access_token": "FAKE.JWT.TOKEN"}}))
    if url.endswith("/workflows/sdlc-code-flow/start"):
        return R(json.dumps({"iid": "prod-iid-123"}))
    return R("{}")

def run_start(env=None, login_ok=True):
    global patched_run
    CALLS.clear()
    old = {k: os.environ.get(k) for k in ("READ_API", "UIUX_AUDIT_PASS")}
    orig = subprocess.run
    def pr(cmd, *a, **k):
        url = cmd[cmd.index("-X") + 2] if "-X" in cmd else ""
        CALLS.append(cmd)
        if url.endswith("/auth/login"):
            return R(json.dumps({"data": {"access_token": "FAKE.JWT"}} if login_ok else {"error": "bad creds"}))
        if url.endswith("/start"):
            return R(json.dumps({"iid": "prod-iid-123"}))
        return R("{}")
    subprocess.run = pr
    try:
        for kk, vv in (env or {}).items():
            if vv is None: os.environ.pop(kk, None)
            else: os.environ[kk] = vv
        return m._start_via_product_api("boss", {"projectId": "aaf", "feature_request": "x"})
    finally:
        subprocess.run = orig
        for kk, vv in old.items():
            if vv is None: os.environ.pop(kk, None)
            else: os.environ[kk] = vv


print("\n════ A. 走產品 API,不走引擎 ════")
res = run_start({"READ_API": "http://api:8080"})
urls = [c[c.index("-X") + 2] for c in CALLS if "-X" in c]
check("先登入 /auth/login", any("/auth/login" in u for u in urls), urls)
check("再打產品 API /workflows/sdlc-code-flow/start",
      any(u.endswith("/workflows/sdlc-code-flow/start") for u in urls), urls)
check("**沒有**打引擎的 /sdlc-code-flow(那條會繞過 #285)",
      not any(u.rstrip("/").endswith(":8081/sdlc-code-flow") or
              (u.endswith("/sdlc-code-flow") and "/workflows/" not in u) for u in urls), urls)
start_call = next((c for c in CALLS if "-X" in c and c[c.index("-X")+2].endswith("/start")), None)
check("啟動帶了 Bearer 權杖", start_call and "Authorization: Bearer FAKE.JWT" in start_call, start_call)
check("回 {'id': iid}（與引擎回應相容）", res.get("id") == "prod-iid-123", res)

print("\n════ B. 登不進 → 回空,而且不繞道打引擎 ════")
# 這一組是重點:登入失敗時**絕不**退回直接打引擎 —— 那會把要修的洞又打開。
res2 = run_start({"READ_API": "http://api:8080"}, login_ok=False)
urls2 = [c[c.index("-X") + 2] for c in CALLS if "-X" in c]
check("登入失敗回 {}（當成沒開成）", res2 == {}, res2)
check("失敗後沒有打任何 /start", not any(u.endswith("/start") for u in urls2), urls2)
check("失敗後沒有繞去打引擎",
      not any(u.endswith("/sdlc-code-flow") and "/workflows/" not in u for u in urls2), urls2)

print("\n════ C. 密碼取自 env,可覆蓋 ════")
run_start({"READ_API": "http://api:8080", "UIUX_AUDIT_PASS": "s3cret"})
login_call = next((c for c in CALLS if "-X" in c and c[c.index("-X")+2].endswith("/auth/login")), None)
check("登入用的是 UIUX_AUDIT_PASS 的值",
      login_call and '"s3cret"' in login_call[-1], login_call and login_call[-1][:80])

print("\n" + "═" * 46)
print("  通過 %d,失敗 %d" % (ok, fail))
sys.exit(1 if fail else 0)
