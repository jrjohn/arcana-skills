#!/usr/bin/env python3
"""自動開的單必須指名回答人 —— 跑法:python3 audit_owner_selftest.py

## 為什麼

2026-08-31 量到:6 條 sdlc-code-flow 停在「需求詢問」,最久的卡了 3 天。

先確認**不是被藏起來**:引擎(帶 group=role-manager)、Data Index(state=Ready)、
收件匣 API(canApprove=true)、畫面(前三列就有兩筆)—— 每一層都看得到。

差別在一個欄位:

    人開的單    requester='boss'   projectId='aaf'
    機器開的單  requester=None     projectId=None

`uiux_audit_flow` 開單時只送 feature_request / repo / base / slug / uiFacing。
IntakeReview 一判定資訊不足就會停下來問,而那個問題沒有指名任何人。

修法是 fail-closed:指派不到人就不開單。**少開一張單,好過多一張沒人回答的單。**
而且要說出來 —— 一個 `skipped: 3` 看起來跟去重跳過一模一樣。

注意:arcana-skills 目前沒有 CI,所以這支不會自動跑。這是實話,不是設計。
"""
import importlib.util, json, os, sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
os.environ.setdefault("STUB", "")
spec = importlib.util.spec_from_file_location("atn_server", os.path.join(D, "server.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ok = fail = 0
def check(label, cond):
    global ok, fail
    if cond: ok += 1; print("  ✓ %s" % label)
    else:    fail += 1; print("  ✗ %s" % label)


# 形狀取自 uiux_audit_flow 真正的解析器,不是我以為的形狀:
# 它只認**以 `{"routes` 開頭**的那一行,而且用 `severity == "fail"` 篩,不是 `verdict`。
# 第一版兩個都猜錯,結果整個稽核提早 return,而 B 組卻是綠的 ——
# 「一張單都沒開」對「根本沒跑到開單那步」也成立。那是假綠,不是通過。
FINDINGS = {"routes": ["/org", "/workflow"], "findings": [
    {"route": "/org", "detail": "標題中英夾雜", "severity": "fail"},
    {"route": "/workflow", "detail": "錯誤狀態是空的", "severity": "fail"},
]}
POSTS = []


def run_audit(env):
    """跑一次稽核,攔下所有對引擎的 POST。

    攔在 `_curl_json` —— 那是它唯一對外送東西的地方,所以攔到的就是真的送出去的,
    不是我以為送出去的。
    """
    POSTS.clear()
    real_curl = m._curl_json if hasattr(m, "_curl_json") else None

    def fake_docker(*a, **k):
        class R:
            returncode = 0
            stdout = json.dumps(FINDINGS)   # 已是 `{"routes` 開頭
            stderr = ""
        return R()

    import subprocess
    orig_run = subprocess.run
    def patched_run(cmd, *a, **k):
        c = cmd if isinstance(cmd, list) else [str(cmd)]
        if c and c[0] == "docker":
            return fake_docker()
        if c and c[0] == "gh":
            class R: returncode = 0; stdout = "[]"; stderr = ""
            return R()
        if c and c[0] == "curl":
            body = None
            for i, x in enumerate(c):
                if x == "-d" and i + 1 < len(c):
                    body = json.loads(c[i + 1])
            url = c[3] if len(c) > 3 else ""
            POSTS.append((url, body))
            class R:
                returncode = 0
                stdout = json.dumps({"id": "fake-iid", "data": {"ProcessInstances": []}})
                stderr = ""
            return R()
        return orig_run(cmd, *a, **k)
    subprocess.run = patched_run
    old = {k: os.environ.get(k) for k in
           ("UIUX_AUDIT_REQUESTER", "UIUX_AUDIT_PROJECT", "UIUX_AUDIT_MAX")}
    try:
        for k, v in env.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v
        return m.uiux_audit_flow({})
    finally:
        subprocess.run = orig_run
        for k, v in old.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v


print("\n════ A. 有指派回答人時,開單並帶上 requester ════")
r = run_audit({"UIUX_AUDIT_REQUESTER": "boss", "UIUX_AUDIT_PROJECT": "aaf"})
starts = [b for u, b in POSTS if b and "feature_request" in b]
check("稽核跑完沒有提早 return（%s）" % ((r or {}).get("error") or "無錯誤"),
      "error" not in (r or {}))
check("有開單（%d 張）" % len(starts), len(starts) >= 1)
check("每張單都帶 requester",
      bool(starts) and all(b.get("requester") == "boss" for b in starts))
check("每張單都帶 projectId",
      bool(starts) and all(b.get("projectId") == "aaf" for b in starts))
check("原有欄位沒有掉",
      bool(starts) and all(all(k in b for k in
          ("feature_request", "repo", "base", "slug", "uiFacing")) for b in starts))
check("回報 started > 0", (r or {}).get("started", 0) >= 1)
check("沒有人被列為 unowned", not (r or {}).get("unowned"))

print("\n════ B. 指派不到人時,fail-closed 且說得出來 ════")
# 這一組是重點:沉默地照開才是舊行為,而舊行為的後果是 3 天沒人回答的單。
r2 = run_audit({"UIUX_AUDIT_REQUESTER": None, "UIUX_AUDIT_PROJECT": "aaf"})
starts2 = [b for u, b in POSTS if b and "feature_request" in b]
check("稽核真的跑到了開單那一步（防假綠）",
      (r2 or {}).get("fails", 0) >= 1 and "error" not in (r2 or {}))
check("一張單都沒開", not starts2)
check("列出被跳過的 slug", bool((r2 or {}).get("unowned")))
check("說得出理由（不是一個光禿禿的 skipped）",
      "指名回答人" in ((r2 or {}).get("unownedReason") or ""))
check("skipped 有反映出來", (r2 or {}).get("skipped", 0) >= 1)
check("started 為 0", (r2 or {}).get("started", 0) == 0)

print("\n════ C. 空白字串等同沒設定 ════")
r3 = run_audit({"UIUX_AUDIT_REQUESTER": "   "})
check("只有空白也算沒指派", not [b for u, b in POSTS if b and "feature_request" in b])
check("同樣說得出理由", bool((r3 or {}).get("unownedReason")))

print("\n" + "═" * 46)
print("  通過 %d,失敗 %d" % (ok, fail))
sys.exit(1 if fail else 0)
