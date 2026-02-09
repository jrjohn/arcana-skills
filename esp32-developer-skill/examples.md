# ESP32 Developer Skill - Code Examples

## Table of Contents
1. [New Command Implementation](#new-command-implementation)
2. [BLE Service with Custom Characteristic](#ble-service-with-custom-characteristic)
3. [Crypto Session Lifecycle](#crypto-session-lifecycle)
4. [MQTT5 Sensor Telemetry](#mqtt5-sensor-telemetry)
5. [Observable Sensor with Cross-Task Events](#observable-sensor-with-cross-task-events)
6. [Arcana Frame Round-Trip](#arcana-frame-round-trip)
7. [WiFi+BLE Coexistence Setup](#wifiuble-coexistence-setup)
8. [OTA Firmware Update](#ota-firmware-update)
9. [NVS Encrypted Key Storage](#nvs-encrypted-key-storage)
10. [FreeRTOS Task Architecture](#freertos-task-architecture)

---

## New Command Implementation

### Step 1: Define Command in CommandDefs.h

```cpp
// components/CommandService/include/CommandDefs.h

// Cluster IDs (Matter/ZCL-style)
enum class ClusterId : uint8_t {
    kSystem   = 0x00,
    kSensor   = 0x01,
    kBle      = 0x02,
    kMqtt     = 0x03,
    kSecurity = 0x04,
    kDevice   = 0x05,  // NEW: Device management cluster
};

// Device cluster commands
enum class DeviceCmd : uint8_t {
    kReboot       = 0x00,
    kFactoryReset = 0x01,
    kSetName      = 0x02,
    kGetConfig    = 0x03,
};

// Request/Response structs (matches nanopb generated)
struct DeviceSetNameRequest {
    char name[32];
    size_t name_len;
};

struct DeviceSetNameResponse {
    CommandStatus status;
    char previous_name[32];
    size_t previous_name_len;
};
```

### Step 2: Create Command Handler

```cpp
// components/CommandService/include/handlers/DeviceSetNameHandler.h
#pragma once

#include "CommandDefs.h"
#include "CommandDispatcher.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include <cstring>

static constexpr const char* TAG = "DevSetName";

class DeviceSetNameHandler {
public:
    static CommandStatus execute(const CommandRequest& req,
                                 CommandResponse& rsp) {
        // Decode request payload via nanopb
        DeviceSetNameRequest set_req{};
        if (req.payload_len == 0 || req.payload_len > sizeof(set_req.name)) {
            ESP_LOGE(TAG, "Invalid name length: %zu", req.payload_len);
            return CommandStatus::kInvalidField;
        }

        memcpy(set_req.name, req.payload, req.payload_len);
        set_req.name_len = req.payload_len;

        // Read current name from NVS
        nvs_handle_t nvs;
        esp_err_t err = nvs_open("device", NVS_READWRITE, &nvs);
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "NVS open failed: %s", esp_err_to_name(err));
            return CommandStatus::kHardwareError;
        }

        // Get previous name for response
        DeviceSetNameResponse set_rsp{};
        size_t prev_len = sizeof(set_rsp.previous_name);
        err = nvs_get_str(nvs, "name", set_rsp.previous_name, &prev_len);
        if (err == ESP_OK) {
            set_rsp.previous_name_len = prev_len;
        }

        // Write new name
        err = nvs_set_str(nvs, "name", set_req.name);
        if (err != ESP_OK) {
            nvs_close(nvs);
            ESP_LOGE(TAG, "NVS write failed: %s", esp_err_to_name(err));
            return CommandStatus::kHardwareError;
        }

        err = nvs_commit(nvs);
        nvs_close(nvs);

        if (err != ESP_OK) {
            return CommandStatus::kHardwareError;
        }

        // Build response
        set_rsp.status = CommandStatus::kSuccess;
        rsp.cluster_id = req.cluster_id;
        rsp.command_id = req.command_id;
        rsp.sequence = req.sequence;
        rsp.status = CommandStatus::kSuccess;
        memcpy(rsp.payload, &set_rsp, sizeof(set_rsp));
        rsp.payload_len = sizeof(set_rsp);

        ESP_LOGI(TAG, "Device name changed to: %s", set_req.name);
        return CommandStatus::kSuccess;
    }
};
```

### Step 3: Register in CommandFactory

```cpp
// components/CommandService/src/command_factory.cpp
#include "CommandFactory.h"
#include "handlers/DeviceSetNameHandler.h"
// ... other handlers

void CommandFactory::registerAll(CommandDispatcher& dispatcher) {
    // ... existing registrations ...

    // Device cluster 0x05
    dispatcher.registerHandler(
        static_cast<uint8_t>(ClusterId::kDevice),
        static_cast<uint8_t>(DeviceCmd::kSetName),
        DeviceSetNameHandler::execute);
}
```

### Step 4: Define nanopb Proto

```protobuf
// components/CommandService/proto/device.proto
syntax = "proto3";

message DeviceSetNameRequest {
    string name = 1;
}

message DeviceSetNameResponse {
    uint32 status = 1;
    string previous_name = 2;
}
```

```
// components/CommandService/proto/device.options
DeviceSetNameRequest.name         max_size:32
DeviceSetNameResponse.previous_name max_size:32
```

### Step 5: Unit Test

```cpp
// pytest/test_device_cmd.cpp (host-based test with mocks)
#include <gtest/gtest.h>
#include "handlers/DeviceSetNameHandler.h"

TEST(DeviceSetNameHandler, ValidName) {
    CommandRequest req{};
    req.cluster_id = 0x05;
    req.command_id = 0x02;
    req.sequence = 42;
    const char* name = "MyDevice";
    memcpy(req.payload, name, strlen(name));
    req.payload_len = strlen(name);

    CommandResponse rsp{};
    auto status = DeviceSetNameHandler::execute(req, rsp);

    EXPECT_EQ(status, CommandStatus::kSuccess);
    EXPECT_EQ(rsp.cluster_id, 0x05);
    EXPECT_EQ(rsp.sequence, 42);
}

TEST(DeviceSetNameHandler, EmptyName) {
    CommandRequest req{};
    req.payload_len = 0;

    CommandResponse rsp{};
    auto status = DeviceSetNameHandler::execute(req, rsp);

    EXPECT_EQ(status, CommandStatus::kInvalidField);
}

TEST(DeviceSetNameHandler, NameTooLong) {
    CommandRequest req{};
    req.payload_len = 64;  // Exceeds 32-byte limit

    CommandResponse rsp{};
    auto status = DeviceSetNameHandler::execute(req, rsp);

    EXPECT_EQ(status, CommandStatus::kInvalidField);
}
```

---

## BLE Service with Custom Characteristic

### Define Custom UUIDs

```cpp
// components/BleService/include/ble_uuids.h
#pragma once
#include "esp_bt_defs.h"

// Arcana Service UUID: 6E400001-B5A3-F393-E0A9-E50E24DCCA9E
static const uint8_t arcana_svc_uuid[16] = {
    0x9E, 0xCA, 0xDC, 0x24, 0x0E, 0xE5, 0xA9, 0xE0,
    0x93, 0xF3, 0xA3, 0xB5, 0x01, 0x00, 0x40, 0x6E
};

// Command Write UUID: 6E400002-...
static const uint8_t cmd_write_uuid[16] = {
    0x9E, 0xCA, 0xDC, 0x24, 0x0E, 0xE5, 0xA9, 0xE0,
    0x93, 0xF3, 0xA3, 0xB5, 0x02, 0x00, 0x40, 0x6E
};

// Response Notify UUID: 6E400003-...
static const uint8_t cmd_response_uuid[16] = {
    0x9E, 0xCA, 0xDC, 0x24, 0x0E, 0xE5, 0xA9, 0xE0,
    0x93, 0xF3, 0xA3, 0xB5, 0x03, 0x00, 0x40, 0x6E
};

// Sensor Data Notify UUID: 6E400004-...
static const uint8_t sensor_data_uuid[16] = {
    0x9E, 0xCA, 0xDC, 0x24, 0x0E, 0xE5, 0xA9, 0xE0,
    0x93, 0xF3, 0xA3, 0xB5, 0x04, 0x00, 0x40, 0x6E
};
```

### Add GATT Attribute Table Entry

```cpp
// components/BleService/src/gatt_server.cpp

// Attribute table indices
enum GattDbIdx {
    IDX_SVC,

    // Command Write Characteristic
    IDX_CMD_CHAR,
    IDX_CMD_VAL,

    // Response Notify Characteristic
    IDX_RSP_CHAR,
    IDX_RSP_VAL,
    IDX_RSP_CCC,

    // Sensor Data Notify Characteristic (NEW)
    IDX_SENSOR_CHAR,
    IDX_SENSOR_VAL,
    IDX_SENSOR_CCC,

    IDX_COUNT,
};

static const uint8_t char_prop_write = ESP_GATT_CHAR_PROP_BIT_WRITE;
static const uint8_t char_prop_notify = ESP_GATT_CHAR_PROP_BIT_NOTIFY;
static uint16_t ccc_val = 0x0000;

static const esp_gatts_attr_db_t gatt_db[IDX_COUNT] = {
    // Primary Service Declaration
    [IDX_SVC] = {{ESP_GATT_AUTO_RSP},
        {ESP_UUID_LEN_16, (uint8_t*)&primary_service_uuid,
         ESP_GATT_PERM_READ, sizeof(arcana_svc_uuid),
         sizeof(arcana_svc_uuid), (uint8_t*)&arcana_svc_uuid}},

    // Command Write Characteristic Declaration
    [IDX_CMD_CHAR] = {{ESP_GATT_AUTO_RSP},
        {ESP_UUID_LEN_16, (uint8_t*)&character_declaration_uuid,
         ESP_GATT_PERM_READ, sizeof(uint8_t),
         sizeof(uint8_t), (uint8_t*)&char_prop_write}},

    // Command Write Value (App handles response)
    [IDX_CMD_VAL] = {{ESP_GATT_RSP_BY_APP},
        {ESP_UUID_LEN_128, (uint8_t*)&cmd_write_uuid,
         ESP_GATT_PERM_WRITE_ENCRYPTED, 512, 0, nullptr}},

    // Response Notify Characteristic Declaration
    [IDX_RSP_CHAR] = {{ESP_GATT_AUTO_RSP},
        {ESP_UUID_LEN_16, (uint8_t*)&character_declaration_uuid,
         ESP_GATT_PERM_READ, sizeof(uint8_t),
         sizeof(uint8_t), (uint8_t*)&char_prop_notify}},

    // Response Notify Value
    [IDX_RSP_VAL] = {{ESP_GATT_AUTO_RSP},
        {ESP_UUID_LEN_128, (uint8_t*)&cmd_response_uuid,
         ESP_GATT_PERM_READ, 512, 0, nullptr}},

    // Response CCCD
    [IDX_RSP_CCC] = {{ESP_GATT_AUTO_RSP},
        {ESP_UUID_LEN_16, (uint8_t*)&ccc_uuid,
         ESP_GATT_PERM_READ | ESP_GATT_PERM_WRITE,
         sizeof(uint16_t), sizeof(uint16_t), (uint8_t*)&ccc_val}},

    // Sensor Data Notify Characteristic Declaration
    [IDX_SENSOR_CHAR] = {{ESP_GATT_AUTO_RSP},
        {ESP_UUID_LEN_16, (uint8_t*)&character_declaration_uuid,
         ESP_GATT_PERM_READ, sizeof(uint8_t),
         sizeof(uint8_t), (uint8_t*)&char_prop_notify}},

    // Sensor Data Notify Value
    [IDX_SENSOR_VAL] = {{ESP_GATT_AUTO_RSP},
        {ESP_UUID_LEN_128, (uint8_t*)&sensor_data_uuid,
         ESP_GATT_PERM_READ, 512, 0, nullptr}},

    // Sensor Data CCCD
    [IDX_SENSOR_CCC] = {{ESP_GATT_AUTO_RSP},
        {ESP_UUID_LEN_16, (uint8_t*)&ccc_uuid,
         ESP_GATT_PERM_READ | ESP_GATT_PERM_WRITE,
         sizeof(uint16_t), sizeof(uint16_t), (uint8_t*)&ccc_val}},
};
```

### Implement Notification with MTU Awareness

```cpp
// components/BleService/src/gatt_server.cpp

esp_err_t GattServer::sendNotification(uint16_t conn_id,
                                        GattDbIdx char_idx,
                                        const uint8_t* data,
                                        size_t data_len) {
    uint16_t handle = handle_table_[char_idx];
    uint16_t mtu = getMtu(conn_id);
    uint16_t max_payload = mtu - 3;  // ATT header overhead

    if (data_len <= max_payload) {
        // Single notification
        return esp_ble_gatts_send_indicate(
            gatts_if_, conn_id, handle,
            data_len, const_cast<uint8_t*>(data), false);
    }

    // Fragmented notification for large payloads
    size_t offset = 0;
    uint16_t fragment_idx = 0;
    while (offset < data_len) {
        size_t chunk = std::min(static_cast<size_t>(max_payload - 2),
                                data_len - offset);

        // Fragment header: [fragment_idx:1B][more_fragments:1B][data]
        uint8_t frag_buf[max_payload];
        frag_buf[0] = fragment_idx++;
        frag_buf[1] = (offset + chunk < data_len) ? 0x01 : 0x00;
        memcpy(&frag_buf[2], &data[offset], chunk);

        esp_err_t err = esp_ble_gatts_send_indicate(
            gatts_if_, conn_id, handle,
            chunk + 2, frag_buf, false);

        if (err != ESP_OK) {
            ESP_LOGE(TAG, "Fragment %d send failed: %s",
                     fragment_idx - 1, esp_err_to_name(err));
            return err;
        }

        offset += chunk;
        // Wait for congestion to clear
        vTaskDelay(pdMS_TO_TICKS(10));
    }

    return ESP_OK;
}

uint16_t GattServer::getMtu(uint16_t conn_id) {
    auto it = mtu_map_.find(conn_id);
    return (it != mtu_map_.end()) ? it->second : 23;  // Default MTU
}
```

### Handle MTU Exchange

```cpp
// In GATTS event handler
case ESP_GATTS_MTU_EVT:
    ESP_LOGI(TAG, "MTU updated: conn=%d, mtu=%d",
             param->mtu.conn_id, param->mtu.mtu);
    mtu_map_[param->mtu.conn_id] = param->mtu.mtu;
    break;
```

---

## Crypto Session Lifecycle

### Full ECDH Key Exchange Implementation

```cpp
// components/CommandService/include/KeyExchange.h
#pragma once

#include "CryptoEngine.h"
#include "SessionManager.h"
#include "esp_log.h"
#include "mbedtls/ecdh.h"
#include "mbedtls/hkdf.h"
#include "mbedtls/md.h"
#include "mbedtls/entropy.h"
#include "mbedtls/ctr_drbg.h"
#include <cstring>

static constexpr const char* TAG = "KeyExchange";

class KeyExchange {
public:
    static constexpr size_t kPubKeySize = 64;  // Uncompressed P-256: X(32) + Y(32)
    static constexpr size_t kSharedSecretSize = 32;

    struct ExchangeResult {
        bool success;
        uint8_t device_pub[kPubKeySize];
        uint32_t session_id;
    };

    static ExchangeResult perform(
        SessionManager& session_mgr,
        uint16_t conn_id,
        const uint8_t* peer_pub, size_t peer_pub_len)
    {
        ExchangeResult result{};

        if (peer_pub_len != kPubKeySize) {
            ESP_LOGE(TAG, "Invalid peer public key length: %zu", peer_pub_len);
            return result;
        }

        // Initialize mbedTLS ECDH context
        mbedtls_ecdh_context ecdh;
        mbedtls_ecdh_init(&ecdh);

        mbedtls_entropy_context entropy;
        mbedtls_entropy_init(&entropy);

        mbedtls_ctr_drbg_context ctr_drbg;
        mbedtls_ctr_drbg_init(&ctr_drbg);

        const char* pers = "arcana_ecdh";
        int ret = mbedtls_ctr_drbg_seed(&ctr_drbg, mbedtls_entropy_func,
            &entropy, (const uint8_t*)pers, strlen(pers));
        if (ret != 0) {
            ESP_LOGE(TAG, "DRBG seed failed: %d", ret);
            goto cleanup;
        }

        // Setup ECDH with P-256 curve
        ret = mbedtls_ecdh_setup(&ecdh, MBEDTLS_ECP_DP_SECP256R1);
        if (ret != 0) {
            ESP_LOGE(TAG, "ECDH setup failed: %d", ret);
            goto cleanup;
        }

        // Generate ephemeral device keypair
        ret = mbedtls_ecdh_gen_public(
            &ecdh.MBEDTLS_PRIVATE(grp),
            &ecdh.MBEDTLS_PRIVATE(d),
            &ecdh.MBEDTLS_PRIVATE(Q),
            mbedtls_ctr_drbg_random, &ctr_drbg);
        if (ret != 0) {
            ESP_LOGE(TAG, "ECDH keygen failed: %d", ret);
            goto cleanup;
        }

        // Export device public key (uncompressed: X || Y)
        {
            size_t olen = 0;
            uint8_t pub_buf[65];  // 0x04 + X(32) + Y(32)
            ret = mbedtls_ecp_point_write_binary(
                &ecdh.MBEDTLS_PRIVATE(grp),
                &ecdh.MBEDTLS_PRIVATE(Q),
                MBEDTLS_ECP_PF_UNCOMPRESSED,
                &olen, pub_buf, sizeof(pub_buf));
            if (ret != 0 || olen != 65) {
                ESP_LOGE(TAG, "Export device pub failed: %d", ret);
                goto cleanup;
            }
            memcpy(result.device_pub, &pub_buf[1], kPubKeySize);  // Skip 0x04 prefix
        }

        // Import peer public key
        {
            uint8_t peer_buf[65];
            peer_buf[0] = 0x04;  // Uncompressed prefix
            memcpy(&peer_buf[1], peer_pub, kPubKeySize);

            ret = mbedtls_ecp_point_read_binary(
                &ecdh.MBEDTLS_PRIVATE(grp),
                &ecdh.MBEDTLS_PRIVATE(Qp),
                peer_buf, 65);
            if (ret != 0) {
                ESP_LOGE(TAG, "Import peer pub failed: %d", ret);
                goto cleanup;
            }
        }

        // Compute shared secret
        {
            uint8_t shared[kSharedSecretSize];
            size_t olen = 0;
            ret = mbedtls_ecdh_calc_secret(
                &ecdh, &olen, shared, sizeof(shared),
                mbedtls_ctr_drbg_random, &ctr_drbg);
            if (ret != 0 || olen != kSharedSecretSize) {
                ESP_LOGE(TAG, "ECDH shared secret failed: %d", ret);
                goto cleanup;
            }

            // Create or get session
            CryptoEngine::Session* session = session_mgr.createSession(conn_id);
            if (!session) {
                ESP_LOGE(TAG, "No free session slot");
                goto cleanup;
            }

            result.session_id = session->session_id;

            // Derive session key using HKDF-SHA256
            uint8_t salt[4];
            memcpy(salt, &session->session_id, 4);

            const char* info = "arcana-cmd-v1";
            ret = mbedtls_hkdf(
                mbedtls_md_info_from_type(MBEDTLS_MD_SHA256),
                salt, sizeof(salt),
                shared, kSharedSecretSize,
                (const uint8_t*)info, strlen(info),
                session->key, CryptoEngine::kKeySize);

            // CRITICAL: Zero shared secret immediately
            mbedtls_platform_zeroize(shared, sizeof(shared));

            if (ret != 0) {
                ESP_LOGE(TAG, "HKDF derivation failed: %d", ret);
                session_mgr.destroySession(conn_id);
                goto cleanup;
            }

            result.success = true;
            ESP_LOGI(TAG, "Key exchange complete: conn=%d, sid=0x%08lx",
                     conn_id, result.session_id);
        }

    cleanup:
        mbedtls_ecdh_free(&ecdh);
        mbedtls_ctr_drbg_free(&ctr_drbg);
        mbedtls_entropy_free(&entropy);
        return result;
    }
};
```

### Encrypt-Then-Frame Pipeline

```cpp
// components/CommandService/src/command_pipeline.cpp

esp_err_t CommandPipeline::sendEncryptedResponse(
    uint16_t conn_id,
    const CommandResponse& rsp)
{
    // Step 1: Serialize with nanopb
    uint8_t proto_buf[256];
    size_t proto_len = 0;
    if (!CommandCodec::encode(rsp, proto_buf, sizeof(proto_buf), proto_len)) {
        ESP_LOGE(TAG, "nanopb encode failed");
        return ESP_ERR_INVALID_SIZE;
    }

    // Step 2: Encrypt with AES-256-CCM
    auto* session = session_mgr_.getSession(conn_id);
    if (!session || !session->active) {
        ESP_LOGE(TAG, "No active session for conn=%d", conn_id);
        return ESP_ERR_INVALID_STATE;
    }

    uint8_t cipher_buf[256 + CryptoEngine::kTagSize];
    uint8_t tag[CryptoEngine::kTagSize];

    // AAD = cluster_id || command_id || sequence
    uint8_t aad[4] = {rsp.cluster_id, rsp.command_id,
                       static_cast<uint8_t>(rsp.sequence >> 8),
                       static_cast<uint8_t>(rsp.sequence & 0xFF)};

    ESP_RETURN_ON_ERROR(
        crypto_.encrypt(*session, proto_buf, proto_len,
                        aad, sizeof(aad), cipher_buf, tag),
        TAG, "Encryption failed");

    // Append tag to ciphertext
    memcpy(&cipher_buf[proto_len], tag, CryptoEngine::kTagSize);
    size_t encrypted_len = proto_len + CryptoEngine::kTagSize;

    // Step 3: Build Arcana Frame
    uint8_t frame_buf[512];
    uint8_t flags = 0x01;  // ENCRYPTED flag
    size_t frame_len = ArcanaFrame::build(
        flags, 0x00, cipher_buf, encrypted_len,
        frame_buf, sizeof(frame_buf));

    if (frame_len == 0) {
        ESP_LOGE(TAG, "Frame build failed");
        return ESP_ERR_INVALID_SIZE;
    }

    // Step 4: Send via BLE notification
    return ble_service_.sendNotification(
        conn_id, IDX_RSP_VAL, frame_buf, frame_len);
}
```

### Decrypt-Then-Dispatch Pipeline

```cpp
esp_err_t CommandPipeline::onCommandReceived(
    uint16_t conn_id,
    const uint8_t* data, size_t len)
{
    // Step 1: Parse Arcana Frame
    auto frame = ArcanaFrame::parse(data, len);
    if (!frame.valid) {
        ESP_LOGE(TAG, "Invalid frame (magic/CRC mismatch)");
        return ESP_ERR_INVALID_CRC;
    }

    // Step 2: Decrypt if encrypted flag set
    uint8_t plain_buf[256];
    size_t plain_len = 0;

    if (frame.flags & 0x01) {  // ENCRYPTED
        auto* session = session_mgr_.getSession(conn_id);
        if (!session || !session->active) {
            ESP_LOGE(TAG, "Encrypted frame but no session");
            return ESP_ERR_INVALID_STATE;
        }

        if (frame.payload_len < CryptoEngine::kTagSize) {
            return ESP_ERR_INVALID_SIZE;
        }

        plain_len = frame.payload_len - CryptoEngine::kTagSize;
        const uint8_t* tag = &frame.payload[plain_len];

        // Reconstruct AAD from frame header context
        uint8_t aad[1] = {frame.stream_id};

        ESP_RETURN_ON_ERROR(
            crypto_.decrypt(*session,
                           frame.payload, plain_len,
                           aad, sizeof(aad),
                           tag, plain_buf),
            TAG, "Decryption/auth failed (tampered frame?)");
    } else {
        // Unencrypted frame (only allowed for key exchange)
        memcpy(plain_buf, frame.payload, frame.payload_len);
        plain_len = frame.payload_len;
    }

    // Step 3: Decode with nanopb
    CommandRequest req{};
    if (!CommandCodec::decode(plain_buf, plain_len, req)) {
        ESP_LOGE(TAG, "nanopb decode failed");
        return ESP_ERR_INVALID_ARG;
    }

    // Step 4: Dispatch to handler
    CommandResponse rsp{};
    CommandStatus status = dispatcher_.dispatch(req, rsp);

    if (status != CommandStatus::kSuccess) {
        ESP_LOGW(TAG, "Command %02x:%02x failed: %d",
                 req.cluster_id, req.command_id,
                 static_cast<int>(status));
    }

    // Step 5: Send encrypted response
    return sendEncryptedResponse(conn_id, rsp);
}
```

---

## MQTT5 Sensor Telemetry

### Periodic Sensor Publishing

```cpp
// main/sensor_task.cpp
#include "Observable.h"
#include "EventQueue.h"
#include "esp_mqtt_client.h"
#include "esp_log.h"
#include "cJSON.h"
#include <cstdio>

static constexpr const char* TAG = "SensorTask";

struct SensorReading {
    float temperature;
    float humidity;
    float pressure;
    int64_t timestamp_ms;
};

static Observable<SensorReading, 4> sensor_data;
static EventQueue<SensorReading, 8> mqtt_publish_queue;

// Sensor polling task
void sensorPollingTask(void* param) {
    while (true) {
        SensorReading reading{};
        reading.temperature = readTemperature();  // Hardware abstraction
        reading.humidity = readHumidity();
        reading.pressure = readPressure();
        reading.timestamp_ms = esp_timer_get_time() / 1000;

        // Update observable (notifies BLE subscribers)
        sensor_data.setValue(reading);

        // Also push to MQTT queue
        mqtt_publish_queue.send(reading, pdMS_TO_TICKS(100));

        vTaskDelay(pdMS_TO_TICKS(CONFIG_SENSOR_POLL_INTERVAL_MS));
    }
}

// MQTT publish task
void mqttPublishTask(void* param) {
    auto* mqtt_client = static_cast<esp_mqtt_client_handle_t>(param);

    while (true) {
        SensorReading reading{};
        if (!mqtt_publish_queue.receive(reading, pdMS_TO_TICKS(5000))) {
            continue;  // Timeout, no data
        }

        // Build JSON telemetry payload
        cJSON* root = cJSON_CreateObject();
        cJSON_AddNumberToObject(root, "temperature", reading.temperature);
        cJSON_AddNumberToObject(root, "humidity", reading.humidity);
        cJSON_AddNumberToObject(root, "pressure", reading.pressure);
        cJSON_AddNumberToObject(root, "timestamp", reading.timestamp_ms);

        char* json_str = cJSON_PrintUnformatted(root);
        cJSON_Delete(root);

        if (json_str) {
            char topic[64];
            snprintf(topic, sizeof(topic),
                     "arcana/device/%s/telemetry", CONFIG_DEVICE_ID);

            int msg_id = esp_mqtt_client_publish(
                mqtt_client, topic, json_str, 0,
                0,    // QoS 0 for telemetry (best effort)
                0);   // No retain

            if (msg_id < 0) {
                ESP_LOGW(TAG, "MQTT publish failed");
            }

            free(json_str);
        }
    }
}
```

### MQTT Command Bridge (Unified Pipeline)

```cpp
// main/mqtt_bridge.cpp
// Commands received over MQTT use the SAME pipeline as BLE

static CommandPipeline* cmd_pipeline = nullptr;

void onMqttCommandReceived(const uint8_t* data, size_t len) {
    // MQTT commands arrive as Arcana Frames (same binary format)
    // The MQTT session has its own crypto session (session_id from MQTT auth)
    constexpr uint16_t kMqttVirtualConnId = 0xFFFF;

    esp_err_t err = cmd_pipeline->onCommandReceived(
        kMqttVirtualConnId, data, len);

    if (err != ESP_OK) {
        ESP_LOGE(TAG, "MQTT command processing failed: %s",
                 esp_err_to_name(err));
    }
}

// MQTT response goes back on response topic
esp_err_t sendMqttResponse(const uint8_t* frame, size_t frame_len) {
    char topic[64];
    snprintf(topic, sizeof(topic),
             "arcana/device/%s/rsp", CONFIG_DEVICE_ID);

    int msg_id = esp_mqtt_client_publish(
        mqtt_client, topic,
        reinterpret_cast<const char*>(frame), frame_len,
        1,    // QoS 1 for command responses (guaranteed delivery)
        0);

    return (msg_id >= 0) ? ESP_OK : ESP_FAIL;
}
```

---

## Observable Sensor with Cross-Task Events

### Temperature Sensor with BLE + MQTT Dual Output

```cpp
// components/ObservableSensor/src/temperature_sensor.cpp
#include "Observable.h"
#include "EventQueue.h"
#include "StaticObservable.h"
#include "esp_log.h"

static constexpr const char* TAG = "TempSensor";

// Singleton temperature observable
using TempObservable = StaticObservable<float, 4>;

// Event types for cross-task communication
struct TempEvent {
    enum Type { kUpdate, kAlarm, kCalibrate } type;
    float value;
    int64_t timestamp;
};

static EventQueue<TempEvent, 16> temp_event_queue;

void temperatureMonitorTask(void* param) {
    auto& temp = TempObservable::instance();

    // Observer 1: BLE notification
    temp.subscribe([](const float& old_val, const float& new_val) {
        if (std::abs(new_val - old_val) > 0.5f) {
            // Significant change - notify BLE connected clients
            uint8_t data[4];
            memcpy(data, &new_val, sizeof(float));
            ble_service_notify_all(IDX_SENSOR_VAL, data, sizeof(data));
        }
    });

    // Observer 2: Threshold alarm
    temp.subscribe([](const float& old_val, const float& new_val) {
        if (new_val > CONFIG_TEMP_ALARM_HIGH && old_val <= CONFIG_TEMP_ALARM_HIGH) {
            TempEvent evt{TempEvent::kAlarm, new_val,
                          esp_timer_get_time() / 1000};
            temp_event_queue.send(evt, 0);  // Non-blocking
            ESP_LOGW(TAG, "Temperature alarm: %.1f C", new_val);
        }
    });

    // Observer 3: Logging
    temp.subscribe([](const float& old_val, const float& new_val) {
        ESP_LOGI(TAG, "Temperature: %.1f -> %.1f C", old_val, new_val);
    });

    // Polling loop
    while (true) {
        float reading = readTemperatureHardware();
        temp.setValue(reading);
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

// Event consumer task (MQTT + alert processing)
void tempEventConsumerTask(void* param) {
    while (true) {
        TempEvent evt{};
        if (temp_event_queue.receive(evt, portMAX_DELAY)) {
            switch (evt.type) {
            case TempEvent::kAlarm:
                // Publish alarm to MQTT with QoS 1
                publishMqttAlarm("temperature", evt.value, evt.timestamp);
                // Trigger buzzer/LED
                gpio_set_level(GPIO_NUM_48, 1);
                vTaskDelay(pdMS_TO_TICKS(500));
                gpio_set_level(GPIO_NUM_48, 0);
                break;

            case TempEvent::kUpdate:
                publishMqttTelemetry("temperature", evt.value, evt.timestamp);
                break;

            default:
                break;
            }
        }
    }
}
```

---

## Arcana Frame Round-Trip

### Complete Frame Build + Parse Test

```cpp
// pytest/test_arcana_frame.cpp
#include <gtest/gtest.h>
#include "ArcanaFrame.h"
#include <cstring>

TEST(ArcanaFrame, BuildAndParse) {
    // Payload: a simple command
    uint8_t payload[] = {0x01, 0x00, 0x42, 0xDE, 0xAD};
    size_t payload_len = sizeof(payload);

    // Build frame
    uint8_t frame_buf[128];
    uint8_t flags = 0x01;  // Encrypted
    uint8_t stream_id = 0x00;
    size_t frame_len = ArcanaFrame::build(
        flags, stream_id, payload, payload_len,
        frame_buf, sizeof(frame_buf));

    ASSERT_GT(frame_len, 0u);
    EXPECT_EQ(frame_len, ArcanaFrame::kOverhead + 1 + payload_len);

    // Verify magic bytes
    EXPECT_EQ(frame_buf[0], 0xAR);
    EXPECT_EQ(frame_buf[1], 0xCA);
    EXPECT_EQ(frame_buf[2], 0x01);  // Version
    EXPECT_EQ(frame_buf[3], 0x01);  // Flags (encrypted)

    // Parse frame
    auto result = ArcanaFrame::parse(frame_buf, frame_len);
    ASSERT_TRUE(result.valid);
    EXPECT_EQ(result.flags, 0x01);
    EXPECT_EQ(result.stream_id, 0x00);
    EXPECT_EQ(result.payload_len, payload_len);
    EXPECT_EQ(memcmp(result.payload, payload, payload_len), 0);
}

TEST(ArcanaFrame, InvalidMagic) {
    uint8_t bad_frame[] = {0xFF, 0xFF, 0x01, 0x00, 0x00,
                           0x01, 0x00, 0x42, 0x00, 0x00};
    auto result = ArcanaFrame::parse(bad_frame, sizeof(bad_frame));
    EXPECT_FALSE(result.valid);
}

TEST(ArcanaFrame, CorruptedCRC) {
    uint8_t payload[] = {0x42};
    uint8_t frame_buf[128];
    size_t frame_len = ArcanaFrame::build(
        0x00, 0x00, payload, 1, frame_buf, sizeof(frame_buf));

    // Corrupt CRC
    frame_buf[frame_len - 1] ^= 0xFF;

    auto result = ArcanaFrame::parse(frame_buf, frame_len);
    EXPECT_FALSE(result.valid);
}

TEST(ArcanaFrame, MaxPayload) {
    // Test with large payload (MTU-3 = 514 bytes)
    uint8_t payload[514];
    memset(payload, 0xAA, sizeof(payload));

    uint8_t frame_buf[600];
    size_t frame_len = ArcanaFrame::build(
        0x01, 0x00, payload, sizeof(payload),
        frame_buf, sizeof(frame_buf));

    ASSERT_GT(frame_len, 0u);

    auto result = ArcanaFrame::parse(frame_buf, frame_len);
    ASSERT_TRUE(result.valid);
    EXPECT_EQ(result.payload_len, sizeof(payload));
}
```

---

## WiFi+BLE Coexistence Setup

### Complete Initialization Sequence

```cpp
// main/app_main.cpp
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_bt.h"
#include "esp_bt_main.h"
#include "esp_coex.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "BleService.h"
#include "CommandService.h"

static constexpr const char* TAG = "AppMain";

static void wifiEventHandler(void* arg, esp_event_base_t base,
                              int32_t id, void* data) {
    if (base == WIFI_EVENT) {
        switch (id) {
        case WIFI_EVENT_STA_START:
            esp_wifi_connect();
            break;
        case WIFI_EVENT_STA_DISCONNECTED:
            ESP_LOGW(TAG, "WiFi disconnected, reconnecting...");
            vTaskDelay(pdMS_TO_TICKS(1000));
            esp_wifi_connect();
            break;
        }
    } else if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP) {
        auto* event = static_cast<ip_event_got_ip_t*>(data);
        ESP_LOGI(TAG, "Got IP: " IPSTR, IP2STR(&event->ip_info.ip));

        // SAFE to start MQTT now
        mqttInit();
    }
}

extern "C" void app_main() {
    // Phase 1: NVS initialization
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES ||
        err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ESP_ERROR_CHECK(nvs_flash_init());
    }

    // Phase 2: Event loop
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    // Phase 3: Coexistence (BEFORE WiFi and BLE)
    ESP_ERROR_CHECK(esp_coex_preference_set(ESP_COEX_PREFER_BALANCE));

    // Phase 4: WiFi initialization
    ESP_ERROR_CHECK(esp_netif_init());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t wifi_cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&wifi_cfg));

    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        WIFI_EVENT, ESP_EVENT_ANY_ID, &wifiEventHandler, nullptr, nullptr));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        IP_EVENT, IP_EVENT_STA_GOT_IP, &wifiEventHandler, nullptr, nullptr));

    wifi_config_t wifi_config = {};
    strlcpy((char*)wifi_config.sta.ssid, CONFIG_WIFI_SSID,
            sizeof(wifi_config.sta.ssid));
    strlcpy((char*)wifi_config.sta.password, CONFIG_WIFI_PASSWORD,
            sizeof(wifi_config.sta.password));

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    // Phase 5: BLE initialization
    ESP_ERROR_CHECK(esp_bt_controller_mem_release(ESP_BT_MODE_CLASSIC_BT));

    esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_bt_controller_init(&bt_cfg));
    ESP_ERROR_CHECK(esp_bt_controller_enable(ESP_BT_MODE_BLE));
    ESP_ERROR_CHECK(esp_bluedroid_init());
    ESP_ERROR_CHECK(esp_bluedroid_enable());

    // Phase 6: Application components
    BleService::instance().init();
    CommandService::instance().init();

    // Phase 7: Create application tasks
    xTaskCreatePinnedToCore(sensorPollingTask, "sensor",
        2048, nullptr, 10, nullptr, 1);
    xTaskCreatePinnedToCore(tempEventConsumerTask, "temp_evt",
        4096, nullptr, 12, nullptr, 0);

    ESP_LOGI(TAG, "Arcana ESP32-S3 started");
    ESP_LOGI(TAG, "Free DRAM: %lu bytes",
             heap_caps_get_free_size(MALLOC_CAP_8BIT));
    ESP_LOGI(TAG, "Free PSRAM: %lu bytes",
             heap_caps_get_free_size(MALLOC_CAP_SPIRAM));
}
```

---

## OTA Firmware Update

### Secure OTA via MQTT Command

```cpp
// components/CommandService/include/handlers/OtaUpdateHandler.h
#pragma once

#include "CommandDefs.h"
#include "esp_ota_ops.h"
#include "esp_https_ota.h"
#include "esp_log.h"

static constexpr const char* TAG = "OTA";

class OtaUpdateHandler {
public:
    static CommandStatus execute(const CommandRequest& req,
                                 CommandResponse& rsp) {
        // Payload contains firmware URL (null-terminated string)
        if (req.payload_len == 0 || req.payload_len > 255) {
            return CommandStatus::kInvalidField;
        }

        char url[256] = {};
        memcpy(url, req.payload, req.payload_len);

        ESP_LOGI(TAG, "Starting OTA from: %s", url);

        // Send immediate ACK before starting OTA
        rsp.status = CommandStatus::kSuccess;
        rsp.cluster_id = req.cluster_id;
        rsp.command_id = req.command_id;
        rsp.sequence = req.sequence;

        // Start OTA in separate task (long-running)
        char* url_copy = strdup(url);
        xTaskCreatePinnedToCore(otaTask, "ota", 8192,
            url_copy, 5, nullptr, 0);

        return CommandStatus::kSuccess;
    }

private:
    static void otaTask(void* param) {
        char* url = static_cast<char*>(param);

        // Switch coexistence to WiFi-prefer for fast download
        esp_coex_preference_set(ESP_COEX_PREFER_WIFI);

        esp_http_client_config_t http_cfg = {
            .url = url,
            .cert_pem = server_cert_pem,
            .timeout_ms = 30000,
        };

        esp_https_ota_config_t ota_cfg = {
            .http_config = &http_cfg,
        };

        esp_err_t err = esp_https_ota(&ota_cfg);
        free(url);

        // Restore coexistence balance
        esp_coex_preference_set(ESP_COEX_PREFER_BALANCE);

        if (err == ESP_OK) {
            ESP_LOGI(TAG, "OTA success, rebooting in 2s...");
            vTaskDelay(pdMS_TO_TICKS(2000));
            esp_restart();
        } else {
            ESP_LOGE(TAG, "OTA failed: %s", esp_err_to_name(err));
        }

        vTaskDelete(nullptr);
    }
};
```

---

## NVS Encrypted Key Storage

### Storing Persistent Keys Securely

```cpp
// components/CommandService/src/nvs_key_store.cpp
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_log.h"
#include "mbedtls/platform_util.h"
#include <cstring>

static constexpr const char* TAG = "NvsKeyStore";
static constexpr const char* NVS_NAMESPACE = "crypto_keys";

class NvsKeyStore {
public:
    esp_err_t storePsk(const char* key_name,
                       const uint8_t* key, size_t key_len) {
        nvs_handle_t handle;
        ESP_RETURN_ON_ERROR(
            nvs_open(NVS_NAMESPACE, NVS_READWRITE, &handle),
            TAG, "NVS open failed");

        esp_err_t err = nvs_set_blob(handle, key_name, key, key_len);
        if (err == ESP_OK) {
            err = nvs_commit(handle);
        }

        nvs_close(handle);
        return err;
    }

    esp_err_t loadPsk(const char* key_name,
                      uint8_t* key, size_t* key_len) {
        nvs_handle_t handle;
        ESP_RETURN_ON_ERROR(
            nvs_open(NVS_NAMESPACE, NVS_READONLY, &handle),
            TAG, "NVS open failed");

        esp_err_t err = nvs_get_blob(handle, key_name, key, key_len);
        nvs_close(handle);
        return err;
    }

    esp_err_t deletePsk(const char* key_name) {
        nvs_handle_t handle;
        ESP_RETURN_ON_ERROR(
            nvs_open(NVS_NAMESPACE, NVS_READWRITE, &handle),
            TAG, "NVS open failed");

        esp_err_t err = nvs_erase_key(handle, key_name);
        if (err == ESP_OK) {
            err = nvs_commit(handle);
        }

        nvs_close(handle);
        return err;
    }

    void wipeAll() {
        nvs_handle_t handle;
        if (nvs_open(NVS_NAMESPACE, NVS_READWRITE, &handle) == ESP_OK) {
            nvs_erase_all(handle);
            nvs_commit(handle);
            nvs_close(handle);
            ESP_LOGW(TAG, "All stored keys wiped");
        }
    }
};
```

---

## FreeRTOS Task Architecture

### Complete Task Creation with Priorities

```cpp
// main/task_init.cpp
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_task_wdt.h"
#include "esp_log.h"

static constexpr const char* TAG = "TaskInit";

// Task handles for monitoring
static TaskHandle_t crypto_task_handle = nullptr;
static TaskHandle_t ble_task_handle = nullptr;
static TaskHandle_t mqtt_task_handle = nullptr;
static TaskHandle_t sensor_task_handle = nullptr;
static TaskHandle_t cmd_task_handle = nullptr;

void initApplicationTasks() {
    // Priority order: Crypto(20) > BLE(19) > Cmd(18) > MQTT(15) > Sensor(10)

    xTaskCreatePinnedToCore(
        cryptoTask, "crypto",
        8192,       // Stack: 8KB (ECDH P-256 needs ~6KB)
        nullptr,
        20,         // Highest app priority
        &crypto_task_handle,
        1);         // Core 1 (computation core)

    xTaskCreatePinnedToCore(
        bleEventTask, "ble",
        4096,       // Stack: 4KB
        nullptr,
        19,
        &ble_task_handle,
        0);         // Core 0 (radio core)

    xTaskCreatePinnedToCore(
        commandDispatchTask, "cmd",
        4096,
        nullptr,
        18,
        &cmd_task_handle,
        1);

    xTaskCreatePinnedToCore(
        mqttClientTask, "mqtt",
        4096,
        nullptr,
        15,
        &mqtt_task_handle,
        0);         // Core 0 (network core)

    xTaskCreatePinnedToCore(
        sensorPollingTask, "sensor",
        2048,       // Stack: 2KB (lightweight)
        nullptr,
        10,
        &sensor_task_handle,
        1);

    // Register all tasks with watchdog (10s timeout from sdkconfig)
    esp_task_wdt_add(crypto_task_handle);
    esp_task_wdt_add(ble_task_handle);
    esp_task_wdt_add(cmd_task_handle);
    esp_task_wdt_add(mqtt_task_handle);
    esp_task_wdt_add(sensor_task_handle);

    ESP_LOGI(TAG, "All application tasks created");
}

// Diagnostic: print task watermarks
void printTaskWatermarks() {
    ESP_LOGI(TAG, "=== Task Stack Watermarks ===");
    ESP_LOGI(TAG, "crypto:  %u bytes free",
             uxTaskGetStackHighWaterMark(crypto_task_handle) * sizeof(StackType_t));
    ESP_LOGI(TAG, "ble:     %u bytes free",
             uxTaskGetStackHighWaterMark(ble_task_handle) * sizeof(StackType_t));
    ESP_LOGI(TAG, "cmd:     %u bytes free",
             uxTaskGetStackHighWaterMark(cmd_task_handle) * sizeof(StackType_t));
    ESP_LOGI(TAG, "mqtt:    %u bytes free",
             uxTaskGetStackHighWaterMark(mqtt_task_handle) * sizeof(StackType_t));
    ESP_LOGI(TAG, "sensor:  %u bytes free",
             uxTaskGetStackHighWaterMark(sensor_task_handle) * sizeof(StackType_t));
}

// Example: crypto task with watchdog feed
void cryptoTask(void* param) {
    while (true) {
        // Process crypto requests from queue
        CryptoRequest req{};
        if (crypto_queue.receive(req, pdMS_TO_TICKS(1000))) {
            processCryptoRequest(req);
        }

        // CRITICAL: Feed watchdog every iteration
        esp_task_wdt_reset();
    }
}
```

### Task Communication Pattern

```cpp
// Inter-task communication using EventQueue + command pattern

// BLE -> Command Dispatch (via queue)
static EventQueue<RawCommand, 8> ble_cmd_queue;

void onBleCommandWrite(uint16_t conn_id, const uint8_t* data, size_t len) {
    RawCommand cmd{};
    cmd.conn_id = conn_id;
    cmd.transport = Transport::kBle;
    memcpy(cmd.data, data, std::min(len, sizeof(cmd.data)));
    cmd.len = len;

    if (!ble_cmd_queue.send(cmd, pdMS_TO_TICKS(100))) {
        ESP_LOGW(TAG, "Command queue full, dropping");
    }
}

// Command Dispatch -> Crypto (via queue)
static EventQueue<CryptoRequest, 4> crypto_queue;

void commandDispatchTask(void* param) {
    while (true) {
        RawCommand cmd{};
        if (ble_cmd_queue.receive(cmd, pdMS_TO_TICKS(1000))) {
            // Parse frame
            auto frame = ArcanaFrame::parse(cmd.data, cmd.len);
            if (!frame.valid) continue;

            if (frame.flags & 0x01) {
                // Need decryption - forward to crypto task
                CryptoRequest crypto_req{};
                crypto_req.type = CryptoOp::kDecrypt;
                crypto_req.conn_id = cmd.conn_id;
                memcpy(crypto_req.data, frame.payload, frame.payload_len);
                crypto_req.len = frame.payload_len;
                crypto_queue.send(crypto_req);
            } else {
                // Unencrypted - dispatch directly (key exchange only)
                processUnencryptedCommand(cmd);
            }
        }

        esp_task_wdt_reset();
    }
}
```

---

## CMakeLists.txt Examples

### Top-Level CMakeLists.txt

```cmake
# CMakeLists.txt
cmake_minimum_required(VERSION 3.16)

set(EXTRA_COMPONENT_DIRS
    ${CMAKE_CURRENT_SOURCE_DIR}/components/ObservableSensor
    ${CMAKE_CURRENT_SOURCE_DIR}/components/BleService
    ${CMAKE_CURRENT_SOURCE_DIR}/components/CommandService
)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(arcana-embedded-esp32)
```

### Component CMakeLists.txt (CommandService)

```cmake
# components/CommandService/CMakeLists.txt
idf_component_register(
    SRCS
        "src/command_dispatcher.cpp"
        "src/command_factory.cpp"
        "src/command_codec.cpp"
        "src/arcana_frame.cpp"
        "src/crypto_engine.cpp"
        "src/session_manager.cpp"
        "src/key_exchange.cpp"
    INCLUDE_DIRS
        "include"
    REQUIRES
        bt
        mbedtls
        nvs_flash
        esp_event
    PRIV_REQUIRES
        ObservableSensor
        BleService
)

# nanopb generation
set(NANOPB_DIR ${CMAKE_CURRENT_SOURCE_DIR}/proto)
nanopb_generate_cpp(PROTO_SRCS PROTO_HDRS
    ${NANOPB_DIR}/command.proto
    ${NANOPB_DIR}/device.proto
)
target_sources(${COMPONENT_LIB} PRIVATE ${PROTO_SRCS})
target_include_directories(${COMPONENT_LIB} PUBLIC ${CMAKE_CURRENT_BINARY_DIR})
```

### Component CMakeLists.txt (BleService)

```cmake
# components/BleService/CMakeLists.txt
idf_component_register(
    SRCS
        "src/ble_service.cpp"
        "src/gap_manager.cpp"
        "src/gatt_server.cpp"
        "src/gatt_client.cpp"
    INCLUDE_DIRS
        "include"
    REQUIRES
        bt
        esp_event
    PRIV_REQUIRES
        nvs_flash
)
```

### Component CMakeLists.txt (ObservableSensor)

```cmake
# components/ObservableSensor/CMakeLists.txt
idf_component_register(
    SRCS
        "src/observable_sensor.cpp"
    INCLUDE_DIRS
        "include"
    REQUIRES
        freertos
)
```
