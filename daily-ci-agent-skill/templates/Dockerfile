FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Taipei \
    PATH=/usr/local/bin:/usr/bin:/bin

# Core deps + GitHub CLI repo + Claude CLI (Anthropic native binary)
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl wget gnupg cron jq git \
        python3 python3-pip python3-venv \
        tzdata locales passwd util-linux \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        | gpg --dearmor -o /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y --no-install-recommends gh \
    && ln -fs /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# Install Claude CLI (native binary, arm64/x64 auto-detected)
RUN curl -fsSL https://claude.ai/install.sh | bash -s -- --install-dir /usr/local/bin \
    || (echo "Claude install.sh failed; fallback to npm route" && \
        curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
        apt-get install -y --no-install-recommends nodejs && \
        npm install -g @anthropic-ai/claude-code)

# Install arch-qube (Python CLI) into a venv
RUN python3 -m venv /opt/arch-qube-venv \
    && /opt/arch-qube-venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/arch-qube-venv/bin/pip install --no-cache-dir 'git+https://github.com/<YOUR-ORG>/<YOUR-ARCH-TOOL>.git' \
        || echo "arch-qube install deferred (handled at runtime in daily-run.sh)"

# Non-root user for running claude (--dangerously-skip-permissions refuses root)
RUN /usr/sbin/useradd -M -d /root -s /bin/bash claude-agent

COPY entrypoint.sh /entrypoint.sh
COPY crontab /etc/cron.d/daily-ci-agent
COPY scripts/daily-run.sh /usr/local/bin/daily-run.sh
COPY prompts/daily.md /opt/prompt/daily.md

RUN chmod +x /entrypoint.sh /usr/local/bin/daily-run.sh \
    && chmod 0644 /etc/cron.d/daily-ci-agent \
    && touch /var/log/daily-run.log

WORKDIR /root
CMD ["/entrypoint.sh"]
