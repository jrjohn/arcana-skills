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
COPY server.py /usr/local/bin/agent-task-node.py

ENV PORT=8090 \
    AGENT_TASK_TIMEOUT=900
EXPOSE 8090

# Run as the same non-root agent user the base image uses for tool caches.
# (claude-home is bind-mounted at /root/.claude by compose; HOME stays /root.)
ENTRYPOINT ["python3", "/usr/local/bin/agent-task-node.py"]
