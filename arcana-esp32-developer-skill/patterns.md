# ESP32 Developer Skill - Design Patterns

## Table of Contents
1. [Observable Pattern Variants](#observable-pattern-variants)
2. [Command Dispatch Pattern](#command-dispatch-pattern)
3. [Codec Chain Pattern](#codec-chain-pattern)
4. [Singleton Facade Pattern](#singleton-facade-pattern)
5. [Session Lifecycle Pattern](#session-lifecycle-pattern)
6. [Event Queue Pattern](#event-queue-pattern)
7. [Protocol Pipeline Pattern](#protocol-pipeline-pattern)
8. [Resource Guard Pattern](#resource-guard-pattern)
9. [Coexistence Arbitration Pattern](#coexistence-arbitration-pattern)
10. [Memory Allocation Strategy](#memory-allocation-strategy)

---

## Observable Pattern Variants

### Pattern Overview

```
+---------------------------------------------------------------+
|                   Observable Pattern Family                     |
|  +-------------------+  +------------------+  +--------------+ |
|  | Observable<T,N>   |  | StaticObservable |  | EventQueue   | |
|  | Instance-scoped   |  | Singleton-scoped |  | Cross-task   | |
|  | Mutex-protected   |  | Static storage   |  | ISR-safe     | |
|  | Direct callbacks  |  | Global access    |  | Async decouple| |
|  +-------------------+  +------------------+  +--------------+ |
+---------------------------------------------------------------+
```

### Variant 1: Observable<T, N> - Instance Observable

**When to use**: Per-sensor instance that multiple components observe.

```cpp
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

**Constraints**:
- Callbacks run on the caller's task (inside mutex)
- Do NOT call `setValue` on another Observable from within a callback (deadlock risk)
- MaxObservers is compile-time (fixed array, no heap)

### Variant 2: StaticObservable<T, N> - Singleton Observable

**When to use**: System-wide unique sensors (CPU temperature, battery level).

```cpp
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
    StaticObservable(const StaticObservable&) = delete;
    StaticObservable& operator=(const StaticObservable&) = delete;
    Observable<T, MaxObservers> observable_;
};

// Usage:
using SystemTemp = StaticObservable<float, 4>;
SystemTemp::instance().setValue(42.5f);
```

### Variant 3: EventQueue<T, N> - Async Cross-Task Observable

**When to use**: Decoupled communication between FreeRTOS tasks, ISR-safe.

```cpp
template <typename T, size_t Depth = 8>
class EventQueue {
public:
    EventQueue() : queue_(xQueueCreate(Depth, sizeof(T))) {
        configASSERT(queue_ != nullptr);
    }

    ~EventQueue() { vQueueDelete(queue_); }

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

    bool peek(T& event) const {
        return xQueuePeek(queue_, &event, 0) == pdTRUE;
    }

    size_t available() const {
        return uxQueueMessagesWaiting(queue_);
    }

private:
    QueueHandle_t queue_;
};
```

### Choosing the Right Variant

| Scenario | Variant | Reason |
|----------|---------|--------|
| Temperature sensor with BLE + display | `Observable<float, 4>` | Multiple local observers |
| System battery level (global) | `StaticObservable<float, 2>` | Single source of truth |
| Sensor -> MQTT task | `EventQueue<SensorEvent, 16>` | Cross-task, async |
| GPIO ISR -> processing task | `EventQueue<GpioEvent, 32>` | ISR-safe with `sendFromISR` |
| BLE notification to N clients | `Observable<BleNotif, 8>` | Per-connection observers |

---

## Command Dispatch Pattern

### Architecture (Matter/ZCL-Style)

```
+-------------------------------------------------------------------+
|                          Incoming Frame                             |
|  [Magic][Ver][Flags][StreamID][Len][Encrypted Payload][CRC-16]     |
+-------------------------------------------------------------------+
         |
         v
+-------------------------------------------------------------------+
|  ArcanaFrame::parse()  -->  CryptoEngine::decrypt()                |
+-------------------------------------------------------------------+
         |
         v
+-------------------------------------------------------------------+
|  CommandCodec::decode()  (nanopb)                                  |
|  { cluster_id: 0x01, command_id: 0x00, sequence: 42, payload }    |
+-------------------------------------------------------------------+
         |
         v
+-------------------------------------------------------------------+
|  CommandDispatcher::dispatch(cluster_id, command_id)               |
|                                                                     |
|  handlers_[makeKey(0x01, 0x00)]  -->  SensorReadHandler::execute() |
+-------------------------------------------------------------------+
         |
         v
+-------------------------------------------------------------------+
|  CommandResponse { status, payload }                                |
|  --> CommandCodec::encode() --> CryptoEngine::encrypt()             |
|  --> ArcanaFrame::build() --> BLE Notify / MQTT Publish             |
+-------------------------------------------------------------------+
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Lookup structure | `std::unordered_map<uint16_t, Handler>` | O(1) dispatch, 256 max commands |
| Key encoding | `(cluster << 8) | command` | Single 16-bit lookup key |
| Handler type | `std::function` | Supports free functions and lambdas |
| Registration | Static `CommandFactory::registerAll()` | Compile-time completeness check |
| Error return | `CommandStatus` enum | Maps to wire format status byte |

### Adding a New Cluster

```cpp
// 1. Define new cluster and commands
enum class LedCmd : uint8_t {
    kSetColor    = 0x00,
    kSetPattern  = 0x01,
    kGetState    = 0x02,
};

// 2. Create handler
class LedSetColorHandler {
public:
    static CommandStatus execute(const CommandRequest& req,
                                 CommandResponse& rsp) {
        if (req.payload_len != 3) {  // R, G, B
            return CommandStatus::kInvalidField;
        }

        uint8_t r = req.payload[0];
        uint8_t g = req.payload[1];
        uint8_t b = req.payload[2];

        setLedColor(r, g, b);  // Hardware call

        rsp.status = CommandStatus::kSuccess;
        return CommandStatus::kSuccess;
    }
};

// 3. Register in factory
constexpr uint8_t kLedCluster = 0x05;
dispatcher.registerHandler(kLedCluster,
    static_cast<uint8_t>(LedCmd::kSetColor),
    LedSetColorHandler::execute);
```

---

## Codec Chain Pattern

### Pipeline Stages

```
Encode Path (outgoing):
  Struct --> nanopb encode --> AES-256-CCM encrypt --> Frame build --> Tx

Decode Path (incoming):
  Rx --> Frame parse --> AES-256-CCM decrypt --> nanopb decode --> Struct
```

### Codec Chain Implementation

```cpp
class CodecChain {
public:
    // Full encode pipeline
    esp_err_t encode(const CommandResponse& rsp,
                     CryptoEngine::Session& session,
                     uint8_t* frame_buf, size_t frame_buf_len,
                     size_t& frame_len) {
        // Stage 1: Serialize
        uint8_t proto_buf[256];
        size_t proto_len = 0;
        if (!CommandCodec::encode(rsp, proto_buf, sizeof(proto_buf), proto_len)) {
            return ESP_ERR_INVALID_SIZE;
        }

        // Stage 2: Encrypt
        uint8_t cipher_buf[256 + CryptoEngine::kTagSize];
        uint8_t tag[CryptoEngine::kTagSize];
        uint8_t aad[4] = {rsp.cluster_id, rsp.command_id,
                           static_cast<uint8_t>(rsp.sequence >> 8),
                           static_cast<uint8_t>(rsp.sequence & 0xFF)};

        ESP_RETURN_ON_ERROR(
            crypto_.encrypt(session, proto_buf, proto_len,
                           aad, sizeof(aad), cipher_buf, tag),
            TAG, "Encrypt failed");

        memcpy(&cipher_buf[proto_len], tag, CryptoEngine::kTagSize);
        size_t encrypted_len = proto_len + CryptoEngine::kTagSize;

        // Stage 3: Frame
        frame_len = ArcanaFrame::build(
            0x01,   // ENCRYPTED flag
            0x00,   // stream_id
            cipher_buf, encrypted_len,
            frame_buf, frame_buf_len);

        return (frame_len > 0) ? ESP_OK : ESP_ERR_INVALID_SIZE;
    }

    // Full decode pipeline
    esp_err_t decode(const uint8_t* frame_buf, size_t frame_len,
                     CryptoEngine::Session& session,
                     CommandRequest& req) {
        // Stage 1: Parse frame
        auto frame = ArcanaFrame::parse(frame_buf, frame_len);
        if (!frame.valid) return ESP_ERR_INVALID_CRC;

        // Stage 2: Decrypt
        if (!(frame.flags & 0x01)) {
            return ESP_ERR_NOT_SUPPORTED;  // Must be encrypted
        }

        size_t cipher_len = frame.payload_len - CryptoEngine::kTagSize;
        const uint8_t* tag = &frame.payload[cipher_len];
        uint8_t plain_buf[256];
        uint8_t aad[1] = {frame.stream_id};

        ESP_RETURN_ON_ERROR(
            crypto_.decrypt(session, frame.payload, cipher_len,
                           aad, sizeof(aad), tag, plain_buf),
            TAG, "Decrypt/auth failed");

        // Stage 3: Deserialize
        if (!CommandCodec::decode(plain_buf, cipher_len, req)) {
            return ESP_ERR_INVALID_ARG;
        }

        return ESP_OK;
    }

private:
    CryptoEngine crypto_;
};
```

### Error Propagation Through Chain

| Stage | Error | Action |
|-------|-------|--------|
| Frame parse | Invalid magic/CRC | Drop frame, log warning |
| Decrypt | Auth tag mismatch | Drop frame, log error (tampering!) |
| nanopb decode | Malformed protobuf | Drop frame, send error response |
| Dispatch | Unknown cluster/command | Send `kUnsupportedCommand` response |
| Handler | Business logic error | Send specific error status |

---

## Singleton Facade Pattern

### BleService as Facade

```
+-------------------------------------------------------------------+
|                      BleService (Facade)                            |
|                                                                     |
|  Public API:                                                        |
|    init()                                                           |
|    startAdvertising()                                               |
|    stopAdvertising()                                                |
|    sendNotification(conn_id, data, len)                             |
|    scanStart() / scanStop()                                         |
|    connectTo(address)                                               |
|                                                                     |
|  Delegates to:                                                      |
|  +-------------------+  +-------------------+  +------------------+ |
|  |   GapManager      |  |   GattServer      |  |   GattClient     | |
|  | - adv params      |  | - attr table      |  | - scan results   | |
|  | - scan params     |  | - event handler   |  | - remote services| |
|  | - conn params     |  | - handle table    |  | - event handler  | |
|  | - security/bond   |  | - MTU tracking    |  | - MTU tracking   | |
|  +-------------------+  +-------------------+  +------------------+ |
+-------------------------------------------------------------------+
```

### Implementation

```cpp
// components/BleService/include/BleService.h
class BleService {
public:
    static BleService& instance() {
        static BleService inst;
        return inst;
    }

    esp_err_t init() {
        ESP_RETURN_ON_ERROR(gap_.init(), TAG, "GAP init failed");
        ESP_RETURN_ON_ERROR(gatt_server_.init(), TAG, "GATTS init failed");
        ESP_RETURN_ON_ERROR(gatt_client_.init(), TAG, "GATTC init failed");
        return ESP_OK;
    }

    // Peripheral role (GATT Server)
    esp_err_t startAdvertising() { return gap_.startAdvertising(); }
    esp_err_t stopAdvertising() { return gap_.stopAdvertising(); }

    esp_err_t sendNotification(uint16_t conn_id,
                                uint16_t char_idx,
                                const uint8_t* data,
                                size_t len) {
        return gatt_server_.sendNotification(conn_id, char_idx, data, len);
    }

    // Central role (GATT Client)
    esp_err_t scanStart(uint32_t duration_s) {
        return gatt_client_.scanStart(duration_s);
    }

    esp_err_t connectTo(const esp_bd_addr_t addr) {
        return gatt_client_.connectTo(addr);
    }

    // Connection management
    uint16_t getMtu(uint16_t conn_id) {
        return gatt_server_.getMtu(conn_id);
    }

    bool isConnected(uint16_t conn_id) const {
        return gap_.isConnected(conn_id);
    }

private:
    BleService() = default;
    BleService(const BleService&) = delete;

    GapManager gap_;
    GattServer gatt_server_;
    GattClient gatt_client_;
};
```

### Why Facade for BLE

| Without Facade | With Facade |
|---------------|-------------|
| App calls `esp_ble_gap_*` directly | App calls `BleService::startAdvertising()` |
| Must manage GAP + GATTS + GATTC callbacks | Single entry point handles all |
| Easy to forget coexistence rules | Facade enforces rules internally |
| Multiple components reference raw handles | Handle table encapsulated |

---

## Session Lifecycle Pattern

### State Machine

```
+--------+     createSession()     +-----------+
| VACANT | ----------------------> | ALLOCATED |
+--------+                         +-----------+
    ^                                     |
    |                                     | performKeyExchange()
    |                                     v
    |                              +-------------+
    | destroySession()             | KEY_EXCHANGE |
    | (zero key material)          +-------------+
    |                                     |
    |                                     | ECDH + HKDF complete
    |                                     v
    |                              +-----------+
    +--------- timeout/disconnect  |  ACTIVE   |
                                   +-----------+
                                          |
                                          | encrypt() / decrypt()
                                          | (nonce_counter++)
                                          v
                                   +-----------+
                                   |  ACTIVE   | (same state, counter increments)
                                   +-----------+
```

### Session Slot Management

```cpp
class SessionManager {
    static constexpr size_t kMaxSessions = 4;

    struct SessionSlot {
        CryptoEngine::Session session;
        uint16_t conn_id;
        int64_t created_at;
        int64_t last_active;
        enum State { kVacant, kAllocated, kKeyExchange, kActive } state;
    };

    SessionSlot slots_[kMaxSessions]{};

    SessionSlot* findSlot(uint16_t conn_id) {
        for (auto& s : slots_) {
            if (s.state != SessionSlot::kVacant && s.conn_id == conn_id) {
                return &s;
            }
        }
        return nullptr;
    }

    SessionSlot* allocateSlot() {
        // Find vacant slot
        for (auto& s : slots_) {
            if (s.state == SessionSlot::kVacant) return &s;
        }
        // Evict oldest inactive session
        SessionSlot* oldest = nullptr;
        for (auto& s : slots_) {
            if (!oldest || s.last_active < oldest->last_active) {
                oldest = &s;
            }
        }
        if (oldest) {
            mbedtls_platform_zeroize(oldest->session.key,
                CryptoEngine::kKeySize);
            oldest->state = SessionSlot::kVacant;
        }
        return oldest;
    }
};
```

---

## Resource Guard Pattern

### RAII for ESP-IDF Resources

```cpp
// Mutex guard using FreeRTOS semaphore
class MutexGuard {
public:
    explicit MutexGuard(SemaphoreHandle_t mutex,
                        TickType_t timeout = portMAX_DELAY)
        : mutex_(mutex)
        , acquired_(xSemaphoreTake(mutex, timeout) == pdTRUE) {}

    ~MutexGuard() {
        if (acquired_) xSemaphoreGive(mutex_);
    }

    bool acquired() const { return acquired_; }

    MutexGuard(const MutexGuard&) = delete;
    MutexGuard& operator=(const MutexGuard&) = delete;

private:
    SemaphoreHandle_t mutex_;
    bool acquired_;
};

// Usage:
void Observable::setValue(const T& val) {
    MutexGuard lock(mutex_, pdMS_TO_TICKS(100));
    if (!lock.acquired()) {
        ESP_LOGW(TAG, "Mutex timeout in setValue");
        return;
    }
    // Safe to modify state
    value_ = val;
}
```

### NVS Handle Guard

```cpp
class NvsGuard {
public:
    NvsGuard(const char* ns, nvs_open_mode_t mode)
        : handle_(0), valid_(false) {
        valid_ = (nvs_open(ns, mode, &handle_) == ESP_OK);
    }

    ~NvsGuard() {
        if (valid_) nvs_close(handle_);
    }

    nvs_handle_t get() const { return handle_; }
    bool valid() const { return valid_; }

private:
    nvs_handle_t handle_;
    bool valid_;
};

// Usage:
esp_err_t readConfig() {
    NvsGuard nvs("config", NVS_READONLY);
    if (!nvs.valid()) return ESP_ERR_NVS_NOT_FOUND;

    size_t len = 0;
    return nvs_get_blob(nvs.get(), "key", buffer, &len);
}
```

### mbedTLS Context Guard

```cpp
class CcmGuard {
public:
    CcmGuard() { mbedtls_ccm_init(&ctx_); }
    ~CcmGuard() { mbedtls_ccm_free(&ctx_); }

    mbedtls_ccm_context* get() { return &ctx_; }

    esp_err_t setKey(const uint8_t* key, size_t bits) {
        return (mbedtls_ccm_setkey(&ctx_, MBEDTLS_CIPHER_ID_AES,
                key, bits) == 0) ? ESP_OK : ESP_FAIL;
    }

private:
    mbedtls_ccm_context ctx_;
};

// Usage:
esp_err_t encrypt(const uint8_t* key, ...) {
    CcmGuard ccm;
    ESP_RETURN_ON_ERROR(ccm.setKey(key, 256), TAG, "Key setup failed");

    int ret = mbedtls_ccm_encrypt_and_tag(ccm.get(), ...);
    return (ret == 0) ? ESP_OK : ESP_FAIL;
    // ccm context automatically freed on scope exit
}
```

---

## Coexistence Arbitration Pattern

### Dynamic Priority Switching

```cpp
class CoexArbitrator {
public:
    enum class Mode {
        kBalance,     // Normal operation
        kWifiBoost,   // OTA download, large MQTT transfer
        kBleBoost,    // Key exchange, large BLE transfer
    };

    void setMode(Mode mode) {
        switch (mode) {
        case Mode::kBalance:
            esp_coex_preference_set(ESP_COEX_PREFER_BALANCE);
            break;
        case Mode::kWifiBoost:
            esp_coex_preference_set(ESP_COEX_PREFER_WIFI);
            break;
        case Mode::kBleBoost:
            esp_coex_preference_set(ESP_COEX_PREFER_BT);
            break;
        }
        current_mode_ = mode;
        ESP_LOGI(TAG, "Coex mode: %d", static_cast<int>(mode));
    }

    // Auto-restore after scoped operation
    class ScopedMode {
    public:
        ScopedMode(CoexArbitrator& arb, Mode mode)
            : arb_(arb), previous_(arb.current_mode_) {
            arb_.setMode(mode);
        }
        ~ScopedMode() { arb_.setMode(previous_); }
    private:
        CoexArbitrator& arb_;
        Mode previous_;
    };

private:
    Mode current_mode_ = Mode::kBalance;
};

// Usage:
void performOta(const char* url) {
    CoexArbitrator::ScopedMode boost(coex_arb, CoexArbitrator::Mode::kWifiBoost);
    // WiFi has priority during this scope
    esp_https_ota(&ota_cfg);
    // Automatically restores Balance mode when scope exits
}
```

---

## Memory Allocation Strategy

### Decision Tree

```
Need memory allocation?
    |
    +-- Is it in ISR? --> NO heap allocation. Use static buffer or queue.
    |
    +-- Is it < 512B? --> Stack allocation (local array)
    |
    +-- Is it < 4KB? --> DRAM heap (MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT)
    |
    +-- Is it >= 4KB? --> PSRAM heap (MALLOC_CAP_SPIRAM)
    |
    +-- Is it a singleton? --> Static allocation (file-scope or class static)
    |
    +-- Does it live forever? --> Static allocation
    |
    +-- Is the count fixed at compile time? --> Fixed array, template param
```

### Allocation Helpers

```cpp
// Typed PSRAM allocator
template <typename T>
T* psramAlloc(size_t count = 1) {
    return static_cast<T*>(
        heap_caps_calloc(count, sizeof(T), MALLOC_CAP_SPIRAM));
}

// Typed DRAM allocator
template <typename T>
T* dramAlloc(size_t count = 1) {
    return static_cast<T*>(
        heap_caps_calloc(count, sizeof(T),
            MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT));
}

// Scoped heap allocation (RAII)
template <typename T>
class HeapBuffer {
public:
    HeapBuffer(size_t count, uint32_t caps)
        : ptr_(static_cast<T*>(heap_caps_calloc(count, sizeof(T), caps)))
        , count_(count) {}

    ~HeapBuffer() { if (ptr_) heap_caps_free(ptr_); }

    T* get() { return ptr_; }
    const T* get() const { return ptr_; }
    size_t size() const { return count_; }
    explicit operator bool() const { return ptr_ != nullptr; }

    HeapBuffer(const HeapBuffer&) = delete;
    HeapBuffer& operator=(const HeapBuffer&) = delete;

private:
    T* ptr_;
    size_t count_;
};

// Usage:
void processLargePayload(const uint8_t* data, size_t len) {
    // Allocate work buffer from PSRAM
    HeapBuffer<uint8_t> work_buf(len * 2, MALLOC_CAP_SPIRAM);
    if (!work_buf) {
        ESP_LOGE(TAG, "PSRAM alloc failed for %zu bytes", len * 2);
        return;
    }

    // Use work_buf.get() for processing
    memcpy(work_buf.get(), data, len);
    // ... process ...
    // Automatically freed when scope exits
}
```

### Memory Budget Enforcement

```cpp
// Diagnostic command handler (System cluster 0x00, cmd 0x03)
class DiagHeapHandler {
public:
    static CommandStatus execute(const CommandRequest& req,
                                 CommandResponse& rsp) {
        struct HeapInfo {
            uint32_t dram_free;
            uint32_t dram_min;
            uint32_t psram_free;
            uint32_t psram_min;
            uint32_t dram_largest_block;
        } __attribute__((packed));

        HeapInfo info{};
        info.dram_free = heap_caps_get_free_size(MALLOC_CAP_8BIT);
        info.dram_min = heap_caps_get_minimum_free_size(MALLOC_CAP_8BIT);
        info.psram_free = heap_caps_get_free_size(MALLOC_CAP_SPIRAM);
        info.psram_min = heap_caps_get_minimum_free_size(MALLOC_CAP_SPIRAM);
        info.dram_largest_block =
            heap_caps_get_largest_free_block(MALLOC_CAP_8BIT);

        memcpy(rsp.payload, &info, sizeof(info));
        rsp.payload_len = sizeof(info);
        rsp.status = CommandStatus::kSuccess;

        ESP_LOGI(TAG, "DRAM: %lu free (%lu min), PSRAM: %lu free",
                 info.dram_free, info.dram_min, info.psram_free);

        return CommandStatus::kSuccess;
    }
};
```

---

## Pattern Summary Table

| Pattern | Component | Purpose | Key Constraint |
|---------|-----------|---------|----------------|
| Observable<T,N> | ObservableSensor | Value-change notifications | MaxObservers at compile-time |
| StaticObservable | ObservableSensor | Singleton sensor access | One instance per type |
| EventQueue<T,N> | ObservableSensor | Cross-task async events | ISR-safe, fixed depth |
| Command Dispatch | CommandService | Route by cluster:command | O(1) lookup, 256 max |
| Codec Chain | CommandService | Serialize-encrypt-frame pipeline | Fixed buffer sizes |
| Singleton Facade | BleService | Unified BLE API | Single instance |
| Session Lifecycle | CommandService | Crypto session state machine | Max 4 concurrent |
| Resource Guard | All | RAII for ESP-IDF resources | Scope-based cleanup |
| Coex Arbitration | System | WiFi/BLE priority switching | Mode restore on scope exit |
| Memory Strategy | All | DRAM/PSRAM/stack allocation | No heap in ISR |
