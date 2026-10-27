#!/usr/bin/env python3
"""測試映像是打分數的尺:AI 節點換掉它會被還原;漂移時 preflight 自己重建 —— 跑法:python3 runner_guard_selftest.py

2026-10-04 #539 那一輪,implement 的 AI 自己 `docker build -t aaf-test-runner:local`(用 PR 的樹),
之後三輪 preflight 全部「映像與 main 不一致」拒絕開工。

  A 組:守衛 —— 用真的 docker,在一個沒人用的測試標籤上模擬「AI 換掉映像」→ 要被還原、要留紀錄
  B 組:例外 —— 平台自己重建(_RUNNER_PLATFORM_GEN 變了)→ 不還原
  C 組:沒動 —— 映像沒被碰 → 不留紀錄、備份標籤要清掉
  D 組:接線 —— preflight 漂移時真的呼叫自動重建;每個 AI 節點的提示都帶著規則

需要 docker 與兩個本機映像(alpine:3、postgres:18-alpine);沒有就明說沒跑,不算通過。
注意:arcana-skills 沒有 CI,這支不會自動跑。
"""
import importlib.util, inspect, os, subprocess, sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
os.environ.setdefault("STUB", "")
spec = importlib.util.spec_from_file_location("atn_server", os.path.join(D, "server.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ok = fail = 0
def check(label, cond):
    global ok, fail
    if cond: ok += 1; print("  ✓ %s" % label)
    else:    fail += 1; print("  ✗ %s" % label)

def sh(*a):
    return subprocess.run(list(a), capture_output=True, text=True)

IMG = "aaf-runner-guard-selftest:local"          # 絕不碰真的 aaf-test-runner:local
SRC_A, SRC_B = "alpine:3", "postgres:18-alpine"   # 兩個內容不同的映像
have = all(sh("docker", "image", "inspect", x).returncode == 0 for x in (SRC_A, SRC_B))
guard_tags = lambda: [l for l in sh("docker", "images", "--format", "{{.Repository}}:{{.Tag}}",
                                    "aaf-runner-guard").stdout.split() if l]

if not have:
    print("  ⚠ notRun —— 沒有 docker 或缺 %s / %s;A–C 組不算通過" % (SRC_A, SRC_B))
else:
    id_a = m._runner_image_id(SRC_A)
    id_b = m._runner_image_id(SRC_B)

    print("A 組 —— AI 節點換掉映像 → 還原")
    sh("docker", "tag", SRC_A, IMG)
    os.environ["TEST_RUNNER_IMAGE"] = IMG
    real_core = m._invoke_claude_core
    def tamper(prompt, schema, payload, wall, cwd=None):
        sh("docker", "tag", SRC_B, IMG)          # 模擬 AI 跑 docker build -t <img>
        return {"result": "done"}
    m._invoke_claude_core = tamper
    out = m._invoke_claude("做事", {}, {}, 60)
    check("節點結束後映像被還原成原本那一個", m._runner_image_id(IMG) == id_a)
    check("節點結果記下 _runnerTamper,而且寫著已還原",
          isinstance(out.get("_runnerTamper"), dict) and out["_runnerTamper"].get("restored") is True)
    check("備份標籤用完就清掉", guard_tags() == [])

    print("B 組 —— 平台自己重建 → 不還原")
    sh("docker", "tag", SRC_A, IMG)
    def platform_rebuild(prompt, schema, payload, wall, cwd=None):
        sh("docker", "tag", SRC_B, IMG)
        m._RUNNER_PLATFORM_GEN[0] += 1           # 平台的 _rebuild_runner_from_base 會遞增它
        return {"result": "done"}
    m._invoke_claude_core = platform_rebuild
    out = m._invoke_claude("做事", {}, {}, 60)
    check("平台重建的新映像留著", m._runner_image_id(IMG) == id_b)
    check("不算竄改(沒有 _runnerTamper)", "_runnerTamper" not in out)

    print("C 組 —— 映像沒被碰")
    sh("docker", "tag", SRC_A, IMG)
    seen = {}
    def honest(prompt, schema, payload, wall, cwd=None):
        seen["prompt"] = prompt
        return {"result": "done"}
    m._invoke_claude_core = honest
    out = m._invoke_claude("做事", {}, {}, 60)
    check("映像不變、沒有紀錄", m._runner_image_id(IMG) == id_a and "_runnerTamper" not in out)
    check("備份標籤清掉", guard_tags() == [])
    check("提示裡帶著「測試映像是打分數的尺」的規則", "打分數的尺" in seen.get("prompt", ""))
    m._invoke_claude_core = real_core
    sh("docker", "image", "rm", IMG)

print("D 組 —— 接線")
pre = inspect.getsource(m.preflight)
check("preflight 漂移時呼叫 _rebuild_runner_from_base,重建後再比一次",
      "_rebuild_runner_from_base(img, repo, base)" in pre and pre.count("_image_blobs(img)") >= 2)
check("自動重建可以用 RUNNER_SELF_HEAL=0 關掉", "RUNNER_SELF_HEAL" in pre)
reb = inspect.getsource(m._rebuild_runner_from_base)
check("重建用的是 base 的樹(clone --branch base),不是 PR 的", '"--branch", base' in reb)
check("平台重建會遞增 _RUNNER_PLATFORM_GEN(守衛才分得出是誰換的)", "_RUNNER_PLATFORM_GEN[0] += 1" in reb)
check("兩條呼叫路徑(run_claude / run_claude_generic)都走 _invoke_claude",
      "_invoke_claude(" in inspect.getsource(m.run_claude) and "_invoke_claude(" in inspect.getsource(m.run_claude_generic))

print()
print("pass —— %d 項" % ok if fail == 0 else "gap —— %d 項不符(共 %d)" % (fail, ok + fail))
sys.exit(1 if fail else 0)
