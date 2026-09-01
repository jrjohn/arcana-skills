#!/usr/bin/env python3
"""流程變數一律走 `_pv` 的自驗 —— 跑法:python3 pv_discipline_selftest.py

## 為什麼需要一支「整類」的檢查

2026-08-28 這一天,同一個坑踩了**三次**:

    _intake_form_section  兩處  → 使用者的填答讀不到,同樣的問題被問了第二次
    write_specs           一處  → docs/specs/ 永遠是空的,歷史規格全部遺失
    _gen_testcases 等     三處  → 讀不到 SRS,測試案例是憑空猜的

每一次的修法都對,但每一次都只修了「當時被抓到的那幾行」。第三次之後可以確定:
逐行修不會收斂 —— 因為這不是三個 bug,是一個**紀律**沒有被機械化檢查。

`_pv` 的 docstring 早就寫清楚差異:`do_implement` 把變數放頂層,而 `do_execute`
(驅動 SA / SD / uiux / IntakeReview)把每一個實例變數塞在 `data` 底下。
讀錯地方**不會報錯**,只會安靜地拿到 None —— 然後被 `or ""` / `if not x: continue`
吸收掉,失敗因此完全看不見。

所以這支不驗「某一行對不對」,而是驗**整個模組有沒有繞過 `_pv` 讀流程變數**。

注意:arcana-skills 目前沒有 CI,所以這支不會自動跑。這是實話,不是設計。
"""
import ast, os, re, sys

D = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(D, "server.py")

ok = fail = 0
def check(label, cond):
    global ok, fail
    if cond: ok += 1; print("  ✓ %s" % label)
    else:    fail += 1; print("  ✗ %s" % label)

# 這些鍵是**流程實例變數** —— 它們可能在頂層,也可能在 `data` 底下,取決於
# dispatcher 用哪個 verb。清單刻意保守:只列真的會由流程帶進來的。
FLOW_KEYS = {
    "srs", "sdd", "uiuxSpec", "intakeForm", "intakeRound", "design",
    "feature_request", "target_users", "placement", "acceptance",
    "out_of_scope", "pm_answers", "pm_questions", "pm_assumptions",
    "slug", "repo", "base", "projectId", "testReport", "pmReview",
}

src = open(SRC, encoding="utf-8").read()
tree = ast.parse(src)


def offenders():
    """`<payload-ish>.get("<流程變數>")` 的呼叫位置。

    只看 `.get(...)`,不看下標 —— 下標拿不到會 KeyError(**會叫**),
    而 `.get` 拿不到回 None(**不會叫**)。這支要抓的正是不會叫的那一種。
    """
    out = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "get" and n.args):
            continue
        recv = n.func.value
        if not (isinstance(recv, ast.Name) and recv.id in ("payload", "p")):
            continue
        # `p` 是迴圈或推導式綁出來的 → 它是**被迭代出來的一列**(例如註冊表回應的
        # `body["projects"]`),不是流程 payload。同名不同物。
        #
        # 這一條原本是用「整個函式豁免」處理的,而對照組證明那是萬用擋箭牌:
        # 在被豁免的函式裡塞一行真的 `payload.get("srs")`,閘照樣綠。
        # 豁免擋掉的是雜訊,同時也擋掉了訊號 —— 所以改成看**這個名字怎麼來的**。
        if recv.id == "p" and _is_iteration_bound(n.lineno):
            continue
        a0 = n.args[0]
        if isinstance(a0, ast.Constant) and a0.value in FLOW_KEYS:
            out.append((a0.value, n.lineno))
        # **變數當鍵也要抓。** 對照組實測:把 write_specs 改回 `payload.get(key)` 時,
        # 只看字串常數的判準回報「0 處」—— 整類檢查對真正發生過的那個 bug 是瞎的,
        # 而它看起來完全正常(C 組的具名案例才紅)。
        # 迴圈變數是最典型的寫法(`for name, key in (...)`),不能漏。
        elif isinstance(a0, ast.Name):
            out.append(("<變數:%s>" % a0.id, n.lineno))
    # `do_implement` 這條路的變數**本來就在頂層**,那裡用 payload.get 是對的。
    # 不排除它,這支就會天天喊狼 —— 而喊狼的檢查會被下一個人關掉。
    #
    # 判準用「這一行落在哪個 top-level 函式裡」,不是用行號區間:函式會搬家,
    # 行號會漂,而搬家之後漂掉的判準看起來仍然正常。
    allow = _funcs_allowed_top_level()
    return [(k, l) for k, l in out if _func_at(l) not in allow]


def _is_iteration_bound(lineno):
    """這一行所在的 for / 推導式,是不是用 `p` 當迭代變數。"""
    for n in ast.walk(tree):
        binds = None
        if isinstance(n, (ast.For, ast.AsyncFor)):
            binds = [n.target]
            span = (n.lineno, max(getattr(x, "end_lineno", n.lineno) or n.lineno
                                  for x in (n.body or [n])))
        elif isinstance(n, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            binds = [g.target for g in n.generators]
            span = (n.lineno, getattr(n, "end_lineno", n.lineno) or n.lineno)
        if not binds:
            continue
        if not (span[0] <= lineno <= span[1]):
            continue
        for t in binds:
            for nm in ast.walk(t):
                if isinstance(nm, ast.Name) and nm.id == "p":
                    return True
    return False


def _func_at(lineno):
    """這一行屬於哪個 top-level 函式。"""
    best = None
    for n in ast.iter_child_nodes(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.lineno <= lineno:
            if best is None or n.lineno > best.lineno:
                best = n
    return best.name if best else None


def _funcs_allowed_top_level():
    """由 `do_implement` 驅動、變數確實在頂層的函式。

    這份名單是**豁免**,每一個都要說得出為什麼 —— 沒有理由的豁免等於把檢查關掉。
    """
    return {
        # implement 這條路:dispatcher 明確把 repo/base/slug 放頂層(見 _pv docstring)
        "implement_flow",
        "coverage_flow",
        "_arch_qube",      # 只讀 _piid / slug 當工作目錄名,拿不到會退回 "adhoc"
        "_sonar",
        "run_release",
        "publish_flow",
        # 以下三個讀的不是流程變數,或有等價的 fallback —— 逐一說明,
        # 因為沒有理由的豁免等於把檢查關掉:
        "prompt_readmesync",   # readmesync 是獨立 verb(PROMPTS 裡),payload 自己就是頂層
        "_registry_project",   # `p` 是**註冊表的一列**,不是流程 payload —— 同名不同物
        "site_flow",           # 讀 `path`(HTTP 路徑),不是流程變數;且它是獨立 verb
        "uiux_audit_flow",     # repo 讀不到時退回 UIUX_AUDIT_REPO 環境變數,不會靜默變空
        "test_flow",           # 只剩 _piid/slug 當工作目錄名,拿不到退回 "adhoc"
        "_pv",                 # `_pv` 自己就是那個包裝 —— 它當然要用 payload.get
    }


print("\n════ A. 沒有人繞過 _pv 讀流程變數 ════")
bad = offenders()
check("payload.get(<流程變數>) 應為 0 處(%s)"
      % (", ".join("%s:%d" % (k, l) for k, l in sorted(bad, key=lambda z: z[1])) or "無"),
      not bad)

print("\n════ B. _pv 本身還在,而且真的兩邊都找 ════")
# 沒有這一組,A 組可以靠「把 _pv 刪掉、全部改回 payload.get」來作弊 —— 那時 A 仍然綠。
import importlib.util
os.environ.setdefault("STUB", "")
spec = importlib.util.spec_from_file_location("atn_server", SRC)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
check("_pv 存在", hasattr(m, "_pv"))
check("值在頂層時讀得到", m._pv({"srs": "TOP"}, "srs") == "TOP")
check("值在 data 底下時讀得到", m._pv({"data": {"srs": "NESTED"}}, "srs") == "NESTED")
check("頂層優先於 data", m._pv({"srs": "TOP", "data": {"srs": "NESTED"}}, "srs") == "TOP")
check("兩邊都沒有時回 default", m._pv({}, "srs", "DEF") == "DEF")
check("空字串視同沒有(才會往 data 找)", m._pv({"srs": "", "data": {"srs": "N"}}, "srs") == "N")

print("\n════ C. 這一天踩過的三處,逐一釘住 ════")
# 具名案例。A 組是整類,C 組是「這幾個真的發生過」—— 兩者都要,
# 因為整類檢查若哪天被放寬,具名案例會先紅。
named = [
    ("write_specs 讀 srs/sdd/uiuxSpec", "def write_specs", ['_pv(payload, key']),
    ("_acceptance_brief 讀 srs", "def _acceptance_brief", ['_pv(payload, "srs"']),
    ("_gen_testcases 讀 srs", "def _gen_testcases", ['_pv(payload, "srs"']),
]
for label, marker, needles in named:
    i = src.find(marker)
    seg = src[i:i + 2500] if i >= 0 else ""
    check(label, i >= 0 and all(x in seg for x in needles))

print("\n════ D. 第三種擺法:worker 把規格包進 design ════")
# 為什麼有這一組:C 組全綠、A 組全綠,而 docs/specs/ 依然是空的(實例 c2a019d0)。
# 「都改成 _pv 了」不等於「讀得到」—— worker 的 do_implement 把 srs/sdd/uiuxSpec
# 放進 build_implement_design() 組出的 `design` 物件,那是頂層與 data 之外的第三個位置。
check("design 底下讀得到", m._pv({"design": {"srs": "IN-DESIGN"}}, "srs") == "IN-DESIGN")
check("頂層優先於 design", m._pv({"srs": "T", "design": {"srs": "D"}}, "srs") == "T")
check("data 優先於 design", m._pv({"data": {"srs": "N"}, "design": {"srs": "D"}}, "srs") == "N")
check("design 不是 dict 時不炸", m._pv({"design": "字串"}, "srs", "DEF") == "DEF")
check("三處皆無仍回 default", m._pv({"design": {}}, "srs", "DEF") == "DEF")

# 端到端:用 worker 真正送出的 payload 形狀跑 write_specs。
# 這一組才是驗收 —— 前面那些證明 _pv 會找,這一組證明規格真的落地。
import tempfile
worker_shaped = {
    "repo": "jrjohn/arcana-ai-bpm", "base": "main", "slug": "specs-land-in-repo",
    "prompt": "...",
    "design": {"srs": {"problem": "P"}, "sdd": {"files": ["a"]}, "uiuxSpec": None},
}
got = m.write_specs(tempfile.mkdtemp(), "specs-land-in-repo", worker_shaped)
check("worker 形狀 → SRS.md 與 SDD.md 都寫出來(%s)" % (got or "無"),
      any(x.endswith("SRS.md") for x in got) and any(x.endswith("SDD.md") for x in got))
check("uiuxSpec 是 None 時不寫空的 UIUX.md",
      not any(x.endswith("UIUX.md") for x in got))

print("\n" + "═" * 46)
print("  通過 %d,失敗 %d" % (ok, fail))
sys.exit(1 if fail else 0)
