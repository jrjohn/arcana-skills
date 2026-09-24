#!/usr/bin/env python3
"""失控告警(2026-09-14 事故)—— 跑法:python3 runaway_guard_selftest.py

只驗「該寄的寄一次、不該寄的不寄、壞結果不會弄壞任務回應」。不打網路:_send_email 換成記錄器。
"""
import importlib.util, os, sys, time
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); os.environ.setdefault("STUB", "")
spec = importlib.util.spec_from_file_location("atn_server", os.path.join(D, "server.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ok = fail = 0
def check(l, c):
    global ok, fail
    if c: ok += 1; print("  ✓", l)
    else: fail += 1; print("  ✗", l)

SENT = []
m._send_email = lambda subject, text: SENT.append(subject) or True
class _SyncThread:  # run the email "thread" inline so the assertions see it
    def __init__(self, target, args=(), daemon=None): self.t, self.a = target, args
    def start(self): self.t(*self.a)
m._gthreading.Thread = _SyncThread
def reset():
    SENT.clear(); m._burn.clear(); m._last_alert.clear()

print("\n════ 用量告警:看持續的量,不是單一任務 ════")
reset()
for _ in range(20):
    m._account("fix", {}, {"_usage": {"output": 15_000}})       # 300K,正常忙碌的一小時
check("正常量(300K)不寄信", SENT == [])
for _ in range(40):
    m._account("fix", {}, {"_usage": {"output": 15_000}})       # 累積到 900K
check("超過門檻只寄一封(冷卻中不重寄)", len(SENT) == 1 and "用量過高" in SENT[0])
reset()
m._burn.append((time.time() - m.BURN_WINDOW_S - 60, 10_000_000))
m._account("fix", {}, {"_usage": {"output": 1_000}})
check("視窗外的舊用量不算", SENT == [])

print("\n════ 修復放棄:同一個 job 只通知一次 ════")
reset()
m._account("escalate", {"job": "a/main", "attempts": 3}, {"resolution": "retry"})
check("resolution=retry 不寄(還會再試)", SENT == [])
m._account("escalate", {"job": "a/main", "attempts": 3}, {"resolution": "recorded", "reason": "x"})
m._account("escalate", {"job": "a/main", "attempts": 3}, {"resolution": "recorded", "reason": "x"})
check("recorded 寄一封,重複不再寄", len(SENT) == 1 and "a/main" in SENT[0])
m._account("escalate", {"job": "b/main"}, {"resolution": "closed"})
check("另一個 job 的 closed 另寄一封", len(SENT) == 2 and "b/main" in SENT[1])

print("\n════ 壞結果不能弄壞任務 ════")
reset()
try:
    m._account("fix", {}, None); m._account("fix", {}, {"_usage": None}); m._account("escalate", {}, {})
    check("None / 缺 _usage / 空結果都不丟例外", True)
except Exception as e:
    check(f"None / 缺 _usage / 空結果都不丟例外 ({e})", False)
src = open(os.path.join(D, "server.py"), encoding="utf-8").read()
check("do_POST 真的有呼叫 _account(不是建好沒人叫)", "_account(task, payload, result)" in src)

print(f"\n{ok} passed, {fail} failed")
sys.exit(1 if fail else 0)
