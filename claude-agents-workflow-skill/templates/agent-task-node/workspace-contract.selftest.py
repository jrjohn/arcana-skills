#!/usr/bin/env python3
"""工作區佈局契約 —— 兩份實作,一套佈局,而且**彼此讀得懂對方**。

    WS_SHELL=/path/to/arcana-ai-bpm/scripts/workspace-git.sh \\
      python3 workspace-contract.selftest.py

為什麼會有兩份實作:管線走 `server.py`(Python,在 run 之中),維運走
`workspace-git.sh`(CLI,在 run 之外)。跨 repo 呼叫對方會把「管線能不能起工作區」
綁在另一個 repo 的 checkout 上 —— 那比重複更糟。

**但重複會漂移。** 所以這一支同時對兩份跑,而且判準不是「結構長得一樣」——
結構長得一樣可以兩邊一起錯。判準是**互相讀得懂對方產生的東西**:

    shell 建的工作區,Python 那邊的 `stat` 要數得到、`diff` 要看得懂
    Python 建的工作區,shell 的 `stat` / `diff` 也要

一邊改了佈局而另一邊沒跟上,這一支就紅。這是「接受兩份實作」唯一負擔得起的方式。
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.environ.get('SDLC_SERVER_PY') or os.path.join(HERE, 'server.py')
SHELL = os.environ.get('WS_SHELL') or os.path.expanduser(
    '~/Documents/projects/aaf-designer-catalog/scripts/workspace-git.sh')

if not os.path.exists(SHELL):
    # **不是通過。** 少一份實作就等於這個契約只被驗了一半,而一半的契約
    # 正是「兩邊悄悄分家」開始的地方。
    print('  notRun —— 找不到 shell 那一份實作(%s)。' % SHELL)
    print('  用 WS_SHELL 指定 arcana-ai-bpm 的 scripts/workspace-git.sh。')
    sys.exit(2)

PROJECTS = {'projects': []}


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
REG = 'http://127.0.0.1:%d/' % PORT

# 用一個真的、很小的 repo:第二個產品。契約測的是佈局,不是內容。
REPO = 'jrjohn/sdlc-second-product'
PID = 'second-product'
PROJECTS = {'projects': [{'projectId': PID, 'repo': REPO, 'integrationBranch': 'main',
                          'displayName': 'S7 第二個產品', 'status': 'active'}]}

ROOT = tempfile.mkdtemp()
os.environ.update({'STUB': '1', 'SDLC_REGISTRY_URL': REG, 'AGENT_WORK': ROOT,
                   'WORKSPACE_GIT': '1', 'WORK_ROOT': ROOT})

spec = importlib.util.spec_from_file_location('s', SERVER)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.WORK_ROOT = ROOT
if hasattr(mod, '_instance_root'):
    mod._instance_root = lambda piid: os.path.join(ROOT, piid) if piid else None

bad = 0


def say(ok, name, detail=''):
    global bad
    print('  %s %-38s %s' % ('✓' if ok else '✗', name, detail[:44]))
    if not ok:
        bad += 1


def sh(*args):
    return subprocess.run(['bash', SHELL, *args], capture_output=True, text=True,
                          env=dict(os.environ), timeout=1800)


print('  ── 兩份實作各建一個工作區 ──')
r = sh('new', 'by-shell', PID)
say(r.returncode == 0, 'shell 建 by-shell', (r.stdout + r.stderr).strip()[:44])

root_py = os.path.join(ROOT, 'by-python')
ok_py = mod._ensure_instance_workspace({'_piid': 'by-python', 'repo': REPO, 'base': 'main',
                                        'projectId': PID, 'slug': 'x'})
say(bool(ok_py), 'python 建 by-python', str(ok_py or '')[-40:])

print()
print('  ── 契約:同一套佈局 ──')
L = mod.WORKSPACE_LAYOUT
pool = os.path.join(ROOT, L['pool'].format(projectId=PID))
say(os.path.isdir(pool), '一個專案一份物件庫(照代號)', os.path.basename(pool))
say(os.path.exists(os.path.join(pool, 'project.json')), '物件庫自帶 project.json')
for inst in ('by-shell', 'by-python'):
    wt = os.path.join(ROOT, L['worktree'].format(instance=inst))
    br = subprocess.run(['git', '-C', wt, 'rev-parse', '--abbrev-ref', 'HEAD'],
                        capture_output=True, text=True).stdout.strip()
    say(br == L['branch'].format(instance=inst), '%s 的分支' % inst, br)
    mp = os.path.join(ROOT, L['meta'].format(instance=inst))
    try:
        m = json.load(open(mp))
        miss = [k for k in L['metaKeys'] if k not in m]
    except Exception as e:                                   # noqa: BLE001
        m, miss = {}, ['(讀不到:%s)' % e]
    say(not miss, '%s 的 metadata 欄位齊全' % inst, ','.join(miss) or 'projectId=%s' % m.get('projectId'))

print()
print('  ── 契約的重點:彼此讀得懂對方 ──')
# shell 的 stat 必須數得到 python 建的那一個,反之亦然。
out = sh('stat', PID).stdout
say('by-python' not in out and PID in out and ' 2 ' in out.replace('\t', ' '),
    'shell 的 stat 數得到兩個(含 python 建的)', out.strip().splitlines()[-1][:44] if out.strip() else '(空)')

# python 這邊在 shell 建的工作區上 commit,再讓 shell 的 diff 讀出來
open(os.path.join(ROOT, 'by-shell', 'repo', 'FROM-PY.txt'), 'w').write('py wrote this\n')
h = mod._git_commit_node({'_piid': 'by-shell'}, 'sa', 'python 在 shell 的工作區上寫')
say(bool(h), 'python 在 shell 建的工作區上 commit', str(h))
d = sh('diff', 'by-shell', 'sa').stdout
say('FROM-PY.txt' in d, 'shell 的 diff 讀得懂那個 commit', d.strip().splitlines()[-1][:44] if d.strip() else '(空)')

# 反向:shell commit,python 讀
open(os.path.join(ROOT, 'by-python', 'repo', 'FROM-SH.txt'), 'w').write('shell wrote this\n')
r = sh('commit', 'by-python', 'sd', 'shell 在 python 的工作區上寫')
say(r.returncode == 0 and 'by-python/sd' in r.stdout, 'shell 在 python 建的工作區上 commit',
    r.stdout.strip()[:44])
wt = os.path.join(ROOT, 'by-python', 'repo')
log = subprocess.run(['git', '-C', wt, 'log', '-1', '--format=%s'],
                     capture_output=True, text=True).stdout.strip()
say(log.startswith(L['commitPrefix'].format(node='sd')),
    'commit 訊息符合契約前綴', log[:44])

print()
if bad == 0:
    print('  pass —— 兩份實作同一套佈局,而且互相讀得懂對方產生的東西')
else:
    print('  gap —— %d 格不符:兩份實作已經開始分家' % bad)
subprocess.run(['rm', '-rf', ROOT])
sys.exit(1 if bad else 0)
