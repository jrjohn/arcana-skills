#!/usr/bin/env python3
"""implement 自檢回歸閘的自驗 —— 跑法:python3 selftest_gate_selftest.py

重點是 B 組與 C 組,不是 A。

A 只證明「新 gap 會被抓到」,而那從來不是難的部分。難的是另外兩件:

  B. **環境自帶的 gap 不能誤擋。** 2026-08-26 實測:一行都沒改的 main 在 agent
     容器裡跑 run-selftests.sh 就是 rc=1(workspace-git.selftest.sh gap ——
     它在 Jenkins 是 notApplicable,在這裡卻跑得起來而且不成立)。照「有 gap 就擋」
     寫,每一輪 implement 都會被自己的環境擋死。

  C. **問不到 ≠ 沒有回歸。** 基準或事後量測失敗時,必須是 notRun,不能靜靜放行。
     這條流水線反覆出現的病就是把缺席讀成通過。

注意:arcana-skills 目前沒有 CI,所以這支不會自動跑。這是實話,不是設計。
"""
import importlib.util, os, sys, subprocess, tempfile

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
os.environ.setdefault("STUB", "")

spec = importlib.util.spec_from_file_location("atn_server", os.path.join(D, "server.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
print("  server.py import 成功")

ok = fail = 0
def check(label, cond):
    global ok, fail
    if cond: ok += 1; print("  ✓ %s" % label)
    else:    fail += 1; print("  ✗ %s" % label)


def fake_repo(runner_body):
    """造一個假 repo,scripts/run-selftests.sh 印出指定內容。"""
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "scripts"))
    p = os.path.join(d, "scripts", "run-selftests.sh")
    with open(p, "w", encoding="utf-8") as f:
        f.write(runner_body)
    os.chmod(p, 0o755)
    return d


# runner 的真實輸出格式(取自 2026-08-26 的實跑)
GREEN = """#!/usr/bin/env bash
echo "  ✓ ci-verdict.selftest.sh   pass"
echo "  pass 19 / gap 0 / notRun 0"
exit 0
"""
ENV_GAP = """#!/usr/bin/env bash
echo "  ✗ workspace-git.selftest.sh   gap —— 彙總漏了專案"
echo "  pass 18 / gap 1 / notRun 0"
echo "  gap —— workspace-git.selftest.sh"
exit 1
"""
ENV_GAP_PLUS_NEW = """#!/usr/bin/env bash
echo "  pass 17 / gap 2 / notRun 0"
echo "  gap —— workspace-git.selftest.sh"
echo "  gap —— list-provenance.control.py"
exit 1
"""
BROKEN_FORMAT = """#!/usr/bin/env bash
echo "something went very wrong"
exit 3
"""

print("\n════ A. 讀得出 runner 點名的是哪幾支 ════")
check("全綠 → 空集合", m._selftest_gaps(fake_repo(GREEN)) == set())
check("一個 gap → 讀得出檔名",
      m._selftest_gaps(fake_repo(ENV_GAP)) == {"workspace-git.selftest.sh"})
check("兩個 gap → 兩個都讀得出",
      m._selftest_gaps(fake_repo(ENV_GAP_PLUS_NEW)) ==
      {"workspace-git.selftest.sh", "list-provenance.control.py"})

print("\n════ B. 環境自帶的 gap 不得誤擋(這是設計的支點) ════")
base = m._selftest_gaps(fake_repo(ENV_GAP))
after_same = m._selftest_gaps(fake_repo(ENV_GAP))
check("基準有、事後也有 → 沒有新 gap(不擋)", (after_same - base) == set())

after_new = m._selftest_gaps(fake_repo(ENV_GAP_PLUS_NEW))
new = after_new - base
check("多了一支 → 只點名新的那一支(這就是 PR #281 的情況)",
      new == {"list-provenance.control.py"})
check("不把環境自帶的那支算進來", "workspace-git.selftest.sh" not in new)

base_green = m._selftest_gaps(fake_repo(GREEN))
check("基準全綠、事後冒出 gap → 抓得到",
      (m._selftest_gaps(fake_repo(ENV_GAP)) - base_green) == {"workspace-git.selftest.sh"})

print("\n════ C. 問不到 ≠ 沒有回歸 ════")
check("沒有那支腳本 → None,不是空集合", m._selftest_gaps(tempfile.mkdtemp()) is None)
check("輸出格式不認得且 rc!=0 → None,不是空集合",
      m._selftest_gaps(fake_repo(BROKEN_FORMAT)) is None)
check("None 與 set() 是不同的東西(呼叫端必須分開處理)",
      m._selftest_gaps(tempfile.mkdtemp()) is not set())

print("\n════ D. 修好了也要看得出來 ════")
fixed = base - m._selftest_gaps(fake_repo(GREEN))
check("基準有、事後沒有 → 算「順帶修好」而不是新 gap",
      fixed == {"workspace-git.selftest.sh"} and
      (m._selftest_gaps(fake_repo(GREEN)) - base) == set())

print("\n" + "═" * 46)
print("  通過 %d,失敗 %d" % (ok, fail))
sys.exit(1 if fail else 0)
