# ESP32 Developer Skill - Technical Reference

## Table of Contents
1. [Project Structure](#project-structure)
2. [Three-Layer Architecture](#three-layer-architecture)
3. [Arcana Frame Protocol](#arcana-frame-protocol)
4. [Command Table](#command-table)
5. [BLE GATT Service Table](#ble-gatt-service-table)
6. [Cryptographic Parameters](#cryptographic-parameters)
7. [MQTT5 Topic Structure](#mqtt5-topic-structure)
8. [Memory Map](#memory-map)
9. [Kconfig Options](#kconfig-options)
10. [Partition Table](#partition-table)
11. [FreeRTOS Task Table](#freertos-task-table)
12. [Error Codes](#error-codes)
13. [ESP-IDF API Quick Reference](#esp-idf-api-quick-reference)

---

## Project Structure

```
arcana-embedded-esp32/
├── CMakeLists.txt
├── main/
│   ├── CMakeLists.txt
│   ├── app_main.cpp              # Entry: NVS, WiFi, BLE, coex init
│   ├── Kconfig.projbuild         # Project Kconfig menu
│   └── mqtt_client.cpp           # MQTT5 client setup + event handler
├── components/
│   ├── ObservableSensor/
│   │   ├── CMakeLists.txt
│   │   ├── include/
│   │   │   ├── Observable.h      # Observable<T,N>
│   │   │   ├── StaticObservable.h
│   │   │   └── EventQueue.h      # FreeRTOS queue wrapper
│   │   └── src/
│   │       └── observable_sensor.cpp
│   ├── BleService/
│   │   ├── CMakeLists.txt
│   │   ├── include/
│   │   │   ├── BleService.h      # Facade
│   │   │   ├── GapManager.h      # GAP advertising/scanning
│   │   │   ├── GattServer.h      # GATT Server (peripheral)
│   │   │   ├── GattClient.h      # GATT Client (central)
│   │   │   └── ble_uuids.h       # 128-bit UUID definitions
│   │   └── src/
│   │       ├── ble_service.cpp
│   │       ├── gap_manager.cpp
│   │       ├── gatt_server.cpp
│   │       └── gatt_client.cpp
│   └── CommandService/
│       ├── CMakeLists.txt
│       ├── include/
│       │   ├── CommandDefs.h      # Enums, structs
│       │   ├── CommandDispatcher.h
│       │   ├── CommandFactory.h   # Handler registration
│       │   ├── CommandCodec.h     # nanopb encode/decode
│       │   ├── ArcanaFrame.h      # Frame build/parse + CRC-16
│       │   ├── CryptoEngine.h     # AES-256-CCM
│       │   ├── SessionManager.h   # Session lifecycle
│       │   └── KeyExchange.h      # ECDH P-256 + HKDF
│       ├── src/
│       │   ├── command_dispatcher.cpp
│       │   ├── command_factory.cpp
│       │   ├── command_codec.cpp
│       │   ├── arcana_frame.cpp
│       │   ├── crypto_engine.cpp
│       │   ├── session_manager.cpp
│       │   └── key_exchange.cpp
│       └── proto/
│           ├── command.proto      # nanopb definitions
│           └── command.options    # Field size constraints
├── partitions.csv
├── sdkconfig.defaults
└── pytest/
    ├── test_frame.py
    ├── test_codec.py
    └── test_crypto.py
```

---

## Three-Layer Architecture

### Layer Dependencies

| Layer | Depends On | Provides |
|-------|-----------|----------|
| Application | Protocol, System | Business logic, sensor mgmt, command handling |
| Protocol | System | Serialization, encryption, framing, transport |
| System | Hardware | FreeRTOS, WiFi, BLE controller, flash, PSRAM |

### Component Dependency Graph

```
ObservableSensor  -->  freertos
BleService        -->  bt, esp_event, nvs_flash
CommandService    -->  bt, mbedtls, nvs_flash, esp_event, ObservableSensor, BleService
main              -->  all components + wifi, mqtt
```

---

## Arcana Frame Protocol

### Wire Format

```
Byte:  0     1     2     3     4     5     6     7..N-2   N-1   N
     +-----+-----+-----+-----+-----+-----+-----+--------+-----+-----+
     | 0xAR| 0xCA| Ver | Flag| SID | LenL| LenH| Payload| CRCL| CRCH|
     +-----+-----+-----+-----+-----+-----+-----+--------+-----+-----+
     |<--- Magic -->|                     |<--LE-->|       |<--LE-->|
```

### Field Specification

| Field | Offset | Bytes | Type | Description |
|-------|--------|-------|------|-------------|
| Magic | 0 | 2 | uint16 | `0xAR 0xCA` sync marker |
| Version | 2 | 1 | uint8 | Protocol version (`0x01`) |
| Flags | 3 | 1 | bitfield | See Flags table below |
| StreamID | 4 | 1 | uint8 | Multiplexing stream identifier |
| Length | 5 | 2 | uint16 LE | Payload byte count (max 65535) |
| Payload | 7 | N | bytes | Encrypted nanopb data |
| CRC-16 | 7+N | 2 | uint16 LE | CRC-16/CCITT over bytes 0..(6+N) |

### Flags Bitfield

| Bit | Mask | Name | Description |
|-----|------|------|-------------|
| 0 | `0x01` | ENCRYPTED | Payload is AES-256-CCM encrypted |
| 1 | `0x02` | COMPRESSED | Payload is zlib-compressed (pre-encryption) |
| 2 | `0x04` | FRAGMENTED | Multi-frame message fragment |
| 3 | `0x08` | ACK_REQUIRED | Sender expects ACK frame |
| 4-7 | | Reserved | Must be zero |

### CRC-16/CCITT Parameters

| Parameter | Value |
|-----------|-------|
| Polynomial | 0x1021 |
| Initial value | 0xFFFF |
| Input reflected | No |
| Output reflected | No |
| Final XOR | 0x0000 |
| Coverage | Bytes 0 through (6 + payload_len) |

### Overhead Calculation

| Component | Bytes |
|-----------|-------|
| Header (Magic + Ver + Flags + SID + Length) | 7 |
| CRC-16 | 2 |
| **Total frame overhead** | **9** |
| AES-256-CCM auth tag (in payload) | 8 |
| **Total protocol overhead** | **17** |

---

## Command Table

### Cluster 0x00: System

| Cmd ID | Name | Direction | Payload | Response |
|--------|------|-----------|---------|----------|
| 0x00 | Ping | Bidir | Empty | Echo (timestamp) |
| 0x01 | Reset | To Device | Reset type (1B) | ACK |
| 0x02 | Info | To Device | Empty | FW version, chip ID, uptime |
| 0x03 | DiagHeap | To Device | Empty | DRAM/PSRAM free/min/largest |
| 0x04 | TaskList | To Device | Empty | Task names, stacks, priorities |

### Cluster 0x01: Sensor

| Cmd ID | Name | Direction | Payload | Response |
|--------|------|-----------|---------|----------|
| 0x00 | Read | To Device | Sensor ID (1B) | Sensor value (float32) |
| 0x01 | Subscribe | To Device | Sensor ID, interval_ms | ACK + periodic notify |
| 0x02 | Calibrate | To Device | Sensor ID, offset (float32) | ACK |
| 0x03 | Threshold | To Device | Sensor ID, high/low (float32) | ACK |

### Cluster 0x02: BLE

| Cmd ID | Name | Direction | Payload | Response |
|--------|------|-----------|---------|----------|
| 0x00 | Scan | To Device | Duration (uint16), filter | Scan result list |
| 0x01 | Connect | To Device | BD_ADDR (6B) | Connection status |
| 0x02 | Disconnect | To Device | Conn ID (2B) | ACK |
| 0x03 | ParamUpdate | To Device | Conn ID, min/max interval | ACK |

### Cluster 0x03: MQTT

| Cmd ID | Name | Direction | Payload | Response |
|--------|------|-----------|---------|----------|
| 0x00 | Publish | To Device | Topic + payload | Msg ID |
| 0x01 | Subscribe | To Device | Topic + QoS | ACK |
| 0x02 | Unsubscribe | To Device | Topic | ACK |
| 0x03 | Status | To Device | Empty | Connected, broker, stats |

### Cluster 0x04: Security

| Cmd ID | Name | Direction | Payload | Response |
|--------|------|-----------|---------|----------|
| 0x00 | KeyExchange | Bidir | Public key (64B) | Public key (64B) + session_id (4B) |
| 0x01 | SessionInfo | To Device | Session ID (4B) | Nonce counter, created_at |
| 0x02 | RotateKey | Bidir | New public key (64B) | New public key (64B) |
| 0x03 | Wipe | To Device | Confirmation code | ACK (destroys all sessions) |

---

## BLE GATT Service Table

### Arcana Command Service (Primary)

| Index | Type | UUID | Permissions | Properties |
|-------|------|------|-------------|------------|
| IDX_SVC | Service Decl | 0x2800 | Read | Primary Service |
| IDX_CMD_CHAR | Char Decl | 0x2803 | Read | Write |
| IDX_CMD_VAL | Char Value | 6E400002-... (128-bit) | Write Encrypted | - |
| IDX_RSP_CHAR | Char Decl | 0x2803 | Read | Notify |
| IDX_RSP_VAL | Char Value | 6E400003-... (128-bit) | Read | - |
| IDX_RSP_CCC | CCCD | 0x2902 | Read, Write | - |
| IDX_SENSOR_CHAR | Char Decl | 0x2803 | Read | Notify |
| IDX_SENSOR_VAL | Char Value | 6E400004-... (128-bit) | Read | - |
| IDX_SENSOR_CCC | CCCD | 0x2902 | Read, Write | - |

### UUID Definitions

| Name | UUID (128-bit) | Purpose |
|------|---------------|---------|
| Arcana Service | `6E400001-B5A3-F393-E0A9-E50E24DCCA9E` | Primary service |
| Command Write | `6E400002-B5A3-F393-E0A9-E50E24DCCA9E` | Write encrypted frames |
| Response Notify | `6E400003-B5A3-F393-E0A9-E50E24DCCA9E` | Response notifications |
| Sensor Data | `6E400004-B5A3-F393-E0A9-E50E24DCCA9E` | Sensor data notifications |

### GAP Advertising Data

| Field | Value | Description |
|-------|-------|-------------|
| Flags | 0x06 | General Discoverable + BR/EDR Not Supported |
| Complete Name | "Arcana-XXXX" | Last 4 hex digits of MAC |
| Service UUID | 6E400001-... | Arcana service |
| TX Power | 0 dBm | Default |
| Manufacturer Data | 2-byte company ID + version | Optional |

---

## Cryptographic Parameters

### AES-256-CCM

| Parameter | Value |
|-----------|-------|
| Algorithm | AES-CCM (RFC 3610) |
| Key size | 256 bits (32 bytes) |
| Nonce size | 13 bytes |
| Auth tag size | 8 bytes |
| Nonce format | `[session_id:4B][counter:8B][0x00:1B]` |
| Counter | Monotonic uint64, incremented after each encrypt/decrypt |

### ECDH P-256

| Parameter | Value |
|-----------|-------|
| Curve | secp256r1 (NIST P-256) |
| Key type | Ephemeral (regenerated per connection) |
| Public key format | Uncompressed: X(32B) + Y(32B) = 64B |
| Shared secret | 32 bytes |

### HKDF-SHA256

| Parameter | Value |
|-----------|-------|
| Hash | SHA-256 |
| Salt | `session_id` (4 bytes) |
| Info | `"arcana-cmd-v1"` (ASCII) |
| Output | 32 bytes (AES-256 key) |

### Session Parameters

| Parameter | Value |
|-----------|-------|
| Max concurrent sessions | 4 |
| Session ID | 4-byte random (`esp_random()`) |
| Nonce counter initial | 0 |
| Key zeroing | `mbedtls_platform_zeroize()` on destroy |

---

## MQTT5 Topic Structure

| Topic Pattern | Direction | QoS | Retained | Description |
|--------------|-----------|-----|----------|-------------|
| `arcana/device/{id}/cmd` | Cloud->Device | 1 | No | Encrypted command frames |
| `arcana/device/{id}/rsp` | Device->Cloud | 1 | No | Encrypted response frames |
| `arcana/device/{id}/telemetry` | Device->Cloud | 0 | No | Periodic sensor JSON |
| `arcana/device/{id}/status` | Device->Cloud | 1 | Yes | LWT: online/offline |
| `arcana/device/{id}/ota` | Cloud->Device | 1 | No | OTA firmware URL |
| `arcana/fleet/broadcast` | Cloud->Devices | 1 | No | Fleet-wide commands |

### MQTT Connection Parameters

| Parameter | Value |
|-----------|-------|
| Protocol | MQTT v5.0 |
| Transport | TLS (port 8883) |
| Keep-alive | 120 seconds |
| Clean session | false (persistent subscriptions) |
| Reconnect timeout | 10,000 ms (exponential backoff) |
| Socket timeout | 5,000 ms |

---

## Memory Map

### ESP32-S3 N16R8 Resources

| Memory | Base Address | Size | Used | Free |
|--------|-------------|------|------|------|
| IRAM | 0x40370000 | 128 KB | ~96 KB | ~32 KB |
| DRAM | 0x3FC88000 | 334 KB | ~131 KB | ~203 KB |
| RTC FAST | 0x600FE000 | 8 KB | ~0 KB | ~8 KB |
| PSRAM | 0x3C000000 | 8 MB | ~512 KB | ~7.5 MB |
| Flash | - | 16 MB | ~1.34 MB | ~14.6 MB |

### Per-Component DRAM Allocation

| Component | Budget | Notes |
|-----------|--------|-------|
| FreeRTOS kernel | 20 KB | Task TCBs, queues, timers, semaphores |
| WiFi driver | 40 KB | TX/RX buffers, connection state |
| Bluedroid BLE | 45 KB | GAP + GATT Server + GATT Client + L2CAP |
| Crypto sessions (x4) | 8 KB | AES key (32B) + ECDH state per slot |
| nanopb buffers | 4 KB | Encode/decode scratch buffers |
| Command pipeline | 8 KB | Dispatcher map + factory + codec |
| Observable sensors | 4 KB | Observer callbacks + value storage |
| MQTT client | 12 KB | Connection + TX/RX buffers |
| Application code | 16 KB | Custom logic, task stacks (partial) |

### PSRAM Usage

| Allocation | Size | Purpose |
|-----------|------|---------|
| Work buffers | ~256 KB | Large payload processing |
| OTA staging | ~128 KB | Firmware download buffer |
| Log buffer | ~64 KB | Circular log for diagnostics |
| Available | ~7.5 MB | Application use |

---

## Kconfig Options

### BLE Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_BT_ENABLED` | y | Enable Bluetooth |
| `CONFIG_BT_BLUEDROID_ENABLED` | y | Use Bluedroid stack |
| `CONFIG_BT_GATTS_ENABLE` | y | GATT Server role |
| `CONFIG_BT_GATTC_ENABLE` | y | GATT Client role |
| `CONFIG_BT_BLE_SMP_ENABLE` | y | Security Manager Protocol |
| `CONFIG_BT_BLE_42_FEATURES_SUPPORTED` | y | BLE 4.2 features |
| `CONFIG_BT_BLE_50_FEATURES_SUPPORTED` | y | BLE 5.0 features |

### WiFi & Coexistence

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_ESP_WIFI_ENABLED` | y | Enable WiFi |
| `CONFIG_SW_COEXIST_ENABLE` | y | Software WiFi/BLE coexistence |

### Crypto (mbedTLS)

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_MBEDTLS_HARDWARE_AES` | y | Hardware AES acceleration |
| `CONFIG_MBEDTLS_AES_USE_INTERRUPT` | y | AES interrupt mode |
| `CONFIG_MBEDTLS_CCM_C` | y | AES-CCM cipher mode |
| `CONFIG_MBEDTLS_ECDH_C` | y | ECDH key agreement |
| `CONFIG_MBEDTLS_ECP_DP_SECP256R1_ENABLED` | y | P-256 curve |
| `CONFIG_MBEDTLS_HKDF_C` | y | HKDF key derivation |

### FreeRTOS

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_FREERTOS_HZ` | 1000 | Tick rate (1ms resolution) |
| `CONFIG_FREERTOS_UNICORE` | n | Dual-core SMP mode |

### PSRAM

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_SPIRAM` | y | Enable PSRAM |
| `CONFIG_SPIRAM_MODE_OCT` | y | Octal SPI PSRAM mode |
| `CONFIG_SPIRAM_SPEED_80M` | y | 80MHz PSRAM clock |

### MQTT

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_MQTT_PROTOCOL_5` | y | MQTT v5.0 protocol |
| `CONFIG_MQTT_TRANSPORT_SSL` | y | TLS transport |

### System

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_PARTITION_TABLE_CUSTOM` | y | Custom partition table |
| `CONFIG_ESP_COREDUMP_ENABLE_TO_FLASH` | y | Core dump to flash |
| `CONFIG_ESP_COREDUMP_DATA_FORMAT_ELF` | y | ELF format core dumps |
| `CONFIG_ESP_TASK_WDT_EN` | y | Task watchdog enabled |
| `CONFIG_ESP_TASK_WDT_TIMEOUT_S` | 10 | Watchdog timeout (seconds) |
| `CONFIG_COMPILER_OPTIMIZATION_PERF` | y | Performance optimization |

### Custom Project Kconfig

```
# main/Kconfig.projbuild
menu "Arcana Device Configuration"

    config DEVICE_ID
        string "Device ID"
        default "arcana-001"
        help
            Unique device identifier for MQTT topics.

    config WIFI_SSID
        string "WiFi SSID"
        default ""

    config WIFI_PASSWORD
        string "WiFi Password"
        default ""

    config MQTT_BROKER_URI
        string "MQTT Broker URI"
        default "mqtts://broker.example.com"

    config MQTT_USERNAME
        string "MQTT Username"
        default ""

    config MQTT_PASSWORD
        string "MQTT Password"
        default ""

    config SENSOR_POLL_INTERVAL_MS
        int "Sensor polling interval (ms)"
        default 1000
        range 100 60000

    config TEMP_ALARM_HIGH
        int "Temperature alarm threshold (C)"
        default 45
        range 0 100

endmenu
```

---

## Partition Table

### partitions.csv

| Name | Type | SubType | Offset | Size | Notes |
|------|------|---------|--------|------|-------|
| nvs | data | nvs | 0x9000 | 24 KB | Non-volatile storage |
| phy_init | data | phy | 0xF000 | 4 KB | PHY calibration data |
| otadata | data | ota | 0x10000 | 8 KB | OTA state tracking |
| ota_0 | app | ota_0 | 0x20000 | 1.75 MB | Primary firmware slot |
| ota_1 | app | ota_1 | 0x1E0000 | 1.75 MB | Secondary firmware slot |
| coredump | data | coredump | 0x3A0000 | 64 KB | Core dump storage |
| nvs_keys | data | nvs_keys | 0x3B0000 | 4 KB | NVS encryption keys |

### Flash Layout (16MB Total)

```
0x000000  +-------------------+
          | Bootloader (28KB) |
0x009000  +-------------------+
          | NVS (24KB)        |
0x00F000  +-------------------+
          | PHY Init (4KB)    |
0x010000  +-------------------+
          | OTA Data (8KB)    |
0x020000  +-------------------+
          | OTA_0 (1.75MB)    |  <-- Active firmware
0x1E0000  +-------------------+
          | OTA_1 (1.75MB)    |  <-- Update firmware
0x3A0000  +-------------------+
          | Core Dump (64KB)  |
0x3B0000  +-------------------+
          | NVS Keys (4KB)    |
0x3B1000  +-------------------+
          | Free (~4.7MB)     |
0xFFFFFF  +-------------------+
```

---

## FreeRTOS Task Table

| Task Name | Stack | Priority | Core | Purpose | Watchdog |
|-----------|-------|----------|------|---------|----------|
| crypto | 8192 B | 20 | 1 | AES-256-CCM + ECDH computation | Yes |
| ble | 4096 B | 19 | 0 | BLE event processing (GAP/GATT) | Yes |
| cmd | 4096 B | 18 | 1 | Command dispatch + codec | Yes |
| mqtt | 4096 B | 15 | 0 | MQTT5 client loop | Yes |
| sensor | 2048 B | 10 | 1 | Sensor polling + Observable update | Yes |
| main | 4096 B | 5 | 0 | Init + watchdog supervisor | No |
| IDLE0 | 1024 B | 0 | 0 | FreeRTOS idle (Core 0) | No |
| IDLE1 | 1024 B | 0 | 1 | FreeRTOS idle (Core 1) | No |

### Core Assignment Strategy

| Core 0 | Core 1 |
|--------|--------|
| BLE (radio processing) | Crypto (computation) |
| MQTT (network I/O) | Command dispatch |
| WiFi (radio processing) | Sensor polling |
| Main (init + supervisor) | |

---

## Error Codes

### CommandStatus

| Code | Value | Description |
|------|-------|-------------|
| kSuccess | 0x00 | Command executed successfully |
| kUnsupportedCluster | 0x01 | Unknown cluster ID |
| kUnsupportedCommand | 0x02 | Unknown command ID in cluster |
| kInvalidField | 0x03 | Payload field validation failed |
| kResourceExhausted | 0x04 | No memory, no session slot, queue full |
| kNotAuthorized | 0x05 | No active crypto session |
| kHardwareError | 0x06 | Sensor/peripheral hardware failure |
| kTimeout | 0x07 | Operation timed out |
| kCryptoError | 0x08 | Encryption/decryption failure |
| kSessionExpired | 0x09 | Session timed out or invalidated |

### ESP-IDF Common Error Codes

| Code | Constant | Typical Cause |
|------|----------|---------------|
| 0 | `ESP_OK` | Success |
| 0x101 | `ESP_ERR_NO_MEM` | Heap exhausted |
| 0x102 | `ESP_ERR_INVALID_ARG` | Bad parameter |
| 0x103 | `ESP_ERR_INVALID_STATE` | Wrong state for operation |
| 0x104 | `ESP_ERR_INVALID_SIZE` | Buffer too small |
| 0x105 | `ESP_ERR_NOT_FOUND` | Requested resource missing |
| 0x106 | `ESP_ERR_NOT_SUPPORTED` | Feature not enabled |
| 0x107 | `ESP_ERR_TIMEOUT` | Operation timed out |
| 0x108 | `ESP_ERR_INVALID_RESPONSE` | Bad response from peer |
| 0x109 | `ESP_ERR_INVALID_CRC` | CRC check failed |

---

## ESP-IDF API Quick Reference

### BLE (Bluedroid)

| Function | Purpose |
|----------|---------|
| `esp_ble_gap_start_advertising(&params)` | Start BLE advertising |
| `esp_ble_gap_stop_advertising()` | Stop advertising |
| `esp_ble_gap_update_conn_params(&params)` | Update connection params |
| `esp_ble_gap_set_scan_params(&params)` | Configure scanning |
| `esp_ble_gap_start_scanning(duration)` | Start scan |
| `esp_ble_gatts_register_callback(cb)` | Register GATTS callback |
| `esp_ble_gatts_app_register(app_id)` | Register GATTS application |
| `esp_ble_gatts_create_attr_tab(db, if, count, id)` | Create attribute table |
| `esp_ble_gatts_send_indicate(if, conn, handle, len, val, confirm)` | Send notification/indication |
| `esp_ble_gattc_register_callback(cb)` | Register GATTC callback |
| `esp_ble_gattc_open(if, addr, type, direct)` | Connect to remote server |

### WiFi

| Function | Purpose |
|----------|---------|
| `esp_wifi_init(&cfg)` | Initialize WiFi driver |
| `esp_wifi_set_mode(mode)` | Set STA/AP/STA+AP mode |
| `esp_wifi_set_config(if, &cfg)` | Set SSID/password |
| `esp_wifi_start()` | Start WiFi |
| `esp_wifi_connect()` | Connect to AP |

### Crypto (mbedTLS)

| Function | Purpose |
|----------|---------|
| `mbedtls_ccm_init(&ctx)` | Initialize CCM context |
| `mbedtls_ccm_setkey(&ctx, cipher, key, bits)` | Set AES key |
| `mbedtls_ccm_encrypt_and_tag(...)` | Encrypt + generate auth tag |
| `mbedtls_ccm_auth_decrypt(...)` | Decrypt + verify auth tag |
| `mbedtls_ecdh_setup(&ctx, group)` | Setup ECDH |
| `mbedtls_ecdh_gen_public(...)` | Generate keypair |
| `mbedtls_ecdh_calc_secret(...)` | Compute shared secret |
| `mbedtls_hkdf(md, salt, ikm, info, okm)` | Key derivation |
| `mbedtls_platform_zeroize(buf, len)` | Secure memory wipe |

### FreeRTOS

| Function | Purpose |
|----------|---------|
| `xTaskCreatePinnedToCore(fn, name, stack, param, prio, handle, core)` | Create pinned task |
| `xQueueCreate(depth, item_size)` | Create queue |
| `xQueueSend(q, item, timeout)` | Send to queue |
| `xQueueReceive(q, item, timeout)` | Receive from queue |
| `xSemaphoreCreateMutex()` | Create mutex |
| `xSemaphoreTake(s, timeout)` | Acquire mutex |
| `xSemaphoreGive(s)` | Release mutex |
| `uxTaskGetStackHighWaterMark(handle)` | Get minimum free stack |
| `esp_task_wdt_reset()` | Feed task watchdog |

### Heap

| Function | Purpose |
|----------|---------|
| `heap_caps_malloc(size, caps)` | Allocate with capabilities |
| `heap_caps_calloc(n, size, caps)` | Allocate zeroed |
| `heap_caps_free(ptr)` | Free allocation |
| `heap_caps_get_free_size(caps)` | Get free bytes |
| `heap_caps_get_minimum_free_size(caps)` | Get historical minimum |
| `heap_caps_get_largest_free_block(caps)` | Get largest contiguous block |

### Capability Flags

| Flag | Description |
|------|-------------|
| `MALLOC_CAP_8BIT` | Byte-addressable (DRAM + PSRAM) |
| `MALLOC_CAP_INTERNAL` | Internal SRAM only |
| `MALLOC_CAP_SPIRAM` | PSRAM only |
| `MALLOC_CAP_DMA` | DMA-capable memory |
| `MALLOC_CAP_EXEC` | Executable (IRAM) |
