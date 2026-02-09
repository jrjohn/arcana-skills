# Verification Commands Reference

All ESP-IDF build, flash, monitor, and diagnostic commands.

## Build Commands

```bash
# Full build
idf.py build

# Clean build
idf.py fullclean && idf.py build

# Build with verbose output
idf.py build -v

# Check component sizes
idf.py size-components

# Check total firmware size
idf.py size

# Set target (first time only)
idf.py set-target esp32s3

# Configure menuconfig
idf.py menuconfig
```

## Flash & Monitor Commands

```bash
# Flash firmware (auto-detect port)
idf.py flash

# Flash to specific port
idf.py -p /dev/ttyUSB0 flash

# Flash and immediately monitor
idf.py -p /dev/ttyUSB0 flash monitor

# Monitor only (serial output)
idf.py -p /dev/ttyUSB0 monitor

# Flash at higher baud rate
idf.py -p /dev/ttyUSB0 -b 921600 flash

# Erase flash completely
idf.py -p /dev/ttyUSB0 erase-flash

# Flash specific partition
idf.py -p /dev/ttyUSB0 partition-table-flash
```

## Memory Verification

```bash
# Check DRAM/IRAM/Flash usage
idf.py size 2>&1 | grep -E "DRAM|IRAM|Flash|Total"

# Per-component size breakdown
idf.py size-components 2>&1 | head -30

# Check DRAM usage vs budget (must be < 267KB = 80% of 334KB)
idf.py size 2>&1 | grep "DRAM"

# Runtime heap check (in monitor output)
# Look for: "Free DRAM: XXXXX bytes"
# Look for: "Free PSRAM: XXXXX bytes"
```

## Code Quality Checks

```bash
# Check for unencrypted command sends
grep -rn "send\|write" components/CommandService/src/ | grep -v "encrypt\|cipher\|tag\|nonce"

# Check for unchecked ESP-IDF calls
grep -rn "esp_ble_\|esp_wifi_\|esp_mqtt_" components/ main/ | grep -v "ESP_ERROR_CHECK\|ESP_RETURN_ON_ERROR\|err\|ret"

# Check nanopb max_size constraints
grep -rn "max_size" components/CommandService/proto/*.options

# Check for hardcoded secrets
grep -rn "password.*=.*\"\|secret.*=.*\"\|key.*=.*{0x" main/ components/

# Check for heap allocation in ISR context
grep -rn "malloc\|calloc\|new " components/ main/ | grep -i "isr\|interrupt"

# Check for std::string/vector in DRAM paths
grep -rn "std::string\|std::vector" components/ | grep -v "test\|example"

# Check task stack sizes
grep -rn "xTaskCreate\|xTaskCreatePinnedToCore" main/ components/ | grep -oE "[0-9]+"

# Check watchdog feeds
grep -rn "esp_task_wdt_reset\|esp_task_wdt_add" main/ components/
```

## BLE Verification

```bash
# Check GATT attribute table completeness
grep -rn "IDX_" components/BleService/ | grep -c "enum"
grep -rn "gatt_db\[" components/BleService/ | grep -c "ESP_GATT"

# Check advertising restart after disconnect
grep -rn "ESP_GATTS_DISCONNECT_EVT" -A5 components/BleService/

# Check MTU handling
grep -rn "ESP_GATTS_MTU_EVT\|getMtu" components/BleService/

# Check encrypted write permission
grep -rn "PERM_WRITE_ENCRYPTED" components/BleService/
```

## Security Verification

```bash
# Verify ECDH is ephemeral (no key storage)
grep -rn "nvs_set.*priv\|nvs_set.*key" components/CommandService/ | grep -v "session\|psk"

# Verify nonce counter increment
grep -rn "nonce_counter++" components/CommandService/

# Verify key zeroing on destroy
grep -rn "mbedtls_platform_zeroize\|memset.*key.*0" components/CommandService/

# Verify session limit
grep -rn "kMaxSessions\|max_sessions" components/CommandService/
```

## OTA Verification

```bash
# Verify dual OTA partitions
grep -c "ota_" partitions.csv

# Check OTA partition sizes
grep "ota_" partitions.csv

# Verify app fits in OTA partition
idf.py size 2>&1 | grep "Total image size"
```

## Pre-PR Verification (All-in-One)

```bash
echo "=== PRE-PR VERIFICATION ===" && \
echo "1. Build..." && \
idf.py build 2>&1 | tail -5 && \
echo "2. Size..." && \
idf.py size 2>&1 | grep -E "DRAM|Total" && \
echo "3. Secrets..." && \
(grep -rqn "password.*=.*\"\|key.*=.*{0x" main/ components/ && \
  echo "WARN: Potential secrets" || echo "PASS") && \
echo "4. Error handling..." && \
UNCHECKED=$(grep -rn "esp_ble_\|esp_wifi_" components/ main/ | \
  grep -cv "ESP_ERROR_CHECK\|ESP_RETURN_ON_ERROR\|err\|ret") && \
echo "Unchecked ESP calls: $UNCHECKED" && \
echo "5. nanopb bounds..." && \
grep -c "max_size" components/CommandService/proto/*.options 2>/dev/null && \
echo "=== VERIFICATION COMPLETE ==="
```

## Core Dump Analysis

```bash
# Read core dump from flash
idf.py coredump-info -p /dev/ttyUSB0

# Detailed core dump with backtrace
idf.py coredump-debug -p /dev/ttyUSB0

# Save core dump to file
espcoredump.py info_corefile -t b64 -c <base64_dump> build/arcana-embedded-esp32.elf
```
