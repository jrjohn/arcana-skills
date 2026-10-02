#!/usr/bin/env python3
"""一個產品只有一份 session.db,而且放在不會壞的地方 —— 跑法:python3 project_memory_single_db_selftest.py

2026-10-02 查到兩件事:
  1. 31 輪 sdlc-code-flow 有節點寫到 `_memory/arcana-ai-bpm/`(其中 23 輪帶著 projectId=aaf,
     只是那幾個節點的 payload 沒帶)→ 同一個產品兩份記憶,兩份都是殘的。
  2. db 放在 Docker Desktop 從 Mac 掛進來的資料夾,4 個程序同時寫 40 秒就壞;
     放 Docker volume 61 萬筆 integrity_check ok。

  A 組:產品鍵 —— 物件 / 字串 / payload / 註冊表都對到同一個 id;對不到時「不用記憶」,絕不退回 repo 名
  B 組:資料庫路徑 —— PROJECT_MEM_DB_ROOT 有設就放那裡,而且每個讀寫的地方都走同一個函式
  C 組:真的註冊表(連不到明說沒跑,不算通過)

注意:arcana-skills 沒有 CI,這支不會自動跑。
"""
import importlib.util, inspect, json, os, sys, tempfile, urllib.request

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

REG = [{"projectId": "aaf", "repo": "jrjohn/arcana-ai-bpm", "integrationBranch": "main"},
       {"projectId": "s7", "repo": "jrjohn/other-product", "integrationBranch": "main"}]
REPO = "jrjohn/arcana-ai-bpm"

print("A 組 —— 產品鍵")
m._registry_projects_cached = lambda ttl=300: REG
check("preflight 放的整筆專案(dict)→ 取 projectId(以前會變成 \"{'projectId': ...}\" → 沒記憶)",
      m._project_slug({"_sdlc_project": {"projectId": "aaf", "tier": "company"}, "repo": REPO}) == "aaf")
check("_sdlc_project 是字串 → 照用", m._project_slug({"_sdlc_project": "aaf"}) == "aaf")
check("payload 頂層有 projectId", m._project_slug({"projectId": "aaf", "repo": REPO}) == "aaf")
check("projectId 放在 data 底下", m._project_slug({"data": {"projectId": "aaf", "repo": REPO}}) == "aaf")
check("沒有 projectId、只有 repo → 查註冊表得到 aaf(以前會回 arcana-ai-bpm,開第二份記憶)",
      m._project_slug({"repo": REPO, "base": "main"}) == "aaf")
check("repo 大小寫不同也對得到", m._project_slug({"repo": "JRJohn/Arcana-AI-BPM"}) == "aaf")
m._registry_projects_cached = lambda ttl=300: None
r = m._project_slug({"repo": REPO})
check("註冊表連不到 → 不用記憶(\"\"),絕不退回 repo 名", r == "" and r != "arcana-ai-bpm")
m._registry_projects_cached = lambda ttl=300: REG
check("註冊表裡沒有這個 repo → 不用記憶", m._project_slug({"repo": "jrjohn/unknown"}) == "")
check("沒有 repo 也沒有 projectId → \"\"", m._project_slug({}) == "")
two = REG + [{"projectId": "aaf-rel", "repo": REPO, "integrationBranch": "release"}]
check("同一個 repo 兩個專案 → 用整合分支挑", m._project_id_for_repo(two, REPO, "release") == "aaf-rel")
check("同一個 repo 兩個專案、沒有分支可挑 → 分不出來就不猜", m._project_id_for_repo(two, REPO, "") == "")

print("B 組 —— 資料庫路徑")
home = "/work/_memory/aaf"
m.PROJECT_MEM_DB_ROOT = ""
check("沒設 PROJECT_MEM_DB_ROOT → 跟逐字稿同目錄(舊行為)", m._project_mem_db(home) == home + "/session.db")
with tempfile.TemporaryDirectory() as t:
    m.PROJECT_MEM_DB_ROOT = t
    p = m._project_mem_db(home)
    check("有設 → <root>/<產品>/session.db,而且目錄建好了",
          p == os.path.join(t, "aaf", "session.db") and os.path.isdir(os.path.join(t, "aaf")))
m.PROJECT_MEM_DB_ROOT = ""
src = inspect.getsource(m)
helper = inspect.getsource(m._project_mem_db)
check("模組裡寫死 <home>/session.db 的只剩 _project_mem_db 自己",
      src.count('os.path.join(home, "session.db")') == helper.count('os.path.join(home, "session.db")') == 1
      and "CRS_DB=%s/session.db" not in src)
for fn in ("project_memory_recall", "project_memory_ingest", "_memory_brief"):
    check("%s 走 _project_mem_db" % fn, "_project_mem_db(home)" in inspect.getsource(getattr(m, fn)))

print("C 組 —— 真的註冊表")
url = os.environ.get("SDLC_REGISTRY_URL", "http://localhost:8088/api/v1/workflows/sdlc-projects")
try:
    with urllib.request.urlopen(url, timeout=10) as r:
        live = json.load(r).get("projects") or []
    check("真的註冊表:jrjohn/arcana-ai-bpm@main → aaf", m._project_id_for_repo(live, REPO, "main") == "aaf")
except Exception as e:                                          # noqa: BLE001
    print("  ⚠ notRun —— 連不到註冊表(%s);不算通過" % e)

print()
print("pass —— %d 項" % ok if fail == 0 else "gap —— %d 項不符(共 %d)" % (fail, ok + fail))
sys.exit(1 if fail else 0)
