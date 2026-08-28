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

print("\n════ E. 這支模組裡沒有叫不出來的名字 ════")
# 為什麼要有這一組:2026-08-28 的事故是 `log(...)` —— 一個**全檔都沒有定義**的名字。
# A~D 四組把 `_selftest_gaps` 測得很仔細,卻一次都沒有執行到「呼叫它的那一行」。
# 純函式測得再好,也證明不了 caller 跑不跑得起來。
#
# 判準要能分辨「函式內部自己定義的區域名」與「真的不存在」——
# 第一版沒分,於是 `_git` / `_build_gate` 這些巢狀 def 全被誤報成缺失(15 個)。
# 一個天天喊狼的檢查,下一個人會直接把它關掉。
import ast as _ast, builtins as _bi
_src = open(os.path.join(D, "server.py"), encoding="utf-8").read()
_tree = _ast.parse(_src)
_global = set(dir(_bi)) | set(vars(m).keys())

def _names_bound_in(fn):
    """這個函式(含巢狀)自己綁定的名字:參數、賦值、巢狀 def/class、import、for、with、except。"""
    out = set(a.arg for a in list(fn.args.args) + list(fn.args.kwonlyargs) + list(fn.args.posonlyargs))
    if fn.args.vararg: out.add(fn.args.vararg.arg)
    if fn.args.kwarg: out.add(fn.args.kwarg.arg)
    for n in _ast.walk(fn):
        if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef)):
            out.add(n.name)
            if n is not fn:
                out |= set(a.arg for a in n.args.args)
        elif isinstance(n, _ast.Name) and isinstance(n.ctx, _ast.Store):
            out.add(n.id)
        elif isinstance(n, (_ast.Import, _ast.ImportFrom)):
            out |= {(a.asname or a.name).split(".")[0] for a in n.names}
        elif isinstance(n, _ast.ExceptHandler) and n.name:
            out.add(n.name)
    return out

# 只看「同一個函式內」還不夠:巢狀函式看得到**外層**的名字(閉包)。
# 第二版因此把 `_git` / `_changed_subapps` 誤報成缺失 —— 它們定義在外層、
# 被內層的 `_build_gate` 用到。所以要沿著巢狀鏈把每一層的綁定都收進來。
_missing = {}
def _scan(fn, inherited):
    scope = inherited | _names_bound_in(fn)
    for n in _ast.iter_child_nodes(fn):
        _walk_calls(n, scope)
def _walk_calls(node, scope):
    if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
        _scan(node, scope)
        return
    if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name):
        k = node.func.id
        if k not in _global and k not in scope:
            _missing.setdefault(k, node.lineno)
    for c in _ast.iter_child_nodes(node):
        _walk_calls(c, scope)
for _fn in [x for x in _ast.iter_child_nodes(_tree)
            if isinstance(x, (_ast.FunctionDef, _ast.AsyncFunctionDef))]:
    _scan(_fn, set())
check("沒有呼叫不存在的名字(%s)" % (", ".join("%s:%d" % (k, v) for k, v in sorted(_missing.items())) or "無"),
      not _missing)

print("\n" + "═" * 46)
print("  通過 %d,失敗 %d" % (ok, fail))
sys.exit(1 if fail else 0)
