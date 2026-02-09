---
name: esp32-developer-skill
description: ESP32-S3 IoT development guide based on Arcana Embedded ESP32 production-ready IoT command platform. Provides comprehensive support for BLE dual-role (GATT Server/Client via Bluedroid), AES-256-CCM encryption with ECDH P-256 key exchange, Observable sensor pattern, nanopb protobuf, Arcana Frame Protocol, MQTT5, and WiFi+BLE coexistence on FreeRTOS. Suitable for ESP32-S3 firmware development, architecture design, security review, and debugging.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# ESP32 Developer Skill

Professional ESP32-S3 IoT development skill based on [Arcana Embedded ESP32](https://github.com/jrjohn/arcana-embedded-esp32) production-ready IoT command platform.

**Target**: ESP32-S3 (512KB SRAM, 8MB PSRAM, 16MB Flash)
**Stack**: C++17, ESP-IDF v5.5, FreeRTOS, Bluedroid BLE, AES-256-CCM, nanopb, MQTT5

---

## Quick Reference Card

### New Command Checklist:
```
1. Define command enum in CommandDefs.h (cluster:command pair)
2. Create CommandHandler subclass with execute() override
3. Register handler in CommandFactory::create()
4. Add nanopb .proto + .options for payload serialization
5. Implement encode/decode in CommandCodec
6. Add unit test with known-good byte sequence
7. Verify round-trip: encode -> frame -> encrypt -> decrypt -> deframe -> decode
```

### New BLE Service Checklist:
```
1. Define UUID in ble_uuids.h (128-bit for custom, 16-bit for SIG)
2. Add GATT attribute table entry in gatt_db[]
3. Implement read/write/notify callbacks in GattServer
4. Register event handler in BleService facade
5. Add MTU-aware fragmentation if payload > (MTU - 3)
6. Test with nRF Connect: write characteristic, verify notify
7. Verify WiFi+BLE coexistence under load
```

### Quick Diagnosis:
| Symptom | Check Command |
|---------|---------------|
| BLE crash on connect | `grep "ESP_GATTS_CONNECT_EVT" main/ components/` check conn_id reuse |
| Encryption fails | Verify ECDH key exchange completed before first AES-256-CCM op |
| MQTT disconnect | `grep "MQTT_EVENT_DISCONNECTED" main/ components/` check WiFi coexistence |
| Stack overflow | `idf.py monitor` + `uxTaskGetStackHighWaterMark()` per task |
| Frame CRC mismatch | Verify byte order (little-endian) in Length and CRC-16 fields |
| nanopb encode fail | Check `.options` max_size matches buffer, verify `pb_encode` return |
| PSRAM alloc fail | `heap_caps_get_free_size(MALLOC_CAP_SPIRAM)` check fragmentation |

---

## Rules Priority

### CRITICAL (Must Fix Immediately)

| Rule | Description | Verification |
|------|-------------|--------------|
| Encryption Always On | ALL command payloads over BLE/MQTT MUST use AES-256-CCM | `grep "aes_ccm_encrypt" components/CommandService/` |
| ECDH Before Commands | Key exchange MUST complete before any encrypted command | Check session state machine |
| Memory Budget | DRAM usage MUST stay below 80% (267KB of 334KB) | `heap_caps_get_free_size(MALLOC_CAP_8BIT)` |
| BLE Coexistence | WiFi+BLE MUST use coexistence API, never raw radio access | Check `esp_coex_preference_set()` in init |
| Stack Sizes | FreeRTOS task stacks MUST be sized per measured watermark + 512B margin | `uxTaskGetStackHighWaterMark()` |
| Frame Validation | ALL incoming frames MUST validate Magic, CRC-16, and Length before parse | Check `ArcanaFrame::validate()` |
| Session Limit | Maximum 4 concurrent crypto sessions (SRAM constraint) | Check `SessionManager::kMaxSessions` |

### IMPORTANT (Should Fix Before PR)

| Rule | Description | Verification |
|------|-------------|--------------|
| nanopb Bounds | All nanopb fields MUST have max_size in .options | `grep "max_size" *.options` |
| Error Propagation | All ESP-IDF calls MUST check esp_err_t return | `grep "ESP_ERROR_CHECK\|ESP_RETURN_ON_ERROR" components/` |
| MTU Awareness | BLE payloads MUST respect negotiated MTU (default 23, max 517) | Check MTU exchange in GAP |
| MQTT QoS | Sensor data uses QoS 0, commands use QoS 1 | Check publish calls |
| Task Priorities | Crypto > BLE > MQTT > Sensor > Logging | Check `xTaskCreate` priority args |
| Watchdog | All long-running tasks MUST feed task watchdog | `esp_task_wdt_reset()` |

### RECOMMENDED (Nice to Have)

| Rule | Description |
|------|-------------|
| OTA Rollback | Anti-rollback counter in eFuse for firmware validation |
| Power Profiling | Measure sleep/active current per BLE advertising interval |
| Partition Encryption | Enable flash encryption for production builds |
| Diagnostic Commands | System cluster 0x00 includes heap, uptime, task stats |

---

## Error Handling

### ESP-IDF Error Model

```cpp
// CRITICAL: Always check esp_err_t returns
esp_err_t err = esp_ble_gatts_send_indicate(
    gatts_if, conn_id, attr_handle, value_len, value, false);
if (err != ESP_OK) {
    ESP_LOGE(TAG, "Send indicate failed: %s", esp_err_to_name(err));
    return err;
}

// Use ESP_RETURN_ON_ERROR for chained calls
ESP_RETURN_ON_ERROR(esp_wifi_init(&cfg), TAG, "WiFi init failed");
ESP_RETURN_ON_ERROR(esp_wifi_set_mode(WIFI_MODE_STA), TAG, "WiFi mode failed");
ESP_RETURN_ON_ERROR(esp_wifi_start(), TAG, "WiFi start failed");
```

### Error Handling Flow

```
+---------------------------------------------------------------+
|                       Error Flow                                |
+---------------------------------------------------------------+
|  Transport Layer (BLE/MQTT):                                    |
|    - Detect connection/disconnect events                        |
|    - Report transport errors via esp_err_t                      |
|    - Trigger reconnect with exponential backoff                 |
+---------------------------------------------------------------+
|  Protocol Layer (Frame/Codec/Crypto):                           |
|    - Validate frame integrity (Magic + CRC-16)                  |
|    - Check decryption auth tag (AES-256-CCM 8B tag)             |
|    - Return specific error codes for each failure               |
|    - NEVER silently discard corrupt frames                      |
+---------------------------------------------------------------+
|  Application Layer (CommandService):                            |
|    - Map protocol errors to command responses                   |
|    - Send error response frame back to sender                   |
|    - Log error with ESP_LOGE for diagnostics                    |
|    - Update observable state for UI notification                 |
+---------------------------------------------------------------+
|  System Layer (FreeRTOS):                                       |
|    - Panic handler for unrecoverable errors                     |
|    - Core dump to flash partition                               |
|    - Watchdog timeout = task-level restart                       |
+---------------------------------------------------------------+
```

### Command Error Response

```cpp
// components/CommandService/include/CommandDefs.h
enum class CommandStatus : uint8_t {
    kSuccess           = 0x00,
    kUnsupportedCluster = 0x01,
    kUnsupportedCommand = 0x02,
    kInvalidField      = 0x03,
    kResourceExhausted = 0x04,
    kNotAuthorized     = 0x05,
    kHardwareError     = 0x06,
    kTimeout           = 0x07,
    kCryptoError       = 0x08,
    kSessionExpired    = 0x09,
};
```

---

## Three-Layer Architecture

```
+===================================================================+
|                      APPLICATION LAYER                              |
|  +------------------+  +----------------+  +--------------------+  |
|  | ObservableSensor  |  |  BleService    |  |  CommandService    |  |
|  | Observable<T,N>   |  |  (Facade)      |  |  Dispatcher        |  |
|  | EventQueue        |  |  GAP Manager   |  |  Factory           |  |
|  | StaticObservable  |  |  GATT Server   |  |  Codec (nanopb)    |  |
|  |                   |  |  GATT Client   |  |  KeyExchange       |  |
|  +--------+----------+  +-------+--------+  +--------+-----------+  |
|           |                      |                     |            |
+===========|======================|=====================|============+
|           v                      v                     v            |
|                       PROTOCOL LAYER                                |
|  +----------------------------------------------------------------+ |
|  |  Serialization (nanopb) --> Encryption (AES-256-CCM)           | |
|  |  --> Framing (Arcana Frame) --> Transport (BLE GATT / MQTT5)   | |
|  +----------------------------------------------------------------+ |
|                                                                     |
+=====================================================================+
|                        SYSTEM LAYER                                  |
|  +-------------+  +----------------+  +---------------------------+ |
|  | WiFi+BLE    |  |  FreeRTOS      |  |  ESP32-S3 Hardware        | |
|  | Coexistence |  |  Task Scheduler|  |  512KB SRAM, 8MB PSRAM    | |
|  | esp_coex    |  |  Queues/Mutex  |  |  16MB Flash, Dual-Core    | |
|  +-------------+  +----------------+  +---------------------------+ |
+=====================================================================+
```

### Layer Responsibilities

| Layer | Responsibility | Components |
|-------|----------------|------------|
| **Application** | Business logic, sensor management, command handling | ObservableSensor, BleService, CommandService, MQTT5 |
| **Protocol** | Data transformation pipeline: serialize, encrypt, frame, transport | nanopb, AES-256-CCM, ArcanaFrame, BLE GATT / MQTT |
| **System** | Hardware abstraction, OS services, radio coexistence | ESP-IDF drivers, FreeRTOS, esp_coex, partition table |

### Data Flow (Command Round-Trip)

```
Mobile App                          ESP32-S3
    |                                   |
    |-- BLE Write Characteristic ------>|
    |                                   | 1. GATT Server receives raw bytes
    |                                   | 2. ArcanaFrame::parse() validates
    |                                   |    Magic(0xAR CA) + CRC-16
    |                                   | 3. AES-256-CCM decrypt payload
    |                                   |    (verify 8B auth tag)
    |                                   | 4. nanopb decode to Command struct
    |                                   | 5. CommandDispatcher routes by
    |                                   |    cluster_id:command_id
    |                                   | 6. CommandHandler::execute()
    |                                   | 7. Build response Command struct
    |                                   | 8. nanopb encode response
    |                                   | 9. AES-256-CCM encrypt
    |                                   | 10. ArcanaFrame::build()
    |                                   | 11. GATT Notify/Indicate
    |<-- BLE Notification --------------|
    |                                   |
```

---

## Observable Pattern

### Three Variants

| Variant | Use Case | Storage | Thread Safety |
|---------|----------|---------|---------------|
| `Observable<T, N>` | Dynamic sensor with N observer slots | Instance member | Mutex-protected |
| `StaticObservable<T, N>` | Singleton sensor (e.g., system temp) | Static storage | Mutex-protected |
| `EventQueue<T, N>` | Async event dispatch across tasks | FreeRTOS queue | Queue-safe (ISR-compatible) |

### Observable<T, N> Template

```cpp
// components/ObservableSensor/include/Observable.h
template <typename T, size_t MaxObservers = 4>
class Observable {
public:
    using Callback = std::function<void(const T& old_val, const T& new_val)>;

    bool subscribe(Callback cb) {
        std::lock_guard<SemaphoreHandle_t> lock(mutex_);
        if (count_ >= MaxObservers) return false;
        observers_[count_++] = std::move(cb);
        return true;
    }

    void setValue(const T& new_val) {
        std::lock_guard<SemaphoreHandle_t> lock(mutex_);
        if (value_ != new_val) {
            T old = value_;
            value_ = new_val;
            for (size_t i = 0; i < count_; ++i) {
                observers_[i](old, value_);
            }
        }
    }

    const T& getValue() const { return value_; }

private:
    T value_{};
    Callback observers_[MaxObservers]{};
    size_t count_ = 0;
    SemaphoreHandle_t mutex_ = xSemaphoreCreateMutex();
};
```

### EventQueue<T, N> for Cross-Task Notifications

```cpp
// components/ObservableSensor/include/EventQueue.h
template <typename T, size_t Depth = 8>
class EventQueue {
public:
    EventQueue() : queue_(xQueueCreate(Depth, sizeof(T))) {
        configASSERT(queue_ != nullptr);
    }

    bool send(const T& event, TickType_t timeout = portMAX_DELAY) {
        return xQueueSend(queue_, &event, timeout) == pdTRUE;
    }

    bool sendFromISR(const T& event) {
        BaseType_t woken = pdFALSE;
        bool ok = xQueueSendFromISR(queue_, &event, &woken) == pdTRUE;
        portYIELD_FROM_ISR(woken);
        return ok;
    }

    bool receive(T& event, TickType_t timeout = portMAX_DELAY) {
        return xQueueReceive(queue_, &event, timeout) == pdTRUE;
    }

private:
    QueueHandle_t queue_;
};
```

### StaticObservable for Singleton Sensors

```cpp
// components/ObservableSensor/include/StaticObservable.h
template <typename T, size_t MaxObservers = 4>
class StaticObservable {
public:
    static StaticObservable& instance() {
        static StaticObservable inst;
        return inst;
    }

    bool subscribe(typename Observable<T, MaxObservers>::Callback cb) {
        return observable_.subscribe(std::move(cb));
    }

    void setValue(const T& val) { observable_.setValue(val); }
    const T& getValue() const { return observable_.getValue(); }

private:
    StaticObservable() = default;
    Observable<T, MaxObservers> observable_;
};
```

---

## BLE Dual-Role Architecture

### Bluedroid Stack Architecture

```
+-------------------------------------------------------------------+
|                        BleService (Facade)                          |
|  +--------------------+  +------------------+  +----------------+  |
|  |    GAP Manager      |  |   GATT Server    |  |  GATT Client   |  |
|  | - Advertising       |  | - Service Table  |  | - Scan         |  |
|  | - Connection Params |  | - Read/Write CB  |  | - Connect      |  |
|  | - Security (LE SC)  |  | - Notifications  |  | - Discover     |  |
|  | - Bonding           |  | - Indications    |  | - Read/Write   |  |
|  +--------------------+  +------------------+  +----------------+  |
|                                                                     |
|  Bluedroid API Layer:                                               |
|  esp_ble_gap_*  |  esp_ble_gatts_*  |  esp_ble_gattc_*             |
+-------------------------------------------------------------------+
|                   ESP-IDF BLE Controller                            |
|                   (NimBLE or Bluedroid)                              |
+-------------------------------------------------------------------+
```

### GAP Configuration

```cpp
// Advertising parameters for dual-role
static esp_ble_adv_params_t adv_params = {
    .adv_int_min = 0x20,     // 20ms minimum interval
    .adv_int_max = 0x40,     // 40ms maximum interval
    .adv_type = ADV_TYPE_IND,
    .own_addr_type = BLE_ADDR_TYPE_PUBLIC,
    .channel_map = ADV_CHNL_ALL,
    .adv_filter_policy = ADV_FILTER_ALLOW_SCAN_ANY_CON_ANY,
};

// Connection parameter update for throughput
static esp_ble_conn_update_params_t conn_params = {
    .min_int = 0x06,    // 7.5ms (fastest)
    .max_int = 0x10,    // 20ms
    .latency = 0,       // No slave latency
    .timeout = 400,     // 4s supervision timeout
};
```

### GATT Server Service Table

```cpp
// GATT attribute table definition
static const esp_gatts_attr_db_t gatt_db[] = {
    // Service Declaration (Arcana Command Service)
    [IDX_SVC] = {{ESP_GATT_AUTO_RSP},
        {ESP_UUID_LEN_16, (uint8_t*)&primary_service_uuid,
         ESP_GATT_PERM_READ, sizeof(arcana_svc_uuid),
         sizeof(arcana_svc_uuid), (uint8_t*)&arcana_svc_uuid}},

    // Command Write Characteristic
    [IDX_CMD_CHAR] = {{ESP_GATT_AUTO_RSP},
        {ESP_UUID_LEN_16, (uint8_t*)&character_declaration_uuid,
         ESP_GATT_PERM_READ, sizeof(uint8_t),
         sizeof(uint8_t), (uint8_t*)&char_prop_write}},

    [IDX_CMD_VAL] = {{ESP_GATT_RSP_BY_APP},  // App handles response
        {ESP_UUID_LEN_128, (uint8_t*)&cmd_write_uuid,
         ESP_GATT_PERM_WRITE_ENCRYPTED, 512,
         0, nullptr}},

    // Response Notify Characteristic
    [IDX_RSP_CHAR] = {{ESP_GATT_AUTO_RSP},
        {ESP_UUID_LEN_16, (uint8_t*)&character_declaration_uuid,
         ESP_GATT_PERM_READ, sizeof(uint8_t),
         sizeof(uint8_t), (uint8_t*)&char_prop_notify}},

    [IDX_RSP_VAL] = {{ESP_GATT_AUTO_RSP},
        {ESP_UUID_LEN_128, (uint8_t*)&cmd_response_uuid,
         ESP_GATT_PERM_READ, 512,
         0, nullptr}},

    [IDX_RSP_CCC] = {{ESP_GATT_AUTO_RSP},
        {ESP_UUID_LEN_16, (uint8_t*)&ccc_uuid,
         ESP_GATT_PERM_READ | ESP_GATT_PERM_WRITE,
         sizeof(uint16_t), sizeof(uint16_t), (uint8_t*)&ccc_val}},
};
```

### GATT Server Event Handler

```cpp
void BleService::gattsEventHandler(
    esp_gatts_cb_event_t event,
    esp_gatt_if_t gatts_if,
    esp_ble_gatts_cb_param_t* param)
{
    switch (event) {
    case ESP_GATTS_REG_EVT:
        esp_ble_gatts_create_attr_tab(gatt_db, gatts_if,
            IDX_COUNT, 0);
        break;

    case ESP_GATTS_CREAT_ATTR_TAB_EVT:
        if (param->add_attr_tab.status == ESP_GATT_OK) {
            memcpy(handle_table_, param->add_attr_tab.handles,
                   sizeof(handle_table_));
            esp_ble_gatts_start_service(
                handle_table_[IDX_SVC]);
        }
        break;

    case ESP_GATTS_CONNECT_EVT: {
        uint16_t conn_id = param->connect.conn_id;
        ESP_LOGI(TAG, "Client connected, conn_id=%d", conn_id);
        // Update connection parameters for throughput
        esp_ble_gap_update_conn_params(&conn_params);
        // Initialize crypto session
        session_mgr_.createSession(conn_id);
        break;
    }

    case ESP_GATTS_WRITE_EVT:
        if (param->write.handle == handle_table_[IDX_CMD_VAL]) {
            onCommandReceived(param->write.conn_id,
                param->write.value, param->write.len);
        }
        break;

    case ESP_GATTS_DISCONNECT_EVT:
        session_mgr_.destroySession(param->disconnect.conn_id);
        esp_ble_gap_start_advertising(&adv_params);
        break;

    default:
        break;
    }
}
```

### GATT Client (Scanner + Central)

```cpp
void BleService::gattcEventHandler(
    esp_gattc_cb_event_t event,
    esp_gatt_if_t gattc_if,
    esp_ble_gattc_cb_param_t* param)
{
    switch (event) {
    case ESP_GATTC_REG_EVT:
        esp_ble_gap_set_scan_params(&scan_params);
        break;

    case ESP_GATTC_SEARCH_CMPL_EVT:
        // Service discovery complete - find Arcana service
        esp_ble_gattc_get_char_by_uuid(
            gattc_if, param->search_cmpl.conn_id,
            arcana_svc_handle_, arcana_svc_end_handle_,
            cmd_write_uuid_, &char_count, char_elem);
        break;

    case ESP_GATTC_NOTIFY_EVT:
        // Received notification from remote GATT Server
        onRemoteNotification(param->notify.conn_id,
            param->notify.value, param->notify.value_len);
        break;

    default:
        break;
    }
}
```

---

## Command Pipeline

### Command Dispatch Architecture (Matter/ZCL-Style)

```
+-------------------------------------------------------------------+
|                     Command Dispatch Table                          |
+-------------------------------------------------------------------+
| Cluster ID  | Cluster Name | Commands                              |
|-------------|-------------|---------------------------------------|
| 0x00        | System      | Ping, Reset, Info, DiagHeap, TaskList |
| 0x01        | Sensor      | Read, Subscribe, Calibrate, Threshold |
| 0x02        | BLE         | Scan, Connect, Disconnect, ParamUpdate|
| 0x03        | MQTT        | Publish, Subscribe, Unsubscribe, Stat |
| 0x04        | Security    | KeyExchange, SessionInfo, Rotate, Wipe|
+-------------------------------------------------------------------+
```

### CommandDispatcher

```cpp
// components/CommandService/include/CommandDispatcher.h
class CommandDispatcher {
public:
    using Handler = std::function<CommandStatus(
        const CommandRequest& req, CommandResponse& rsp)>;

    void registerHandler(uint8_t cluster, uint8_t command, Handler h) {
        handlers_[makeKey(cluster, command)] = std::move(h);
    }

    CommandStatus dispatch(const CommandRequest& req,
                          CommandResponse& rsp) {
        auto it = handlers_.find(makeKey(req.cluster_id, req.command_id));
        if (it == handlers_.end()) {
            return CommandStatus::kUnsupportedCommand;
        }
        return it->second(req, rsp);
    }

private:
    static uint16_t makeKey(uint8_t cluster, uint8_t cmd) {
        return (static_cast<uint16_t>(cluster) << 8) | cmd;
    }

    std::unordered_map<uint16_t, Handler> handlers_;
};
```

### CommandFactory

```cpp
// components/CommandService/include/CommandFactory.h
class CommandFactory {
public:
    static void registerAll(CommandDispatcher& dispatcher) {
        // System cluster 0x00
        dispatcher.registerHandler(0x00, 0x00, SystemPingHandler::execute);
        dispatcher.registerHandler(0x00, 0x01, SystemResetHandler::execute);
        dispatcher.registerHandler(0x00, 0x02, SystemInfoHandler::execute);
        dispatcher.registerHandler(0x00, 0x03, DiagHeapHandler::execute);

        // Sensor cluster 0x01
        dispatcher.registerHandler(0x01, 0x00, SensorReadHandler::execute);
        dispatcher.registerHandler(0x01, 0x01, SensorSubscribeHandler::execute);
        dispatcher.registerHandler(0x01, 0x02, SensorCalibrateHandler::execute);

        // BLE cluster 0x02
        dispatcher.registerHandler(0x02, 0x00, BleScanHandler::execute);
        dispatcher.registerHandler(0x02, 0x01, BleConnectHandler::execute);

        // MQTT cluster 0x03
        dispatcher.registerHandler(0x03, 0x00, MqttPublishHandler::execute);
        dispatcher.registerHandler(0x03, 0x01, MqttSubscribeHandler::execute);

        // Security cluster 0x04
        dispatcher.registerHandler(0x04, 0x00, KeyExchangeHandler::execute);
        dispatcher.registerHandler(0x04, 0x01, SessionInfoHandler::execute);
    }
};
```

### CommandCodec (nanopb Serialization)

```cpp
// components/CommandService/include/CommandCodec.h
class CommandCodec {
public:
    static bool encode(const CommandResponse& rsp,
                       uint8_t* buf, size_t buf_len, size_t& out_len) {
        pb_ostream_t stream = pb_ostream_from_buffer(buf, buf_len);
        ArcanaResponse pb_rsp = ArcanaResponse_init_zero;

        pb_rsp.cluster_id = rsp.cluster_id;
        pb_rsp.command_id = rsp.command_id;
        pb_rsp.status = static_cast<uint8_t>(rsp.status);
        pb_rsp.sequence = rsp.sequence;

        if (rsp.payload_len > 0) {
            pb_rsp.payload.size = rsp.payload_len;
            memcpy(pb_rsp.payload.bytes, rsp.payload, rsp.payload_len);
            pb_rsp.has_payload = true;
        }

        if (!pb_encode(&stream, ArcanaResponse_fields, &pb_rsp)) {
            ESP_LOGE(TAG, "nanopb encode failed: %s",
                     PB_GET_ERROR(&stream));
            return false;
        }

        out_len = stream.bytes_written;
        return true;
    }

    static bool decode(const uint8_t* buf, size_t buf_len,
                       CommandRequest& req) {
        pb_istream_t stream = pb_istream_from_buffer(buf, buf_len);
        ArcanaRequest pb_req = ArcanaRequest_init_zero;

        if (!pb_decode(&stream, ArcanaRequest_fields, &pb_req)) {
            ESP_LOGE(TAG, "nanopb decode failed: %s",
                     PB_GET_ERROR(&stream));
            return false;
        }

        req.cluster_id = pb_req.cluster_id;
        req.command_id = pb_req.command_id;
        req.sequence = pb_req.sequence;
        req.payload_len = pb_req.payload.size;
        memcpy(req.payload, pb_req.payload.bytes, req.payload_len);
        return true;
    }
};
```

---

## Arcana Frame Protocol

### Frame Structure (9 Bytes Overhead)

```
+--------+--------+-------+-------+----------+--------+----------+
| Byte 0 | Byte 1 | Byte 2| Byte 3| Byte 4-5 | Byte 6 | Byte N   |
|        |        |       |       |          | to N-3 |  to N-1  |
+--------+--------+-------+-------+----------+--------+----------+
| Magic  | Magic  | Ver   | Flags | Length   | Payload| CRC-16   |
| 0xAR   | 0xCA   | 0x01  |       | (LE)     |        | (LE)     |
+--------+--------+-------+-------+----------+--------+----------+
```

### Field Details

| Field | Offset | Size | Description |
|-------|--------|------|-------------|
| Magic | 0 | 2B | `0xAR 0xCA` - Frame sync marker |
| Version | 2 | 1B | Protocol version (currently 0x01) |
| Flags | 3 | 1B | Bit 0: encrypted, Bit 1: compressed, Bit 2: fragmented |
| Length | 4 | 2B | Payload length (little-endian, max 65535) |
| Payload | 6 | N | Encrypted nanopb-serialized command data |
| CRC-16 | 6+N | 2B | CRC-16/CCITT over bytes 0 to 5+N (little-endian) |

### Flags Bit Field

| Bit | Name | Description |
|-----|------|-------------|
| 0 | `ENCRYPTED` | Payload is AES-256-CCM encrypted |
| 1 | `COMPRESSED` | Payload is zlib-compressed before encryption |
| 2 | `FRAGMENTED` | Frame is part of a multi-frame message |
| 3 | `ACK_REQUIRED` | Sender expects acknowledgment frame |
| 4-7 | Reserved | Must be 0 |

### Frame Builder and Parser

```cpp
// components/CommandService/include/ArcanaFrame.h
class ArcanaFrame {
public:
    static constexpr uint16_t kMagic = 0xCAAR;  // Little-endian: AR CA
    static constexpr uint8_t kVersion = 0x01;
    static constexpr size_t kHeaderSize = 6;     // Magic+Ver+Flags+Len
    static constexpr size_t kCrcSize = 2;
    static constexpr size_t kOverhead = kHeaderSize + kCrcSize;  // 8B

    struct ParseResult {
        bool valid;
        uint8_t flags;
        uint8_t stream_id;
        const uint8_t* payload;
        size_t payload_len;
    };

    static size_t build(uint8_t flags, uint8_t stream_id,
                        const uint8_t* payload, size_t payload_len,
                        uint8_t* out_buf, size_t out_buf_len) {
        if (out_buf_len < kOverhead + payload_len) return 0;

        size_t pos = 0;
        out_buf[pos++] = 0xAR;
        out_buf[pos++] = 0xCA;
        out_buf[pos++] = kVersion;
        out_buf[pos++] = flags;
        out_buf[pos++] = stream_id;
        // Length (little-endian)
        out_buf[pos++] = payload_len & 0xFF;
        out_buf[pos++] = (payload_len >> 8) & 0xFF;
        // Payload
        memcpy(&out_buf[pos], payload, payload_len);
        pos += payload_len;
        // CRC-16 over everything before CRC
        uint16_t crc = crc16_ccitt(out_buf, pos);
        out_buf[pos++] = crc & 0xFF;
        out_buf[pos++] = (crc >> 8) & 0xFF;

        return pos;
    }

    static ParseResult parse(const uint8_t* buf, size_t len) {
        ParseResult r{};
        if (len < kOverhead + 1) return r;  // Need at least 1B payload
        if (buf[0] != 0xAR || buf[1] != 0xCA) return r;
        if (buf[2] != kVersion) return r;

        r.flags = buf[3];
        r.stream_id = buf[4];
        r.payload_len = buf[5] | (buf[6] << 8);

        if (len < kHeaderSize + 1 + r.payload_len + kCrcSize) return r;

        // Verify CRC-16
        size_t crc_offset = kHeaderSize + 1 + r.payload_len;
        uint16_t expected = buf[crc_offset] | (buf[crc_offset + 1] << 8);
        uint16_t actual = crc16_ccitt(buf, crc_offset);
        if (expected != actual) return r;

        r.payload = &buf[kHeaderSize + 1];
        r.valid = true;
        return r;
    }

private:
    static uint16_t crc16_ccitt(const uint8_t* data, size_t len) {
        uint16_t crc = 0xFFFF;
        for (size_t i = 0; i < len; ++i) {
            crc ^= static_cast<uint16_t>(data[i]) << 8;
            for (int j = 0; j < 8; ++j) {
                crc = (crc & 0x8000) ? (crc << 1) ^ 0x1021 : crc << 1;
            }
        }
        return crc;
    }
};
```

---

## Security Architecture

### Cryptographic Primitives

| Primitive | Algorithm | Parameters |
|-----------|-----------|------------|
| Symmetric Encryption | AES-256-CCM | 256-bit key, 13B nonce, 8B auth tag |
| Key Agreement | ECDH P-256 | secp256r1 (NIST P-256) |
| Key Derivation | HKDF-SHA256 | 32B output, context-specific info |
| Session ID | Random | 4B per connection |
| Nonce Counter | Monotonic | Per-session, never reused |

### ECDH Key Exchange Flow

```
Mobile App                              ESP32-S3
    |                                       |
    |  1. Generate ephemeral P-256 keypair  |
    |     (app_pub, app_priv)               |
    |                                       |  1. Generate ephemeral P-256 keypair
    |                                       |     (dev_pub, dev_priv)
    |                                       |
    |  2. Send KeyExchange command -------->|
    |     { cluster:0x04, cmd:0x00,         |
    |       payload: app_pub (64B) }        |
    |                                       |
    |                                       |  3. shared = ECDH(dev_priv, app_pub)
    |                                       |  4. session_key = HKDF-SHA256(
    |                                       |       shared, salt=session_id,
    |                                       |       info="arcana-cmd-v1", len=32)
    |                                       |
    |  5. <-- KeyExchange response ---------|
    |     { payload: dev_pub (64B),         |
    |       session_id (4B) }               |
    |                                       |
    |  6. shared = ECDH(app_priv, dev_pub)  |
    |  7. session_key = HKDF-SHA256(...)    |
    |                                       |
    |  === Session Established ===          |
    |  Both sides have identical            |
    |  session_key (256-bit AES key)        |
    |                                       |
```

### AES-256-CCM Encryption

```cpp
// components/CommandService/include/CryptoEngine.h
class CryptoEngine {
public:
    static constexpr size_t kKeySize = 32;     // 256 bits
    static constexpr size_t kNonceSize = 13;   // CCM nonce
    static constexpr size_t kTagSize = 8;      // Auth tag
    static constexpr size_t kOverhead = kTagSize;  // Added to ciphertext

    struct Session {
        uint8_t key[kKeySize];
        uint32_t session_id;
        uint64_t nonce_counter;  // Monotonic, never reused
        bool active;
    };

    esp_err_t encrypt(Session& session,
                      const uint8_t* plaintext, size_t plain_len,
                      const uint8_t* aad, size_t aad_len,
                      uint8_t* ciphertext, uint8_t* tag) {
        uint8_t nonce[kNonceSize];
        buildNonce(session, nonce);

        mbedtls_ccm_context ctx;
        mbedtls_ccm_init(&ctx);
        ESP_RETURN_ON_ERROR(
            mbedtls_ccm_setkey(&ctx, MBEDTLS_CIPHER_ID_AES,
                session.key, kKeySize * 8) == 0
                ? ESP_OK : ESP_ERR_INVALID_STATE,
            TAG, "AES key setup failed");

        int ret = mbedtls_ccm_encrypt_and_tag(
            &ctx, plain_len,
            nonce, kNonceSize,
            aad, aad_len,
            plaintext, ciphertext,
            tag, kTagSize);

        mbedtls_ccm_free(&ctx);
        session.nonce_counter++;  // CRITICAL: always increment

        return ret == 0 ? ESP_OK : ESP_ERR_INVALID_STATE;
    }

    esp_err_t decrypt(Session& session,
                      const uint8_t* ciphertext, size_t cipher_len,
                      const uint8_t* aad, size_t aad_len,
                      const uint8_t* tag,
                      uint8_t* plaintext) {
        uint8_t nonce[kNonceSize];
        buildNonce(session, nonce);

        mbedtls_ccm_context ctx;
        mbedtls_ccm_init(&ctx);
        mbedtls_ccm_setkey(&ctx, MBEDTLS_CIPHER_ID_AES,
            session.key, kKeySize * 8);

        int ret = mbedtls_ccm_auth_decrypt(
            &ctx, cipher_len,
            nonce, kNonceSize,
            aad, aad_len,
            ciphertext, plaintext,
            tag, kTagSize);

        mbedtls_ccm_free(&ctx);

        if (ret != 0) {
            ESP_LOGE(TAG, "Auth tag verification FAILED (tampered?)");
            return ESP_ERR_INVALID_STATE;
        }

        session.nonce_counter++;
        return ESP_OK;
    }

private:
    void buildNonce(const Session& session, uint8_t* nonce) {
        // Nonce: [session_id:4B][counter:8B][padding:1B]
        memcpy(nonce, &session.session_id, 4);
        memcpy(nonce + 4, &session.nonce_counter, 8);
        nonce[12] = 0x00;
    }
};
```

### Session Manager

```cpp
// components/CommandService/include/SessionManager.h
class SessionManager {
public:
    static constexpr size_t kMaxSessions = 4;  // SRAM constraint

    CryptoEngine::Session* createSession(uint16_t conn_id) {
        for (auto& slot : sessions_) {
            if (!slot.active) {
                slot.active = true;
                slot.session_id = esp_random();
                slot.nonce_counter = 0;
                conn_map_[conn_id] = &slot;
                ESP_LOGI(TAG, "Session created: conn=%d, sid=0x%08lx",
                         conn_id, slot.session_id);
                return &slot;
            }
        }
        ESP_LOGW(TAG, "No free session slots (max=%d)", kMaxSessions);
        return nullptr;
    }

    void destroySession(uint16_t conn_id) {
        auto it = conn_map_.find(conn_id);
        if (it != conn_map_.end()) {
            // CRITICAL: Zero key material before releasing
            mbedtls_platform_zeroize(it->second->key,
                CryptoEngine::kKeySize);
            it->second->active = false;
            conn_map_.erase(it);
        }
    }

    CryptoEngine::Session* getSession(uint16_t conn_id) {
        auto it = conn_map_.find(conn_id);
        return (it != conn_map_.end()) ? it->second : nullptr;
    }

private:
    CryptoEngine::Session sessions_[kMaxSessions]{};
    std::unordered_map<uint16_t, CryptoEngine::Session*> conn_map_;
};
```

---

## MQTT5 Integration

### MQTT5 Client Configuration

```cpp
// main/mqtt_client.cpp
static void mqttInit() {
    esp_mqtt5_client_config_t mqtt_cfg = {
        .broker = {
            .address = {
                .uri = CONFIG_MQTT_BROKER_URI,
                .port = 8883,
                .transport = MQTT_TRANSPORT_OVER_SSL,
            },
            .verification = {
                .certificate = server_cert_pem,
            },
        },
        .credentials = {
            .username = CONFIG_MQTT_USERNAME,
            .authentication = {
                .password = CONFIG_MQTT_PASSWORD,
            },
        },
        .session = {
            .keepalive = 120,
            .disable_clean_session = false,
        },
        .network = {
            .reconnect_timeout_ms = 10000,
            .timeout_ms = 5000,
        },
    };

    esp_mqtt_client_handle_t client = esp_mqtt_client_init(&mqtt_cfg);
    esp_mqtt_client_register_event(client, ESP_EVENT_ANY_ID,
        mqttEventHandler, client);
    esp_mqtt_client_start(client);
}
```

### MQTT Event Handler

```cpp
static void mqttEventHandler(void* arg,
    esp_event_base_t base, int32_t event_id, void* data)
{
    auto* event = static_cast<esp_mqtt_event_handle_t>(data);

    switch (event->event_id) {
    case MQTT_EVENT_CONNECTED:
        ESP_LOGI(TAG, "MQTT connected");
        // Subscribe to command topic with QoS 1
        esp_mqtt_client_subscribe(event->client,
            "arcana/device/" CONFIG_DEVICE_ID "/cmd", 1);
        break;

    case MQTT_EVENT_DATA:
        // Received command over MQTT - same pipeline as BLE
        onMqttCommandReceived(
            reinterpret_cast<const uint8_t*>(event->data),
            event->data_len);
        break;

    case MQTT_EVENT_DISCONNECTED:
        ESP_LOGW(TAG, "MQTT disconnected, will auto-reconnect");
        break;

    case MQTT_EVENT_ERROR:
        if (event->error_handle->error_type ==
            MQTT_ERROR_TYPE_TCP_TRANSPORT) {
            ESP_LOGE(TAG, "MQTT transport error: %s",
                esp_err_to_name(event->error_handle->esp_tls_last_esp_err));
        }
        break;

    default:
        break;
    }
}
```

### MQTT Topic Structure

| Topic Pattern | Direction | QoS | Description |
|--------------|-----------|-----|-------------|
| `arcana/device/{id}/cmd` | Cloud -> Device | 1 | Encrypted command frames |
| `arcana/device/{id}/rsp` | Device -> Cloud | 1 | Encrypted response frames |
| `arcana/device/{id}/telemetry` | Device -> Cloud | 0 | Sensor data (periodic) |
| `arcana/device/{id}/status` | Device -> Cloud | 1 | Online/offline LWT |
| `arcana/device/{id}/ota` | Cloud -> Device | 1 | OTA firmware URL |

---

## WiFi+BLE Coexistence

### Coexistence Configuration

```cpp
// main/app_main.cpp
void initCoexistence() {
    // CRITICAL: Must set coexistence mode BEFORE starting WiFi or BLE
    esp_coex_preference_set(ESP_COEX_PREFER_BALANCE);

    // WiFi init
    wifi_init_config_t wifi_cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&wifi_cfg));
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));

    // BLE init
    ESP_ERROR_CHECK(esp_bt_controller_init(&bt_cfg));
    ESP_ERROR_CHECK(esp_bt_controller_enable(ESP_BT_MODE_BLE));
    ESP_ERROR_CHECK(esp_bluedroid_init());
    ESP_ERROR_CHECK(esp_bluedroid_enable());
}
```

### Coexistence Modes

| Mode | WiFi | BLE | Use Case |
|------|------|-----|----------|
| `ESP_COEX_PREFER_WIFI` | Priority | Degraded | Firmware OTA download |
| `ESP_COEX_PREFER_BT` | Degraded | Priority | BLE key exchange |
| `ESP_COEX_PREFER_BALANCE` | Shared | Shared | Normal operation |

### Timing Budget

```
WiFi+BLE Time-Division (Balance Mode):
+---+---+---+---+---+---+---+---+---+---+
| W | B | W | B | W | W | B | W | B | W |  (10ms slots)
+---+---+---+---+---+---+---+---+---+---+
W = WiFi transmission window
B = BLE advertising/connection event

Constraint: BLE connection interval >= 20ms when WiFi is active
            MQTT keepalive >= 60s to tolerate WiFi bursts
```

---

## Memory Budget

### ESP32-S3 Memory Map

| Region | Total | Used | Free | Usage |
|--------|-------|------|------|-------|
| DRAM | 334 KB | ~131 KB | ~203 KB | 39% |
| IRAM | 128 KB | ~96 KB | ~32 KB | 75% |
| Flash (.text + .rodata) | 1.5 MB | ~1.34 MB | ~160 KB | 91% |
| PSRAM | 8 MB | ~512 KB | ~7.5 MB | 6% |

### Per-Component DRAM Budget

| Component | Budget | Actual | Notes |
|-----------|--------|--------|-------|
| FreeRTOS kernel | 20 KB | ~18 KB | Tasks, queues, timers |
| WiFi stack | 40 KB | ~37 KB | Buffers, state |
| BLE Bluedroid | 45 KB | ~42 KB | GAP + GATT + L2CAP |
| Crypto sessions (4x) | 8 KB | ~6 KB | 4 x AES key + ECDH state |
| nanopb buffers | 4 KB | ~3 KB | Encode/decode buffers |
| Command pipeline | 8 KB | ~6 KB | Dispatcher + factory |
| Observable sensors | 4 KB | ~3 KB | 4 observers x N sensors |
| MQTT client | 12 KB | ~10 KB | Connection + buffers |
| Application logic | 16 KB | ~6 KB | Custom code (~17KB total) |
| **Total** | **157 KB** | **~131 KB** | **Headroom: ~26 KB** |

### Memory Allocation Rules

```
RULE 1: PSRAM for large buffers (> 512B)
  heap_caps_malloc(size, MALLOC_CAP_SPIRAM)

RULE 2: DRAM for real-time data (< 512B, latency-critical)
  heap_caps_malloc(size, MALLOC_CAP_8BIT | MALLOC_CAP_INTERNAL)

RULE 3: Stack allocation for frame buffers (< 1KB)
  uint8_t frame_buf[512];  // On task stack

RULE 4: Static allocation for singleton components
  static CryptoEngine::Session sessions[4];

RULE 5: NEVER use std::string or std::vector in DRAM-critical paths
  Use fixed-size arrays with compile-time bounds
```

### Task Stack Sizes

| Task | Stack Size | Priority | Core | Purpose |
|------|-----------|----------|------|---------|
| ble_task | 4096 B | 19 | 0 | BLE event processing |
| crypto_task | 8192 B | 20 | 1 | AES-256-CCM + ECDH |
| mqtt_task | 4096 B | 15 | 0 | MQTT5 client loop |
| sensor_task | 2048 B | 10 | 1 | Sensor polling + Observable |
| cmd_task | 4096 B | 18 | 1 | Command dispatch |
| main_task | 4096 B | 5 | 0 | Initialization + watchdog |

---

## Partition Table

### partitions.csv

```
# Name,      Type, SubType,  Offset,   Size,   Flags
nvs,         data, nvs,      0x9000,   0x6000,
phy_init,    data, phy,      0xf000,   0x1000,
otadata,     data, ota,      0x10000,  0x2000,
ota_0,       app,  ota_0,    0x20000,  0x1C0000,  (1.75MB)
ota_1,       app,  ota_1,    0x1E0000, 0x1C0000,  (1.75MB)
coredump,    data, coredump, 0x3A0000, 0x10000,   (64KB)
nvs_keys,    data, nvs_keys, 0x3B0000, 0x1000,
```

---

## Kconfig Defaults (sdkconfig.defaults)

```ini
# BLE
CONFIG_BT_ENABLED=y
CONFIG_BT_BLUEDROID_ENABLED=y
CONFIG_BT_BLE_42_FEATURES_SUPPORTED=y
CONFIG_BT_BLE_50_FEATURES_SUPPORTED=y
CONFIG_BT_GATTS_ENABLE=y
CONFIG_BT_GATTC_ENABLE=y
CONFIG_BT_BLE_SMP_ENABLE=y

# WiFi + Coexistence
CONFIG_ESP_WIFI_ENABLED=y
CONFIG_SW_COEXIST_ENABLE=y

# FreeRTOS
CONFIG_FREERTOS_HZ=1000
CONFIG_FREERTOS_UNICORE=n

# PSRAM
CONFIG_SPIRAM=y
CONFIG_SPIRAM_MODE_OCT=y
CONFIG_SPIRAM_SPEED_80M=y

# mbedTLS for AES-256-CCM + ECDH
CONFIG_MBEDTLS_HARDWARE_AES=y
CONFIG_MBEDTLS_AES_USE_INTERRUPT=y
CONFIG_MBEDTLS_CCM_C=y
CONFIG_MBEDTLS_ECDH_C=y
CONFIG_MBEDTLS_ECP_DP_SECP256R1_ENABLED=y
CONFIG_MBEDTLS_HKDF_C=y

# MQTT
CONFIG_MQTT_PROTOCOL_5=y
CONFIG_MQTT_TRANSPORT_SSL=y

# Partition Table
CONFIG_PARTITION_TABLE_CUSTOM=y
CONFIG_PARTITION_TABLE_CUSTOM_FILENAME="partitions.csv"

# Core Dump
CONFIG_ESP_COREDUMP_ENABLE_TO_FLASH=y
CONFIG_ESP_COREDUMP_DATA_FORMAT_ELF=y

# Watchdog
CONFIG_ESP_TASK_WDT_EN=y
CONFIG_ESP_TASK_WDT_TIMEOUT_S=10

# Optimization
CONFIG_COMPILER_OPTIMIZATION_PERF=y
```

---

## Code Review Checklist

### Security Review

- [ ] All commands encrypted with AES-256-CCM after key exchange
- [ ] ECDH keypair is ephemeral (regenerated per connection)
- [ ] Nonce counter is monotonic and never reused
- [ ] Key material zeroed on session destroy (`mbedtls_platform_zeroize`)
- [ ] No plaintext secrets in NVS (use NVS encryption)
- [ ] Auth tag (8B) verified before processing decrypted payload
- [ ] Session slots limited to 4 (no unbounded allocation)

### Memory Review

- [ ] No `malloc()` in ISR context
- [ ] Large buffers (>512B) allocated from PSRAM
- [ ] Stack sizes measured with `uxTaskGetStackHighWaterMark()`
- [ ] No `std::string` / `std::vector` in hot paths
- [ ] Fixed-size arrays for protocol buffers
- [ ] `heap_caps_get_free_size()` checked in diagnostic command

### BLE Review

- [ ] GATT attribute table uses correct permissions (ENCRYPTED for write)
- [ ] MTU negotiated before large transfers
- [ ] Connection parameter update requested after connect
- [ ] Advertising restarts after disconnect
- [ ] GATT Client discovery completes before read/write
- [ ] Notification enabled check (CCC descriptor) before sending

### Protocol Review

- [ ] Frame Magic bytes verified (0xAR 0xCA)
- [ ] CRC-16 computed over header + payload (not including CRC itself)
- [ ] Length field is little-endian
- [ ] nanopb `.options` max_size set for all bytes/string fields
- [ ] Command cluster:command pair registered in factory

### FreeRTOS Review

- [ ] No blocking calls from ISR (`FromISR` variants used)
- [ ] Mutex acquired with timeout (not `portMAX_DELAY` in time-critical paths)
- [ ] Queue depths sized for burst (8+ for event queues)
- [ ] Task priorities follow: Crypto > BLE > MQTT > Sensor > Log
- [ ] Watchdog fed in all long-running loops

---

## Common Issues

### Issue: BLE + WiFi Mutual Interference

**Symptom**: BLE connections drop when WiFi transmits large payloads.
**Cause**: Coexistence not configured or set to WiFi-prefer.
**Fix**:
```cpp
esp_coex_preference_set(ESP_COEX_PREFER_BALANCE);
// Increase BLE connection interval to >= 20ms
conn_params.min_int = 0x10;  // 20ms
```

### Issue: AES-256-CCM Nonce Reuse

**Symptom**: Decryption succeeds but produces garbage plaintext.
**Cause**: Nonce counter not incremented after encrypt/decrypt, or counter reset on reconnect without new key exchange.
**Fix**: Always increment `nonce_counter++` after every encrypt AND decrypt. Force new ECDH on reconnect.

### Issue: nanopb Buffer Overflow

**Symptom**: `pb_encode` returns false, `PB_GET_ERROR` says "buffer too small".
**Cause**: `.options` file not specifying `max_size` or buffer allocated too small.
**Fix**:
```
// command.options
ArcanaRequest.payload  max_size:256
ArcanaResponse.payload max_size:256
```

### Issue: Stack Overflow in Crypto Task

**Symptom**: Guru Meditation Error: Core 1 panic (Stack canary watchpoint triggered).
**Cause**: mbedtls ECDH P-256 uses ~6KB stack. Task stack too small.
**Fix**: Set crypto task stack to 8192B minimum:
```cpp
xTaskCreatePinnedToCore(cryptoTask, "crypto", 8192,
    nullptr, 20, &crypto_handle, 1);
```

### Issue: MQTT Reconnect Storm

**Symptom**: MQTT connects and disconnects in rapid loop, flooding broker.
**Cause**: Missing exponential backoff, or WiFi not yet connected when MQTT starts.
**Fix**: Wait for `WIFI_EVENT_STA_GOT_IP` before starting MQTT client. Use `reconnect_timeout_ms = 10000` with backoff.

### Issue: Observable Callback Deadlock

**Symptom**: System freezes when `setValue()` triggers a callback that calls `setValue()` on another Observable.
**Cause**: Nested mutex acquisition with same priority.
**Fix**: Use `EventQueue` pattern instead of direct callbacks for cross-component notifications:
```cpp
// Instead of direct callback:
sensor.subscribe([&mqtt](auto& old, auto& val) {
    mqtt.publish(val);  // DANGEROUS: may deadlock
});

// Use event queue:
sensor.subscribe([&queue](auto& old, auto& val) {
    queue.send(SensorEvent{val});  // Safe: non-blocking queue send
});
```

---

## Project Directory Structure

```
arcana-embedded-esp32/
├── CMakeLists.txt                    # Top-level CMake
├── main/
│   ├── CMakeLists.txt
│   ├── app_main.cpp                  # Entry point: init all components
│   ├── Kconfig.projbuild             # Project-level menu config
│   └── mqtt_client.cpp               # MQTT5 client setup
├── components/
│   ├── ObservableSensor/
│   │   ├── CMakeLists.txt
│   │   ├── include/
│   │   │   ├── Observable.h          # Observable<T,N> template
│   │   │   ├── StaticObservable.h    # Singleton variant
│   │   │   └── EventQueue.h          # FreeRTOS queue wrapper
│   │   └── src/
│   │       └── observable_sensor.cpp
│   ├── BleService/
│   │   ├── CMakeLists.txt
│   │   ├── include/
│   │   │   ├── BleService.h          # Facade class
│   │   │   ├── GapManager.h          # GAP advertising/scanning
│   │   │   ├── GattServer.h          # GATT Server (peripheral)
│   │   │   ├── GattClient.h          # GATT Client (central)
│   │   │   └── ble_uuids.h           # UUID definitions
│   │   └── src/
│   │       ├── ble_service.cpp
│   │       ├── gap_manager.cpp
│   │       ├── gatt_server.cpp
│   │       └── gatt_client.cpp
│   └── CommandService/
│       ├── CMakeLists.txt
│       ├── include/
│       │   ├── CommandDefs.h          # Cluster/command enums
│       │   ├── CommandDispatcher.h    # Dispatch by cluster:command
│       │   ├── CommandFactory.h       # Handler registration
│       │   ├── CommandCodec.h         # nanopb encode/decode
│       │   ├── ArcanaFrame.h          # Frame build/parse
│       │   ├── CryptoEngine.h         # AES-256-CCM + ECDH
│       │   ├── SessionManager.h       # Session lifecycle
│       │   └── KeyExchange.h          # ECDH P-256 handshake
│       ├── src/
│       │   ├── command_dispatcher.cpp
│       │   ├── command_factory.cpp
│       │   ├── command_codec.cpp
│       │   ├── arcana_frame.cpp
│       │   ├── crypto_engine.cpp
│       │   ├── session_manager.cpp
│       │   └── key_exchange.cpp
│       └── proto/
│           ├── command.proto          # nanopb protobuf definitions
│           └── command.options        # nanopb field options
├── partitions.csv                     # Custom partition table
├── sdkconfig.defaults                 # Default Kconfig values
└── pytest/                            # Host-based unit tests
    ├── test_frame.py
    ├── test_codec.py
    └── test_crypto.py
```

---

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| ESP-IDF | v5.5 | SDK & build system |
| C++ | 17 | Application language |
| ESP32-S3 | N16R8 | MCU (dual-core Xtensa LX7, 240MHz) |
| FreeRTOS | 10.5.1 | RTOS kernel (SMP) |
| Bluedroid | ESP-IDF built-in | BLE stack (GAP + GATT + SMP) |
| mbedTLS | 3.x (ESP-IDF) | AES-256-CCM, ECDH P-256, HKDF |
| nanopb | 0.4.x | Protobuf for embedded (no heap) |
| MQTT | v5.0 | Cloud connectivity |
| CMake | 3.24+ | Build system |

### Architecture Rating: 9.2/10

| Category | Score | Notes |
|----------|-------|-------|
| Security | 9.5 | AES-256-CCM + ECDH + session mgmt |
| Memory Efficiency | 9.0 | 39% DRAM, static alloc, nanopb |
| Protocol Design | 9.5 | Unified frame, 9B overhead |
| Code Quality | 9.0 | C++17, templates, RAII |
| Extensibility | 9.0 | Observable + Command dispatch |
| BLE Architecture | 9.5 | Dual-role, facade pattern |
| WiFi Coexistence | 8.5 | Functional but needs tuning |

---

## Instructions

When handling ESP32-S3 development tasks, follow these principles:

### Always Do:
1. **Check `esp_err_t` returns** on every ESP-IDF API call
2. **Use `ESP_RETURN_ON_ERROR`** for chained initialization
3. **Encrypt all payloads** after session establishment
4. **Validate frames** (Magic, CRC-16, Length) before parsing
5. **Measure stack watermarks** before finalizing task stack sizes
6. **Use PSRAM** for buffers > 512 bytes
7. **Feed watchdog** in long-running loops
8. **Zero key material** when destroying sessions

### Never Do:
1. **Never reuse AES nonces** - monotonic counter, new key on reconnect
2. **Never allocate heap in ISR** - use `FromISR` queue variants
3. **Never use `std::string`** in DRAM-critical code paths
4. **Never skip MTU negotiation** before large BLE transfers
5. **Never start MQTT before WiFi is connected** (`WIFI_EVENT_STA_GOT_IP`)
6. **Never access BLE and WiFi radio without coexistence API**
7. **Never store plaintext keys in NVS** - use NVS encryption
8. **Never exceed 4 concurrent crypto sessions** (SRAM limit)

### Quick Verification Commands

```bash
# 1. Build project
idf.py build 2>&1 | tail -20

# 2. Check DRAM usage
idf.py size-components | grep -E "DRAM|Total"

# 3. Flash and monitor
idf.py -p /dev/ttyUSB0 flash monitor

# 4. Check for unencrypted commands
grep -rn "send\|write" components/CommandService/src/ | grep -v "encrypt\|cipher"

# 5. Verify nanopb options
grep -rn "max_size" components/CommandService/proto/*.options

# 6. Check esp_err_t handling
grep -rn "esp_ble_\|esp_wifi_\|esp_mqtt_" components/ main/ | grep -v "ESP_ERROR_CHECK\|ESP_RETURN_ON_ERROR\|err\|ret"
```

---

## When to Use This Skill

- ESP32-S3 firmware development with BLE and/or WiFi
- IoT command protocol design and implementation
- BLE GATT Server/Client development with Bluedroid
- Secure communication with AES-256-CCM + ECDH
- Observable sensor pattern implementation
- MQTT5 integration with cloud platforms
- Memory-constrained embedded development
- Code review for IoT security and reliability
- FreeRTOS task architecture design
- WiFi+BLE coexistence debugging
