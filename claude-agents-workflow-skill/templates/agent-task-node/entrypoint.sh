#!/usr/bin/env sh
# agent-task-node 的啟動包裝 —— 只做一件事:讓 claude CLI 跟得上,然後把控制權交出去。
#
# ## 為什麼需要它
#
# claude CLI 是從 daily-ci-agent 基底映像繼承的,`npm i -g` 發生在**建置時**,所以
# 版本被映像釘死。2026-08-20 實測:容器裡 2.1.185(symlink 日期 Jun 22),npm 上
# 已經是 2.1.237 —— 落後 52 個版本,而且沒有任何地方會說。
#
# 內建的自動更新在這裡不會作用:這個節點跑的是 headless 的 `claude -p`,那個模式
# 不做更新檢查。所以要嘛重建映像、要嘛在啟動時更新 —— 這支選後者,因為這個容器
# 一起就是好幾天,重建的頻率遠低於它該跟上的頻率。
#
# ## 三條規矩
#
# 1. **升級失敗不擋啟動。** 沒有網路、npm 掛了、registry 慢 —— 都不該讓這個節點
#    起不來。失敗就用映像裡那一版繼續跑,但要說出來。
# 2. **版本一定印出來。** 靜靜升級和靜靜沒升級,在 log 上長得一模一樣;而這個 repo
#    已經為「看不出有沒有生效」付過太多次代價。
# 3. **可以釘住。** `CLAUDE_CLI_PIN=1` 就完全不動它 —— 新版改壞了行為時,要有一條
#    不必重建映像就能退回去的路。
set -u

BEFORE=$(claude --version 2>/dev/null || echo "查不到")

if [ "${CLAUDE_CLI_PIN:-0}" = "1" ]; then
  echo "[entrypoint] CLAUDE_CLI_PIN=1 —— 不升級,維持 $BEFORE" >&2
else
  echo "[entrypoint] 目前 $BEFORE,嘗試升級到 latest…" >&2
  # `|| true` 是刻意的(見規矩 1)。timeout 讓 registry 慢的時候不會卡死啟動。
  if timeout "${CLAUDE_CLI_UPDATE_TIMEOUT:-180}" \
       npm i -g @anthropic-ai/claude-code@latest --silent >/dev/null 2>&1; then
    AFTER=$(claude --version 2>/dev/null || echo "查不到")
    if [ "$AFTER" = "$BEFORE" ]; then
      echo "[entrypoint] 已是最新:$AFTER" >&2
    else
      echo "[entrypoint] 已升級:$BEFORE → $AFTER" >&2
    fi
  else
    echo "[entrypoint] ⚠ 升級沒成功(網路/registry/逾時)—— 沿用 $BEFORE 繼續啟動" >&2
  fi
fi

echo "[entrypoint] claude = $(claude --version 2>/dev/null || echo '查不到')" >&2
exec python3 /usr/local/bin/agent-task-node.py "$@"
