#!/usr/bin/env bash
#
# install-semantic-docker.sh — Docker variant of install-semantic.sh
#
# Use this if you already have Docker (Desktop on macOS, or daemon on Linux).
# Runs Ollama in a container instead of as a native binary.
#
# Trade-offs vs native install-semantic.sh:
#   + No native binary in ~/claude-archive/ollama-bin/
#   + Easier full uninstall (one container + one volume)
#   + Same command on macOS and Linux
#   - On macOS: Docker uses Linux VM, NO Metal GPU acceleration
#     → bge-m3 embedding: ~3-5x slower vs native (~500ms vs ~140ms per call)
#     → Backfill 100k rows: ~6-12 hours instead of ~2-3 hours
#   - On Linux with NVIDIA: Docker can passthrough GPU (--gpus=all), faster
#
# Usage:
#   ./install-semantic-docker.sh

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE_DIR="$HOME/claude-archive"
BIN_DIR="$HOME/bin"
CONTAINER_NAME="claude-archive-ollama"
IMAGE="ollama/ollama:latest"

echo "==> install-semantic-docker.sh"
echo "    skill source: $SKILL_DIR"
echo "    archive dir:  $ARCHIVE_DIR"
echo "    container:    $CONTAINER_NAME"

# 0. Sanity: docker available?
if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker not found. Install Docker Desktop (macOS) or docker-engine (Linux) first."
    echo "       Or use ./install-semantic.sh for the native binary path."
    exit 1
fi
if ! docker info >/dev/null 2>&1; then
    echo "ERROR: docker daemon not running. Start Docker Desktop."
    exit 1
fi
echo "    docker: $(docker --version)"

mkdir -p "$ARCHIVE_DIR" "$BIN_DIR"

# 1. Pull image (~1GB compressed)
echo "==> pulling ollama/ollama image (~1GB)..."
docker pull "$IMAGE"

# 2. Stop + remove existing container if any (idempotent re-run)
if docker inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
    echo "==> removing existing container '$CONTAINER_NAME'..."
    docker rm -f "$CONTAINER_NAME" >/dev/null
fi

# 3. Run container with named volume for model persistence + restart policy
#    Port 11434 published so embed.py / vsearch.py reach it as if local
echo "==> starting ollama container..."
GPU_FLAG=""
if [ -n "${OLLAMA_GPU:-}" ] && [ "$OLLAMA_GPU" = "all" ]; then
    GPU_FLAG="--gpus=all"
    echo "    GPU passthrough enabled (Linux + NVIDIA)"
fi

docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    -p 127.0.0.1:11434:11434 \
    -v ollama:/root/.ollama \
    -e OLLAMA_KEEP_ALIVE=30m \
    $GPU_FLAG \
    "$IMAGE"

# Wait for container to be ready
echo "    waiting for daemon..."
for i in 1 2 3 4 5 6 7 8 9 10; do
    if curl -s --max-time 2 http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "    daemon ready"
        break
    fi
    sleep 2
done

# 4. Pull embedding model
echo "==> pulling bge-m3 (~1.2 GB)..."
docker exec "$CONTAINER_NAME" ollama pull bge-m3

# 5. Python venv
if [ ! -d "$ARCHIVE_DIR/.venv" ]; then
    echo "==> creating venv at $ARCHIVE_DIR/.venv"
    python3 -m venv "$ARCHIVE_DIR/.venv"
fi
echo "==> installing python deps..."
"$ARCHIVE_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$ARCHIVE_DIR/.venv/bin/pip" install --quiet sqlite-vec requests

# 6. Copy scripts (same as native variant)
echo "==> installing embed.py / embed_parallel.py / vsearch.py / vsearch-since.py / vsearch / gen-recent-context.sh ..."
cp "$SKILL_DIR/scripts/embed.py"              "$ARCHIVE_DIR/embed.py"
cp "$SKILL_DIR/scripts/embed_parallel.py"     "$ARCHIVE_DIR/embed_parallel.py"
cp "$SKILL_DIR/scripts/vsearch.py"            "$ARCHIVE_DIR/vsearch.py"
cp "$SKILL_DIR/scripts/vsearch-since.py"      "$ARCHIVE_DIR/vsearch-since.py"
cp "$SKILL_DIR/scripts/vsearch"               "$BIN_DIR/vsearch"
cp "$SKILL_DIR/scripts/build.py"              "$ARCHIVE_DIR/build.py"
cp "$SKILL_DIR/scripts/gen-recent-context.sh" "$ARCHIVE_DIR/gen-recent-context.sh"
chmod +x "$ARCHIVE_DIR/embed.py" "$ARCHIVE_DIR/embed_parallel.py" "$ARCHIVE_DIR/vsearch.py" "$ARCHIVE_DIR/vsearch-since.py" "$BIN_DIR/vsearch" "$ARCHIVE_DIR/build.py" "$ARCHIVE_DIR/gen-recent-context.sh"

# 7. Convenience wrapper to talk to docker container
cat > "$BIN_DIR/ollama" <<EOF
#!/usr/bin/env bash
# Pass through to ollama in docker container
exec docker exec -it $CONTAINER_NAME ollama "\$@"
EOF
chmod +x "$BIN_DIR/ollama"

# 8. Kick off backfill
TOTAL_ROWS=$(sqlite3 "$ARCHIVE_DIR/sessions.db" "SELECT COUNT(*) FROM msg" 2>/dev/null || echo 0)
EMBED_ROWS=$(sqlite3 "$ARCHIVE_DIR/sessions.db" "SELECT COUNT(*) FROM msg_vec" 2>/dev/null || echo 0)
PENDING=$((TOTAL_ROWS - EMBED_ROWS))

echo "==> rows to backfill: $PENDING (of $TOTAL_ROWS total)"
if [ "$PENDING" -gt 0 ]; then
    echo "==> launching parallel backfill in background (8 workers; Docker on macOS = 3-5x slower than native)"
    echo "    log: $ARCHIVE_DIR/backfill.log"
    nohup "$ARCHIVE_DIR/.venv/bin/python" "$ARCHIVE_DIR/embed_parallel.py" 8 \
        > "$ARCHIVE_DIR/backfill.log" 2>&1 &
    echo "    PID: $!"
fi

echo
echo "==> done. Check status:"
echo "      docker ps | grep $CONTAINER_NAME"
echo "      docker stats $CONTAINER_NAME       # resource use"
echo "      tail -f $ARCHIVE_DIR/backfill.log"
echo
echo "==> uninstall:"
echo "      docker rm -f $CONTAINER_NAME"
echo "      docker volume rm ollama"
