# ESP32 Developer Skill

Professional ESP32-S3 IoT development skill based on [Arcana Embedded ESP32](https://github.com/jrjohn/arcana-embedded-esp32) production-ready IoT command platform.

## Version

**v1.0** - Initial Release
- Complete three-layer architecture (Application / Protocol / System)
- Observable sensor pattern with three variants
- BLE dual-role architecture (GATT Server + Client via Bluedroid)
- AES-256-CCM encryption with ECDH P-256 key exchange
- Arcana Frame Protocol (9B overhead, CRC-16 integrity)
- Command pipeline with Matter/ZCL-style dispatch
- MQTT5 integration with WiFi+BLE coexistence
- Memory budget and allocation rules

## Structure

```
esp32-developer-skill/
├── SKILL.md                           # Main skill file (core rules & architecture)
├── README.md                          # This file
├── examples.md                        # C++17 ESP-IDF code examples
├── patterns.md                        # IoT design patterns
├── reference.md                       # API reference & protocol specs
├── verification/
│   └── commands.md                    # ESP-IDF build/flash/monitor commands
├── patterns/
│   └── command-pipeline.md            # Command dispatch pattern deep dive
└── checklists/
    └── production-ready.md            # IoT production readiness checklist
```

## Priority Rules

| Priority | Rule | Description |
|----------|------|-------------|
| CRITICAL | Encryption Always On | All command payloads use AES-256-CCM |
| CRITICAL | ECDH Before Commands | Key exchange before encrypted commands |
| CRITICAL | Memory Budget | DRAM below 80% (267KB of 334KB) |
| CRITICAL | BLE Coexistence | WiFi+BLE use coexistence API |
| IMPORTANT | nanopb Bounds | All fields have max_size in .options |
| IMPORTANT | Error Propagation | All ESP-IDF calls check esp_err_t |
| RECOMMENDED | OTA Rollback | Anti-rollback counter in eFuse |

## Tech Stack

| Technology | Version |
|------------|---------|
| ESP-IDF | v5.5 |
| C++ | 17 |
| ESP32-S3 | N16R8 (512KB SRAM, 8MB PSRAM, 16MB Flash) |
| FreeRTOS | 10.5.1 (SMP dual-core) |
| Bluedroid | ESP-IDF built-in |
| mbedTLS | 3.x (AES-256-CCM, ECDH P-256, HKDF) |
| nanopb | 0.4.x |
| MQTT | v5.0 |

## Documentation Files

| File | Description |
|------|-------------|
| [SKILL.md](SKILL.md) | Core skill instructions, architecture, and rules |
| [examples.md](examples.md) | Complete C++17 code examples |
| [patterns.md](patterns.md) | IoT design patterns reference |
| [reference.md](reference.md) | API reference, frame protocol, Kconfig |
| [verification/commands.md](verification/commands.md) | Build, flash, and diagnostic commands |
| [patterns/command-pipeline.md](patterns/command-pipeline.md) | Command dispatch deep dive |
| [checklists/production-ready.md](checklists/production-ready.md) | Production & security checklists |

## When to Use This Skill

- ESP32-S3 firmware development with BLE and/or WiFi
- IoT command protocol design and implementation
- BLE GATT Server/Client development with Bluedroid
- Secure communication (AES-256-CCM + ECDH P-256)
- Observable sensor pattern implementation
- MQTT5 cloud integration
- Memory-constrained embedded development
- Code review for IoT security and reliability
