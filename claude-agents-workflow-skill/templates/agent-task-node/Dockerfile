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
ENTRYPOINT ["python3", "/usr/local/bin/agent-task-node.py"]
