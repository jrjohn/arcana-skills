# TESTED: 2025-02 | Rocky VM (ARM64) | Go 1.24 + protobuf/gRPC + alpine:3.21
# ============================================
# Go Multi-Stage Dockerfile
# DevOps Skill Template
# ============================================

# Stage 1: Build
FROM golang:1.24-alpine AS builder

WORKDIR /app

# Install build dependencies (git for modules, protobuf for gRPC)
RUN apk add --no-cache git protobuf protobuf-dev

# Install protoc-gen-go and protoc-gen-go-grpc
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@latest && \
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

# Copy dependency files (cached layer)
COPY go.mod go.sum ./
RUN go mod download

# Copy source
COPY . .

# Generate protobuf (if proto/ directory exists)
RUN if [ -d "proto" ]; then \
      find proto -name "*.proto" -exec protoc \
        --go_out=. --go_opt=paths=source_relative \
        --go-grpc_out=. --go-grpc_opt=paths=source_relative \
        {} +; \
    fi

# Static build (no CGO)
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o server ./cmd/server

# Stage 2: Runtime
FROM alpine:3.21

# Install ca-certificates for HTTPS
RUN apk add --no-cache ca-certificates

# Security: non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

# Copy binary
COPY --from=builder /app/server .

# Set ownership
RUN chown -R appuser:appgroup /app

USER appuser

# Expose port
EXPOSE {{APP_PORT}}

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:{{APP_PORT}}/health || exit 1

CMD ["/app/server"]
