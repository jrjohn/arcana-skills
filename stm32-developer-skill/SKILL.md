---
name: stm32-developer-skill
description: STM32 embedded development guide based on Arcana Embedded STM32 architecture. Provides comprehensive support for Observable Pattern on STM32F051C8 (8KB RAM, 64KB Flash) with FreeRTOS, zero-copy model passing, dual-priority queuing, static allocation, and ISR-safe publishing. Suitable for embedded C++14 development, architecture design, code review, memory optimization, and real-time debugging.
allowed-tools: [Read, Grep, Glob, Bash, Write, Edit]
---

# STM32 Developer Skill

Professional STM32/FreeRTOS/C++14 embedded development skill based on [Arcana Embedded STM32](https://github.com/jrjohn/arcana-embedded-stm32) production architecture.

---

## Quick Reference Card

### New Observer Checklist:
```
1. Define callback signature: void (*callback)(const ModelType&, void*)
2. Create observer struct with callback + context pointer
3. Subscribe via observable.subscribe(&observer)
4. Verify observer count <= MAX_OBSERVERS (4)
5. Implement callback with const reference (zero-copy)
6. Test with both normal and high-priority publish
7. Verify stack usage with arm-none-eabi-size
```

### New Model Checklist:
```
1. Define struct in Models.hpp (POD type, no heap)
2. Keep sizeof(Model) <= queue item size
3. Add static_assert for size verification
4. Register model type in Observable<T> template instantiation
5. Verify total RAM impact: sizeof(Model) * (HIGH_QUEUE + NORMAL_QUEUE)
6. Test zero-copy passing through publish/notify chain
```

### Quick Diagnosis:
| Symptom | Check Command |
|---------|---------------|
| Queue overflow | Check `getStats()` for dropped events |
| Stack overflow | `arm-none-eabi-size -A build/*.elf` check stack sections |
| ISR latency spike | Verify `publishFromISR` uses `portYIELD_FROM_ISR` |
| Observer not called | Check subscribe count, verify dispatcher task running |
| Hard fault | Check stack sizes in FreeRTOSConfig.h, alignment of models |
| High CPU usage | Verify `osDelay` or `xQueueReceive` with `portMAX_DELAY` |

---

## Rules Priority

### CRITICAL (Must Fix Immediately)

| Rule | Description | Verification |
|------|-------------|--------------|
| No Heap Allocation | NEVER use `malloc`, `new`, `std::vector`, `std::string` at runtime | `grep -rn "malloc\|new \|std::vector\|std::string" Core/` |
| Stack Overflow Guard | Every task stack must be verified against worst-case depth | `arm-none-eabi-size -A build/*.elf` |
| ISR Safety | ISR code must ONLY call `publishFromISR` / `publishHighPriorityFromISR` | `grep -rn "publish(" Core/Src/*.cpp` in ISR context |
| Observer Limit | MAX_OBSERVERS = 4 per Observable, NEVER exceed | Check `subscribe()` return values |
| Queue Size Bounds | High=4, Normal=8, fixed at compile time | Verify in Observable.hpp defines |
| RAM Budget | Total RAM usage MUST stay under 8,192 bytes (8KB) | `arm-none-eabi-size build/*.elf` |
| Flash Budget | Total Flash usage MUST stay under 65,536 bytes (64KB) | `arm-none-eabi-size build/*.elf` |
| Volatile for ISR | Shared variables between ISR and task MUST be `volatile` | Review ISR-shared globals |
| Critical Section | Shared data access must use `taskENTER_CRITICAL` / `taskEXIT_CRITICAL` | Review multi-task shared data |

### IMPORTANT (Should Fix Before PR)

| Rule | Description | Verification |
|------|-------------|--------------|
| Zero-Copy Model | Models passed by const reference, never copied unnecessarily | Check callback signatures |
| Error Callback | Set error callback via `setErrorCallback()` for queue overflow | Verify error handling path |
| Static Allocation | All objects allocated statically (global/static scope) | `grep -rn "new \|malloc" Core/` |
| Priority Inversion | High-priority events processed before normal | Test dual-priority ordering |
| FreeRTOS Config | Heap scheme = heap_4, tick rate = 1000Hz | Check FreeRTOSConfig.h |
| Model Alignment | Structs must be properly aligned for ARM Cortex-M0 | Check `__attribute__((aligned))` |
| Const Correctness | Observer callbacks receive `const T&` | Review all callback signatures |

### RECOMMENDED (Nice to Have)

| Rule | Description |
|------|-------------|
| Performance Logging | Track event latency with DWT cycle counter |
| Watchdog Timer | IWDG configured for task hang detection |
| Power Management | Use `__WFI()` in idle task for low power |
| Debug UART | Printf retargeting for debug output |

---

## Error Handling Pattern

### Observable Error Types

```cpp
// Core/Inc/Observable.hpp
enum class ObservableError : uint8_t {
    QueueFull,           // Queue has no space for new event
    QueueNotReady,       // Dispatcher not started yet
    InvalidModel,        // Model validation failed
    NoObservers          // No observers subscribed
};
```

### Error Callback Pattern

```cpp
// Set error callback for queue overflow handling
using ErrorCallback = void (*)(ObservableError error, void* context);

class ObservableDispatcher {
public:
    void setErrorCallback(ErrorCallback cb, void* ctx) {
        errorCallback_ = cb;
        errorContext_ = ctx;
    }

private:
    ErrorCallback errorCallback_ = nullptr;
    void* errorContext_ = nullptr;

    void reportError(ObservableError error) {
        if (errorCallback_) {
            errorCallback_(error, errorContext_);
        }
    }
};
```

### Queue Overflow Handling

```cpp
// CRITICAL: Events are LOST on queue overflow - no retry mechanism
// Application must handle this gracefully

void onObservableError(ObservableError error, void* context) {
    switch (error) {
        case ObservableError::QueueFull:
            // Log dropped event, increment counter
            errorStats.droppedEvents++;
            break;
        case ObservableError::QueueNotReady:
            // Dispatcher task not started - startup ordering issue
            Error_Handler();
            break;
        case ObservableError::InvalidModel:
            // Should not happen in production
            assert(false);
            break;
        case ObservableError::NoObservers:
            // Non-fatal: event published but nobody listening
            break;
    }
}

// Register during init (before scheduler starts)
dispatcher.setErrorCallback(onObservableError, nullptr);
```

---

## Memory Budget

### RAM Breakdown (STM32F051C8 - 8,192 bytes total)

| Component | Bytes | % of Total |
|-----------|-------|------------|
| FreeRTOS Kernel | ~1,200 | 14.6% |
| Task Stacks (3 tasks) | ~1,536 | 18.8% |
| Observable Dispatcher | ~320 | 3.9% |
| Event Queues (High+Normal) | ~480 | 5.9% |
| Observer Arrays | ~128 | 1.6% |
| Model Instances | ~192 | 2.3% |
| Application Variables | ~500 | 6.1% |
| **Total Used** | **~4,356** | **53.2%** |
| **Free** | **~3,836** | **46.8%** |

### Flash Breakdown (STM32F051C8 - 65,536 bytes total)

| Component | Bytes | % of Total |
|-----------|-------|------------|
| Startup + Vector Table | ~512 | 0.8% |
| HAL Drivers | ~4,096 | 6.3% |
| FreeRTOS | ~5,120 | 7.8% |
| Observable Framework | ~2,560 | 3.9% |
| Application Logic | ~3,680 | 5.6% |
| C++ Runtime (minimal) | ~1,000 | 1.5% |
| **Total Used** | **~16,968** | **25.9%** |
| **Free** | **~48,568** | **74.1%** |

### Stack Size Guidelines

| Task | Stack Words | Stack Bytes | Purpose |
|------|------------|-------------|---------|
| Dispatcher | 128 | 512 | Event dispatch loop |
| TimerService | 128 | 512 | Timer tick publisher |
| CounterService | 128 | 512 | Event observer/counter |
| Idle Task | 64 | 256 | FreeRTOS idle |

### Memory Rules

```
RULE 1: NEVER exceed 75% RAM usage (6,144 bytes) - leave headroom for stack growth
RULE 2: Each new model adds: sizeof(Model) * 12 bytes to queue storage
RULE 3: Each new observer adds: 8 bytes (callback + context pointer)
RULE 4: Each new task adds: stack_words * 4 + 88 bytes (TCB)
```

---

## Observable Pattern Architecture

### System Overview

```
                    STM32F051C8 Observable Architecture
    ================================================================

    +-----------------+     +------------------+
    | TimerService    |     | ISR Handler      |
    | (Publisher)     |     | (TIM/GPIO/UART)  |
    +--------+--------+     +--------+---------+
             |                       |
             | publish()             | publishFromISR()
             |                       |
    +--------v-----------------------v---------+
    |          ObservableDispatcher             |
    |  +-----------------------------------+   |
    |  | High Priority Queue (4 items)     |   |
    |  | [evt][evt][evt][evt]              |   |
    |  +-----------------------------------+   |
    |  | Normal Priority Queue (8 items)   |   |
    |  | [evt][evt][evt][evt][evt]...      |   |
    |  +-----------------------------------+   |
    |                  |                       |
    |          dispatch task                   |
    |          (FreeRTOS)                      |
    +------------------+-----------------------+
                       |
                       | notify() - zero copy
                       |
          +------------+------------+
          |            |            |
    +-----v----+ +----v-----+ +---v--------+
    | Counter  | | Time     | | Observer   |
    | Service  | | Display  | | N (max 4)  |
    | Observer | | Observer | |            |
    +----------+ +----------+ +------------+
```

### Event Flow (Normal Priority)

```
    Publisher Task              Dispatcher Task            Observer Callbacks
    =============              ===============            ==================
         |                          |                          |
    1. publish(model)               |                          |
         |                          |                          |
    2. xQueueSend                   |                          |
       (normalQueue)                |                          |
         |                          |                          |
         |                     3. xQueueReceive                |
         |                        (blocking)                   |
         |                          |                          |
         |                     4. for each observer:           |
         |                          |------ notify(model) ---->|
         |                          |          (const T&)      |
         |                          |                     5. callback(model, ctx)
         |                          |<-------------------------|
         |                          |                          |
```

### Event Flow (ISR to Task)

```
    ISR Context                 Dispatcher Task            Observer Callbacks
    ===========                 ===============            ==================
         |                          |                          |
    1. publishFromISR(model)        |                          |
         |                          |                          |
    2. xQueueSendFromISR            |                          |
       (highPriorityQueue)          |                          |
         |                          |                          |
    3. portYIELD_FROM_ISR           |                          |
       (if higher priority          |                          |
        task woken)                 |                          |
         |                     4. xQueueReceive                |
         |                        (high queue first)           |
         |                          |                          |
         |                     5. notify all observers         |
         |                          |------ callback --------->|
         |                          |                          |
```

---

## Dual-Priority Queue System

### Queue Configuration

```cpp
// Observable.hpp - Queue size definitions
static constexpr uint8_t HIGH_PRIORITY_QUEUE_SIZE = 4;
static constexpr uint8_t NORMAL_PRIORITY_QUEUE_SIZE = 8;

// Queue item structure (stored by value - zero copy to observers)
struct QueueItem {
    uint8_t modelType;      // Model discriminator
    uint8_t padding[3];     // Alignment padding
    union {
        TimeModel time;
        CounterModel counter;
        // Add new model types here
    } data;
};
```

### Priority Dispatch Logic

```cpp
// Dispatcher processes HIGH priority queue first, then NORMAL
void ObservableDispatcher::dispatchTask(void* param) {
    auto* self = static_cast<ObservableDispatcher*>(param);

    for (;;) {
        QueueItem item;

        // 1. Always drain high-priority queue first
        while (xQueueReceive(self->highQueue_, &item, 0) == pdTRUE) {
            self->dispatch(item);
        }

        // 2. Process one normal-priority item (or block if both empty)
        if (xQueueReceive(self->normalQueue_, &item, portMAX_DELAY) == pdTRUE) {
            self->dispatch(item);
        }
    }
}
```

### Queue Usage Guidelines

| Priority | Queue Size | Use Case | Latency |
|----------|-----------|----------|---------|
| High | 4 items | ISR events, safety-critical | ~22us |
| Normal | 8 items | Periodic updates, UI refresh | ~50us |

```
WARNING: Events are LOST when queue is full.
- High priority: max 4 pending events before overflow
- Normal priority: max 8 pending events before overflow
- Use hasQueueSpace() to check before publishing non-critical events
- NEVER check hasQueueSpace() from ISR (not ISR-safe for checking)
```

---

## FreeRTOS Integration

### Task Configuration

```cpp
// FreeRTOSConfig.h - Key settings for STM32F051C8
#define configUSE_PREEMPTION            1
#define configCPU_CLOCK_HZ              (48000000)    // 48 MHz HSI
#define configTICK_RATE_HZ              ((TickType_t)1000)  // 1ms tick
#define configMAX_PRIORITIES            (7)
#define configMINIMAL_STACK_SIZE        ((uint16_t)64)
#define configTOTAL_HEAP_SIZE           ((size_t)4096)  // heap_4 scheme
#define configMAX_TASK_NAME_LEN         (8)
#define configUSE_MUTEXES               1
#define configUSE_COUNTING_SEMAPHORES   1
#define configUSE_QUEUE_SETS            0           // Save Flash
#define configUSE_TIMERS                1
#define configTIMER_TASK_STACK_DEPTH    64
#define configUSE_MALLOC_FAILED_HOOK    1
#define configCHECK_FOR_STACK_OVERFLOW  2           // Method 2 (paint+check)

// Memory scheme
#define configSUPPORT_STATIC_ALLOCATION   1
#define configSUPPORT_DYNAMIC_ALLOCATION  1         // heap_4 for FreeRTOS internals
```

### Task Creation Pattern

```cpp
// App.cpp - Static task creation
static StaticTask_t dispatcherTaskTCB;
static StackType_t  dispatcherTaskStack[128];

static StaticTask_t timerTaskTCB;
static StackType_t  timerTaskStack[128];

void App::init() {
    // Create dispatcher task (highest priority among app tasks)
    dispatcher_.start(
        "Dispatch",
        osPriorityAboveNormal,
        dispatcherTaskStack,
        sizeof(dispatcherTaskStack) / sizeof(StackType_t),
        &dispatcherTaskTCB
    );

    // Create timer service task
    xTaskCreateStatic(
        TimerService::taskEntry,
        "Timer",
        128,
        &timerService_,
        osPriorityNormal,
        timerTaskStack,
        &timerTaskTCB
    );
}
```

### FreeRTOS Queue Integration

```cpp
// Observable uses FreeRTOS queues internally
class ObservableDispatcher {
private:
    QueueHandle_t highQueue_;
    QueueHandle_t normalQueue_;

    // Static queue storage (no heap allocation for queues)
    static StaticQueue_t highQueueBuffer_;
    static StaticQueue_t normalQueueBuffer_;
    static uint8_t highQueueStorage_[HIGH_PRIORITY_QUEUE_SIZE * sizeof(QueueItem)];
    static uint8_t normalQueueStorage_[NORMAL_PRIORITY_QUEUE_SIZE * sizeof(QueueItem)];

public:
    void init() {
        highQueue_ = xQueueCreateStatic(
            HIGH_PRIORITY_QUEUE_SIZE,
            sizeof(QueueItem),
            highQueueStorage_,
            &highQueueBuffer_
        );

        normalQueue_ = xQueueCreateStatic(
            NORMAL_PRIORITY_QUEUE_SIZE,
            sizeof(QueueItem),
            normalQueueStorage_,
            &normalQueueBuffer_
        );
    }
};
```

---

## ISR Safety Patterns

### Publishing from ISR

```cpp
// CRITICAL: Only use FromISR variants inside interrupt handlers
void TIM2_IRQHandler(void) {
    HAL_TIM_IRQHandler(&htim2);
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef* htim) {
    if (htim->Instance == TIM2) {
        TimeModel model;
        model.seconds = tickCount / 1000;
        model.milliseconds = tickCount % 1000;

        // CORRECT: Use FromISR variant
        BaseType_t xHigherPriorityTaskWoken = pdFALSE;
        observable.publishFromISR(model, &xHigherPriorityTaskWoken);
        portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
    }
}

// FORBIDDEN patterns in ISR:
// observable.publish(model);         -- WILL CAUSE HARD FAULT
// xQueueSend(queue, &item, timeout); -- WILL CAUSE HARD FAULT if timeout > 0
// taskENTER_CRITICAL();              -- Use taskENTER_CRITICAL_FROM_ISR()
// vTaskDelay();                      -- WILL CAUSE HARD FAULT
// printf();                          -- WILL CAUSE HARD FAULT
```

### ISR-Safe API Summary

| Regular API | ISR-Safe API | Notes |
|-------------|-------------|-------|
| `publish()` | `publishFromISR()` | Must pass `pxHigherPriorityTaskWoken` |
| `publishHighPriority()` | `publishHighPriorityFromISR()` | For safety-critical ISR events |
| `taskENTER_CRITICAL()` | `taskENTER_CRITICAL_FROM_ISR()` | Returns interrupt mask |
| `xQueueSend()` | `xQueueSendFromISR()` | Zero timeout only |
| `xSemaphoreGive()` | `xSemaphoreGiveFromISR()` | Must check task woken |

### ISR Timing Constraints

```
ARM Cortex-M0 ISR Guidelines:
- ISR body: < 10us (480 cycles at 48MHz)
- publishFromISR: ~2us (96 cycles) - just a queue enqueue
- portYIELD_FROM_ISR: ~1us if context switch needed
- Total ISR time with publish: ~3-5us

NEVER do in ISR:
- Floating point operations (Cortex-M0 has no FPU)
- Memory allocation (malloc/new)
- Blocking calls (delay, semaphore wait)
- Printf / UART transmit with blocking
- Complex computation (> 480 cycles)
```

---

## Static Allocation Patterns

### Global Static Objects

```cpp
// App.hpp - All objects statically allocated
class App {
private:
    // Observable framework (static lifetime)
    ObservableDispatcher dispatcher_;
    Observable<TimeModel> timeObservable_;
    Observable<CounterModel> counterObservable_;

    // Services (static lifetime)
    TimerService timerService_;
    CounterService counterService_;
    TimeDisplayService timeDisplayService_;

    // Observer registrations (static lifetime)
    Observer<TimeModel> counterObserver_;
    Observer<TimeModel> displayObserver_;
    Observer<CounterModel> counterDisplayObserver_;

public:
    void init();
    void run();  // Starts FreeRTOS scheduler (never returns)
};

// main.c - Single static App instance
static App app;

int main(void) {
    HAL_Init();
    SystemClock_Config();
    app.init();
    app.run();  // Never returns
}
```

### Static Buffer Pattern

```cpp
// For string formatting without heap allocation
class TimeDisplayService {
private:
    // Static buffer for display formatting
    char displayBuffer_[32];  // Fixed-size, no heap

    void formatTime(const TimeModel& model) {
        // snprintf is safe - bounded by buffer size
        snprintf(displayBuffer_, sizeof(displayBuffer_),
                 "%02u:%02u:%02u.%03u",
                 model.hours, model.minutes,
                 model.seconds, model.milliseconds);
    }
};
```

### Static Container Pattern

```cpp
// Fixed-size array instead of std::vector
template <typename T, uint8_t MaxSize>
class StaticArray {
private:
    T items_[MaxSize];
    uint8_t count_ = 0;

public:
    bool add(const T& item) {
        if (count_ >= MaxSize) return false;
        items_[count_++] = item;
        return true;
    }

    bool remove(uint8_t index) {
        if (index >= count_) return false;
        for (uint8_t i = index; i < count_ - 1; i++) {
            items_[i] = items_[i + 1];
        }
        count_--;
        return true;
    }

    uint8_t size() const { return count_; }
    const T& operator[](uint8_t index) const { return items_[index]; }
    T& operator[](uint8_t index) { return items_[index]; }
};
```

---

## Zero-Copy Model Passing

### Model Definition Pattern

```cpp
// Core/Inc/Models.hpp
// All models are POD types - trivially copyable for queue transport

struct TimeModel {
    uint8_t hours;
    uint8_t minutes;
    uint8_t seconds;
    uint16_t milliseconds;
};
static_assert(sizeof(TimeModel) <= 8, "TimeModel exceeds queue item budget");
static_assert(std::is_trivially_copyable<TimeModel>::value,
              "TimeModel must be trivially copyable for queue transport");

struct CounterModel {
    uint32_t count;
    uint32_t overflowCount;
};
static_assert(sizeof(CounterModel) <= 8, "CounterModel exceeds queue item budget");
static_assert(std::is_trivially_copyable<CounterModel>::value,
              "CounterModel must be trivially copyable for queue transport");
```

### Zero-Copy Observer Callback

```cpp
// Observer receives const reference - no copy
using ObserverCallback = void (*)(const TimeModel& model, void* context);

// Callback implementation - model is accessed by reference from queue storage
void onTimeUpdate(const TimeModel& model, void* context) {
    auto* service = static_cast<CounterService*>(context);
    // model is valid only during this callback invocation
    // DO NOT store pointer/reference to model for later use
    service->processTime(model);
}
```

### Queue Transport (Single Copy)

```
Model lifecycle:
1. Publisher creates model on stack       [stack copy]
2. xQueueSend copies model into queue     [queue copy] -- ONLY COPY
3. Dispatcher reads from queue            [reference to queue storage]
4. Observer callback receives const ref   [zero copy - same memory]
5. After all observers notified, queue slot is freed

Total copies: 1 (publisher stack -> queue)
Observer access: 0 copies (const reference to queue storage)
```

---

## Performance Metrics

### Measured Performance (STM32F051C8 @ 48MHz)

| Metric | Value | Notes |
|--------|-------|-------|
| Event latency (publish to notify) | ~22us | Normal priority, single observer |
| High-priority event latency | ~12us | Pre-empts normal processing |
| Context switch time | ~10us | FreeRTOS task switch |
| publishFromISR time | ~2us | Queue enqueue only |
| CPU usage (idle) | < 1% | With 3 services running |
| Queue throughput | ~45K events/sec | Normal priority, sustained |
| Observer notify overhead | ~1us per observer | Callback dispatch |

### Performance Rules

```
RULE 1: Observer callbacks MUST complete in < 100us
RULE 2: ISR publish MUST complete in < 5us
RULE 3: Total ISR time MUST be < 10us
RULE 4: Dispatcher task should not block for > 1ms on any single event
RULE 5: If CPU usage > 10%, review observer callback complexity
```

---

## Code Review Checklist

### Required Items
- [ ] No heap allocation (`malloc`, `new`, `std::vector`, `std::string`)
- [ ] All objects statically allocated (global or static scope)
- [ ] Observer count <= MAX_OBSERVERS (4) per Observable
- [ ] ISR code uses only `*FromISR()` API variants
- [ ] `portYIELD_FROM_ISR()` called after every `*FromISR()` queue operation
- [ ] All models are POD types with `static_assert` for size
- [ ] Task stack sizes verified with `arm-none-eabi-size`
- [ ] RAM usage < 75% of 8KB (< 6,144 bytes)
- [ ] Flash usage < 90% of 64KB (< 58,982 bytes)
- [ ] Error callback registered for queue overflow handling
- [ ] `volatile` keyword on all ISR-shared variables
- [ ] Critical sections protect multi-task shared data

### Performance Checks
- [ ] Observer callbacks complete in < 100us
- [ ] ISR handlers complete in < 10us
- [ ] No floating-point in ISR (Cortex-M0 has no FPU)
- [ ] No blocking calls in high-priority task callbacks
- [ ] Queue sizes appropriate for event rate

### Safety Checks
- [ ] Stack overflow detection enabled (`configCHECK_FOR_STACK_OVERFLOW = 2`)
- [ ] Malloc failed hook enabled (`configUSE_MALLOC_FAILED_HOOK = 1`)
- [ ] Hard fault handler implemented with debug output
- [ ] Watchdog timer configured (IWDG)
- [ ] All function pointers validated before call

---

## Common Issues

### Hard Fault / Crash

| Cause | Solution |
|-------|----------|
| Stack overflow | Increase task stack size, reduce local variables |
| Null function pointer | Validate observer callback before calling |
| Unaligned access | Use `__attribute__((aligned(4)))` on structs |
| ISR calling non-ISR API | Switch to `*FromISR()` variants |
| Heap exhaustion | Eliminate dynamic allocation, use static buffers |

### Queue Issues

| Cause | Solution |
|-------|----------|
| Events dropped | Increase queue size or reduce publish rate |
| Observer not notified | Verify `subscribe()` succeeded (check return value) |
| Stale data in observer | Model valid only during callback - copy if needed |
| Priority inversion | Check dispatcher task priority is highest among app tasks |

### Build Issues

| Cause | Solution |
|-------|----------|
| Linker error: undefined reference | Check `.cpp` file added to build |
| C++ exception support bloat | Use `-fno-exceptions -fno-rtti` flags |
| Flash overflow | Enable `-Os`, remove unused HAL modules |
| RAM overflow | Reduce stack sizes, remove unused variables |

### FreeRTOS Issues

| Cause | Solution |
|-------|----------|
| Task not running | Check `xTaskCreate` return value, verify priority |
| Deadlock | Review mutex/semaphore acquisition order |
| Timer callback late | Increase timer task priority |
| Idle task starved | Reduce high-priority task CPU usage |

---

## Instructions

When handling STM32/FreeRTOS/C++14 embedded development tasks, follow these principles:

### Quick Verification Commands

Use these commands to quickly check for common issues:

```bash
# 1. Check for heap allocation (MUST be empty)
grep -rn "malloc\|calloc\|realloc\|free\b\|new \|delete " Core/Inc/ Core/Src/

# 2. Check for std library heap usage (MUST be empty)
grep -rn "std::vector\|std::string\|std::map\|std::list\|std::shared_ptr\|std::unique_ptr" Core/

# 3. Verify ISR safety - find publish calls and check for FromISR
grep -rn "\.publish(" Core/Src/ | grep -i "irq\|handler\|callback"

# 4. Check observer limits
grep -rn "subscribe(" Core/Src/*.cpp | wc -l

# 5. Verify static_assert on all model types
grep -rn "static_assert.*sizeof\|static_assert.*trivially" Core/Inc/Models.hpp

# 6. Check RAM/Flash usage
arm-none-eabi-size -A build/*.elf

# 7. Check for volatile on ISR-shared variables
grep -rn "volatile" Core/Inc/ Core/Src/

# 8. Verify FreeRTOS stack overflow detection is enabled
grep -rn "configCHECK_FOR_STACK_OVERFLOW" Core/Inc/FreeRTOSConfig.h

# 9. Check task stack sizes
grep -rn "StackType_t\|configMINIMAL_STACK_SIZE\|stack_size\|stackSize" Core/

# 10. Verify no floating point in ISR context
grep -rn "float\|double" Core/Src/*IRQ* Core/Src/*Handler*

# 11. Build the project
make -j$(nproc) 2>&1 | tail -20
```

CRITICAL: All heap allocation checks MUST return empty. Any use of `malloc`, `new`, `std::vector`, or `std::string` in application code is a critical defect.

If any of these return unexpected results, FIX THEM before completing the task.

---

## Project Setup - CRITICAL

IMPORTANT: This reference project has been validated with tested STM32CubeIDE settings and linker configuration. NEVER reconfigure the memory layout, linker script, or FreeRTOS heap scheme, or it will cause runtime crashes.

**Step 1**: Clone the reference project
```bash
git clone https://github.com/jrjohn/arcana-embedded-stm32.git [new-project-directory]
cd [new-project-directory]
```

**Step 2**: Reinitialize Git
```bash
rm -rf .git
git init
git add .
git commit -m "Initial commit from arcana-embedded-stm32 template"
```

**Step 3**: Open in STM32CubeIDE
- Import as existing STM32CubeIDE project
- Verify target: STM32F051C8Tx
- Verify toolchain: GNU ARM Embedded 10.3+

**Step 4**: Modify for your application
Only modify the following:
- Service classes in `Core/Src/` and `Core/Inc/`
- Model definitions in `Core/Inc/Models.hpp`
- Observer registrations in `Core/Src/App.cpp`
- Pin/peripheral configuration via STM32CubeMX (.ioc file)

**Core architecture files to KEEP** (do not delete):
- `Core/Inc/Observable.hpp` - Observable pattern core
- `Core/Src/Observable.cpp` - Observable implementation
- `Core/Inc/App.hpp` - Application interface
- `Core/Src/App.cpp` - Application setup
- `Core/Inc/FreeRTOSConfig.h` - RTOS configuration
- `STM32F051C8TX_FLASH.ld` - Linker script
- `Drivers/` - STM32 HAL drivers
- `Middlewares/` - FreeRTOS kernel

**Example files to REPLACE**:
- `Core/Inc/TimerService.hpp` - Replace with your publisher
- `Core/Inc/CounterService.hpp` - Replace with your observer
- `Core/Inc/TimeDisplayService.hpp` - Replace with your observer
- `Core/Inc/Models.hpp` - Replace with your model definitions
- `Core/Src/TimerService.cpp` - Replace publisher implementation
- `Core/Src/CounterService.cpp` - Replace observer implementation
- `Core/Src/TimeDisplayService.cpp` - Replace observer implementation

**Step 5**: Build and verify
```bash
make -j$(nproc)
arm-none-eabi-size build/*.elf
# Verify: RAM < 6,144 bytes, Flash < 58,982 bytes
```

### Prohibited Actions
- **DO NOT** use `malloc`, `new`, or any dynamic allocation in application code
- **DO NOT** modify the linker script memory regions
- **DO NOT** change FreeRTOS heap scheme from `heap_4`
- **DO NOT** add C++ exceptions (`-fno-exceptions` is required)
- **DO NOT** add RTTI (`-fno-rtti` is required)
- **DO NOT** use `std::string`, `std::vector`, or STL containers with heap allocation
- **DO NOT** exceed MAX_OBSERVERS (4) per Observable instance

### Allowed Modifications
- Add new Observer/Publisher service classes (following existing patterns)
- Add new Model types in `Models.hpp` (with `static_assert` for size)
- Modify peripheral configuration (GPIO, UART, TIM, SPI, I2C)
- Adjust task priorities and stack sizes (with verification)
- Add HAL peripheral initialization code

---

## Project Structure

```
arcana-embedded-stm32/
├── Core/
│   ├── Inc/
│   │   ├── Observable.hpp           # Observable pattern core template
│   │   ├── Models.hpp               # All model/event definitions
│   │   ├── TimerService.hpp         # Publisher: timer tick events
│   │   ├── CounterService.hpp       # Observer: counts events
│   │   ├── TimeDisplayService.hpp   # Observer: formats time display
│   │   ├── App.hpp                  # Application orchestrator
│   │   ├── FreeRTOSConfig.h         # FreeRTOS configuration
│   │   ├── main.h                   # HAL pin definitions
│   │   └── stm32f0xx_hal_conf.h     # HAL module selection
│   ├── Src/
│   │   ├── Observable.cpp           # Observable implementation
│   │   ├── TimerService.cpp         # Timer publisher implementation
│   │   ├── CounterService.cpp       # Counter observer implementation
│   │   ├── TimeDisplayService.cpp   # Display observer implementation
│   │   ├── App.cpp                  # App init + task creation
│   │   ├── main.c                   # HAL init + App entry
│   │   ├── stm32f0xx_it.c          # Interrupt handlers
│   │   └── system_stm32f0xx.c      # System clock config
│   └── Startup/
│       └── startup_stm32f051c8tx.s  # Vector table + reset handler
├── Drivers/
│   ├── CMSIS/                       # ARM CMSIS headers
│   └── STM32F0xx_HAL_Driver/        # ST HAL library
├── Middlewares/
│   └── Third_Party/
│       └── FreeRTOS/                # FreeRTOS kernel
│           ├── Source/
│           │   ├── tasks.c
│           │   ├── queue.c
│           │   ├── timers.c
│           │   └── portable/
│           │       ├── GCC/ARM_CM0/  # Cortex-M0 port
│           │       └── MemMang/
│           │           └── heap_4.c  # Memory scheme
│           └── Include/
├── STM32F051C8TX_FLASH.ld           # Linker script (8KB RAM, 64KB Flash)
├── Makefile                          # Build system
└── .cproject / .project              # STM32CubeIDE project files
```

---

## Observable API Summary

### Observable<T>

| Method | Context | Description |
|--------|---------|-------------|
| `subscribe(observer*)` | Task | Register observer (max 4) |
| `unsubscribe(observer*)` | Task | Remove observer |
| `publish(const T&)` | Task | Enqueue to normal queue |
| `publishHighPriority(const T&)` | Task | Enqueue to high queue |
| `publishFromISR(const T&, BaseType_t*)` | ISR | Enqueue from interrupt |
| `publishHighPriorityFromISR(const T&, BaseType_t*)` | ISR | High-priority from ISR |
| `notify(const T&)` | Dispatcher | Call all observer callbacks |

### ObservableDispatcher

| Method | Description |
|--------|-------------|
| `start(name, priority, stack, size, tcb)` | Start dispatcher task |
| `enqueue(QueueItem&)` | Add to normal queue |
| `enqueueHighPriority(QueueItem&)` | Add to high queue |
| `hasQueueSpace(priority)` | Check if queue has room |
| `getStats()` | Get queue statistics |
| `setErrorCallback(cb, ctx)` | Set error handler |

---

## Tech Stack Reference

| Technology | Version | Purpose |
|------------|---------|---------|
| STM32F051C8 | Rev Z | Target MCU (Cortex-M0, 48MHz) |
| FreeRTOS | 10.4.6+ | Real-time operating system |
| C++14 | GCC 10.3+ | Application language standard |
| STM32CubeIDE | 1.13+ | IDE and project management |
| STM32 HAL | 1.11.x | Hardware abstraction layer |
| ARM CMSIS | 5.x | Cortex Microcontroller Software Interface |
| GNU ARM Toolchain | 10.3+ | Cross-compiler (arm-none-eabi-gcc) |
| OpenOCD / ST-Link | Latest | Debug and flash programming |

### Compiler Flags

```
-mcpu=cortex-m0 -mthumb -mfloat-abi=soft
-std=c++14 -fno-exceptions -fno-rtti -fno-threadsafe-statics
-Os -ffunction-sections -fdata-sections
-Wall -Wextra -Werror
```

### Linker Flags

```
-Wl,--gc-sections -Wl,-Map=output.map
-T STM32F051C8TX_FLASH.ld
--specs=nosys.specs --specs=nano.specs
```

---

## Spec Gap Prediction System

When implementing new services from incomplete specifications, PROACTIVELY predict missing requirements:

### New Service Prediction Matrix

When a spec mentions a new "Sensor Service", predict ALL required components:

| Component | Predicted Items | Status |
|-----------|----------------|--------|
| Model | `SensorModel` struct in Models.hpp | Check |
| Service class | `SensorService.hpp` + `.cpp` | Check |
| Observer | Observer callback + registration | Check |
| Task | FreeRTOS task with static stack | Check |
| ISR (if hardware) | `*FromISR()` publish variant | Check |
| Error handling | Queue overflow handler | Check |
| Memory impact | RAM/Flash delta calculation | Check |

### Memory Impact Prediction

For every new component, predict RAM/Flash cost:

```
New Model Type:
  + sizeof(Model) * queue_sizes (high + normal) for queue storage
  + sizeof(QueueItem) if union grows
  + Model definition in Flash (~20 bytes .rodata)
  Predicted: +96 to +192 bytes RAM

New Observer:
  + 8 bytes (callback + context pointer)
  + Observer struct storage (~8 bytes)
  Predicted: +16 bytes RAM

New Task:
  + Stack size (128 words = 512 bytes typical)
  + TCB (88 bytes)
  + Task code in Flash (~200-500 bytes)
  Predicted: +600 bytes RAM, +400 bytes Flash

New Service Class:
  + Member variables (varies)
  + Code in Flash (~500-2000 bytes)
  Predicted: +20-100 bytes RAM, +1000 bytes Flash
```

### Ask Clarification Prompt

When specs are incomplete for embedded, ASK before implementing:

```
The specification mentions "Add temperature monitoring" but doesn't specify:
1. What I2C sensor? (SHT31, BME280, LM75, etc.)
2. Polling interval? (100ms vs 1s has major CPU impact)
3. Should readings publish via normal or high-priority queue?
4. Is ISR-based reading needed (DMA) or blocking I2C OK?
5. How many temperature thresholds/alarms?
6. What is the acceptable RAM budget for this feature?

Please clarify before I proceed with implementation.
```

---

## Peripheral Integration Patterns

### Adding a New Peripheral (Step by Step)

```
Step 1: Configure in STM32CubeMX (.ioc file)
  - Enable peripheral (UART, I2C, SPI, TIM, ADC)
  - Configure pins, clock, DMA if needed
  - Generate code (HAL init functions)

Step 2: Create Model
  - Add struct to Models.hpp
  - Add static_assert for size and trivially_copyable
  - Add to ModelType enum
  - Add to QueueItem union
  - Verify QueueItem size still fits

Step 3: Create Service
  - Header: callback, init, task entry (if needed)
  - Implementation: init, taskLoop, publish logic
  - Follow existing TimerService/CounterService pattern

Step 4: Register in App
  - Add Observable<NewModel> member
  - Add Service member
  - Add Observer member
  - Wire in App::init()
  - Create task in App::createTasks() if needed

Step 5: Verify Memory
  - Build and check arm-none-eabi-size
  - Verify RAM < 75%, Flash < 90%
  - Update memory budget table
```

### HAL Callback to Observable Bridge Pattern

```cpp
// Pattern for connecting any HAL interrupt callback to the Observable system

// 1. Forward-declare observable (defined in App.cpp)
extern Observable<SensorModel> sensorObservable;

// 2. HAL callback (ISR context)
void HAL_I2C_MasterRxCpltCallback(I2C_HandleTypeDef* hi2c) {
    if (hi2c->Instance == I2C1) {
        // 3. Create model from DMA buffer / received data
        SensorModel model;
        model.temperature = parseTemperature(rxBuffer);
        model.humidity = parseHumidity(rxBuffer);
        model.status = 0;

        // 4. Publish via ISR-safe API
        BaseType_t woken = pdFALSE;
        sensorObservable.publishFromISR(model, &woken);

        // 5. ALWAYS yield if higher-priority task was woken
        portYIELD_FROM_ISR(woken);
    }
}
```

---

## Debug and Troubleshooting

### Hard Fault Debugging

```cpp
// Core/Src/stm32f0xx_it.c
void HardFault_Handler(void) {
    // Read fault status registers
    volatile uint32_t* CFSR = (volatile uint32_t*)0xE000ED28;
    volatile uint32_t* HFSR = (volatile uint32_t*)0xE000ED2C;
    volatile uint32_t* MMFAR = (volatile uint32_t*)0xE000ED34;
    volatile uint32_t* BFAR = (volatile uint32_t*)0xE000ED38;

    // Store for debugger inspection
    volatile uint32_t cfsr = *CFSR;
    volatile uint32_t hfsr = *HFSR;
    volatile uint32_t mmfar = *MMFAR;
    volatile uint32_t bfar = *BFAR;

    // Prevent optimization
    (void)cfsr; (void)hfsr; (void)mmfar; (void)bfar;

    // Breakpoint for debugger
    __BKPT(0);

    while (1) {}
}
```

### Stack Overflow Debug Pattern

```cpp
// FreeRTOS stack painting check
// configCHECK_FOR_STACK_OVERFLOW = 2 fills stack with 0xA5
// and checks if watermark is corrupted

extern "C" void vApplicationStackOverflowHook(
    TaskHandle_t xTask, char* pcTaskName
) {
    // pcTaskName tells you which task overflowed
    // Increase that task's stack size

    // For debug: output task name via SWO/ITM/UART
    volatile char* taskName = pcTaskName;
    (void)taskName;  // Inspect in debugger

    __BKPT(0);
    while (1) {}
}
```

### Runtime Statistics (Debug Build Only)

```cpp
#ifdef DEBUG
// Track dispatcher performance
struct RuntimeStats {
    volatile uint32_t maxDispatchTimeUs;
    volatile uint32_t avgDispatchTimeUs;
    volatile uint32_t totalEvents;
    volatile uint32_t maxQueueDepth;
};

static RuntimeStats stats = {};

// In dispatcher loop:
uint32_t start = DWT->CYCCNT;  // Cycle counter (if available on M0+)
dispatch(item);
uint32_t elapsed = DWT->CYCCNT - start;
uint32_t elapsedUs = elapsed / (SystemCoreClock / 1000000);

if (elapsedUs > stats.maxDispatchTimeUs) {
    stats.maxDispatchTimeUs = elapsedUs;
}
stats.totalEvents++;
#endif
```

---

## Architecture Rating: 9.1/10

### Strengths
- Zero-copy model passing minimizes RAM usage
- Dual-priority queuing enables real-time responsiveness
- Static allocation eliminates heap fragmentation
- ISR-safe API prevents hard faults
- Type-safe C++14 templates catch errors at compile time
- 53.2% RAM usage leaves healthy headroom

### Known Limitations
- Fixed 4-observer maximum per Observable
- Single dispatcher task (shared across all Observables)
- No per-observer filtering (all observers get all events)
- Lost events on queue overflow (no retry/backpressure)
- Fixed queue sizes (cannot resize at runtime)
- C++ only (no pure C API)
