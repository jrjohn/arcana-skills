# agent-task-node — Claude execution node for SonataFlow.
# Built FROM the existing daily-ci-agent image so it inherits the claude CLI,
# gh, git, language toolchains, and (via the mounted claude-home) auth.
# Override BASE_IMAGE to point at your agent image.
ARG BASE_IMAGE=daily-ci-agent:latest
FROM ${BASE_IMAGE}

# do_test dispatches to the playwright runner image via the mounted docker.sock — so add just
# the docker CLI (static aarch64 binary, ~50MB; talks to /var/run/docker.sock, no in-image
# daemon). Chromium / build tooling stay in the runner image, not here.
RUN curl -fsSL https://download.docker.com/linux/static/stable/aarch64/docker-27.5.1.tgz -o /tmp/d.tgz \
    && tar xzf /tmp/d.tgz -C /tmp && install /tmp/docker/docker /usr/local/bin/docker \
    && rm -rf /tmp/d.tgz /tmp/docker

# ...and the compose PLUGIN, because the docker CLI alone does not have it: `docker compose` then
# prints docker's own help text and exits non-zero. That is what the coverage step reads as
# "coverage image build failed", so no lcov is produced, so `_sonar` reports ran=False — and the
# PM never sees a Sonar number. 2026-09-07: measured across every sdlc-code-flow round so far.
# A plugin, not a v1 `docker-compose` binary: the code calls `docker compose` (space).
RUN mkdir -p /usr/local/lib/docker/cli-plugins \
    && curl -fsSL https://github.com/docker/compose/releases/download/v2.32.4/docker-compose-linux-aarch64 \
       -o /usr/local/lib/docker/cli-plugins/docker-compose \
    && chmod +x /usr/local/lib/docker/cli-plugins/docker-compose \
    && docker compose version

# server.py only needs python3 (already present in the agent image).
# flow-sim binary (linux) for S3b in-pipeline scenario auto-fill — the agent runs the divergence
# proof itself. Built separately (cargo build --bin flow-sim in a linux rust container) and copied
# in; kept out of git (.gitignore) as a build artifact.
COPY flow-sim /usr/local/bin/flow-sim
RUN chmod +x /usr/local/bin/flow-sim

# Per-product conversation memory. Built WITHOUT --features pg-backend on purpose:
# this binary has no pgsearch/pgsearchd/osearch subcommands compiled in, so it cannot
# reach the shared team PG whatever it is handed. That is the isolation between a
# product's own build history and a person's cross-project archive — structural,
# rather than a rule someone has to keep remembering.
# Rebuild: docker run --rm -v ~/claude-archive/crs:/src -w /src -e CARGO_TARGET_DIR=/t \
#   rust:1-slim-bookworm cargo build --release   (note: no --features pg-backend)
COPY bin/crs-sqlite /root/bin/crs-sqlite

COPY server.py /usr/local/bin/agent-task-node.py

ENV PORT=8090 \
    AGENT_TASK_TIMEOUT=900 \
    # S3b 情境自補。2026-08-04 之前它只存在於**執行中的容器**,repo 裡沒有任何地方
    # 設定它 —— 也就是說重建映像會靜默把它關掉,而症狀是「情境缺格突然開始退回
    # implement」,看起來像流程變笨,不像設定掉了。寫在這裡它才跟著映像走。
    #
    # 開著是安全的:自補的情境必須先被證明會分歧(對著拋棄式引擎跑),證不出來就
    # escalate,而靜態閘照樣擋 —— 它從來不會靜靜放行一個缺口。
    SCENARIO_AUTOFILL=1
EXPOSE 8090

# Run as the same non-root agent user the base image uses for tool caches.
# (claude-home is bind-mounted at /root/.claude by compose; HOME stays /root.)
# claude CLI 跟得上 —— 版本原本被基底映像釘死(2026-08-20 實測落後 52 個版本,
# 而且沒有任何地方會說)。entrypoint 在啟動時升級一次:失敗不擋啟動、版本一定印
# 出來、`CLAUDE_CLI_PIN=1` 可以完全關掉。詳見 entrypoint.sh 檔頭。
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Claude CLI 在**建置時**就裝最新版,不再只靠 entrypoint 啟動時升級。
#
# 2026-10-14:模型 claude-opus-5-5[1m] 開始要求 Claude Code ≥ 2.1.280,而基底映像
# (daily-ci-agent,3 個月沒重建)裡是 2.1.185。entrypoint 的啟動升級只給 180 秒、失敗不擋 ——
# 10-13 那次剛好逾時,於是每個 AI 節點都 `API Error: 400 … does not support this model`,
# 進化圈連兩輪死在 IntakeReview(stderr 是空的,錯誤只在 /console 的 jsonl 裡)。
# 映像本身帶著最新版,啟動升級失敗時退回的就不是三個月前的版本。
#
# 放在最後:CLAUDE_CLI_REFRESH 一變,只有這一層重做,前面的層都吃快取。
# 每週重建(本機 ~/bin/aaf-agent-weekly-rebuild.sh)傳日期進來,讓這一層確實重抓。
ARG CLAUDE_CLI_REFRESH=unset
RUN echo "claude cli refresh: ${CLAUDE_CLI_REFRESH}" \
 && npm i -g @anthropic-ai/claude-code@latest --silent \
 && claude --version

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
