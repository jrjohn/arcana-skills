# STM32 Developer Skill

Professional STM32/FreeRTOS/C++14 embedded development skill based on [Arcana Embedded STM32](https://github.com/jrjohn/arcana-embedded-stm32) production architecture.

## Architecture Rating: 9.1/10

## Key Features

- **Observable Pattern**: Type-safe event-driven architecture for embedded C++14
- **Zero-Copy Model Passing**: Models passed by const reference to observers
- **Dual-Priority Queuing**: High (4 items) and Normal (8 items) priority queues
- **Static Allocation**: No malloc/new at runtime, all objects statically allocated
- **ISR-Safe Publishing**: `publishFromISR` / `publishHighPriorityFromISR` variants
- **FreeRTOS Integration**: Task-based dispatcher with configurable priorities
- **Memory Efficient**: RAM 4,356B/8,192B (53.2%), Flash 16,968B/65,536B (25.9%)

## Quick Start

```bash
# Clone template
git clone https://github.com/jrjohn/arcana-embedded-stm32.git my-project
cd my-project

# Reinitialize
rm -rf .git && git init

# Open in STM32CubeIDE, build, and flash
# Verify memory usage:
arm-none-eabi-size build/*.elf
```

## Documentation Structure

- `SKILL.md` - Main skill reference (loaded by Claude)
- `patterns.md` - Embedded design patterns (Observable, Zero-Copy, Static Allocation)
- `examples.md` - Complete C++14 embedded code examples
- `reference.md` - API reference, memory map, FreeRTOS configuration
- `checklists/production-ready.md` - Pre-release embedded checklist
- `verification/commands.md` - Diagnostic and verification commands
- `patterns/observable-pattern.md` - Deep dive into Observable pattern for STM32

## Performance Benchmarks

| Metric | Value | Context |
|--------|-------|---------|
| Event latency | ~22us | Normal priority, single observer |
| High-priority latency | ~12us | Pre-empts normal processing |
| Context switch | ~10us | FreeRTOS task switch |
| ISR publish time | ~2us | Queue enqueue from interrupt |
| CPU usage | < 1% | 3 services running |
| Queue throughput | ~45K evt/sec | Normal priority, sustained |

## Tech Stack

| Category | Technology |
|----------|------------|
| MCU | STM32F051C8 (Cortex-M0, 48MHz) |
| RTOS | FreeRTOS 10.4.6+ |
| Language | C++14 (GCC 10.3+) |
| IDE | STM32CubeIDE 1.13+ |
| HAL | STM32 HAL 1.11.x |
| Toolchain | GNU ARM Embedded (arm-none-eabi) |
| Debug | OpenOCD / ST-Link |

## License

MIT
