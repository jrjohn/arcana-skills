# Arcana workflow task-worker — Rust (port of worker.py, 2026-06-04; worker.py
# kept in-tree as the behavioral reference until the Rust port has soaked).
# Multi-stage: release build, then a slim runtime.
FROM rust:1-bookworm AS builder
WORKDIR /build
COPY Cargo.toml ./
COPY src ./src
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /build/target/release/workflow-task-worker /usr/local/bin/workflow-task-worker
# Defaults target the in-cluster service names; override per environment.
ENV ENGINE_URL=http://kogito-bpmn:8080 \
    DATA_INDEX_URL=http://data-index:8080 \
    MODE=auto \
    POLL_SECS=5
CMD ["workflow-task-worker"]
