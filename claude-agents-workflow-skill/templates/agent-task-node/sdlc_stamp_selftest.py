#!/usr/bin/env python3
"""git 上要有 CR 身分章的自驗 —— 跑法:python3 sdlc_stamp_selftest.py

2026-09-04 查證:40 個 sdlc 實例、11 個 PR,git 裡零處有 projectId / 實例 id,只有 slug。
這支問三件事:章的內容對不對(缺的要省略、-vN 要能連回同一張 CR)、規格文件資訊表有沒有
寫進去、以及 **真的對一個 git repo amend --trailer 之後,log 讀得到那幾個 key**。
三態:通過 / 失敗 / 未檢查(沒有 git 時第三段記 notrun,不當通過)。
"""
import importlib.util, os, re, subprocess, sys, tempfile
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
spec = importlib.util.spec_from_file_location("atn_server", os.path.join(D, "server.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ok = fail = 0
notrun = []
def check(label, cond):
    global ok, fail
    if cond: ok += 1; print("  ✓ %s" % label)
    else: fail += 1; print("  ✗ %s" % label)
def skip(label, why):
    notrun.append(label); print("  ⊘ %s —— %s(這是「沒檢查」,不是「通過」)" % (label, why))

# 註冊表在自驗裡問不到 —— 讓 _project_of 走 payload 那條路(有 projectId 就直接用)。
m._registry_project_by_id = lambda pid: {"displayName": "AAF"}

print("── 章的內容 ──")
pl = {"projectId": "aaf", "_piid": "6775540d-3602-4ba5-94a2-38d8f7fab59c",
      "slug": "users-page-disable-login-v3"}
st = dict(m._sdlc_stamp(pl))
check("Sdlc-Project 來自 payload 的 projectId", st.get("Sdlc-Project") == "aaf")
check("Sdlc-Instance 來自 _piid", st.get("Sdlc-Instance") == pl["_piid"])
check("Sdlc-Feature 去掉 -vN,能連回同一張 CR", st.get("Sdlc-Feature") == "users-page-disable-login")
check("Sdlc-Slug 保留完整 slug", st.get("Sdlc-Slug") == "users-page-disable-login-v3")
check("Sdlc-Specs 指到 docs/specs/<slug>/", st.get("Sdlc-Specs") == "docs/specs/users-page-disable-login-v3/")
check("順序固定(Project → Instance → Feature → Slug → Specs)",
      [k for k, _ in m._sdlc_stamp(pl)] == ["Sdlc-Project", "Sdlc-Instance", "Sdlc-Feature", "Sdlc-Slug", "Sdlc-Specs"])
st2 = dict(m._sdlc_stamp({"slug": "x"}))
check("沒有 projectId / _piid 時省略,不寫空字串", "Sdlc-Project" not in st2 and "Sdlc-Instance" not in st2)
check("沒有 slug 時 Feature/Slug/Specs 都省略", m._sdlc_stamp({"projectId": "aaf"}) == [("Sdlc-Project", "aaf")])
check("slug 沒有 -vN 時 Feature == Slug", dict(m._sdlc_stamp({"slug": "plain-slug"}))["Sdlc-Feature"] == "plain-slug")
check("沒有任何 id 時 PR 區塊是空字串", m._sdlc_pr_stamp_block({}) == "")
blk = m._sdlc_pr_stamp_block(pl)
check("PR 區塊含每一行 Key: value", all(("%s: %s" % kv) in blk for kv in m._sdlc_stamp(pl)))
check("PR 區塊與 trailer 是同一串字(兩邊 grep 得到一樣的)", all(ln in blk for ln in m._sdlc_stamp_lines(pl)))

print("── 規格文件資訊表 ──")
md = "# SRS —— x\n\n## 文件資訊\n\n| 項目 | 內容 |\n|---|---|\n| 功能代號 | `x` |\n| 文件類型 | SRS |\n\n---\n"
out = m._stamp_spec_markdown(md, pl)
check("功能代號之後插入 專案 列", "| 專案 | `aaf` |" in out)
check("功能代號之後插入 流程實例 列", ("| 流程實例 | `%s` |" % pl["_piid"]) in out)
check("插在功能代號與文件類型之間", out.index("| 專案 |") < out.index("| 文件類型 |"))
check("原有列一個都沒掉", all(ln in out for ln in md.strip().split("\n")))
check("沒有表(不是我們渲染的)就原樣回傳", m._stamp_spec_markdown("# 純文字規格\n", pl) == "# 純文字規格\n")
check("沒有 id 就原樣回傳(不插空列)", m._stamp_spec_markdown(md, {"slug": "x"}) == md)

print("── 真的 git:amend --trailer 後 log 讀得到 ──")
if subprocess.run(["git", "--version"], capture_output=True).returncode != 0:
    skip("git amend trailer", "這裡沒有 git")
else:
    with tempfile.TemporaryDirectory() as td:
        def g(*a): return subprocess.run(["git", "-C", td] + list(a), capture_output=True, text=True)
        g("init", "-q", "-b", "main"); open(os.path.join(td, "f"), "w").write("1")
        g("add", "-A"); g("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "feat: x")
        am = ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "--amend", "--no-edit"]
        for ln in m._sdlc_stamp_lines(pl): am += ["--trailer", ln]
        r = g(*am)
        check("amend --trailer 成功", r.returncode == 0)
        tr = g("log", "-1", "--format=%(trailers)").stdout
        check("git log 的 trailers 讀得到 Sdlc-Instance", "Sdlc-Instance: " + pl["_piid"] in tr)
        check("git log 的 trailers 讀得到 Sdlc-Project", "Sdlc-Project: aaf" in tr)
        check("--grep 找得到(這就是 CR 帳本的查法)", g("log", "--grep=Sdlc-Project: aaf", "--format=%h").stdout.strip() != "")
        body = g("log", "-1", "--format=%B").stdout
        check("原本的標題沒被改", body.startswith("feat: x"))

print("\n" + "═" * 46)
if notrun: print("  未檢查 %d 項:%s" % (len(notrun), ", ".join(notrun)))
print("  通過 %d,失敗 %d" % (ok, fail))
sys.exit(1 if fail else 0)
