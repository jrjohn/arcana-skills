# agent-task-node — Claude execution node for SonataFlow.
# Built FROM the existing daily-ci-agent image so it inherits the claude CLI,
# gh, git, language toolchains, and (via the mounted claude-home) auth.
# Override BASE_IMAGE to point at your agent image.
ARG BASE_IMAGE=daily-ci-agent:latest
FROM ${BASE_IMAGE}

# server.py only needs python3 (already present in the agent image).
COPY server.py /usr/local/bin/agent-task-node.py

ENV PORT=8090 \
    AGENT_TASK_TIMEOUT=900
EXPOSE 8090

# Run as the same non-root agent user the base image uses for tool caches.
# (claude-home is bind-mounted at /root/.claude by compose; HOME stays /root.)
ENTRYPOINT ["python3", "/usr/local/bin/agent-task-node.py"]
