# Embedded Firmware CI/CD Patterns

> DevOps Skill Reference — ESP32 + STM32

## Overview

Embedded firmware CI/CD differs fundamentally from server/web application pipelines:
- **No Docker deploy** — firmware runs on bare metal, not in containers
- **Docker as build env only** — reproducible cross-compilation
- **Physical deployment** — USB/JTAG/SWD flash or OTA updates
- **No SonarQube** — use cppcheck + clang-tidy instead

---

## Build Environment

### ESP32 (ESP-IDF)

| Aspect | Detail |
|--------|--------|
| Docker Image | `espressif/idf:v5.4.1` (~3GB, cached after first pull) |
| Build System | CMake (via `idf.py`) |
| Toolchain | xtensa-esp32-elf-gcc (bundled) |
| Output | `.bin` (app + bootloader + partition table) |
| Config | `sdkconfig` (menuconfig) |

```bash
# Recommended: docker pull + docker compose (CI pipeline)
docker pull espressif/idf:v5.4.1
docker compose run --rm esp32-build

# docker-compose.yml:
# services:
#   esp32-build:
#     image: espressif/idf:v5.4.1
#     working_dir: /project
#     environment:
#       - HOME=/tmp
#     volumes:
#       - .:/project
#     command: idf.py set-target esp32 build

# Alternative: direct build (requires IDF installed)
idf.py set-target esp32    # or esp32s2, esp32s3, esp32c3, esp32c6, esp32h2
idf.py build
```

> **Note**: The espressif/idf image is ~3GB. Using `docker pull` + `docker compose`
> caches the image after the first pull. The `docker build` approach (Dockerfile)
> is available but slower for CI because it re-pulls on context changes.

### STM32 (ARM GCC)

| Aspect | Detail |
|--------|--------|
| Docker Image | `ubuntu:24.04` + gcc-arm-none-eabi |
| Build System | CMake + Make |
| Toolchain | arm-none-eabi-gcc |
| Output | `.bin` / `.hex` / `.elf` |
| Config | CMakeLists.txt + linker script |

```bash
# Build commands
mkdir build && cd build
cmake -DCMAKE_TOOLCHAIN_FILE=../cmake/arm-none-eabi.cmake -DCMAKE_BUILD_TYPE=Release ..
make -j$(nproc)
```

> **Important**: The CMake toolchain file (`arm-none-eabi.cmake`) must include
> `set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)` to prevent CMake from
> failing on the compiler test (arm-none-eabi-gcc cannot link executables
> without a linker script and startup code).

---

## Testing Strategy

### Unit Testing

| Framework | Platform | Runner |
|-----------|----------|--------|
| Unity (ThrowTheSwitch) | Both | Host or QEMU |
| ESP-IDF unity | ESP32 | Device or QEMU |
| CTest | STM32 | Host (native build) |

### Static Analysis

| Tool | Purpose | Integration |
|------|---------|-------------|
| cppcheck | General C/C++ analysis | CLI, CI pipeline |
| clang-tidy | Linting + modernization | CLI, CI pipeline |
| MISRA C checker | Safety compliance | Commercial tools |
| Coverity | Deep static analysis | Commercial, free for OSS |

### QEMU Emulation (ESP32)

```bash
# Run tests in QEMU (no physical device required)
idf.py set-target esp32
idf.py build
idf.py qemu monitor
```

---

## Deployment Methods

### ESP32

| Method | Use Case | Tool |
|--------|----------|------|
| USB/Serial | Development, initial flash | `esptool.py` |
| OTA (HTTP) | Field updates | ESP-IDF OTA component |
| OTA (HTTPS) | Secure field updates | ESP-IDF OTA + TLS |
| OTA (MQTT) | IoT fleet management | AWS IoT / Azure IoT |

```bash
# USB flash
esptool.py --port /dev/ttyUSB0 --baud 460800 \
    write_flash -z \
    0x1000 bootloader.bin \
    0x8000 partition-table.bin \
    0x10000 app.bin

# OTA via HTTP endpoint
curl -X POST http://<device-ip>/ota -F "firmware=@app.bin"
```

### STM32

| Method | Use Case | Tool |
|--------|----------|------|
| ST-Link | Development | `st-flash` |
| J-Link | Development + production | `JLinkExe` |
| OpenOCD | Flexible (multiple probes) | `openocd` |
| SWD | Low-level debug | Hardware debugger |
| DFU (USB) | Field updates (USB boot) | `dfu-util` |
| OTA (custom) | Wireless updates | Application-specific |

```bash
# OpenOCD flash
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg \
    -c "program firmware.bin verify reset exit 0x08000000"

# ST-Link flash
st-flash write firmware.bin 0x08000000

# J-Link flash (via command script)
JLinkExe -device STM32F407VG -if SWD -speed 4000 -CommanderScript flash.jlink
```

---

## Firmware Signing & Security

### ESP32 Secure Boot

| Feature | ESP-IDF Support |
|---------|----------------|
| Secure Boot v2 | `CONFIG_SECURE_BOOT_V2_ENABLED` |
| Flash Encryption | `CONFIG_SECURE_FLASH_ENC_ENABLED` |
| Signed OTA | `espsecure.py sign_data` |
| Key storage | eFuse (one-time programmable) |

```bash
# Sign firmware
espsecure.py sign_data --keyfile signing_key.pem --version 2 --output signed.bin app.bin
```

### STM32 Security

| Feature | Tool |
|---------|------|
| Code signing | OpenSSL / STM32 Secure Boot |
| Read-out protection (RDP) | STM32CubeProgrammer |
| Secure firmware update | SBSFU (STM32 Secure Boot & Firmware Update) |
| Hardware crypto | STM32 HAL crypto library |

```bash
# Sign with OpenSSL
openssl dgst -sha256 -sign private_key.pem -out firmware.sig firmware.bin

# Verify signature
openssl dgst -sha256 -verify public_key.pem -signature firmware.sig firmware.bin
```

---

## CI/CD Pipeline Pattern

```
ESP32 (docker pull + compose):
┌─────────────┐    ┌───────────────────────┐    ┌────────────────┐
│  Git Push    │ →  │  docker pull +        │ →  │  Copy .bin      │
│              │    │  compose run idf.py   │    │  (already host) │
└─────────────┘    └───────────────────────┘    └────────────────┘

STM32 (docker build):
┌─────────────┐    ┌───────────────────────┐    ┌────────────────┐
│  Git Push    │ →  │  docker build         │ →  │  docker cp      │
│              │    │  (Dockerfile.stm32)   │    │  /artifacts/    │
└─────────────┘    └───────────────────────┘    └────────────────┘

Common stages:
                                                        ↓
┌─────────────┐    ┌──────────────────┐    ┌────────────────┐
│  Archive    │ ←  │  Static Analysis  │ ←  │  Unit Tests     │
└─────────────┘    └──────────────────┘    └────────────────┘
       ↓
┌─────────────┐    ┌──────────────────┐
│  Sign       │ →  │  OTA / Storage    │
└─────────────┘    └──────────────────┘
```

### Key Differences from Server CI/CD

| Aspect | Server/Web | Embedded Firmware |
|--------|-----------|-------------------|
| Build output | Docker image | `.bin` / `.hex` / `.elf` |
| Docker role | Build + Runtime | Build only |
| Deploy method | Container orchestration | Flash / OTA |
| Registry | Docker Registry | Artifact storage (Jenkins/Nexus) |
| Quality tool | SonarQube | cppcheck + clang-tidy |
| Test runner | Jest/JUnit/pytest | Unity / CTest / QEMU |
| Rollback | Previous image | Previous firmware version |
| Signing | Docker Content Trust | Firmware signing (RSA/ECDSA) |

---

## OTA Update Architecture

### Simple HTTP OTA (ESP32)

```
┌─────────┐     ┌──────────────┐     ┌──────────┐
│ Jenkins  │ →   │  OTA Server   │ ←   │  Device   │
│ (build)  │     │  (HTTP/S3)    │     │  (poll)   │
└─────────┘     └──────────────┘     └──────────┘
```

### Fleet OTA (IoT Platform)

```
┌─────────┐     ┌──────────────┐     ┌──────────┐
│ Jenkins  │ →   │  IoT Platform  │ →   │  Devices  │
│ (build)  │     │  (AWS/Azure)   │     │  (push)   │
└─────────┘     └──────────────┘     └──────────┘
```

---

## Image Size & Resource Thresholds

| Platform | Flash Warning | Flash Critical | RAM Budget |
|----------|--------------|----------------|------------|
| ESP32 | > 1MB | > 3MB | 520KB total |
| ESP32-S3 | > 2MB | > 8MB | 512KB total |
| STM32F4 | > 512KB | > 1MB | 192KB total |
| STM32H7 | > 1MB | > 2MB | 1MB total |

---

## Toolchain Version Matrix

| Tool | Recommended Version | Notes |
|------|-------------------|-------|
| ESP-IDF | v5.5.x | LTS, production recommended |
| arm-none-eabi-gcc | 13.x | From ARM developer site |
| CMake | 3.28+ | Required by ESP-IDF v5.x |
| OpenOCD | 0.12+ | STM32 support |
| esptool.py | 4.x | Bundled with ESP-IDF |
| cppcheck | 2.x | Static analysis |
