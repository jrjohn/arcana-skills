# STM32 Developer Skill - Code Examples

## Table of Contents
1. [New Observer Service](#new-observer-service)
2. [New Publisher Service](#new-publisher-service)
3. [New Model Definition](#new-model-definition)
4. [ISR Publishing](#isr-publishing)
5. [Timer Service (Reference Publisher)](#timer-service-reference-publisher)
6. [Counter Service (Reference Observer)](#counter-service-reference-observer)
7. [Application Orchestration](#application-orchestration)
8. [Error Handling](#error-handling)
9. [Multi-Model Observer](#multi-model-observer)
10. [UART Debug Output](#uart-debug-output)
11. [Sensor Polling Service](#sensor-polling-service)
12. [Watchdog Service](#watchdog-service)

---

## New Observer Service

### Header (Core/Inc/LedService.hpp)

```cpp
#pragma once

#include "Observable.hpp"
#include "Models.hpp"

class LedService {
public:
    LedService() = default;

    // Initialize GPIO and register as observer
    void init(Observable<CounterModel>& counterObservable);

    // Observer callback - called by dispatcher task
    static void onCounterUpdate(const CounterModel& model, void* context);

private:
    // LED state (no heap allocation)
    bool ledState_ = false;
    uint32_t lastToggleCount_ = 0;
    static constexpr uint32_t TOGGLE_INTERVAL = 10;  // Toggle every 10 counts

    // Observer registration (static lifetime)
    Observer<CounterModel> observer_;

    void toggleLed();
    void setLed(bool on);
};
```

### Implementation (Core/Src/LedService.cpp)

```cpp
#include "LedService.hpp"
#include "main.h"  // For GPIO pin definitions

void LedService::init(Observable<CounterModel>& counterObservable) {
    // Setup observer with callback and context
    observer_.callback = &LedService::onCounterUpdate;
    observer_.context = this;

    // Register with observable (max 4 observers)
    bool success = counterObservable.subscribe(&observer_);
    if (!success) {
        // Observer limit reached - critical configuration error
        Error_Handler();
    }
}

void LedService::onCounterUpdate(const CounterModel& model, void* context) {
    // IMPORTANT: This runs in dispatcher task context, NOT ISR
    auto* self = static_cast<LedService*>(context);

    if (model.count - self->lastToggleCount_ >= TOGGLE_INTERVAL) {
        self->lastToggleCount_ = model.count;
        self->toggleLed();
    }
}

void LedService::toggleLed() {
    ledState_ = !ledState_;
    setLed(ledState_);
}

void LedService::setLed(bool on) {
    HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin,
                      on ? GPIO_PIN_SET : GPIO_PIN_RESET);
}
```

---

## New Publisher Service

### Header (Core/Inc/ButtonService.hpp)

```cpp
#pragma once

#include "Observable.hpp"
#include "Models.hpp"
#include "FreeRTOS.h"
#include "task.h"

class ButtonService {
public:
    ButtonService() = default;

    // Initialize with reference to observable for publishing
    void init(Observable<ButtonModel>& buttonObservable);

    // FreeRTOS task entry point
    static void taskEntry(void* param);

    // ISR callback for button press (called from EXTI handler)
    void onButtonPressISR();

private:
    Observable<ButtonModel>* observable_ = nullptr;

    // Debounce state (no heap)
    volatile bool buttonPressed_ = false;
    uint32_t lastPressTime_ = 0;
    uint32_t pressCount_ = 0;
    static constexpr uint32_t DEBOUNCE_MS = 50;

    void taskLoop();
    bool isDebounced(uint32_t currentTime);
};
```

### Implementation (Core/Src/ButtonService.cpp)

```cpp
#include "ButtonService.hpp"

void ButtonService::init(Observable<ButtonModel>& buttonObservable) {
    observable_ = &buttonObservable;
}

void ButtonService::taskEntry(void* param) {
    auto* self = static_cast<ButtonService*>(param);
    self->taskLoop();
}

void ButtonService::taskLoop() {
    for (;;) {
        // Wait for button press notification (set by ISR)
        if (buttonPressed_) {
            uint32_t now = HAL_GetTick();

            if (isDebounced(now)) {
                lastPressTime_ = now;
                pressCount_++;

                // Create model on stack (will be copied to queue)
                ButtonModel model;
                model.pressCount = pressCount_;
                model.timestamp = now;
                model.isLongPress = false;

                // Publish to observers (normal priority)
                observable_->publish(model);
            }

            buttonPressed_ = false;
        }

        // Yield to other tasks
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

bool ButtonService::isDebounced(uint32_t currentTime) {
    return (currentTime - lastPressTime_) >= DEBOUNCE_MS;
}

// Called from EXTI ISR - must be ISR-safe
void ButtonService::onButtonPressISR() {
    // Just set flag - actual processing in task context
    buttonPressed_ = true;
    // NOTE: If immediate ISR publish is needed:
    // BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    // observable_->publishFromISR(model, &xHigherPriorityTaskWoken);
    // portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
}
```

---

## New Model Definition

### Adding Models (Core/Inc/Models.hpp)

```cpp
#pragma once

#include <cstdint>
#include <type_traits>

// ============================================================
// Time Model - Published by TimerService every second
// ============================================================
struct TimeModel {
    uint8_t hours;          // 0-23
    uint8_t minutes;        // 0-59
    uint8_t seconds;        // 0-59
    uint16_t milliseconds;  // 0-999
};
static_assert(sizeof(TimeModel) <= 8, "TimeModel exceeds queue item budget");
static_assert(std::is_trivially_copyable<TimeModel>::value,
              "TimeModel must be trivially copyable");

// ============================================================
// Counter Model - Published by CounterService on count update
// ============================================================
struct CounterModel {
    uint32_t count;         // Current count value
    uint32_t overflowCount; // Number of overflows
};
static_assert(sizeof(CounterModel) <= 8, "CounterModel exceeds queue item budget");
static_assert(std::is_trivially_copyable<CounterModel>::value,
              "CounterModel must be trivially copyable");

// ============================================================
// Button Model - Published by ButtonService on press
// ============================================================
struct ButtonModel {
    uint32_t pressCount;    // Total press count
    uint32_t timestamp;     // HAL_GetTick() at press time
    bool isLongPress;       // Long press detection
    uint8_t padding[3];     // Explicit alignment padding
};
static_assert(sizeof(ButtonModel) <= 12, "ButtonModel exceeds queue item budget");
static_assert(std::is_trivially_copyable<ButtonModel>::value,
              "ButtonModel must be trivially copyable");

// ============================================================
// Sensor Model - Published by SensorService on new reading
// ============================================================
struct SensorModel {
    int16_t temperature;    // Temperature in 0.1 degree C units
    uint16_t humidity;      // Humidity in 0.1% units
    uint16_t pressure;      // Pressure in hPa
    uint8_t sensorId;       // Which sensor (0-3)
    uint8_t status;         // 0=OK, 1=Error, 2=Stale
};
static_assert(sizeof(SensorModel) == 8, "SensorModel size mismatch");
static_assert(std::is_trivially_copyable<SensorModel>::value,
              "SensorModel must be trivially copyable");

// ============================================================
// ADC Model - Published from ADC DMA complete ISR
// ============================================================
struct AdcModel {
    uint16_t channels[4];   // Up to 4 ADC channels
};
static_assert(sizeof(AdcModel) == 8, "AdcModel size mismatch");
static_assert(std::is_trivially_copyable<AdcModel>::value,
              "AdcModel must be trivially copyable");

// ============================================================
// Model Type Discriminator (for queue union)
// ============================================================
enum class ModelType : uint8_t {
    Time = 0,
    Counter,
    Button,
    Sensor,
    Adc,
    // Add new types here
    COUNT  // Must be last
};

// ============================================================
// Queue Item - Union of all models for queue transport
// ============================================================
struct QueueItem {
    ModelType type;
    uint8_t reserved[3];  // Alignment to 4 bytes
    union {
        TimeModel time;
        CounterModel counter;
        ButtonModel button;
        SensorModel sensor;
        AdcModel adc;
    } data;
};
static_assert(sizeof(QueueItem) <= 16, "QueueItem too large for queue");
```

---

## ISR Publishing

### GPIO EXTI ISR Publishing

```cpp
// Core/Src/stm32f0xx_it.c (or callback in main.c)

// Forward declaration of the button service (defined in App.cpp)
extern ButtonService buttonService;
extern Observable<ButtonModel> buttonObservable;

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin) {
    if (GPIO_Pin == USER_BUTTON_Pin) {
        // Option 1: Set flag for task-level processing (preferred)
        buttonService.onButtonPressISR();

        // Option 2: Direct ISR publish (for time-critical events)
        ButtonModel model;
        model.pressCount = 0;  // Updated in task
        model.timestamp = HAL_GetTick();
        model.isLongPress = false;

        BaseType_t xHigherPriorityTaskWoken = pdFALSE;
        buttonObservable.publishHighPriorityFromISR(
            model, &xHigherPriorityTaskWoken
        );
        portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
    }
}
```

### Timer ISR Publishing

```cpp
// Timer interrupt - periodic high-frequency events
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef* htim) {
    if (htim->Instance == TIM2) {
        static volatile uint32_t tickCount = 0;
        tickCount++;

        // Publish time model every 1000ms
        if (tickCount % 1000 == 0) {
            TimeModel model;
            model.hours = (tickCount / 3600000) % 24;
            model.minutes = (tickCount / 60000) % 60;
            model.seconds = (tickCount / 1000) % 60;
            model.milliseconds = tickCount % 1000;

            BaseType_t xHigherPriorityTaskWoken = pdFALSE;
            // Use normal priority for periodic updates
            timeObservable.publishFromISR(model, &xHigherPriorityTaskWoken);
            portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
        }
    }
}
```

### ADC DMA Complete ISR Publishing

```cpp
// ADC conversion complete via DMA
extern Observable<AdcModel> adcObservable;
static volatile uint16_t adcDmaBuffer[4];  // DMA target buffer

void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc) {
    if (hadc->Instance == ADC1) {
        AdcModel model;
        // Copy DMA buffer to model (single copy)
        for (int i = 0; i < 4; i++) {
            model.channels[i] = adcDmaBuffer[i];
        }

        BaseType_t xHigherPriorityTaskWoken = pdFALSE;
        adcObservable.publishHighPriorityFromISR(
            model, &xHigherPriorityTaskWoken
        );
        portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
    }
}
```

### UART Receive ISR Publishing

```cpp
// UART byte received - publish for protocol parsing in task context
struct UartRxModel {
    uint8_t data[8];    // Received bytes
    uint8_t length;     // Number of valid bytes
    uint8_t portId;     // UART port identifier
    uint8_t padding[2]; // Alignment
};
static_assert(sizeof(UartRxModel) <= 12, "UartRxModel too large");

extern Observable<UartRxModel> uartObservable;

void HAL_UART_RxCpltCallback(UART_HandleTypeDef* huart) {
    if (huart->Instance == USART1) {
        static uint8_t rxByte;

        UartRxModel model;
        model.data[0] = rxByte;
        model.length = 1;
        model.portId = 1;

        BaseType_t xHigherPriorityTaskWoken = pdFALSE;
        uartObservable.publishFromISR(model, &xHigherPriorityTaskWoken);

        // Re-enable receive for next byte
        HAL_UART_Receive_IT(huart, &rxByte, 1);

        portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
    }
}
```

---

## Timer Service (Reference Publisher)

### Header (Core/Inc/TimerService.hpp)

```cpp
#pragma once

#include "Observable.hpp"
#include "Models.hpp"
#include "FreeRTOS.h"
#include "task.h"

class TimerService {
public:
    TimerService() = default;

    void init(Observable<TimeModel>& timeObservable);

    // FreeRTOS task entry point (static for C linkage)
    static void taskEntry(void* param);

private:
    Observable<TimeModel>* observable_ = nullptr;
    uint32_t startTick_ = 0;

    void taskLoop();
    TimeModel calculateTime(uint32_t elapsedMs);
};
```

### Implementation (Core/Src/TimerService.cpp)

```cpp
#include "TimerService.hpp"

void TimerService::init(Observable<TimeModel>& timeObservable) {
    observable_ = &timeObservable;
    startTick_ = HAL_GetTick();
}

void TimerService::taskEntry(void* param) {
    auto* self = static_cast<TimerService*>(param);
    self->taskLoop();
}

void TimerService::taskLoop() {
    TickType_t lastWakeTime = xTaskGetTickCount();

    for (;;) {
        uint32_t elapsed = HAL_GetTick() - startTick_;

        // Create model on stack - will be copied into queue (single copy)
        TimeModel model = calculateTime(elapsed);

        // Publish to all subscribed observers
        observable_->publish(model);

        // Precise 1-second interval using vTaskDelayUntil
        vTaskDelayUntil(&lastWakeTime, pdMS_TO_TICKS(1000));
    }
}

TimeModel TimerService::calculateTime(uint32_t elapsedMs) {
    TimeModel model;
    uint32_t totalSeconds = elapsedMs / 1000;
    model.hours = static_cast<uint8_t>((totalSeconds / 3600) % 24);
    model.minutes = static_cast<uint8_t>((totalSeconds / 60) % 60);
    model.seconds = static_cast<uint8_t>(totalSeconds % 60);
    model.milliseconds = static_cast<uint16_t>(elapsedMs % 1000);
    return model;
}
```

---

## Counter Service (Reference Observer)

### Header (Core/Inc/CounterService.hpp)

```cpp
#pragma once

#include "Observable.hpp"
#include "Models.hpp"

class CounterService {
public:
    CounterService() = default;

    void init(Observable<TimeModel>& timeObservable,
              Observable<CounterModel>& counterObservable);

    // Observer callback
    static void onTimeUpdate(const TimeModel& model, void* context);

    uint32_t getCount() const { return count_; }

private:
    Observable<CounterModel>* counterObservable_ = nullptr;
    Observer<TimeModel> observer_;
    uint32_t count_ = 0;
    uint32_t overflowCount_ = 0;
    static constexpr uint32_t MAX_COUNT = 0xFFFFFFFF;

    void processTime(const TimeModel& model);
    void publishCount();
};
```

### Implementation (Core/Src/CounterService.cpp)

```cpp
#include "CounterService.hpp"

void CounterService::init(Observable<TimeModel>& timeObservable,
                           Observable<CounterModel>& counterObservable) {
    counterObservable_ = &counterObservable;

    // Setup observer
    observer_.callback = &CounterService::onTimeUpdate;
    observer_.context = this;

    // Subscribe to time events
    bool success = timeObservable.subscribe(&observer_);
    if (!success) {
        Error_Handler();  // Observer limit exceeded
    }
}

void CounterService::onTimeUpdate(const TimeModel& model, void* context) {
    auto* self = static_cast<CounterService*>(context);
    self->processTime(model);
}

void CounterService::processTime(const TimeModel& model) {
    // Increment counter (handle overflow)
    if (count_ == MAX_COUNT) {
        count_ = 0;
        overflowCount_++;
    } else {
        count_++;
    }

    // Publish counter update to downstream observers
    publishCount();
}

void CounterService::publishCount() {
    CounterModel model;
    model.count = count_;
    model.overflowCount = overflowCount_;

    // Publish (normal priority - not time critical)
    counterObservable_->publish(model);
}
```

---

## Application Orchestration

### Header (Core/Inc/App.hpp)

```cpp
#pragma once

#include "Observable.hpp"
#include "Models.hpp"
#include "TimerService.hpp"
#include "CounterService.hpp"
#include "TimeDisplayService.hpp"
#include "FreeRTOS.h"
#include "task.h"

class App {
public:
    App() = default;

    // Initialize all services and observables
    void init();

    // Start FreeRTOS scheduler (never returns)
    void run();

private:
    // Observable framework
    ObservableDispatcher dispatcher_;
    Observable<TimeModel> timeObservable_;
    Observable<CounterModel> counterObservable_;

    // Services
    TimerService timerService_;
    CounterService counterService_;
    TimeDisplayService timeDisplayService_;

    // Observer registrations
    Observer<TimeModel> displayObserver_;

    // Static task storage (no heap allocation for tasks)
    static StaticTask_t dispatcherTaskTCB_;
    static StackType_t  dispatcherTaskStack_[128];

    static StaticTask_t timerTaskTCB_;
    static StackType_t  timerTaskStack_[128];

    static StaticTask_t counterTaskTCB_;
    static StackType_t  counterTaskStack_[128];

    void initObservables();
    void initServices();
    void createTasks();
    void registerObservers();

    // Error callback
    static void onObservableError(ObservableError error, void* context);
};
```

### Implementation (Core/Src/App.cpp)

```cpp
#include "App.hpp"

// Static storage definitions
StaticTask_t App::dispatcherTaskTCB_;
StackType_t  App::dispatcherTaskStack_[128];
StaticTask_t App::timerTaskTCB_;
StackType_t  App::timerTaskStack_[128];
StaticTask_t App::counterTaskTCB_;
StackType_t  App::counterTaskStack_[128];

void App::init() {
    initObservables();
    initServices();
    registerObservers();
    createTasks();
}

void App::run() {
    // Start FreeRTOS scheduler - this never returns
    vTaskStartScheduler();

    // Should never reach here
    Error_Handler();
}

void App::initObservables() {
    // Initialize dispatcher (creates queues)
    dispatcher_.init();
    dispatcher_.setErrorCallback(&App::onObservableError, this);

    // Link observables to dispatcher
    timeObservable_.init(&dispatcher_);
    counterObservable_.init(&dispatcher_);
}

void App::initServices() {
    // Initialize services with observable references
    timerService_.init(timeObservable_);
    counterService_.init(timeObservable_, counterObservable_);
    timeDisplayService_.init();
}

void App::registerObservers() {
    // Counter service observes time events
    // (done inside CounterService::init)

    // Display service observes time events
    displayObserver_.callback = &TimeDisplayService::onTimeUpdate;
    displayObserver_.context = &timeDisplayService_;
    timeObservable_.subscribe(&displayObserver_);
}

void App::createTasks() {
    // Dispatcher task (highest app priority)
    dispatcher_.start(
        "Disp",
        osPriorityAboveNormal,
        dispatcherTaskStack_,
        128,
        &dispatcherTaskTCB_
    );

    // Timer service task
    xTaskCreateStatic(
        TimerService::taskEntry,
        "Timer",
        128,
        &timerService_,
        osPriorityNormal,
        timerTaskStack_,
        &timerTaskTCB_
    );
}

void App::onObservableError(ObservableError error, void* context) {
    switch (error) {
        case ObservableError::QueueFull:
            // Log: event dropped due to queue overflow
            break;
        case ObservableError::QueueNotReady:
            Error_Handler();
            break;
        default:
            break;
    }
}
```

### main.c Integration

```c
/* Core/Src/main.c */
#include "main.h"
#include "App.hpp"

// Single static app instance - entire application
static App app;

int main(void) {
    // HAL initialization
    HAL_Init();
    SystemClock_Config();

    // GPIO, UART, TIM, etc. peripheral init
    MX_GPIO_Init();
    MX_USART1_UART_Init();
    MX_TIM2_Init();

    // Initialize application (observables, services, tasks)
    app.init();

    // Start FreeRTOS scheduler (never returns)
    app.run();

    // Should never reach here
    while (1) {}
}
```

---

## Error Handling

### Comprehensive Error Handler

```cpp
// Core/Inc/ErrorHandler.hpp
#pragma once

#include <cstdint>
#include "Observable.hpp"

struct ErrorStats {
    volatile uint32_t droppedEvents;
    volatile uint32_t stackOverflows;
    volatile uint32_t hardFaults;
    volatile uint32_t mallocFailures;
    volatile uint32_t assertFailures;
};

class ErrorHandler {
public:
    static ErrorHandler& instance();

    void onObservableError(ObservableError error);
    void onStackOverflow(TaskHandle_t task, char* taskName);
    void onMallocFailed();
    void onAssertFailed(const char* file, uint32_t line);

    const ErrorStats& getStats() const { return stats_; }

private:
    ErrorHandler() = default;
    ErrorStats stats_ = {};

    // Debug output buffer (static, no heap)
    char debugBuffer_[64];
    void debugPrint(const char* msg);
};
```

### Implementation

```cpp
#include "ErrorHandler.hpp"
#include <cstdio>

ErrorHandler& ErrorHandler::instance() {
    static ErrorHandler handler;
    return handler;
}

void ErrorHandler::onObservableError(ObservableError error) {
    switch (error) {
        case ObservableError::QueueFull:
            stats_.droppedEvents++;
            debugPrint("ERR: Queue full, event dropped");
            break;
        case ObservableError::QueueNotReady:
            stats_.droppedEvents++;
            debugPrint("ERR: Queue not ready");
            break;
        case ObservableError::NoObservers:
            // Non-fatal: log but continue
            debugPrint("WARN: No observers for event");
            break;
        default:
            break;
    }
}

void ErrorHandler::onStackOverflow(TaskHandle_t task, char* taskName) {
    stats_.stackOverflows++;
    snprintf(debugBuffer_, sizeof(debugBuffer_),
             "FATAL: Stack overflow in %s", taskName);
    debugPrint(debugBuffer_);

    // In production: trigger watchdog reset
    // In debug: breakpoint
    __BKPT(0);
}

void ErrorHandler::debugPrint(const char* msg) {
    // Retarget to UART, SWO, or ITM based on build config
    // HAL_UART_Transmit(&huart1, (uint8_t*)msg, strlen(msg), 100);
    (void)msg;  // Suppress unused warning in release build
}
```

### FreeRTOS Hook Functions

```cpp
// Required by FreeRTOS when configUSE_MALLOC_FAILED_HOOK = 1
extern "C" void vApplicationMallocFailedHook(void) {
    ErrorHandler::instance().onMallocFailed();
    // Halt in debug mode
    __BKPT(0);
    for (;;) {}
}

// Required by FreeRTOS when configCHECK_FOR_STACK_OVERFLOW > 0
extern "C" void vApplicationStackOverflowHook(
    TaskHandle_t xTask, char* pcTaskName
) {
    ErrorHandler::instance().onStackOverflow(xTask, pcTaskName);
    for (;;) {}
}

// Idle hook - can be used for power saving
extern "C" void vApplicationIdleHook(void) {
    __WFI();  // Wait for interrupt - saves power
}
```

---

## Multi-Model Observer

### Service Observing Multiple Event Types

```cpp
// Core/Inc/DashboardService.hpp
#pragma once

#include "Observable.hpp"
#include "Models.hpp"

class DashboardService {
public:
    DashboardService() = default;

    void init(Observable<TimeModel>& timeObs,
              Observable<CounterModel>& counterObs,
              Observable<SensorModel>& sensorObs);

    // Separate callbacks for each model type
    static void onTimeUpdate(const TimeModel& model, void* ctx);
    static void onCounterUpdate(const CounterModel& model, void* ctx);
    static void onSensorUpdate(const SensorModel& model, void* ctx);

    // Get current dashboard state
    struct DashboardState {
        TimeModel lastTime;
        CounterModel lastCounter;
        SensorModel lastSensor;
        uint32_t updateCount;
    };

    const DashboardState& getState() const { return state_; }

private:
    // One observer per model type
    Observer<TimeModel> timeObserver_;
    Observer<CounterModel> counterObserver_;
    Observer<SensorModel> sensorObserver_;

    // Dashboard state (updated by callbacks)
    DashboardState state_ = {};
};
```

### Implementation

```cpp
#include "DashboardService.hpp"
#include <cstring>  // for memcpy

void DashboardService::init(Observable<TimeModel>& timeObs,
                             Observable<CounterModel>& counterObs,
                             Observable<SensorModel>& sensorObs) {
    // Register time observer
    timeObserver_.callback = &DashboardService::onTimeUpdate;
    timeObserver_.context = this;
    timeObs.subscribe(&timeObserver_);

    // Register counter observer
    counterObserver_.callback = &DashboardService::onCounterUpdate;
    counterObserver_.context = this;
    counterObs.subscribe(&counterObserver_);

    // Register sensor observer
    sensorObserver_.callback = &DashboardService::onSensorUpdate;
    sensorObserver_.context = this;
    sensorObs.subscribe(&sensorObserver_);
}

void DashboardService::onTimeUpdate(const TimeModel& model, void* ctx) {
    auto* self = static_cast<DashboardService*>(ctx);
    // Copy model data to dashboard state
    // (model reference is only valid during callback)
    memcpy(&self->state_.lastTime, &model, sizeof(TimeModel));
    self->state_.updateCount++;
}

void DashboardService::onCounterUpdate(const CounterModel& model, void* ctx) {
    auto* self = static_cast<DashboardService*>(ctx);
    memcpy(&self->state_.lastCounter, &model, sizeof(CounterModel));
    self->state_.updateCount++;
}

void DashboardService::onSensorUpdate(const SensorModel& model, void* ctx) {
    auto* self = static_cast<DashboardService*>(ctx);
    memcpy(&self->state_.lastSensor, &model, sizeof(SensorModel));
    self->state_.updateCount++;
}
```

---

## UART Debug Output

### Retarget Printf to UART

```cpp
// Core/Src/retarget.cpp
// Printf retargeting for debug output (newlib-nano)

#include <cstdio>
#include <cstdarg>
#include "main.h"

extern UART_HandleTypeDef huart1;

// Static buffer - no heap allocation
static char printBuffer[128];

extern "C" int _write(int file, char* ptr, int len) {
    (void)file;
    HAL_UART_Transmit(&huart1, reinterpret_cast<uint8_t*>(ptr),
                      static_cast<uint16_t>(len), 100);
    return len;
}

// Safe printf wrapper with fixed buffer
void debugPrintf(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    int len = vsnprintf(printBuffer, sizeof(printBuffer), fmt, args);
    va_end(args);

    if (len > 0) {
        HAL_UART_Transmit(&huart1,
                          reinterpret_cast<uint8_t*>(printBuffer),
                          static_cast<uint16_t>(len), 100);
    }
}
```

### Debug Observer for UART Logging

```cpp
// Log all time events to UART
class DebugLogService {
public:
    void init(Observable<TimeModel>& timeObs) {
        observer_.callback = &DebugLogService::onTimeUpdate;
        observer_.context = this;
        timeObs.subscribe(&observer_);
    }

    static void onTimeUpdate(const TimeModel& model, void* ctx) {
        // WARNING: printf in observer callback adds latency
        // Only use in debug builds
        #ifdef DEBUG
        debugPrintf("[TIME] %02u:%02u:%02u.%03u\r\n",
                    model.hours, model.minutes,
                    model.seconds, model.milliseconds);
        #else
        (void)model;
        (void)ctx;
        #endif
    }

private:
    Observer<TimeModel> observer_;
};
```

---

## Sensor Polling Service

### I2C Sensor Publisher

```cpp
// Core/Inc/SensorService.hpp
#pragma once

#include "Observable.hpp"
#include "Models.hpp"
#include "FreeRTOS.h"
#include "task.h"

class SensorService {
public:
    SensorService() = default;

    void init(Observable<SensorModel>& sensorObservable);
    static void taskEntry(void* param);

private:
    Observable<SensorModel>* observable_ = nullptr;

    // Sensor state (no heap)
    SensorModel lastReading_ = {};
    uint32_t readCount_ = 0;
    uint32_t errorCount_ = 0;

    static constexpr uint32_t POLL_INTERVAL_MS = 2000;  // 2 second poll
    static constexpr uint8_t SENSOR_I2C_ADDR = 0x44;    // SHT31 address

    void taskLoop();
    bool readSensor(SensorModel& model);
    bool i2cRead(uint8_t addr, uint8_t* data, uint16_t len);
};
```

### Implementation

```cpp
#include "SensorService.hpp"
#include "main.h"

extern I2C_HandleTypeDef hi2c1;

void SensorService::init(Observable<SensorModel>& sensorObservable) {
    observable_ = &sensorObservable;
}

void SensorService::taskEntry(void* param) {
    auto* self = static_cast<SensorService*>(param);
    self->taskLoop();
}

void SensorService::taskLoop() {
    TickType_t lastWakeTime = xTaskGetTickCount();

    for (;;) {
        SensorModel model;
        model.sensorId = 0;

        if (readSensor(model)) {
            model.status = 0;  // OK
            readCount_++;
            lastReading_ = model;

            // Publish sensor reading
            observable_->publish(model);
        } else {
            model.status = 1;  // Error
            errorCount_++;

            // Still publish error status so observers know
            observable_->publish(model);
        }

        vTaskDelayUntil(&lastWakeTime, pdMS_TO_TICKS(POLL_INTERVAL_MS));
    }
}

bool SensorService::readSensor(SensorModel& model) {
    uint8_t cmd[2] = {0x24, 0x00};  // SHT31: high repeatability
    uint8_t data[6] = {};

    // Send measurement command
    if (HAL_I2C_Master_Transmit(&hi2c1, SENSOR_I2C_ADDR << 1,
                                 cmd, 2, 100) != HAL_OK) {
        return false;
    }

    // Wait for measurement (15ms for high repeatability)
    vTaskDelay(pdMS_TO_TICKS(20));

    // Read 6 bytes: temp MSB, temp LSB, CRC, hum MSB, hum LSB, CRC
    if (HAL_I2C_Master_Receive(&hi2c1, SENSOR_I2C_ADDR << 1,
                                data, 6, 100) != HAL_OK) {
        return false;
    }

    // Convert raw to engineering units
    uint16_t rawTemp = (data[0] << 8) | data[1];
    uint16_t rawHum = (data[3] << 8) | data[4];

    // Temperature in 0.1 C: -45 + 175 * rawTemp / 65535
    model.temperature = static_cast<int16_t>(
        -450 + (1750 * static_cast<int32_t>(rawTemp)) / 65535
    );

    // Humidity in 0.1%: 100 * rawHum / 65535
    model.humidity = static_cast<uint16_t>(
        (1000 * static_cast<uint32_t>(rawHum)) / 65535
    );

    model.pressure = 0;  // Not available on SHT31

    return true;
}
```

---

## Watchdog Service

### IWDG Configuration and Task

```cpp
// Core/Inc/WatchdogService.hpp
#pragma once

#include "FreeRTOS.h"
#include "task.h"
#include "main.h"

class WatchdogService {
public:
    WatchdogService() = default;

    // Initialize IWDG with timeout
    void init(uint32_t timeoutMs);

    // Task that kicks the watchdog
    static void taskEntry(void* param);

    // Call from each task to report "alive"
    void reportAlive(uint8_t taskId);

    // Check if all tasks are alive
    bool allTasksAlive() const;

private:
    static constexpr uint8_t MAX_TASKS = 4;
    volatile uint32_t lastReport_[MAX_TASKS] = {};
    uint32_t timeoutMs_ = 0;
    uint8_t registeredTasks_ = 0;

    void taskLoop();
    void kickWatchdog();
};
```

### Implementation

```cpp
#include "WatchdogService.hpp"

extern IWDG_HandleTypeDef hiwdg;

void WatchdogService::init(uint32_t timeoutMs) {
    timeoutMs_ = timeoutMs;

    // IWDG configuration (done in CubeMX or manually)
    // Prescaler: /256, Reload: calculated from timeout
    // At 40kHz LSI: timeout = (prescaler * reload) / 40000
}

void WatchdogService::taskEntry(void* param) {
    auto* self = static_cast<WatchdogService*>(param);
    self->taskLoop();
}

void WatchdogService::taskLoop() {
    for (;;) {
        if (allTasksAlive()) {
            kickWatchdog();
        }
        // If any task hasn't reported in, watchdog will reset MCU

        vTaskDelay(pdMS_TO_TICKS(timeoutMs_ / 4));
    }
}

void WatchdogService::reportAlive(uint8_t taskId) {
    if (taskId < MAX_TASKS) {
        lastReport_[taskId] = HAL_GetTick();
    }
}

bool WatchdogService::allTasksAlive() const {
    uint32_t now = HAL_GetTick();
    for (uint8_t i = 0; i < registeredTasks_; i++) {
        if ((now - lastReport_[i]) > timeoutMs_) {
            return false;
        }
    }
    return true;
}

void WatchdogService::kickWatchdog() {
    HAL_IWDG_Refresh(&hiwdg);
}
```
