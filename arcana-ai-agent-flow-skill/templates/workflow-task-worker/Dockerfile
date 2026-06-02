# Arcana workflow task-worker — stdlib-only Python, no dependencies.
FROM python:3.12-alpine
WORKDIR /app
COPY worker.py .
# Defaults target the in-cluster service names; override per environment.
ENV ENGINE_URL=http://kogito-bpmn:8080 \
    DATA_INDEX_URL=http://data-index:8080 \
    MODE=auto \
    POLL_SECS=5
CMD ["python3", "worker.py"]
