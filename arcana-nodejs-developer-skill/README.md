# Node.js Developer Skill

Professional Node.js/Express/TypeScript development skill based on [Arcana Cloud Node.js](https://github.com/jrjohn/arcana-cloud-nodejs) enterprise architecture.

## Architecture Rating: 9.5/10

## Key Features

- **Clean Architecture**: Three-layer separation (Controller → Service → Repository)
- **Dual Protocol**: REST + gRPC support with 1.80x performance gain
- **Type Safety**: Full TypeScript with strict mode
- **Dependency Injection**: InversifyJS for IoC
- **ORM**: Prisma with migrations
- **Testing**: Vitest with 538+ tests (90% coverage)
- **Event-Driven**: Domain events with Redis pub/sub

## Quick Start

```bash
# Clone template
git clone https://github.com/jrjohn/arcana-cloud-nodejs.git my-project
cd my-project

# Initialize
rm -rf .git && git init
npm install
npm run prisma:generate

# Verify
npm test
npm run dev
```

## Documentation Structure

- `SKILL.md` - Main skill reference (loaded by Claude)
- `patterns.md` - Design patterns and best practices
- `examples.md` - Complete code examples
- `checklists/production-ready.md` - Pre-release checklist
- `verification/commands.md` - Diagnostic commands

## Performance Benchmarks

| Protocol | Latency | Throughput | Use Case |
|----------|---------|------------|----------|
| Direct | ~0ms | Maximum | Monolithic |
| gRPC | ~0.3ms | 1.80x vs HTTP | Layered/K8s |
| HTTP/JSON | ~1ms | Baseline | External APIs |

## Tech Stack

| Category | Technology |
|----------|------------|
| Runtime | Node.js 22+ |
| Language | TypeScript 5.7+ |
| Framework | Express.js 5.x |
| ORM | Prisma 6.x |
| DI | InversifyJS 7.x |
| RPC | gRPC 1.12+ |
| Testing | Vitest 2.x |
| Validation | Zod 3.x |
| Database | MySQL 8.0+ |
| Cache | Redis 7.0+ |

## License

MIT
