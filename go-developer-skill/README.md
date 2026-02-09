# Go Developer Skill

Professional Go development skill based on [Arcana Cloud Go](https://github.com/jrjohn/arcana-cloud-go) enterprise architecture.

## Architecture Rating: 8.60/10

## Key Features

- **Clean Architecture**: Three-layer separation (Controller -> Service -> Repository/DAO)
- **Dual Protocol**: REST (Gin) + gRPC support with 1.80x performance gain
- **Multi-Database**: MySQL, PostgreSQL, MongoDB via GORM DAO layer
- **Dependency Injection**: Uber fx for IoC
- **Configuration**: Viper with YAML, env, and flag support
- **Logging**: Structured logging with zap
- **Testing**: 428+ tests with testify
- **Plugin System**: Extensible plugin architecture
- **Background Jobs**: Built-in job scheduler and workers
- **SSR Engine**: Server-side rendering support

## Quick Start

```bash
# Clone template
git clone https://github.com/jrjohn/arcana-cloud-go.git my-project
cd my-project

# Initialize
rm -rf .git && git init
go mod tidy

# Verify
go test ./...
go run ./cmd/server/
```

## Documentation Structure

- `SKILL.md` - Main skill reference (loaded by Claude)
- `patterns.md` - Design patterns and best practices
- `examples.md` - Complete code examples
- `reference.md` - Technical reference (config, deployment, APIs)
- `checklists/production-ready.md` - Pre-release checklist
- `verification/commands.md` - Diagnostic commands
- `patterns/service-layer.md` - Service layer deep dive

## Performance Benchmarks

| Protocol | Latency | Throughput | Use Case |
|----------|---------|------------|----------|
| Direct | ~0ms | 60K ops/sec | Monolithic |
| gRPC | ~0.3ms | 1.80x vs HTTP | Layered/K8s |
| HTTP/JSON | ~1ms | Baseline | External APIs |

## Tech Stack

| Category | Technology |
|----------|------------|
| Language | Go 1.23+ |
| REST | Gin 1.10+ |
| RPC | gRPC 1.60+ |
| ORM | GORM 2.x |
| DI | fx (Uber) 1.x |
| Config | Viper 1.x |
| Logging | zap 1.x |
| Auth | golang-jwt v5 |
| Databases | MySQL 8.0+, PostgreSQL 15+, MongoDB 7.0+ |
| Cache | Redis 7.0+ |
| Testing | testify 1.9+ |

## License

MIT
