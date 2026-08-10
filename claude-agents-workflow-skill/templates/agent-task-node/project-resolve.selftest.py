#!/usr/bin/env python3
"""`_project_of` 的對照組 —— 「這次 run 屬於哪個專案」答得出來嗎,答不出來時會說嗎?

    python3 project-resolve.selftest.py

為什麼需要:稽核與成本要 roll up 的單位是**專案**。答錯的代價是這次 run 的數字
全部記到別的專案頭上,而且沒有人會發現 —— 這是一種安靜的錯,所以要用假註冊表
把每一種情況都製造出來看它怎麼答。

**最要緊的是模稜兩可那兩格。** 註冊表的自然鍵是 `(repo, integration_branch)`,
所以同一個 repo 的兩條整合分支是兩個專案;反查命中多筆時正確的答案是「不知道」,
不是挑第一個。挑第一個會過測試、會跑得很順、而且會一直錯下去。
"""
import importlib.util
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.environ.get('SDLC_SERVER_PY') or os.path.join(HERE, 'server.py')

PROJECTS = {"projects": []}


class H(BaseHTTPRequestHandler):
    def do_GET(self):                                       # noqa: N802
        b = json.dumps(PROJECTS).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, *_a):
        pass


httpd = HTTPServer(('127.0.0.1', 0), H)
PORT = httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start()

os.environ.setdefault('STUB', '1')
os.environ['SDLC_REGISTRY_URL'] = 'http://127.0.0.1:%d/' % PORT
spec = importlib.util.spec_from_file_location('s', SERVER)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

REPO = 'acme/widget'


def P(pid, branch='main', repo=REPO, name=None):
    return {'projectId': pid, 'repo': repo, 'integrationBranch': branch,
            'displayName': name or pid, 'status': 'active'}


bad = 0


def case(name, projects, payload, want_pid, want_how_has='', url=None):
    global bad, PROJECTS
    PROJECTS = {'projects': projects}
    os.environ['SDLC_REGISTRY_URL'] = url if url is not None else 'http://127.0.0.1:%d/' % PORT
    pid, pname, how = mod._project_of(payload)
    ok = (pid == want_pid) and (want_how_has in how if want_how_has else True)
    print('  %s %-30s → %-14s %s' % ('✓' if ok else '✗', name, pid or '(不知道)', how[:44]))
    if not ok:
        bad += 1


print('  ── 答得出來的 ──')
case('payload 明說', [P('w1')], {'projectId': 'w1', 'repo': REPO, 'base': 'main'},
     'w1', 'payload')
case('repo+branch 唯一命中', [P('w1')], {'repo': REPO, 'base': 'main'},
     'w1', 'repo+branch')
case('分支對不上但 repo 只有一個', [P('w1', 'release')], {'repo': REPO, 'base': 'main'},
     'w1', 'repo only')

print()
print('  ── 答不出來的:必須說「不知道」,不可以猜 ──')
case('同 repo 兩條產品線', [P('w1', 'main'), P('w2', 'release')],
     {'repo': REPO, 'base': 'nope'}, None, 'ambiguous')
case('同 repo 同分支兩筆(壞資料)', [P('w1'), P('w2')],
     {'repo': REPO, 'base': 'main'}, None, 'ambiguous')
case('根本沒登記', [P('other', 'main', 'someone/else')],
     {'repo': REPO, 'base': 'main'}, None, 'no registered')
case('沒有 repo 可查', [P('w1')], {'base': 'main'}, None, 'no repo')
case('註冊表打不通', [P('w1')], {'repo': REPO, 'base': 'main'},
     None, 'unreachable', url='http://127.0.0.1:9/')

print()
if bad == 0:
    print('  pass —— 答得出來的答得出來,答不出來的說「不知道」而不是猜一個')
else:
    print('  gap —— %d 格不符' % bad)
sys.exit(1 if bad else 0)
