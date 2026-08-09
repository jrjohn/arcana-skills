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
if bad == 0:
    print('  pass —— 四種該擋的都擋了,該放行的放行了,而品質線放寬不了')
else:
    print('  gap —— %d 格不符' % bad)
sys.exit(1 if bad else 0)
