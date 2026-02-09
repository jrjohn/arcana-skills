# STM32 Developer Skill - Design Patterns

## Table of Contents
1. [Observable/Observer Pattern](#observableobserver-pattern)
2. [Zero-Copy Model Passing](#zero-copy-model-passing)
3. [Static Allocation Pattern](#static-allocation-pattern)
4. [FreeRTOS Task Patterns](#freertos-task-patterns)
5. [ISR-Safe Communication](#isr-safe-communication)
6. [Priority Queue Pattern](#priority-queue-pattern)
7. [Callback with Context Pattern](#callback-with-context-pattern)
8. [State Machine Pattern](#state-machine-pattern)
9. [Circular Buffer Pattern](#circular-buffer-pattern)
10. [Singleton for Hardware](#singleton-for-hardware)

---

## Observable/Observer Pattern

### Architecture

```
    ┌──────────────────────────────────────────────────────┐
    │                Observable<T>                          │
    │  ┌────────────────────────────────────────────────┐  │
    │  │  Observer* observers_[MAX_OBSERVERS]            │  │
    │  │  uint8_t observerCount_                         │  │
    │  │  ObservableDispatcher* dispatcher_               │  │
    │  ├────────────────────────────────────────────────┤  │
    │  │  subscribe(observer*) -> bool                   │  │
    │  │  unsubscribe(observer*) -> bool                 │  │
    │  │  publish(const T&)                              │  │
    │  │  publishHighPriority(const T&)                  │  │
    │  │  publishFromISR(const T&, BaseType_t*)          │  │
    │  │  notify(const T&) [called by dispatcher]        │  │
    │  └────────────────────────────────────────────────┘  │
    └──────────────────────────────────────────────────────┘
                            │
                            │ enqueue
                            ▼
    ┌──────────────────────────────────────────────────────┐
    │              ObservableDispatcher                     │
    │  ┌─────────────────────────────┐                     │
    │  │  High Priority Queue (4)    │ ← Processed first   │
    │  └─────────────────────────────┘                     │
    │  ┌─────────────────────────────┐                     │
    │  │  Normal Priority Queue (8)  │ ← Processed second  │
    │  └─────────────────────────────┘                     │
    │  FreeRTOS Task: dispatchTask()                       │
    └──────────────────────────┬───────────────────────────┘
                               │
                               │ notify(const T&)
                               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │ Observer 0 │  │ Observer 1 │  │ Observer 2 │ ... (max 4)
    │ callback() │  │ callback() │  │ callback() │
    │ context*   │  │ context*   │  │ context*   │
    └────────────┘  └────────────┘  └────────────┘
```

### Implementation Pattern

```cpp
// Template class - one instantiation per model type
template <typename T>
class Observable {
public:
    // Observer struct: function pointer + context
    struct Observer {
        void (*callback)(const T&, void*) = nullptr;
        void* context = nullptr;
    };

    bool subscribe(Observer* observer) {
        if (observerCount_ >= MAX_OBSERVERS) return false;
        observers_[observerCount_++] = observer;
        return true;
    }

    bool unsubscribe(Observer* observer) {
        for (uint8_t i = 0; i < observerCount_; i++) {
            if (observers_[i] == observer) {
                // Shift remaining observers
                for (uint8_t j = i; j < observerCount_ - 1; j++) {
                    observers_[j] = observers_[j + 1];
                }
                observerCount_--;
                return true;
            }
        }
        return false;
    }

    void publish(const T& model) {
        QueueItem item;
        item.type = getModelType<T>();
        memcpy(&item.data, &model, sizeof(T));
        dispatcher_->enqueue(item);
    }

    void notify(const T& model) {
        // Called by dispatcher - iterate all observers
        for (uint8_t i = 0; i < observerCount_; i++) {
            if (observers_[i] && observers_[i]->callback) {
                observers_[i]->callback(model, observers_[i]->context);
            }
        }
    }

private:
    static constexpr uint8_t MAX_OBSERVERS = 4;
    Observer* observers_[MAX_OBSERVERS] = {};
    uint8_t observerCount_ = 0;
    ObservableDispatcher* dispatcher_ = nullptr;
};
```

### When to Use
- Decoupling publishers (sensors, timers) from consumers (display, logging)
- Multiple consumers need the same data
- ISR needs to communicate with task-level code
- Event-driven architecture with predictable memory usage

### Constraints
- Maximum 4 observers per Observable instance
- Observer callback must complete quickly (< 100us)
- Model must be POD type (trivially copyable)
- Queue overflow drops events silently (set error callback)

---

## Zero-Copy Model Passing

### Pattern Overview

```
    Publisher                Queue Storage              Observer
    =========               =============              ========

    TimeModel model;        ┌─────────────┐
    model.hours = 12;       │ Queue Slot   │
    model.minutes = 30;     │             │
                            │ [TimeModel] │
    publish(model) ──copy──>│  hours: 12  │──const ref──> callback(model, ctx)
                            │  min: 30    │               // model is reference
                            │  sec: 0     │               // to queue storage
                            └─────────────┘

    Total memory copies: 1 (stack → queue)
    Observer access: 0 copies (const reference)
```

### Implementation Rules

```cpp
// RULE 1: Models must be POD types
struct SensorReading {
    int16_t temperature;    // Fixed-size types only
    uint16_t humidity;
    uint8_t status;
    uint8_t padding[1];     // Explicit padding for alignment
};
static_assert(std::is_trivially_copyable<SensorReading>::value,
              "Must be trivially copyable for memcpy into queue");

// RULE 2: Observer callbacks receive const reference
void onSensorData(const SensorReading& reading, void* ctx) {
    // reading is valid ONLY during this callback
    auto* display = static_cast<Display*>(ctx);
    display->showTemperature(reading.temperature);
    // DO NOT: store &reading for later use
    // DO NOT: pass &reading to another task
}

// RULE 3: If data is needed after callback, explicitly copy
void onSensorData(const SensorReading& reading, void* ctx) {
    auto* logger = static_cast<Logger*>(ctx);
    // Explicit copy when data must persist beyond callback
    SensorReading savedReading = reading;  // Copy is intentional
    logger->bufferReading(savedReading);
}
```

### Anti-Patterns

```cpp
// WRONG: Storing reference to queue data
class BadObserver {
    const SensorReading* lastReading_ = nullptr;  // DANGLING POINTER

    static void onData(const SensorReading& reading, void* ctx) {
        auto* self = static_cast<BadObserver*>(ctx);
        self->lastReading_ = &reading;  // BUG: pointer invalidated after callback
    }
};

// CORRECT: Copy data if needed later
class GoodObserver {
    SensorReading lastReading_ = {};  // Own copy

    static void onData(const SensorReading& reading, void* ctx) {
        auto* self = static_cast<GoodObserver*>(ctx);
        self->lastReading_ = reading;  // Value copy - safe
    }
};
```

---

## Static Allocation Pattern

### Core Principle

All objects have static storage duration. No runtime heap allocation.

```cpp
// CORRECT: Static allocation patterns

// 1. Global objects (file scope)
static App app;                           // Application instance
static ObservableDispatcher dispatcher;   // Singleton dispatcher

// 2. Static class members
class App {
    static StaticTask_t taskTCB_;         // FreeRTOS TCB
    static StackType_t taskStack_[128];   // Task stack
};

// 3. Static local (lazy initialization, but deterministic)
ErrorHandler& ErrorHandler::instance() {
    static ErrorHandler handler;          // Initialized once
    return handler;
}

// 4. Stack-allocated temporaries (in task context)
void publishReading() {
    SensorModel model;                    // Stack - automatic cleanup
    model.temperature = readTemp();
    observable_.publish(model);           // Copied to queue
}   // model destroyed here - safe because queue has its own copy
```

### Static Queue Pattern

```cpp
// FreeRTOS queues with static allocation
class ObservableDispatcher {
private:
    // Queue control blocks (static)
    static StaticQueue_t highQueueCB_;
    static StaticQueue_t normalQueueCB_;

    // Queue storage (static arrays)
    static uint8_t highQueueStorage_[4 * sizeof(QueueItem)];
    static uint8_t normalQueueStorage_[8 * sizeof(QueueItem)];

    QueueHandle_t highQueue_ = nullptr;
    QueueHandle_t normalQueue_ = nullptr;

public:
    void init() {
        highQueue_ = xQueueCreateStatic(
            4, sizeof(QueueItem),
            highQueueStorage_, &highQueueCB_
        );

        normalQueue_ = xQueueCreateStatic(
            8, sizeof(QueueItem),
            normalQueueStorage_, &normalQueueCB_
        );
    }
};

// Static storage definitions in .cpp
StaticQueue_t ObservableDispatcher::highQueueCB_;
StaticQueue_t ObservableDispatcher::normalQueueCB_;
uint8_t ObservableDispatcher::highQueueStorage_[4 * sizeof(QueueItem)];
uint8_t ObservableDispatcher::normalQueueStorage_[8 * sizeof(QueueItem)];
```

### Static Container (No std::vector)

```cpp
// Fixed-capacity array - replacement for std::vector
template <typename T, size_t Capacity>
class StaticVector {
public:
    bool push_back(const T& item) {
        if (size_ >= Capacity) return false;
        data_[size_++] = item;
        return true;
    }

    bool pop_back() {
        if (size_ == 0) return false;
        size_--;
        return true;
    }

    T& operator[](size_t index) { return data_[index]; }
    const T& operator[](size_t index) const { return data_[index]; }
    size_t size() const { return size_; }
    size_t capacity() const { return Capacity; }
    bool empty() const { return size_ == 0; }
    bool full() const { return size_ >= Capacity; }

    T* begin() { return &data_[0]; }
    T* end() { return &data_[size_]; }

private:
    T data_[Capacity];
    size_t size_ = 0;
};

// Usage
StaticVector<SensorReading, 16> readingBuffer;  // 16 readings max, no heap
```

### Forbidden Patterns

```cpp
// ALL OF THESE ARE FORBIDDEN IN EMBEDDED CODE:

std::vector<int> data;          // Heap allocation
std::string name = "sensor";    // Heap allocation
auto* ptr = new SensorData();   // Heap allocation
void* mem = malloc(64);         // Heap allocation
std::shared_ptr<T> sp;          // Heap allocation + overhead
std::unique_ptr<T> up;          // Heap allocation
std::map<int, int> lookup;      // Heap allocation
std::list<int> items;           // Heap allocation per node
```

---

## FreeRTOS Task Patterns

### Task Creation with Static Allocation

```cpp
// Preferred: xTaskCreateStatic - no heap needed for task
static StaticTask_t sensorTaskTCB;
static StackType_t sensorTaskStack[128];  // 512 bytes

TaskHandle_t sensorTask = xTaskCreateStatic(
    SensorService::taskEntry,    // Task function
    "Sensor",                    // Name (max 8 chars)
    128,                         // Stack size in words
    &sensorService,              // Parameter (this pointer)
    osPriorityNormal,            // Priority
    sensorTaskStack,             // Stack buffer
    &sensorTaskTCB               // TCB buffer
);
```

### Periodic Task Pattern

```cpp
void SensorService::taskLoop() {
    TickType_t lastWakeTime = xTaskGetTickCount();

    for (;;) {
        // Do work
        SensorModel reading;
        if (readSensor(reading)) {
            observable_->publish(reading);
        }

        // Precise periodic execution (not affected by task execution time)
        vTaskDelayUntil(&lastWakeTime, pdMS_TO_TICKS(1000));
    }
}
```

### Event-Driven Task Pattern

```cpp
void CommandService::taskLoop() {
    for (;;) {
        CommandItem cmd;
        // Block until command arrives (no polling, no CPU waste)
        if (xQueueReceive(commandQueue_, &cmd, portMAX_DELAY) == pdTRUE) {
            processCommand(cmd);
        }
    }
}
```

### Task Priority Guidelines

```
Priority Level              | Use Case                    | Example
============================|=============================|================
osPriorityRealtime (7)      | Hardware safety, watchdog   | Safety monitor
osPriorityHigh (6)          | Time-critical ISR deferral  | Motor control
osPriorityAboveNormal (5)   | Event dispatcher            | ObservableDispatcher
osPriorityNormal (4)        | Regular application tasks   | SensorService
osPriorityBelowNormal (3)   | Background processing       | Logging
osPriorityLow (2)           | Housekeeping                | Statistics
osPriorityIdle (1)          | Only when nothing else runs | Power saving
```

### Task Communication Patterns

```cpp
// Pattern 1: Queue (preferred for Observable pattern)
QueueHandle_t eventQueue = xQueueCreateStatic(...);
xQueueSend(eventQueue, &item, pdMS_TO_TICKS(10));
xQueueReceive(eventQueue, &item, portMAX_DELAY);

// Pattern 2: Binary Semaphore (for ISR-to-task signaling)
SemaphoreHandle_t isrSignal = xSemaphoreCreateBinaryStatic(&semCB);
// In ISR:
xSemaphoreGiveFromISR(isrSignal, &xHigherPriorityTaskWoken);
// In Task:
xSemaphoreTake(isrSignal, portMAX_DELAY);

// Pattern 3: Task Notification (lightweight, single producer)
// In producer:
xTaskNotifyGive(receiverTaskHandle);
// In receiver:
ulTaskNotifyTake(pdTRUE, portMAX_DELAY);

// Pattern 4: Mutex (for shared resource protection)
SemaphoreHandle_t mutex = xSemaphoreCreateMutexStatic(&mutexCB);
xSemaphoreTake(mutex, portMAX_DELAY);
// Critical section - access shared resource
xSemaphoreGive(mutex);
```

---

## ISR-Safe Communication

### ISR to Task Pattern

```cpp
// PATTERN: ISR sets flag/enqueues, task processes

// ISR side (minimal work)
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin) {
    if (GPIO_Pin == ALARM_Pin) {
        AlarmModel model;
        model.source = AlarmSource::GPIO;
        model.timestamp = HAL_GetTick();  // Safe in ISR

        BaseType_t woken = pdFALSE;
        alarmObservable.publishHighPriorityFromISR(model, &woken);
        portYIELD_FROM_ISR(woken);
    }
}

// Task side (heavy processing)
void AlarmService::onAlarm(const AlarmModel& model, void* ctx) {
    auto* self = static_cast<AlarmService*>(ctx);
    // Safe to do complex work here - we're in task context
    self->evaluateAlarm(model);
    self->logAlarm(model);
    self->notifyOperator(model);
}
```

### Critical Section Pattern

```cpp
// For shared data between tasks (NOT between ISR and task)
class SharedState {
private:
    SemaphoreHandle_t mutex_;
    StaticSemaphore_t mutexCB_;

    struct Data {
        uint32_t value1;
        uint32_t value2;
    } data_ = {};

public:
    void init() {
        mutex_ = xSemaphoreCreateMutexStatic(&mutexCB_);
    }

    Data read() {
        Data copy;
        xSemaphoreTake(mutex_, portMAX_DELAY);
        copy = data_;
        xSemaphoreGive(mutex_);
        return copy;
    }

    void write(const Data& newData) {
        xSemaphoreTake(mutex_, portMAX_DELAY);
        data_ = newData;
        xSemaphoreGive(mutex_);
    }
};
```

### ISR-Shared Variable Pattern

```cpp
// For variables shared between ISR and task
// Use volatile + critical section

class IsrSharedCounter {
private:
    volatile uint32_t count_ = 0;  // volatile: compiler must re-read each time

public:
    // Called from ISR
    void incrementFromISR() {
        // Atomic on Cortex-M0 for aligned 32-bit access
        count_++;
    }

    // Called from task
    uint32_t read() {
        uint32_t copy;
        taskENTER_CRITICAL();
        copy = count_;
        taskEXIT_CRITICAL();
        return copy;
    }

    // Called from task
    uint32_t readAndReset() {
        uint32_t copy;
        taskENTER_CRITICAL();
        copy = count_;
        count_ = 0;
        taskEXIT_CRITICAL();
        return copy;
    }
};
```

---

## Priority Queue Pattern

### Dual-Queue Dispatch

```cpp
// ObservableDispatcher processes high-priority items first
void ObservableDispatcher::dispatchLoop() {
    for (;;) {
        QueueItem item;
        bool processed = false;

        // Phase 1: Drain ALL high-priority items first
        while (xQueueReceive(highQueue_, &item, 0) == pdTRUE) {
            dispatch(item);
            processed = true;
        }

        // Phase 2: Process ONE normal item, then re-check high queue
        if (xQueueReceive(normalQueue_, &item,
                          processed ? 0 : portMAX_DELAY) == pdTRUE) {
            dispatch(item);
        }
    }
}
```

### Priority Selection Guidelines

```
Use HIGH priority for:
- Safety-critical events (over-temperature, over-current)
- ISR-generated events (hardware interrupts)
- Time-critical control loops (motor, PID)
- Alarm conditions

Use NORMAL priority for:
- Periodic sensor readings
- UI/display updates
- Logging and statistics
- Configuration changes
- Non-critical status updates
```

---

## Callback with Context Pattern

### Pattern Structure

```cpp
// The context pointer pattern enables C-compatible callbacks
// while maintaining object-oriented encapsulation

// Callback type: function pointer with context
template <typename T>
struct Observer {
    void (*callback)(const T& model, void* context) = nullptr;
    void* context = nullptr;  // "this" pointer of the observer object
};

// Registration
class MotorController {
    Observer<SpeedModel> speedObserver_;

    void init(Observable<SpeedModel>& speedObs) {
        speedObserver_.callback = &MotorController::onSpeedUpdate;
        speedObserver_.context = this;  // Pass "this" as context
        speedObs.subscribe(&speedObserver_);
    }

    // Static callback - casts context back to this pointer
    static void onSpeedUpdate(const SpeedModel& model, void* context) {
        auto* self = static_cast<MotorController*>(context);
        self->adjustPWM(model.rpm);
    }

    void adjustPWM(uint32_t rpm) {
        // Instance method - full access to member variables
    }
};
```

### Why This Pattern (not std::function)

```
std::function<void(const T&)>  ->  Heap allocation, virtual dispatch, 32+ bytes
void (*)(const T&, void*)      ->  Zero overhead, 8 bytes, ISR-safe

On STM32F051C8 with 8KB RAM, every byte matters.
The callback + context pattern gives us:
- 8 bytes per observer (4 byte function pointer + 4 byte context)
- Zero heap allocation
- Inlineable by compiler
- Works in ISR context
- C linkage compatible
```

---

## State Machine Pattern

### Embedded State Machine (No Heap)

```cpp
// State machine for protocol parsing or device control
class ProtocolParser {
public:
    enum class State : uint8_t {
        Idle,
        WaitingHeader,
        WaitingLength,
        WaitingPayload,
        WaitingChecksum,
        Complete,
        Error
    };

    void reset() {
        state_ = State::Idle;
        payloadIndex_ = 0;
    }

    // Process one byte - called from UART observer callback
    State processByte(uint8_t byte) {
        switch (state_) {
            case State::Idle:
                if (byte == SYNC_BYTE) {
                    state_ = State::WaitingHeader;
                }
                break;

            case State::WaitingHeader:
                header_ = byte;
                state_ = State::WaitingLength;
                break;

            case State::WaitingLength:
                expectedLength_ = byte;
                if (expectedLength_ > MAX_PAYLOAD) {
                    state_ = State::Error;
                } else {
                    payloadIndex_ = 0;
                    state_ = State::WaitingPayload;
                }
                break;

            case State::WaitingPayload:
                payload_[payloadIndex_++] = byte;
                if (payloadIndex_ >= expectedLength_) {
                    state_ = State::WaitingChecksum;
                }
                break;

            case State::WaitingChecksum:
                if (verifyChecksum(byte)) {
                    state_ = State::Complete;
                } else {
                    state_ = State::Error;
                }
                break;

            default:
                state_ = State::Idle;
                break;
        }
        return state_;
    }

private:
    static constexpr uint8_t SYNC_BYTE = 0xAA;
    static constexpr uint8_t MAX_PAYLOAD = 32;

    State state_ = State::Idle;
    uint8_t header_ = 0;
    uint8_t expectedLength_ = 0;
    uint8_t payloadIndex_ = 0;
    uint8_t payload_[MAX_PAYLOAD] = {};  // Fixed buffer, no heap

    bool verifyChecksum(uint8_t received) {
        uint8_t calc = header_ ^ expectedLength_;
        for (uint8_t i = 0; i < expectedLength_; i++) {
            calc ^= payload_[i];
        }
        return calc == received;
    }
};
```

---

## Circular Buffer Pattern

### Lock-Free Single Producer Single Consumer

```cpp
// ISR-safe circular buffer (SPSC - no mutex needed)
template <typename T, size_t Size>
class CircularBuffer {
    static_assert((Size & (Size - 1)) == 0, "Size must be power of 2");

public:
    // Called from ISR (producer)
    bool pushFromISR(const T& item) {
        size_t next = (head_ + 1) & MASK;
        if (next == tail_) return false;  // Full
        buffer_[head_] = item;
        head_ = next;
        return true;
    }

    // Called from task (consumer)
    bool pop(T& item) {
        if (tail_ == head_) return false;  // Empty
        item = buffer_[tail_];
        tail_ = (tail_ + 1) & MASK;
        return true;
    }

    size_t available() const {
        return (head_ - tail_) & MASK;
    }

    bool empty() const { return head_ == tail_; }
    bool full() const { return ((head_ + 1) & MASK) == tail_; }

private:
    static constexpr size_t MASK = Size - 1;
    T buffer_[Size];
    volatile size_t head_ = 0;
    volatile size_t tail_ = 0;
};

// Usage: ISR writes ADC samples, task processes them
static CircularBuffer<uint16_t, 64> adcBuffer;  // 64 samples, 128 bytes
```

---

## Singleton for Hardware

### Hardware Abstraction Singleton

```cpp
// For MCU peripherals that have exactly one instance
class Uart1 {
public:
    static Uart1& instance() {
        static Uart1 uart;  // Initialized once, static storage
        return uart;
    }

    bool transmit(const uint8_t* data, uint16_t len, uint32_t timeout) {
        return HAL_UART_Transmit(&huart1_, data, len, timeout) == HAL_OK;
    }

    bool receive(uint8_t* data, uint16_t len, uint32_t timeout) {
        return HAL_UART_Receive(&huart1_, data, len, timeout) == HAL_OK;
    }

    void enableRxInterrupt() {
        HAL_UART_Receive_IT(&huart1_, &rxByte_, 1);
    }

    // Prevent copy/move (hardware is unique)
    Uart1(const Uart1&) = delete;
    Uart1& operator=(const Uart1&) = delete;
    Uart1(Uart1&&) = delete;
    Uart1& operator=(Uart1&&) = delete;

private:
    Uart1() = default;

    UART_HandleTypeDef huart1_ = {};
    uint8_t rxByte_ = 0;
};
```
