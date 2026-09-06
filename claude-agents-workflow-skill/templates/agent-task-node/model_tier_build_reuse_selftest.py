#!/usr/bin/env python3
"""(h) 分級用模型 + usage 主模型歸屬、(i) rework 沿用上一輪的後端映像 —— 跑法:python3 model_tier_build_reuse_selftest.py"""
import importlib.util, json, os, sys, subprocess
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); os.environ.setdefault("STUB", "")
for k in list(os.environ):
    if k.startswith("AGENT_MODEL"): os.environ.pop(k)
os.environ["AGENT_MODEL"] = "claude-opus-5"
spec = importlib.util.spec_from_file_location("atn_server", os.path.join(D, "server.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ok = fail = 0
def check(l, c):
    global ok, fail
    if c: ok += 1; print("  ✓", l)
    else: fail += 1; print("  ✗", l)

print("\n════ (h) 模型分級:節點 > 動詞 > AGENT_MODEL ════")
check("沒有任何 per-node 設定 → AGENT_MODEL", m._model_for({"_node": "SA", "_task": "sa"}) == "claude-opus-5")
os.environ["AGENT_MODEL_SA"] = "claude-sonnet-5"
check("AGENT_MODEL_SA 命中節點名(大小寫無關)", m._model_for({"_node": "SA", "_task": "sa"}) == "claude-sonnet-5")
os.environ["AGENT_MODEL_PMREVIEW"] = "claude-opus-5"; os.environ["AGENT_MODEL_PM_REVIEW"] = "x"
check("節點名 PmReview → PMREVIEW(非字母數字都壓成 _;pm-review 動詞 → PM_REVIEW)", m._model_key("PmReview") == "PMREVIEW" and m._model_key("pm-review") == "PM_REVIEW")
check("節點名優先於動詞", m._model_for({"_node": "PmReview", "_task": "pm-review"}) == "claude-opus-5")
check("只有動詞設定時用動詞", m._model_for({"_node": "SomethingElse", "_task": "pm-review"}) == "x")
check("無 per-node 設定 → 落回載入時的 AGENT_MODEL(m.MODEL),不是別的", m._model_for({"_node": "Test"}) == m.MODEL == "claude-opus-5")

print("\n════ (h) usage 主模型 = 吃最多 input 的,不是 dict 第一個 ════")
mu = {"claude-haiku-4-5-20251001": {"inputTokens": 1200, "outputTokens": 50},
      "claude-opus-5": {"inputTokens": 90000, "cacheReadInputTokens": 400000, "outputTokens": 3000}}
check("主模型是 opus(haiku 排第一也不會被當主模型)", m._dominant_model(mu) == "claude-opus-5")
check("breakdown 含 cache 讀取,兩個模型都在", m._models_breakdown(mu) == {"claude-haiku-4-5-20251001": 1200, "claude-opus-5": 490000})
check("modelUsage 空 → None,不炸", m._dominant_model({}) is None and m._models_breakdown(None) == {})

print("\n════ (i) 後端映像沿用:label 的 sha vs HEAD 的 arcana-cloud-rust/ 差異 ════")
CALLS = []
def make(label, diff_rc=0, diff_out=""):
    def patched(cmd, *a, **k):
        c = cmd if isinstance(cmd, list) else [str(cmd)]
        class R: returncode = 0; stdout = ""; stderr = ""
        r = R(); CALLS.append(c)
        if c[:3] == ["docker", "image", "inspect"]:
            if label is None: r.returncode = 1
            else: r.stdout = label + "\n"
        elif c[:2] == ["git", "diff"]:
            r.returncode = diff_rc; r.stdout = diff_out
        return r
    return patched
def need(label, **kw):
    CALLS.clear(); orig = subprocess.run; subprocess.run = make(label, **kw)
    try: return m._backend_build_needed("aaf-pr-api:abc", "/tmp/x", "HEADSHA")
    finally: subprocess.run = orig
n, why = need(None);            check("沒有上一輪映像 → 要建", n and "no previous" in why)
n, why = need("HEADSHA");       check("同一個 commit → 沿用", not n and "REUSING" in why)
n, why = need("OLDSHA", diff_out="");                          check("有舊映像且 arcana-cloud-rust/ 沒變 → 沿用", not n and "REUSING" in why)
n, why = need("OLDSHA", diff_out="arcana-cloud-rust/crates/a/src/lib.rs\n"); check("arcana-cloud-rust/ 有變 → 要建", n and "changed" in why)
n, why = need("OLDSHA", diff_rc=128);                          check("舊 commit 不在 clone 裡(git diff 失敗)→ 要建,不猜", n and "not in this clone" in why)
src_code = open(os.path.join(D, "server.py"), encoding="utf-8").read()
check("建置時打上 aaf.sha 與 aaf.pr-api label", '"--label", "aaf.sha=" + head' in src_code and '"aaf.pr-api=1"' in src_code)
check("teardown 不再 rmi 映像(留給下一輪沿用)", 'subprocess.run(["docker", "rmi", "-f", state["image"]]' not in src_code)
print("\n  通過 %d,失敗 %d" % (ok, fail)); sys.exit(1 if fail else 0)
