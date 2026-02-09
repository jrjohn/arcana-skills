# Production Readiness Checklist

## Pre-Release Checklist

### CRITICAL (Must Pass)

- [ ] **Build succeeds** - `idf.py build` completes without errors
- [ ] **Flash fits** - `idf.py size` confirms app < OTA partition (1.75MB)
- [ ] **DRAM under 80%** - `heap_caps_get_free_size(MALLOC_CAP_8BIT)` > 67KB
- [ ] **All commands encrypted** - No unencrypted command frames post-key-exchange
- [ ] **ECDH ephemeral** - New keypair generated per BLE connection
- [ ] **Nonce never reused** - Monotonic counter, new key on reconnect
- [ ] **Key material zeroed** - `mbedtls_platform_zeroize()` on session destroy
- [ ] **No plaintext secrets** - WiFi/MQTT credentials in NVS (not hardcoded)
- [ ] **Frame validation** - Magic, CRC-16, and Length checked before parse
- [ ] **Auth tag verified** - AES-256-CCM 8B tag checked before decryption accepted
- [ ] **Session limit enforced** - Max 4 concurrent crypto sessions

### IMPORTANT (Should Pass)

- [ ] **esp_err_t checked** - All ESP-IDF API returns verified
- [ ] **nanopb max_size set** - All bytes/string fields in .options
- [ ] **MTU negotiated** - BLE MTU exchange before large payloads
- [ ] **Stack watermarks measured** - All tasks have 512B+ margin
- [ ] **Watchdog fed** - All long-running tasks call `esp_task_wdt_reset()`
- [ ] **WiFi+BLE coexistence** - `esp_coex_preference_set()` configured
- [ ] **MQTT waits for WiFi** - Client starts after `IP_EVENT_STA_GOT_IP`
- [ ] **Task priorities correct** - Crypto > BLE > Cmd > MQTT > Sensor
- [ ] **Core pinning verified** - Radio tasks on Core 0, compute on Core 1
- [ ] **OTA partition scheme** - Dual OTA slots in partition table

### RECOMMENDED (Nice to Have)

- [ ] **Flash encryption** - `CONFIG_SECURE_FLASH_ENC_ENABLED`
- [ ] **Secure boot** - `CONFIG_SECURE_BOOT`
- [ ] **Anti-rollback** - eFuse counter for firmware version
- [ ] **Core dump enabled** - `CONFIG_ESP_COREDUMP_ENABLE_TO_FLASH`
- [ ] **Power profiling** - Sleep/active current measured
- [ ] **Diagnostic commands** - System cluster 0x00 returns heap + task stats

---

## Security Review Checklist

- [ ] No hardcoded keys anywhere - `grep -rn "key.*=.*{" components/ main/`
- [ ] ECDH keypair is ephemeral (not stored in NVS)
- [ ] AES-256-CCM nonce counter is uint64 monotonic
- [ ] Session ID is random (`esp_random()`)
- [ ] HKDF salt includes session_id
- [ ] Key exchange is the ONLY unencrypted command allowed
- [ ] Decryption auth failure triggers session teardown
- [ ] No logging of key material (even at DEBUG level)
- [ ] NVS encryption enabled for stored credentials

---

## Memory Review Checklist

- [ ] No `malloc()` / `new` in ISR context
- [ ] Buffers > 512B use PSRAM (`MALLOC_CAP_SPIRAM`)
- [ ] No `std::string` / `std::vector` in DRAM-critical paths
- [ ] Fixed-size arrays for nanopb buffers
- [ ] All `heap_caps_malloc` calls check for `nullptr`
- [ ] DRAM fragmentation acceptable (`heap_caps_get_largest_free_block`)

---

## BLE Review Checklist

- [ ] GATT attribute table permissions are correct (ENCRYPTED for cmd write)
- [ ] Advertising restarts after client disconnect
- [ ] Connection parameter update requested for throughput
- [ ] MTU exchange happens on connect
- [ ] CCC descriptor checked before sending notifications
- [ ] GATT Client discovery completes before read/write

---

## Verification Command

```bash
echo "=== PRODUCTION READINESS CHECK ===" && \
echo "1. Build..." && \
idf.py build --quiet && echo "PASS: Build" || echo "FAIL: Build" && \
echo "2. Size check..." && \
idf.py size 2>&1 | grep -E "Total|DRAM|Flash" && \
echo "3. Hardcoded secrets..." && \
(grep -rqn "password.*=.*\"\|secret.*=.*\"\|key.*=.*{0x" main/ components/ && \
  echo "WARN: Potential hardcoded secrets" || echo "PASS: No hardcoded secrets") && \
echo "4. nanopb bounds..." && \
(grep -c "max_size" components/CommandService/proto/*.options && \
  echo "PASS: nanopb bounds set" || echo "WARN: Missing max_size") && \
echo "5. Error handling..." && \
(grep -rn "esp_ble_\|esp_wifi_\|esp_mqtt_" components/ main/ | \
  grep -v "ESP_ERROR_CHECK\|ESP_RETURN_ON_ERROR\|err\|ret" | \
  head -5 && echo "WARN: Unchecked ESP calls" || echo "PASS: Error handling OK") && \
echo "=== CHECK COMPLETE ==="
```
