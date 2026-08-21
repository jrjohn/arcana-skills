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

# ── 「問不到」與「答案是沒有」要分得開 ────────────────────────────────────────
#
# 2026-08-20:容器裡的 GH_TOKEN 過期,每一發 `gh api` 回 401、退出碼 1。preflight
# 原本只看退出碼,於是把它讀成「declared path(s) do not exist at main」——
# 一輪 sdlc-code-flow 的 SA / SD / uiux / implement 四個節點全部空轉,而唯一的線索
# 指向產品的樹不對,實際上是這個節點的憑證壞了。兩者要做的事完全不同。
#
# 兩種都要擋(缺席不等於通過),但說出來的必須是真的那一種。

class _GhResult:
    def __init__(self, rc, stderr=''):
        self.returncode, self.stderr, self.stdout = rc, stderr, ''


def with_gh(rc, stderr=''):
    """把 preflight 會呼叫的 `gh` 換成假的,其餘 subprocess 照舊。"""
    real = mod.subprocess.run

    def fake(cmd, *a, **k):
        if isinstance(cmd, (list, tuple)) and cmd and cmd[0] == 'gh':
            return _GhResult(rc, stderr)
        return real(cmd, *a, **k)
    return fake


WITH_PATH = profile(app={'appDir': 'dashboard'})


def gh_case(name, rc, stderr, want_ok, want_in):
    real = mod.subprocess.run
    mod.subprocess.run = with_gh(rc, stderr)
    try:
        case(name, lambda: run([ACTIVE], prof=WITH_PATH), want_ok, want_in)
    finally:
        mod.subprocess.run = real


print()
print('  ── 問不到 vs 答案是沒有 ──')
gh_case('gh 回 404 → 真的不存在', 1, 'gh: Not Found (HTTP 404)', False, 'do not exist')
gh_case('gh 回 401 → 是問不到', 1, 'gh: Bad credentials (HTTP 401)', False, '無法確認')
gh_case('gh 回 403 → 是問不到', 1, 'gh: Forbidden (HTTP 403)', False, '無法確認')
gh_case('gh 炸了沒有 HTTP 碼', 1, 'fork/exec: no such file', False, '無法確認')
gh_case('gh 回 0 → 路徑在,放行', 0, '', True, '')

# ── 映像裡的東西,是不是 repo 裡的那一份 ─────────────────────────────────────
#
# 2026-08-20:aaf-test-runner 停在 8/11,烤進去的 run-test.sh 少了
# `${JOURNEYS_B64:-}` 防護,`set -u` 下直接崩。Test 連跑兩輪都回
# 「runner emitted no TESTREPORT」—— 那句話對真因隻字不提。
#
# 這個檢查的第一版比**時間**(映像 .Created vs 該路徑最後一次 commit),
# 2026-08-21 兩種日常情況就把它打壞了:
#   (a) squash-merge 改寫 committer date —— 內容沒動,映像瞬間「變舊」
#   (b) 快取命中的重建不更新 .Created —— 照著訊息重建了,紅字還在
# 而第二次不只是雜訊:它擋下 SA / SD / implement 三個節點,把它們變成同一句
# 錯誤字串,流程照樣走到 Test —— 一個「到 Test 了」的假象,底下什麼都沒做。
#
# 判準因此改成比**內容**(git blob sha,兩邊都是 sha1("blob <len>\0"+content))。
# 這一族要同時擋三個方向:
#   · 內容不同 → 必須擋(而且要說出是哪幾個檔)
#   · 內容相同但時間不同 → **必須放行**(舊判準在這一格是紅的,那就是本次的 bug)
#   · 環境差異(沒有 docker / 讀不到 repo)→ 不擋,也不說它通過

class _R2:
    def __init__(self, rc=0, out='', err=''):
        self.returncode, self.stdout, self.stderr = rc, out, err


SAME = {'run-test.sh': 'a' * 40, 'uiux-checks.mjs': 'b' * 40}


def _fmt(d):
    return ''.join('%s %s\n' % (sha, p) for p, sha in sorted(d.items()))


def with_env(*, image=SAME, repo_tree=SAME, docker_ok=True, gh_ok=True):
    """假造 preflight 會呼叫的兩種外部指令。

    image     —— 映像裡的 {路徑: blob sha}(docker run git hash-object 的輸出)
    repo_tree —— repo 上的 {路徑: blob sha}(gh api git/trees 的輸出)
    docker_ok / gh_ok —— 模擬沒有 docker socket / 讀不到 repo
    """
    real = mod.subprocess.run

    def fake(cmd, *a, **k):
        if isinstance(cmd, (list, tuple)) and cmd:
            if cmd[0] == 'docker':
                if not docker_ok:
                    return _R2(rc=1, out='')
                return _R2(rc=0, out=_fmt(image))
            if cmd[0] == 'gh':
                joined = ' '.join(cmd)
                if 'git/trees/' in joined:
                    if not gh_ok:
                        return _R2(rc=1, out='')
                    return _R2(rc=0, out=_fmt(repo_tree))
                return _R2(rc=0, out='{}')
        return real(cmd, *a, **k)
    return fake


IMG_PROF = profile(app={'appDir': 'dashboard'})


def img_case(name, want_ok, want_in, **kw):
    real = mod.subprocess.run
    mod.subprocess.run = with_env(**kw)
    try:
        case(name, lambda: run([ACTIVE], prof=IMG_PROF), want_ok, want_in)
    finally:
        mod.subprocess.run = real


print()
print('  ── 映像裡的東西,是不是 repo 裡的那一份 ──')

# 逐檔相同 → 放行。**這一格就是 2026-08-21 的假紅**:內容一致、時間不一致,
# 舊判準在這裡是紅的,而它擋掉了三個節點。
img_case('逐檔相同 → 放行', True, '')

# 某支腳本內容不同 → 擋,而且要點名是哪一支(「舊」講不出來的那件事)
img_case('有一支內容不同 → 擋並點名', False, 'run-test.sh',
         image={'run-test.sh': 'c' * 40, 'uiux-checks.mjs': 'b' * 40})

# repo 有、映像沒有(新增的閘沒進映像)→ 擋。這正是 2026-08-20 lint-attribution 那一案。
img_case('repo 新增的閘不在映像裡 → 擋', False, 'lint-attribution.mjs',
         image=SAME,
         repo_tree=dict(SAME, **{'lint-attribution.mjs': 'd' * 40}))

# 映像多出來的檔(npm init 產的 package.json)不算差異 —— 只比 repo 有的那些
img_case('映像多出來的檔不算差異 → 放行', True, '',
         image=dict(SAME, **{'package.json': 'e' * 40, 'package-lock.json': 'f' * 40}))

# 沒有 docker socket → **不擋**(環境差異不是缺陷),但也不說它通過
img_case('沒有 docker → 不擋', True, '', docker_ok=False)

# 讀不到 repo 那一側 → 同上,不擋不通過
img_case('讀不到 repo 樹 → 不擋', True, '', gh_ok=False)

print()
if bad == 0:
    print('  pass —— 該擋的擋了、該放行的放行了、「問不到」不會被說成「不存在」,而內容不同擋得住、內容相同不誤擋、環境差異不誤擋')
else:
    print('  gap —— %d 格不符' % bad)
sys.exit(1 if bad else 0)
