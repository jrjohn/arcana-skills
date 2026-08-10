#!/usr/bin/env python3
"""preflight 的對照組 —— 不碰任何真 repo、不打 GitHub、不動真的註冊表。

    python3 preflight.selftest.py        # exit 0 = 該擋的擋了,該放行的放行了

為什麼需要這一支:`preflight()` 是「在燒掉任何 AI session 之前拒絕」的那一關,
而它從來沒有被證明過**真的會拒絕**。這一族的專案已經有好幾次「寫好了但沒接上」
(full-function-walk 沒折進 allPass、fold-gate 沒接進 run-test.sh、
scale-gate 沒接進 run-walks)—— 每一次讀起來都很正常,漏的那一行不在那裡,
而不在那裡的東西讀不出來。

做法:起一個假的註冊表(本機 HTTP),把 profile 預先塞進 payload 的快取,
然後逐一製造該被拒絕的情況。**E 那一格(一切正常必須放行)和其他格同等重要** ——
只會拒絕的閘和只會放行的閘一樣沒用。

離線的做法:`_load_profile` 會快取在 `payload["_profile"]`,先塞好它就不會去打 gh api;
profile 不宣告任何路徑,最後那段路徑存在性檢查也就不會觸發。
路徑檢查有它自己的題目,不是這一支的。
"""
import importlib.util
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
# 可覆寫,是為了能對**修改前**那一份跑一次 —— 一支只證明現狀的自檢,
# 沒有證明任何事。拿舊的 server.py 跑,品質線那四格必須紅。
SERVER_PY = os.environ.get('PREFLIGHT_SERVER_PY') or os.path.join(HERE, 'server.py')

PROJECTS = {"projects": []}          # 每個案例改這個


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):                                    # noqa: N802
        body = json.dumps(PROJECTS).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_a):                          # 安靜
        pass


httpd = HTTPServer(('127.0.0.1', 0), Handler)
PORT = httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start()

os.environ.setdefault('STUB', '1')
spec = importlib.util.spec_from_file_location('sdlc_server', SERVER_PY)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

REPO = 'acme/widget'
BRANCH = 'main'


def profile(**over):
    p = {'_ref': '.arcana/project.json', 'app': {}, 'nav': {}, 'flow': {}}
    p.update(over)
    return p


def run(registry_projects, *, registry_url=None, prof=None, repo=REPO, base=BRANCH):
    global PROJECTS
    PROJECTS = {'projects': registry_projects}
    os.environ['SDLC_REGISTRY_URL'] = (
        registry_url if registry_url is not None else 'http://127.0.0.1:%d/' % PORT)
    payload = {'repo': repo, 'base': base,
               '_profile': prof if prof is not None else profile()}
    return mod.preflight(payload), payload


ACTIVE = {'projectId': 'widget', 'repo': REPO, 'integrationBranch': BRANCH,
          'status': 'active', 'tier': 'company'}
ONBOARDING = dict(ACTIVE, status='onboarding')
WITH_FLOOR = dict(ACTIVE, qualityFloor={'coverage': 80, 'archQube': 90})

bad = 0


def case(name, fn, want_ok, want_in=''):
    global bad
    try:
        res, _payload = fn()
    except Exception as e:                                       # noqa: BLE001
        print('  ✗ %-24s 例外:%s' % (name, e))
        bad += 1
        return None
    ok = bool(res.get('ok'))
    reason = res.get('reason', '')
    good = ok == want_ok and (want_in in reason if want_in else True)
    print('  %s %-24s ok=%-5s %s' % ('✓' if good else '✗', name, ok, reason[:70]))
    if not good:
        bad += 1
    return res


print('  ── 該擋的有沒有擋 ──')
case('沒有登記', lambda: run([]), False, 'no registered')
case('登記了但非 active', lambda: run([ONBOARDING]), False, 'not ')
case('註冊表連不上', lambda: run([], registry_url='http://127.0.0.1:9/'), False, 'unreachable')
case('profile 身分不符',
     lambda: run([ACTIVE], prof=profile(**{'$repo': 'someone/else'})), False, 'profile claims')

print()
print('  ── 該放行的有沒有放行(和上面同等重要)──')
case('一切正常', lambda: run([ACTIVE]), True)

print()
print('  ── 品質線只能更嚴 ──')


def floor_case(name, declared, expect_coverage, expect_relaxed):
    global bad
    prof = profile(qualityBar=declared)
    res, _ = run([WITH_FLOOR], prof=prof)
    got = (prof.get('qualityBar') or {}).get('coverage')
    said = any('打回' in c for c in (res.get('checks') or []))
    good = res.get('ok') and got == expect_coverage and said == expect_relaxed
    print('  %s %-24s 宣告 %-22s → 生效 coverage=%-4s 記一筆=%s'
          % ('✓' if good else '✗', name, json.dumps(declared), got, said))
    if not good:
        bad += 1


floor_case('想放寬 → 打回', {'coverage': 10, 'archQube': 20}, 80, True)
floor_case('想更嚴 → 照做', {'coverage': 95}, 95, False)
floor_case('沒宣告 → 用下限', {}, 80, False)
floor_case('註冊表沒約束的維度', {'mutationScore': 60}, 80, False)

print()
print('  ── flow-sim 版本握手(S4)——過舊的 binary 會被擋下嗎 ──')


def handshake():
    """`--version` 握手的對照組。

    計畫要的是「binary 回報支援的 schema 版本,過舊即拒絕」。程式碼在那裡,
    而這幾格證明它**會拒絕** —— 含必須放行的那一格。

    binary 是 gitignored 產物、手動 COPY 進映像、沒有任何新鮮度檢查,
    所以這個數字是唯一能讓「映像裡那份太舊」變成一句話而不是一個錯結論的東西:
    舊 binary 拿到宣告 groups 的情境不會報錯,serde 的 default 把它填成 ["human"],
    平台流程的 ai / jenkins 關卡一個都看不到,然後回報「沒有人工關卡」。
    """
    global bad
    binary = os.environ.get('FLOW_SIM_BIN_FOR_TEST') or _find_flow_sim()
    if not binary:
        # notRun 與 notApplicable 的差別在於**由誰說**,而處置不同:
        #
        #   這個 repo 沒有 Rust、也不該有 flow-sim → notApplicable(可見,不擋)
        #   aaf 的 pipeline 建完卻找不到           → notRun(該跑卻沒跑成,要擋)
        #
        # 所以由呼叫端宣告:`FLOW_SIM_REQUIRED=1` 時,缺 binary 是 notRun 而且擋。
        # 一律不擋,會讓「這裡本來就沒有」與「說好要驗卻沒驗到」變成同一件事,
        # 而後者正是這一整輪在拆的那個病。
        if os.environ.get('FLOW_SIM_REQUIRED') == '1':
            global bad
            bad += 1
            print('  ✗ notRun —— 說好要驗握手卻找不到 flow-sim。'
                  '先跑 cargo build -p flow-sim --bin flow-sim。')
            return 2
        print('  notApplicable —— 這個環境沒有 flow-sim(可見,不擋)。'
              '握手在 aaf 的 pipeline 裡驗,那邊 binary 是建出來的。')
        return 3

    # 版本閘的上游要求「這次 PR 有動到流程」。那一步要讀 PR 的改動檔案(gh),
    # 與握手無關 —— stub 掉,讓每一格的結論只可能來自握手本身。
    mod._touched_flows = lambda payload: [{'slug': 'x', 'path': 'x.bpmn2'}]
    os.environ['SCENARIO_AUTOFILL'] = '1'

    def hs(name, min_schema, path, want_in):
        global bad
        os.environ['FLOW_SIM_MIN_SCHEMA'] = str(min_schema)
        os.environ['FLOW_SIM_BIN'] = path
        res = mod._scenario_autofill({'repo': 'x/y', 'base': 'main'})
        reason = res.get('reason', '')
        good = (not res.get('ran')) and (want_in in reason)
        print('  %s %-28s %s' % ('✓' if good else '✗', name, reason[:62]))
        if not good:
            bad += 1

    hs('要求 schema 3(比 binary 新)', 3, binary, 'stale binary')
    hs('binary 根本不存在', 2, '/nonexistent/flow-sim', 'not in agent image')
    # 必須放行的那一格:相符時,停下來的理由不可以是版本。
    hs('要求 schema 2(相符)', 2, binary, 'no repo/branch')
    return 0


def _find_flow_sim():
    # 測試接縫:`FLOW_SIM_NO_SEARCH=1` 讓搜尋一定落空。
    # 沒有它就問不出「說好要驗卻找不到 binary」那一格 —— 這台機器的 fallback
    # 路徑剛好找得到,於是那個前提根本不成立,而我差點把「測試設定錯」讀成
    # 「程式碼不會擋」。
    if os.environ.get('FLOW_SIM_NO_SEARCH') == '1':
        return ''
    for c in ('/usr/local/bin/flow-sim',
              os.path.expanduser('~/Documents/projects/aaf-designer-catalog/'
                                 'arcana-cloud-rust/target/debug/flow-sim')):
        if os.path.exists(c):
            return c
    return ''


_hs_rc = handshake()

print()
print('  ── 宣告的路徑必須存在(S6 的最後一角)──')
if os.environ.get('PREFLIGHT_NETWORK') == '1':
    # 這一格會真的打 gh api —— 路徑存在性只能問 GitHub,所以預設不跑。
    # 預設不跑**不是通過**:下面印的是 notApplicable,而它與 pass 分開計。
    _repo = os.environ.get('PREFLIGHT_NETWORK_REPO', 'jrjohn/arcana-ai-bpm')

    def path_case(name, appdir, want_ok, want_in=''):
        global bad
        prof = profile(app={'appDir': appdir})
        PROJECTS_LOCAL = [{'projectId': 'p', 'repo': _repo, 'integrationBranch': 'main',
                           'status': 'active', 'tier': 'company'}]
        res, _ = run(PROJECTS_LOCAL, prof=prof, repo=_repo)
        ok = bool(res.get('ok'))
        good = ok == want_ok and (want_in in res.get('reason', '') if want_in else True)
        print('  %s %-28s ok=%-5s %s' % ('✓' if good else '✗', name, ok,
                                         (res.get('reason') or 'ok')[:56]))
        if not good:
            bad += 1

    path_case('宣告一個不存在的目錄', 'no-such-dir-xyz', False, 'do not exist')
    path_case('宣告真的存在的目錄', 'dashboard', True)
else:
    print('  notApplicable —— 需要網路(gh api)。PREFLIGHT_NETWORK=1 才跑。')
    print('  這一格不跑不等於通過,只等於沒問。')

print()
if bad == 0:
    print('  pass —— 該擋的擋了,該放行的放行了,品質線放寬不了,過舊的 binary 進不來')
    if _hs_rc == 3:
        print('  (握手那一段是 notApplicable —— 這個環境沒有 flow-sim;'
              '要它成為硬閘就設 FLOW_SIM_REQUIRED=1)')
else:
    print('  gap —— %d 格不符' % bad)
sys.exit(1 if bad else 0)
