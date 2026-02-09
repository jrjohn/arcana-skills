# Rust Developer Skill

Professional Rust microservices development skill based on [Arcana Cloud Rust](https://github.com/jrjohn/arcana-cloud-rust) enterprise architecture.

## Architecture Rating: 8.95/10

## Key Features

- **Clean Architecture**: Three-layer separation (Handler -> Service -> Repository)
- **Dual Protocol**: REST (Axum 0.7 on :8080) + gRPC (Tonic 0.12 on :9090) with 2.1x gRPC speedup
- **Type Safety**: Rust ownership system + trait-based interfaces
- **WASM Plugins**: Hot-loadable plugin system via Wasmtime 27
- **Distributed Job Queue**: Redis-backed with 4-level priority (Critical/High/Normal/Low)
- **Resilience**: Circuit breaker, retry with exponential backoff, rate limiting
- **Security**: JWT + Argon2 + RBAC + mTLS
- **Observability**: Distributed tracing + Prometheus metrics
- **Testing**: 150+ tests (80% coverage)

## Quick Start

```bash
# Clone template
git clone https://github.com/jrjohn/arcana-cloud-rust.git my-project
cd my-project

# Initialize
rm -rf .git && git init
cargo build

# Verify
cargo test
cargo clippy -- -D warnings
```

## Documentation Structure

- `SKILL.md` - Main skill reference (loaded by Claude)
- `patterns.md` - Rust design patterns and best practices
- `examples.md` - Complete Rust code examples
- `reference.md` - Technical reference and API documentation
- `checklists/production-ready.md` - Pre-release checklist
- `verification/commands.md` - Diagnostic commands
- `patterns/service-layer.md` - Service layer deep dive

## Performance Benchmarks

| Protocol | Latency | Throughput | Use Case |
|----------|---------|------------|----------|
| Direct call | ~0.5ms | Maximum | Monolithic |
| gRPC (Tonic) | ~1.2ms | 2.1x vs HTTP | Internal services |
| HTTP/JSON (Axum) | ~2.5ms | Baseline | External APIs |

## Tech Stack

| Category | Technology |
|----------|------------|
| Language | Rust 1.75+ |
| Runtime | Tokio 1.43+ |
| REST Framework | Axum 0.7 |
| gRPC Framework | Tonic 0.12 |
| WASM Runtime | Wasmtime 27 |
| ORM/SQL | SQLx 0.8+ |
| Cache | Redis 7.0+ |
| Auth | jsonwebtoken + argon2 |
| Tracing | tracing + OpenTelemetry |
| Metrics | metrics + Prometheus |
| Testing | mockall + tokio::test |
| Database | MySQL 8.0+ / PostgreSQL 15+ |

## License

MIT
