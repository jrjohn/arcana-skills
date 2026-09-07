#!/usr/bin/env python3
"""arch-qube 報告要用它自己的鍵讀 —— 跑法:python3 arch_qube_report_keys_selftest.py

2026-09-07 拿一份**真的**報告(直接對 dashboard 跑 arcana.boo/arcana/arch-qube:latest 產生)對過:

    {"meta": {"files_scanned": 379, ...},
     "score": {"total": 100.0, "grade": "A+", "pass": true, "threshold": 95.0},
     "rules": [...], "summary": {...}}

而節點讀的是 `files` / `fileCount` 與把 `score` 當數字 —— 兩個都不存在於這個形狀。
結果:閘每一輪都在評 A+ 100 分、掃 379 個檔,而每一輪都被記成「scanned 0 files / notRun」。
PM 從來沒有看過架構分數,disposition 也因此永遠是 escalate。

C 組是重點:舊寫法對著同一份真實報告必須讀不到 —— 一個判準若不能對著壞版本變紅,它就不是判準。
"""
import importlib.util, os, sys
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); os.environ.setdefault("STUB", "")
spec = importlib.util.spec_from_file_location("atn_server", os.path.join(D, "server.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ok = fail = 0
def check(l, c):
    global ok, fail
    if c: ok += 1; print("  ✓", l)
    else: fail += 1; print("  ✗", l)

# 真實形狀(取自實跑產物,只留讀得到的欄位)
REAL = {"meta": {"tool": "arch-qube", "version": "0.1.0", "framework": "angular",
                 "source_root": "/src/src/app", "files_scanned": 379},
        "score": {"total": 100.0, "grade": "A+", "pass": True, "threshold": 95.0},
        "rules": [], "summary": {}}

print("\n════ A. 真實報告讀得到 ════")
check("檔案數 = meta.files_scanned(379)", m._aq_files(REAL) == 379)
check("分數 = score.total(100.0),是數字不是物件", m._aq_score(REAL) == 100.0 and isinstance(m._aq_score(REAL), float))

print("\n════ B. 舊形狀(平的)也要照認,免得換版本就瞎掉 ════")
check("平的 files/score 仍讀得到", m._aq_files({"files": 12}) == 12 and m._aq_score({"score": 88.5}) == 88.5)
check("overallScore 後備", m._aq_score({"overallScore": 91}) == 91.0)
check("summary.score 後備", m._aq_score({"summary": {"score": 77}}) == 77.0)

print("\n════ C. 對照組:舊寫法對同一份真實報告讀不到(這正是這次的缺陷) ════")
old_files = REAL.get("files", REAL.get("fileCount"))
check("舊寫法的 files → None(於是每輪都判 scanned 0 files)", old_files is None)
old_score = REAL.get("score", REAL.get("overallScore"))
check("舊寫法的 score → 物件(float() 會丟例外,落進 except 變另一種 notRun)", isinstance(old_score, dict))
try:
    float(old_score); crashed = False
except Exception:
    crashed = True
check("float(物件) 真的會炸", crashed)

print("\n════ D. 讀不到就說讀不到,不要當成 0 分 ════")
check("沒有分數 → None(呼叫端據此判 notRun,不是 gap)", m._aq_score({"meta": {"files_scanned": 5}}) is None)
check("不是 dict → None,不炸", m._aq_files("boom") is None and m._aq_score(None) is None)
check("score 是空物件 → None", m._aq_score({"score": {}}) is None)

src = open(os.path.join(D, "server.py"), encoding="utf-8").read()
aq = src[src.index("def _arch_qube("):]
check("掃了檔案卻沒分數時,verdict 是 notRun 且說得出鍵", "no score in the report" in aq and "notRun" in aq)
check("scanned 0 files 會附上報告實際有的鍵(下次形狀再變不必重挖)", "報告的鍵" in aq)

print("\n════ E. 覆蓋率報告的路徑要用產生它的工具決定,不是猜 ════")
import tempfile, json as _json
_wd = tempfile.mkdtemp(); os.makedirs(os.path.join(_wd, "dashboard"), exist_ok=True)
open(os.path.join(_wd, "dashboard", "angular.json"), "w").write(_json.dumps({"projects": {"arcana-angular": {}}}))
check("angular 專案名讀自 angular.json(實測就是 arcana-angular)", m._cov_project_dir(_wd, "angular") == "arcana-angular")
check("rust 沒有這層 → 空字串(呼叫端會跳過這個候選)", m._cov_project_dir(_wd, "rust") == "")
check("讀不到 angular.json → 空字串,不是猜一個名字", m._cov_project_dir(tempfile.mkdtemp(), "angular") == "")
_src = open(os.path.join(D, "server.py"), encoding="utf-8").read()
_cov = _src[_src.index("def _sonar_coverage("):]; _cov = _cov[:_cov.index("\ndef ", 10)]
check("先試頂層,再試 coverage/<專案名>/", '"/app/coverage/lcov.info"' in _cov and 'coverage/%s/lcov.info' in _cov)
check("兩個候選都沒有時,從容器裡真的去找", "_find_in_container" in _cov)
check("找不到時說出「找過哪些地方」(下一個人不必從 docker export 挖)", "找過:" in _cov)
check("不再寫死單一 inside 路徑", "inside = " not in _cov)
print("\n  總計 通過 %d,失敗 %d" % (ok, fail)); sys.exit(1 if fail else 0)
