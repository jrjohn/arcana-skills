# Command Pipeline Pattern - Deep Dive

## Overview

The Command Pipeline is the central data processing path for all incoming and outgoing commands in the Arcana ESP32 platform. It provides a unified, transport-agnostic pipeline that handles both BLE and MQTT frames identically.

## Pipeline Architecture

```
+===================================================================+
|                      INBOUND PIPELINE                               |
|                                                                     |
|  Transport (BLE Write / MQTT Data)                                  |
|       |                                                             |
|       v                                                             |
|  +-------------------+                                              |
|  | ArcanaFrame::parse |  Validate: Magic(0xAR CA) + CRC-16         |
|  | (Frame Layer)      |  Extract: flags, stream_id, payload        |
|  +--------+-----------+                                             |
|           |                                                         |
|           v                                                         |
|  +-------------------+                                              |
|  | CryptoEngine::    |  Verify: AES-256-CCM 8B auth tag            |
|  | decrypt()         |  Output: plaintext nanopb bytes              |
|  | (Crypto Layer)    |  Side-effect: nonce_counter++                |
|  +--------+-----------+                                             |
|           |                                                         |
|           v                                                         |
|  +-------------------+                                              |
|  | CommandCodec::    |  nanopb: pb_decode() with max_size bounds    |
|  | decode()          |  Output: CommandRequest struct                |
|  | (Codec Layer)     |  Fields: cluster_id, command_id, sequence    |
|  +--------+-----------+                                             |
|           |                                                         |
|           v                                                         |
|  +-------------------+                                              |
|  | CommandDispatcher |  Lookup: handlers_[(cluster<<8)|command]     |
|  | ::dispatch()      |  Execute: handler(req, rsp)                  |
|  | (Dispatch Layer)  |  Return: CommandStatus                       |
|  +--------+-----------+                                             |
|           |                                                         |
+===========|=========================================================+
            |
            v
+===================================================================+
|                      OUTBOUND PIPELINE                              |
|                                                                     |
|  +-------------------+                                              |
|  | CommandCodec::    |  nanopb: pb_encode()                         |
|  | encode()          |  Output: serialized bytes                    |
|  +--------+-----------+                                             |
|           |                                                         |
|           v                                                         |
|  +-------------------+                                              |
|  | CryptoEngine::    |  AES-256-CCM encrypt + generate auth tag     |
|  | encrypt()         |  Append: 8B auth tag to ciphertext           |
|  | (Crypto Layer)    |  Side-effect: nonce_counter++                |
|  +--------+-----------+                                             |
|           |                                                         |
|           v                                                         |
|  +-------------------+                                              |
|  | ArcanaFrame::build|  Prepend: header (Magic+Ver+Flags+SID+Len)  |
|  | (Frame Layer)     |  Append: CRC-16                              |
|  +--------+-----------+                                             |
|           |                                                         |
|           v                                                         |
|  Transport (BLE Notify / MQTT Publish)                              |
+===================================================================+
```

## Dispatch Mechanism

### Key Generation

The dispatch key is a single 16-bit value combining cluster and command:

```cpp
static uint16_t makeKey(uint8_t cluster, uint8_t cmd) {
    return (static_cast<uint16_t>(cluster) << 8) | cmd;
}
```

This gives us 256 clusters x 256 commands = 65536 possible handlers.

### Handler Registration Pattern

```cpp
// Static registration at startup (no runtime modification)
void CommandFactory::registerAll(CommandDispatcher& dispatcher) {
    // Each handler is a static function: CommandStatus(req, rsp)
    dispatcher.registerHandler(0x00, 0x00, SystemPingHandler::execute);
    dispatcher.registerHandler(0x00, 0x01, SystemResetHandler::execute);
    // ... all handlers registered here
}
```

### Handler Contract

Every command handler MUST follow this contract:

```cpp
class MyHandler {
public:
    static CommandStatus execute(const CommandRequest& req,
                                 CommandResponse& rsp) {
        // 1. Validate request fields
        if (req.payload_len < kMinPayload) {
            return CommandStatus::kInvalidField;
        }

        // 2. Execute business logic
        // ...

        // 3. Build response
        rsp.cluster_id = req.cluster_id;
        rsp.command_id = req.command_id;
        rsp.sequence = req.sequence;
        rsp.status = CommandStatus::kSuccess;

        // 4. Return status
        return CommandStatus::kSuccess;
    }
};
```

## Transport Abstraction

The pipeline is transport-agnostic. Both BLE and MQTT use identical frame format:

```
BLE Path:   GATT Write --> onCommandReceived(conn_id, data, len)
MQTT Path:  MQTT Data  --> onCommandReceived(MQTT_CONN_ID, data, len)
                              |
                              v
                    Same pipeline (parse -> decrypt -> decode -> dispatch)
```

### Virtual Connection IDs

| Transport | conn_id Range | Notes |
|-----------|---------------|-------|
| BLE | 0x0000 - 0xFFFE | Assigned by Bluedroid stack |
| MQTT | 0xFFFF | Virtual conn_id for MQTT session |

## Error Recovery

| Stage | Failure | Recovery |
|-------|---------|----------|
| Frame parse | Bad magic or CRC | Drop frame, log warning |
| Decrypt | Auth tag mismatch | Drop frame, log error, increment tamper counter |
| Decode | nanopb parse error | Send `kInvalidField` error response |
| Dispatch | No handler found | Send `kUnsupportedCommand` error response |
| Handler | Business error | Send specific `CommandStatus` error response |
| Encrypt | Session missing | Drop response, log error |
| Frame build | Buffer overflow | Drop response, log error |
| Transport | Send failed | Retry once, then drop |

## Sequence Numbers

Each command carries a `sequence` number (uint16) that MUST be echoed in the response. This allows the sender to match responses to requests in a pipeline of concurrent commands.

```
Request:  { cluster: 0x01, command: 0x00, sequence: 42, payload: [...] }
Response: { cluster: 0x01, command: 0x00, sequence: 42, status: 0x00, payload: [...] }
```

## Thread Safety

The pipeline is designed for single-threaded access per transport:

- BLE commands are processed on the `cmd` task (via `ble_cmd_queue`)
- MQTT commands are processed on the `cmd` task (via `mqtt_cmd_queue`)
- The `cmd` task drains both queues in priority order (BLE first)
- Crypto operations are offloaded to the `crypto` task via `crypto_queue`

```
ble_task -----> ble_cmd_queue ----+
                                   |
mqtt_task ----> mqtt_cmd_queue ---+--> cmd_task --> crypto_queue --> crypto_task
```
