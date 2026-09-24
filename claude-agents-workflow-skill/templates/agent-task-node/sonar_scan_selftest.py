#!/usr/bin/env python3
"""test 節點的 Sonar 掃描 —— 跑法:python3 sonar_scan_selftest.py

2026-09-24 查到:test 節點的 Sonar **每一輪都失敗**,PM 因此每一輪都判 BLOCKED。
  1. 程式碼被複製到掃描容器的 `/src`,但 sonar-scanner-cli 映像裡**沒有 /src**
     (WORKDIR 是 /usr/src)→ `docker cp` 失敗,結果沒被檢查
  2. 掃描器對著不存在的資料夾跑 → `Project home must be an existing directory: /src`
  3. 理由只留 stdout 的最後 300 字 → 真正的錯誤(在 stderr)從來沒被記下來

  A 組:_scanner_failure 留得住真正的錯誤(輸入 = 當天真實的失敗輸出)
  B 組:_sonar 真的改用 _SCANNER_BASE,而且檢查了複製結果
  C 組:修之前的寫法 / 原始碼,餵給 A、B 必須判紅
  D 組:直接問映像 —— _SCANNER_BASE 存在、/src 不存在(映像哪天改了會在這裡抓到)

注意:arcana-skills 沒有 CI,這支不會自動跑。D 組需要 docker,沒有時明說沒跑,不算通過。
"""
import importlib.util, inspect, os, re, shutil, subprocess, sys, types

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

# 2026-09-24 01:49 那一輪 test 節點裡,掃描器真實的輸出(節錄)
REAL_STDOUT = ("09:02:26.096 INFO  Linux 6.10.14-linuxkit amd64\n"
               "09:02:45.141 INFO  Communicating with SonarQube Community Build 26.6.0.123539\n"
               "09:02:45.154 INFO  JRE provisioning: os[linux], arch[x86_64]\n"
               "09:03:11.641 INFO  EXECUTION FAILURE\n"
               "09:03:11.648 INFO  Total time: 46.011s\n")
REAL_STDERR = ("09:03:11.640 ERROR Error during SonarScanner CLI execution\n"
               "java.lang.IllegalStateException: Project home must be an existing directory: /src\n"
               "\tat org.sonarsource.scanner.lib.internal.facade.Dirs.init(Dirs.java:40)\n"
               "09:03:11.641 ERROR Re-run SonarScanner CLI using the -X switch to enable full debug logging.\n")
run = types.SimpleNamespace(stdout=REAL_STDOUT, stderr=REAL_STDERR, returncode=1)

print("A 組 —— 理由留得住真正的錯誤")
why = m._scanner_failure(run)
check("stdout 有東西時,stderr 的真正原因仍在理由裡", "Project home must be an existing directory" in why)
check("理由裡有 ERROR 行", "ERROR" in why)
quiet = types.SimpleNamespace(stdout="INFO a\nINFO b\n", stderr="", returncode=1)
check("完全沒有錯誤行時,退回輸出的結尾(不是空白)", m._scanner_failure(quiet).endswith("INFO b"))
empty = types.SimpleNamespace(stdout="", stderr="", returncode=1)
check("兩邊都空 → 空字串(呼叫端前面還有 'scanner failed: ')", m._scanner_failure(empty) == "")

def wired(src):
    base_ok = re.search(r'projectBaseDir="\s*\+\s*_SCANNER_BASE', src) is not None
    cp_ok = re.search(r'"docker", "cp", "-", cname \+ ":" \+ _SCANNER_BASE', src) is not None
    checked = "cp.returncode != 0" in src
    no_src = ':/src"' not in src and '"/src/"' not in src
    return base_ok and cp_ok and checked and no_src

print("B 組 —— _sonar 真的接上了")
check("_sonar 用 _SCANNER_BASE、檢查複製結果、不再出現 /src", wired(inspect.getsource(m._sonar)))

print("C 組 —— 修之前的寫法必須判紅")
old_why = (run.stdout or run.stderr or "")[-300:]
check("舊寫法 `(stdout or stderr)[-300:]` 丟掉了真正原因", "Project home" not in old_why)
try:
    old = subprocess.run(["git", "-C", D, "show",
                          "404abe6:claude-agents-workflow-skill/templates/agent-task-node/server.py"],
                         capture_output=True, text=True, timeout=30)
    body = old.stdout
    s0 = body.find("def _sonar(payload):")
    s1 = body.find("\ndef ", s0 + 10)
    if old.returncode != 0 or s0 < 0:
        print("  ? 取不到修之前的版本 —— C 組這條沒跑,不是通過"); fail += 1
    else:
        check("修之前(404abe6)的 _sonar → B 組判紅", not wired(body[s0:s1]))
except Exception as e:
    print("  ? C 組沒跑:%s" % e); fail += 1

print("D 組 —— 直接問映像")
if not shutil.which("docker"):
    print("  ? 沒有 docker —— D 組沒跑,不是通過")
else:
    def has_dir(d):
        r = subprocess.run(["docker", "run", "--rm", "--entrypoint", "sh", m._SONAR_SCANNER_IMAGE,
                            "-c", "test -d %s" % d], capture_output=True, timeout=300)
        return r.returncode == 0
    check("映像裡 %s 存在(程式碼要複製進去的地方)" % m._SCANNER_BASE, has_dir(m._SCANNER_BASE))
    check("映像裡 /src 不存在(這就是舊寫法失敗的原因)", not has_dir("/src"))

print("\n  %d 過 / %d 失敗" % (ok, fail))
sys.exit(1 if fail else 0)
