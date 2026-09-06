#!/usr/bin/env python3
"""UI/UX 稽核 backlog 模式的自驗 —— 跑法:python3 uiux_backlog_selftest.py

## 為什麼

09-04 量到:稽核自動開的 24 張 sdlc 單 **0 落地、13 個殭屍、同一題重開 5 次**。
舊去重只比「活著的實例」與「開著的 PR」—— 一題一結束(中止/升級/PR 關掉),下一輪就再開。
沒有任何地方記得「這題處理過了 / 決定不做」。

新做法:發現 → 指紋去重(比 GitHub issue 的 **open + closed**)→ 開 issue(label uiux-audit),
**不開任何 sdlc 實例**;開單改由人挑。本輪不再 FAIL 的 open issue 自動關閉。

C 組是這次的核心價值:**人關掉的題目不會回來**。對照組把去重改回「只看 open」跑同一份資料,
必須重開 —— 判準若不能對著壞版本變紅,它就不是判準。

注意:arcana-skills 沒有 CI,這支不會自動跑。這是實話,不是設計。
"""
import importlib.util, json, os, sys, subprocess

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
os.environ.setdefault("STUB", "")
os.environ.pop("UIUX_AUDIT_MODE", None)          # 測的就是預設值 = backlog
spec = importlib.util.spec_from_file_location("atn_server", os.path.join(D, "server.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ok = fail = 0
def check(label, cond):
    global ok, fail
    if cond: ok += 1; print("  ✓ %s" % label)
    else:    fail += 1; print("  ✗ %s" % label)

FINDINGS = {"routes": ["/org", "/workflow", "/profile"], "findings": [
    {"route": "/org", "kind": "i18n", "detail": "標題中英夾雜", "severity": "fail"},
    {"route": "/workflow", "kind": "empty-state", "detail": "錯誤狀態是空的", "severity": "fail"},
    {"route": "/profile", "kind": "contrast", "detail": "對比夠", "severity": "pass"},
]}
SLUG_ORG = m._uiux_slug("/org", "i18n"); SLUG_WF = m._uiux_slug("/workflow", "empty-state")
GH = []          # 每一次 gh 呼叫的 argv
STARTS = []      # 任何對引擎/產品 API 的 POST(backlog 模式必須是 0)


def run(existing_issues, create_rc=0, list_rc=0, history_rows=None, env=None, payload=None):
    GH.clear(); STARTS.clear()
    orig = subprocess.run
    def patched(cmd, *a, **k):
        c = cmd if isinstance(cmd, list) else [str(cmd)]
        class R: returncode = 0; stdout = ""; stderr = ""
        r = R()
        if c[:2] == ["docker", "run"]:
            r.stdout = json.dumps(FINDINGS); return r
        if c[0] == "gh":
            GH.append(c)
            if c[1:3] == ["label", "create"]:
                r.returncode = 1; r.stderr = "label already exists"; return r
            if c[1:3] == ["issue", "list"]:
                r.returncode = list_rc; r.stdout = json.dumps(existing_issues) if list_rc == 0 else ""; r.stderr = "boom" if list_rc else ""; return r
            if c[1:3] == ["issue", "create"]:
                r.returncode = create_rc; r.stdout = "https://github.com/x/y/issues/%d\n" % (100 + len(GH)) if create_rc == 0 else ""; r.stderr = "HTTP 403" if create_rc else ""; return r
            if c[1:3] == ["issue", "close"]:
                return r
            return r
        if c[0] == "curl":
            url = c[c.index("-X") + 2] if "-X" in c else ""
            if url.endswith("/graphql"):
                r.stdout = json.dumps({"data": {"ProcessInstances": history_rows or []}}); return r
            STARTS.append(url); r.stdout = "{}"; return r
        return orig(cmd, *a, **k)
    subprocess.run = patched
    saved = {k: os.environ.get(k) for k in (env or {})}
    try:
        for k, v in (env or {}).items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v
        return m.uiux_audit_flow(payload or {})
    finally:
        subprocess.run = orig
        for k, v in saved.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v

def creates(): return [c for c in GH if c[1:3] == ["issue", "create"]]
def closes():  return [c for c in GH if c[1:3] == ["issue", "close"]]
def arg(c, flag): return c[c.index(flag) + 1] if flag in c else ""

print("\n════ A. 新發現 → 開 issue,不開 sdlc 實例 ════")
hist = [{"id": "6775540d-aaaa", "state": "ABORTED", "variables": json.dumps({"feature_request": "舊單" + m._audit_marker(SLUG_ORG)})}]
r = run([], history_rows=hist)
check("mode=backlog、started=0、沒有任何 POST 打到引擎/產品 API(%d)" % len(STARTS), r.get("mode") == "backlog" and r.get("started") == 0 and not STARTS)
check("兩個 FAIL 開兩張,pass 的不開(filed=%d)" % len(r.get("filed", [])), len(creates()) == 2 and len(r.get("filed", [])) == 2)
c0 = creates()[0]
check("label 是 uiux-audit", arg(c0, "--label") == m.UIUX_BACKLOG_LABEL)
check("標題帶指紋、標題讀得回 (route, slug)", m._uiux_parse_title(arg(c0, "--title")) == ("/org", SLUG_ORG))
body = arg(c0, "--body")
check("body 有稽核識別行(人貼進啟動表單時識別碼跟著走)", SLUG_ORG in m._audit_markers_in(body))
check("body 列出這個指紋的歷史實例(6775540d ABORTED)", "6775540d" in body and "ABORTED" in body)
check("body 有怎麼開單", "怎麼開單" in body)
check("findings/fails 計數與舊形狀相容", r.get("findings") == 3 and r.get("fails") == 2 and r.get("skipped") == 0)

print("\n════ B. 同指紋已有 open issue → 不重開 ════")
r = run([{"number": 7, "state": "OPEN", "title": m._uiux_title("/org", "i18n", SLUG_ORG), "url": "u7"}])
check("只開 workflow 那張,org 去重(filed=%d deduped=%d)" % (len(r["filed"]), r["deduped"]), len(creates()) == 1 and r["deduped"] == 1)
check("open 且仍 FAIL 的不會被自動關", not closes())

print("\n════ C. 同指紋 CLOSED:人判不做(not planned)不重開;修好/自動關(completed)再出現要重開 ════")
NP = {"number": 7, "state": "CLOSED", "stateReason": "NOT_PLANNED", "title": m._uiux_title("/org", "i18n", SLUG_ORG), "url": "u7"}
r = run([NP])
check("not planned 算已記:org 不重開(filed=%d deduped=%d)" % (len(r["filed"]), r["deduped"]), len(creates()) == 1 and r["deduped"] == 1)
r = run([dict(NP, stateReason="COMPLETED")])
check("completed(修好過)再出現 = 回歸:org 重開(filed=%d)" % len(r["filed"]), len(creates()) == 2 and r["deduped"] == 0)
# 對照組:舊語意「只看 open」—— 對 not planned 那份資料必須重開。判準要能對著壞版本變紅。
r = run([it for it in [NP] if it["state"] == "OPEN"])
check("對照組:去重只看 open 時,not planned 的 org 會被重開(這正是舊寫法的病)", len(creates()) == 2)

print("\n════ D. 本輪不再 FAIL 的 open issue 自動關閉;沒稽核到的路由不動 ════")
r = run([{"number": 8, "state": "OPEN", "title": m._uiux_title("/org", "spacing", "uiux-org-spacing"), "url": "u8"},
         {"number": 9, "state": "OPEN", "title": m._uiux_title("/governance", "i18n", "uiux-governance-i18n"), "url": "u9"},
         {"number": 10, "state": "CLOSED", "title": m._uiux_title("/org", "old", "uiux-org-old"), "url": "u10"}])
cl = closes()
check("org/spacing(稽核到、沒再 FAIL)被關", len(cl) == 1 and arg(cl[0], "-R") and "8" in cl[0])
check("governance 沒在本輪路由裡 → 不關;已 CLOSED 的不再關", not any("9" in c or "10" in c for c in cl))
check("closed 回報帶 url", r["closed"] == ["u8"])

print("\n════ D2. 自動關閉用 reason=completed(再出現會重開),不是 not planned ════")
r = run([{"number": 8, "state": "OPEN", "title": m._uiux_title("/org", "spacing", "uiux-org-spacing"), "url": "u8"}])
check("close 帶 --reason completed", closes() and arg(closes()[0], "--reason") == "completed")

print("\n════ G. 兩輪同時跑:第二輪必須看得到第一輪剛開的(鎖) ════")
import threading, time as _time
ORDER = []
def run_parallel():
    orig = subprocess.run
    created = []
    def patched(cmd, *a, **k):
        c = cmd if isinstance(cmd, list) else [str(cmd)]
        class R: returncode = 0; stdout = ""; stderr = ""
        r = R()
        if c[:2] == ["docker", "run"]: r.stdout = json.dumps(FINDINGS); return r
        if c[0] == "gh":
            if c[1:3] == ["label", "create"]: r.returncode = 1; r.stderr = "already exists"; return r
            if c[1:3] == ["issue", "list"]:
                ORDER.append("list"); _time.sleep(0.3)   # 拉長「列清單→開單」的窗,沒鎖就一定撞
                r.stdout = json.dumps(list(created)); return r
            if c[1:3] == ["issue", "create"]:
                ORDER.append("create"); url = "https://x/%d" % (len(created) + 1)
                created.append({"number": len(created) + 1, "state": "OPEN", "title": arg(c, "--title"), "url": url})
                r.stdout = url + "\n"; return r
            return r
        if c[0] == "curl": r.stdout = json.dumps({"data": {"ProcessInstances": []}}); return r
        return orig(cmd, *a, **k)
    subprocess.run = patched
    try:
        res = [None, None]
        th = [threading.Thread(target=lambda i=i: res.__setitem__(i, m.uiux_audit_flow({}))) for i in range(2)]
        [x.start() for x in th]; [x.join() for x in th]
        return res, len(created)
    finally:
        subprocess.run = orig
res, total = run_parallel()
check("兩輪並行只開 2 張(不是 4),第二輪 deduped=2(filed=%s/%s, total=%d)" % (len(res[0]["filed"]), len(res[1]["filed"]), total),
      total == 2 and sorted([len(res[0]["filed"]), len(res[1]["filed"])]) == [0, 2] and sorted([res[0]["deduped"], res[1]["deduped"]]) == [0, 2])
check("呼叫順序是 list,create,create,list(第二次 list 在第一輪開完之後)", ORDER[:4] == ["list", "create", "create", "list"])

print("\n════ E. gh 壞掉不能靜默 ════")
r = run([], create_rc=1)
check("create 失敗 → filed 空、errors 兩筆且點名指紋", r["filed"] == [] and len(r["errors"]) == 2 and SLUG_ORG in r["errors"][0])
r = run([], list_rc=1)
check("list 失敗 → 本輪不開單(沒有去重的開單就是洪水)且 errors 說明", not creates() and r["errors"] and "不開單" in r["errors"][0])

print("\n════ F. 上限與回退 ════")
r = run([], env={"UIUX_AUDIT_MAX_ISSUES": "1"})
check("上限 1:開 1 張,另一張進 capped 而不是消失", len(creates()) == 1 and r["capped"] == [SLUG_WF])
r = run([], env={"UIUX_AUDIT_MODE": "start", "UIUX_AUDIT_REQUESTER": ""})
check("UIUX_AUDIT_MODE=start 走舊路徑(沒有 filed 鍵、有 unowned)", "filed" not in r and "unowned" in r)

print("\n  通過 %d,失敗 %d" % (ok, fail)); sys.exit(1 if fail else 0)
