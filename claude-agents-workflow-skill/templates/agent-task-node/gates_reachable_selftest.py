#!/usr/bin/env python3
"""兩個品質閘「跑了卻讀不到」的自驗 —— 跑法:python3 gates_reachable_selftest.py

2026-09-07 實測(每一輪 sdlc-code-flow 都是這樣):
  · arch-qube 真的跑完、真的評了 PASS 100.0/100 (A+),報告裡 files_scanned=1 ——
    而節點回報 notRun / "scanned 0 files"。原因:`docker start -a` 回來時容器已結束,
    後面用 `docker exec` 讀 /output/arch-qube.json 必定失敗,空輸出被讀成「什麼都沒掃到」。
  · sonar 永遠 ran=False,原因是覆蓋率映像「建置失敗」,而真正的失敗是 agent 映像裡
    **沒有 compose 外掛**:`docker compose` 會印出 docker 自己的說明並回非零。

兩者的共同形狀:閘做完了工作,結論卻沒有人拿得到,而拿不到被記成「沒有問題」的鄰居——「沒跑」。
"""
import os, re, sys
D = os.path.dirname(os.path.abspath(__file__))
ok = fail = 0
def check(l, c):
    global ok, fail
    if c: ok += 1; print("  ✓", l)
    else: fail += 1; print("  ✗", l)

src = open(os.path.join(D, "server.py"), encoding="utf-8").read()
aq = src[src.index("def _arch_qube("):]
aq = aq[:aq.index("\ndef ", 10)]
check("arch-qube 用 docker cp 讀報告(對已停止的容器可用)", '"docker", "cp", cname + ":/output/arch-qube.json"' in aq)
check("arch-qube 不再用 docker exec 讀報告(容器那時已結束)", '"docker", "exec", cname, "cat"' not in aq)
check("docker cp 的 tar 串流有被解開", "tarfile" in aq and "extractfile" in aq)
check("解不開時說得出原因,不是靜靜當成沒掃到", "解不開" in aq)
check("啟動仍然是 docker start -a(要等它跑完才能讀)", '"docker", "start", "-a", cname' in aq)

df = open(os.path.join(D, "Dockerfile"), encoding="utf-8").read()
check("Dockerfile 裝了 compose 外掛", "cli-plugins/docker-compose" in df)
check("裝完立刻驗證(docker compose version),裝不起來就建不出映像", "docker compose version" in df)
check("裝的是外掛不是 v1 的 docker-compose 執行檔(程式碼呼叫的是 `docker compose`)",
      "cli-plugins" in df and re.search(r"^RUN\s+.*\bdocker-compose\s*$", df, re.M) is None)
check("compose 與 docker CLI 裝在一起(同一段,版本不會各走各的)",
      df.index("cli-plugins/docker-compose") - df.index("install /tmp/docker/docker") < 900)
print("\n  通過 %d,失敗 %d" % (ok, fail)); sys.exit(1 if fail else 0)
