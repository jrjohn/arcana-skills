#!/usr/bin/env python3
"""排程開輪(loop-drive)—— 跑法:python3 loop_drive_selftest.py

aaf 的 sdlc-loop-driver-flow 每 6 小時叫一次 LoopDrive,worker 轉給這裡的 /task/loop-drive。
要不要真的開一輪由驅動器(aaf repo 的 scripts/sdlc-loop-driver.py)的四道上界決定;
這裡只負責「從 main 取那一份來跑、把結果說清楚」,不複製它的判準。

  A 組:結束碼 → 判定(0 開了/沒單/空跑、1 被擋、2 與其他 = 讀不到)
  B 組:取檔與執行(注入假的)—— 取不到或取到的不是驅動器就不跑;空跑不帶 --start;
        容器網址只補沒設的
  C 組:暫停檔存在 → 不取檔、不執行
  D 組:真的從 GitHub main 取驅動器,對本機服務空跑一次(連不到時明說沒跑,不算通過)

注意:arcana-skills 沒有 CI,這支不會自動跑。
"""
import importlib.util, os, subprocess, sys, tempfile, types

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
os.environ.setdefault("STUB", "")
spec = importlib.util.spec_from_file_location("atn_server", os.path.join(D, "server.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
print("  server.py import 成功(分派名單與分派鏈一致)")

ok = fail = 0
def check(label, cond):
    global ok, fail
    if cond: ok += 1; print("  ✓ %s" % label)
    else:    fail += 1; print("  ✗ %s" % label)

DRIVER = "# 四道上界\ndef run(do_start):\n    pass\n"
def proc(rc=0, out="", err=""):
    return types.SimpleNamespace(returncode=rc, stdout=out, stderr=err)

print("A 組 —— 結束碼 → 判定")
V = m._loop_drive_verdict
check("0 且有「已開:」→ started + id", V(0, "     ✓ 已開:46719701\n", True) == ("started", "46719701"))
check("0、--start、沒開 → idle(沒有單可開)", V(0, "→ 沒有可開的單", True) == ("idle", None))
check("0、空跑 → dry", V(0, "(空跑。要真的開請加 --start)", False) == ("dry", None))
check("1 → braked(上界擋下是它在工作)", V(1, "被上界擋下", True) == ("braked", None))
check("2 → notRun", V(2, "有東西讀不到", True) == ("notRun", None))
check("逾時(None)→ notRun,不是 idle", V(None, "", True) == ("notRun", None))

print("B 組 —— 取檔與執行")
calls = []
def runner(rc=0, out=""):
    def _run(argv, env):
        calls.append((argv, env)); return proc(rc, out)
    return _run

calls.clear()
r = m.loop_drive({}, fetch=lambda: proc(1, "", "HTTP 404"), run=runner())
check("取不到 → notRun,而且沒有執行", r["verdict"] == "notRun" and not calls)
calls.clear()
r = m.loop_drive({}, fetch=lambda: proc(0, '{"message":"Not Found"}'), run=runner())
check("取到的不是驅動器(404 JSON)→ notRun,不拿去執行", r["verdict"] == "notRun" and not calls)
calls.clear()
r = m.loop_drive({}, fetch=lambda: proc(0, DRIVER), run=runner(0, "  → 要開的單:#516 x\n     ✓ 已開:abcdef12\n"))
check("預設 → 帶 --start,判 started,認得單號與實例",
      calls and calls[0][0][-1] == "--start" and r["verdict"] == "started"
      and r["issue"] == 516 and r["instance"] == "abcdef12")
calls.clear()
r = m.loop_drive({"dryRun": "true"}, fetch=lambda: proc(0, DRIVER), run=runner(0, "  → 要開的單:#516 x\n(空跑"))
check("dryRun=true → 不帶 --start,判 dry", calls and "--start" not in calls[0][0] and r["verdict"] == "dry"
      and r["dryRun"] is True and r["started"] is False)
calls.clear()
os.environ["LOOP_ENGINE"] = "http://custom:1"
os.environ.pop("LOOP_DATA_INDEX", None)
m.loop_drive({}, fetch=lambda: proc(0, DRIVER), run=runner(1, "被上界擋下"))
env = calls[0][1]
check("已設的網址不動(LOOP_ENGINE=%s)" % env.get("LOOP_ENGINE"), env.get("LOOP_ENGINE") == "http://custom:1")
check("沒設的補成容器服務名(LOOP_DATA_INDEX=%s)" % env.get("LOOP_DATA_INDEX"),
      env.get("LOOP_DATA_INDEX") == "http://aaf-data-index:8080")
os.environ.pop("LOOP_ENGINE", None)
calls.clear()
def boom(argv, env):
    raise subprocess.TimeoutExpired(argv, 300)
r = m.loop_drive({}, fetch=lambda: proc(0, DRIVER), run=boom)
check("驅動器逾時 → notRun(暫存檔照樣清掉)", r["verdict"] == "notRun")

print("C 組 —— 暫停")
pause = tempfile.NamedTemporaryFile(delete=False); pause.close()
orig = m._LOOP_PAUSE_FILE
m._LOOP_PAUSE_FILE = pause.name
fetched = []
r = m.loop_drive({}, fetch=lambda: fetched.append(1) or proc(0, DRIVER), run=runner())
check("暫停檔存在 → paused,不取檔、不執行", r["verdict"] == "paused" and not fetched)
os.unlink(pause.name)
m._LOOP_PAUSE_FILE = orig

print("D 組 —— 真的從 main 取驅動器,對本機服務空跑")
for k, v in (("LOOP_READ_API", "http://localhost:8088"), ("LOOP_DATA_INDEX", "http://localhost:8180"),
             ("LOOP_ENGINE", "http://localhost:8081")):
    os.environ[k] = v
r = m.loop_drive({"dryRun": "true"})
print("     判定:%s,結束碼 %s" % (r["verdict"], r["exitCode"]))
for line in (r.get("report") or "").strip().splitlines()[-8:]:
    print("     | " + line)
if r["verdict"] == "notRun" and r["exitCode"] is None:
    print("  ? 取不到 main 上的驅動器(沒有 gh 或沒網路)—— D 組沒跑,不算通過")
    fail += 1
else:
    check("真的驅動器空跑:判 dry / braked(不是 started —— 空跑絕不能開輪)",
          r["verdict"] in ("dry", "braked", "notRun") and r["verdict"] != "started" and r["dryRun"])

print()
print("  %d 過 / %d 失敗" % (ok, fail))
sys.exit(1 if fail else 0)
