# STM32 Developer Skill - API Reference

## Table of Contents
1. [Observable API](#observable-api)
2. [ObservableDispatcher API](#observabledispatcher-api)
3. [Observer Struct](#observer-struct)
4. [QueueItem Struct](#queueitem-struct)
5. [Error Types](#error-types)
6. [Memory Map](#memory-map)
7. [FreeRTOS Configuration Reference](#freertos-configuration-reference)
8. [STM32F051C8 Peripheral Map](#stm32f051c8-peripheral-map)
9. [Compiler and Linker Reference](#compiler-and-linker-reference)
10. [HAL Driver Quick Reference](#hal-driver-quick-reference)

---

## Observable API

### `Observable<T>` Template Class

```cpp
template <typename T>
class Observable {
public:
    void init(ObservableDispatcher* dispatcher);
    bool subscribe(Observer<T>* observer);
    bool unsubscribe(Observer<T>* observer);
    void publish(const T& model);
    void publishHighPriority(const T& model);
    void publishFromISR(const T& model, BaseType_t* pxHigherPriorityTaskWoken);
    void publishHighPriorityFromISR(const T& model, BaseType_t* pxHigherPriorityTaskWoken);
    void notify(const T& model);
    uint8_t getObserverCount() const;
};
```

| Method | Context | Returns | Description |
|--------|---------|---------|-------------|
| `init(dispatcher*)` | Setup | void | Link to dispatcher. Call before subscribe/publish. |
| `subscribe(observer*)` | Task | bool | Register observer. Returns false if MAX_OBSERVERS reached. |
| `unsubscribe(observer*)` | Task | bool | Remove observer. Returns false if not found. |
| `publish(model)` | Task | void | Enqueue model to normal-priority queue. |
| `publishHighPriority(model)` | Task | void | Enqueue model to high-priority queue. |
| `publishFromISR(model, woken*)` | ISR | void | ISR-safe enqueue to normal queue. |
| `publishHighPriorityFromISR(model, woken*)` | ISR | void | ISR-safe enqueue to high queue. |
| `notify(model)` | Dispatcher | void | Call all observer callbacks. Internal use. |
| `getObserverCount()` | Any | uint8_t | Current number of subscribed observers. |

### Template Constraints

```
T must satisfy:
  - std::is_trivially_copyable<T>::value == true
  - sizeof(T) <= sizeof(QueueItem::data)  (typically 12 bytes)
  - No pointers to heap memory
  - No virtual functions
  - POD type (Plain Old Data)
```

---

## ObservableDispatcher API

### `ObservableDispatcher` Class

```cpp
class ObservableDispatcher {
public:
    void init();
    void start(const char* name, osPriority_t priority,
               StackType_t* stack, uint32_t stackSize,
               StaticTask_t* tcb);
    bool enqueue(const QueueItem& item);
    bool enqueueHighPriority(const QueueItem& item);
    bool enqueueFromISR(const QueueItem& item, BaseType_t* woken);
    bool enqueueHighPriorityFromISR(const QueueItem& item, BaseType_t* woken);
    bool hasQueueSpace(bool highPriority) const;
    DispatcherStats getStats() const;
    void setErrorCallback(ErrorCallback cb, void* context);
};
```

| Method | Context | Returns | Description |
|--------|---------|---------|-------------|
| `init()` | Setup | void | Create static queues. Call once before start. |
| `start(...)` | Setup | void | Create and start dispatcher FreeRTOS task. |
| `enqueue(item)` | Task | bool | Add item to normal queue. False if full. |
| `enqueueHighPriority(item)` | Task | bool | Add item to high queue. False if full. |
| `enqueueFromISR(item, woken*)` | ISR | bool | ISR-safe enqueue to normal queue. |
| `enqueueHighPriorityFromISR(item, woken*)` | ISR | bool | ISR-safe enqueue to high queue. |
| `hasQueueSpace(highPriority)` | Task | bool | Check if queue has room for one more item. |
| `getStats()` | Any | DispatcherStats | Get queue usage statistics. |
| `setErrorCallback(cb, ctx)` | Setup | void | Set error handler callback. |

### DispatcherStats Struct

```cpp
struct DispatcherStats {
    uint32_t highPriorityEnqueued;      // Total items enqueued to high queue
    uint32_t normalPriorityEnqueued;    // Total items enqueued to normal queue
    uint32_t highPriorityDropped;       // Items dropped (high queue full)
    uint32_t normalPriorityDropped;     // Items dropped (normal queue full)
    uint32_t totalDispatched;           // Total items dispatched to observers
    uint8_t highQueueCurrentSize;       // Current items in high queue
    uint8_t normalQueueCurrentSize;     // Current items in normal queue
};
```

---

## Observer Struct

```cpp
template <typename T>
struct Observer {
    void (*callback)(const T& model, void* context) = nullptr;
    void* context = nullptr;
};
```

| Field | Type | Size | Description |
|-------|------|------|-------------|
| `callback` | Function pointer | 4 bytes | Called when event is dispatched. Must be static method. |
| `context` | `void*` | 4 bytes | Passed to callback. Typically `this` pointer of observer object. |

**Total size per observer: 8 bytes**

### Callback Signature

```cpp
// Callback function signature
void (*callback)(const T& model, void* context);

// model: const reference to event data (valid only during callback)
// context: user-supplied pointer (typically 'this' of the observer class)
```

---

## QueueItem Struct

```cpp
struct QueueItem {
    ModelType type;         // 1 byte: model discriminator
    uint8_t reserved[3];   // 3 bytes: alignment padding
    union {                 // Variable: largest model determines size
        TimeModel time;
        CounterModel counter;
        ButtonModel button;
        SensorModel sensor;
        AdcModel adc;
    } data;
};
```

| Field | Offset | Size | Description |
|-------|--------|------|-------------|
| `type` | 0 | 1 | `ModelType` enum value identifying the model |
| `reserved` | 1 | 3 | Padding for 4-byte alignment |
| `data` | 4 | 8-12 | Union of all model types |
| **Total** | - | **12-16** | Depends on largest model |

### ModelType Enum

```cpp
enum class ModelType : uint8_t {
    Time = 0,       // TimeModel
    Counter = 1,    // CounterModel
    Button = 2,     // ButtonModel
    Sensor = 3,     // SensorModel
    Adc = 4,        // AdcModel
    COUNT           // Must be last (used for validation)
};
```

---

## Error Types

### ObservableError Enum

```cpp
enum class ObservableError : uint8_t {
    QueueFull,       // Queue is full, event was dropped
    QueueNotReady,   // Dispatcher not initialized/started
    InvalidModel,    // Model type validation failed
    NoObservers      // No observers registered (non-fatal)
};
```

| Error | Severity | Recovery | Action |
|-------|----------|----------|--------|
| `QueueFull` | Warning | Automatic | Event lost. Increase queue size or reduce rate. |
| `QueueNotReady` | Critical | Manual | Start dispatcher before publishing. |
| `InvalidModel` | Critical | Manual | Fix model type registration. |
| `NoObservers` | Info | None | Event published but nobody subscribed. |

### ErrorCallback Type

```cpp
using ErrorCallback = void (*)(ObservableError error, void* context);
```

---

## Memory Map

### STM32F051C8 Memory Layout

```
Address Range          Size      Region
================================================================
0x0800_0000-0x0800_FFFF  64 KB    Flash (program memory)
0x2000_0000-0x2000_1FFF   8 KB    SRAM (data memory)
0x4000_0000-0x4002_FFFF  ---      Peripheral registers
0xE000_0000-0xE00F_FFFF  ---      Cortex-M0 private peripherals
```

### Flash Layout

```
0x0800_0000  ┌──────────────────────────┐
             │  Vector Table (0xC0)      │  192 bytes
0x0800_00C0  ├──────────────────────────┤
             │  .text (code)             │  ~14 KB
             │  - HAL drivers            │
             │  - FreeRTOS               │
             │  - Observable framework   │
             │  - Application logic      │
~0x0800_3800 ├──────────────────────────┤
             │  .rodata (constants)      │  ~2 KB
             │  - String literals        │
             │  - Const tables           │
~0x0800_4000 ├──────────────────────────┤
             │  .init_array              │  ~128 bytes
             │  - C++ static init        │
~0x0800_4248 ├──────────────────────────┤
             │  FREE FLASH              │  ~48 KB
0x0800_FFFF  └──────────────────────────┘
```

### SRAM Layout

```
0x2000_0000  ┌──────────────────────────┐
             │  .data (initialized)      │  ~256 bytes
             │  - Global variables       │
             │  - Static objects         │
~0x2000_0100 ├──────────────────────────┤
             │  .bss (zero-initialized)  │  ~512 bytes
             │  - Zero-init globals      │
             │  - Static arrays          │
~0x2000_0300 ├──────────────────────────┤
             │  FreeRTOS Heap (heap_4)   │  4096 bytes
             │  - Task TCBs             │
             │  - Queue storage          │
             │  - Semaphore storage      │
~0x2000_1300 ├──────────────────────────┤
             │  Task Stacks              │  ~1536 bytes
             │  - Dispatcher (512B)      │
             │  - Timer (512B)           │
             │  - Counter (512B)         │
~0x2000_1900 ├──────────────────────────┤
             │  MSP Stack (main)         │  ~256 bytes
             │  (used before scheduler)  │
0x2000_1FFF  └──────────────────────────┘  ← Initial SP
```

### Linker Script Key Sections

```ld
/* STM32F051C8TX_FLASH.ld */
MEMORY {
    RAM    (xrw) : ORIGIN = 0x20000000, LENGTH = 8K
    FLASH  (rx)  : ORIGIN = 0x08000000, LENGTH = 64K
}

/* Key symbols */
_estack = ORIGIN(RAM) + LENGTH(RAM);  /* 0x20002000 - top of RAM */
_Min_Heap_Size  = 0x200;              /* 512 bytes minimum heap */
_Min_Stack_Size = 0x400;              /* 1024 bytes minimum MSP stack */
```

---

## FreeRTOS Configuration Reference

### FreeRTOSConfig.h Key Settings

| Define | Value | Description |
|--------|-------|-------------|
| `configUSE_PREEMPTION` | 1 | Preemptive scheduling enabled |
| `configCPU_CLOCK_HZ` | 48000000 | 48 MHz system clock |
| `configTICK_RATE_HZ` | 1000 | 1 ms tick period |
| `configMAX_PRIORITIES` | 7 | Priority levels 0-6 |
| `configMINIMAL_STACK_SIZE` | 64 | 256 bytes minimum stack |
| `configTOTAL_HEAP_SIZE` | 4096 | 4 KB for heap_4 |
| `configMAX_TASK_NAME_LEN` | 8 | Short names to save RAM |
| `configUSE_MUTEXES` | 1 | Mutex support enabled |
| `configUSE_COUNTING_SEMAPHORES` | 1 | Counting semaphores enabled |
| `configUSE_TIMERS` | 1 | Software timer support |
| `configTIMER_TASK_STACK_DEPTH` | 64 | 256 bytes timer task stack |
| `configUSE_QUEUE_SETS` | 0 | Disabled to save Flash |
| `configSUPPORT_STATIC_ALLOCATION` | 1 | Static allocation enabled |
| `configSUPPORT_DYNAMIC_ALLOCATION` | 1 | Dynamic for FreeRTOS internals |
| `configUSE_MALLOC_FAILED_HOOK` | 1 | Hook on malloc failure |
| `configCHECK_FOR_STACK_OVERFLOW` | 2 | Stack painting + checking |
| `configUSE_IDLE_HOOK` | 1 | Idle hook for `__WFI()` |

### FreeRTOS API Quick Reference (Most Used)

| API | Context | Description |
|-----|---------|-------------|
| `xTaskCreateStatic()` | Setup | Create task with static memory |
| `vTaskDelay(ticks)` | Task | Delay for N ticks |
| `vTaskDelayUntil(&last, period)` | Task | Precise periodic delay |
| `xTaskGetTickCount()` | Task/ISR | Current tick count |
| `taskENTER_CRITICAL()` | Task | Disable interrupts (nesting) |
| `taskEXIT_CRITICAL()` | Task | Re-enable interrupts |
| `xQueueCreateStatic()` | Setup | Create queue with static memory |
| `xQueueSend(q, item, timeout)` | Task | Send to queue |
| `xQueueReceive(q, item, timeout)` | Task | Receive from queue |
| `xQueueSendFromISR(q, item, woken)` | ISR | ISR-safe queue send |
| `xSemaphoreCreateMutexStatic()` | Setup | Create mutex |
| `xSemaphoreTake(sem, timeout)` | Task | Acquire semaphore |
| `xSemaphoreGive(sem)` | Task | Release semaphore |
| `xSemaphoreGiveFromISR(sem, woken)` | ISR | ISR-safe release |
| `portYIELD_FROM_ISR(woken)` | ISR | Context switch from ISR |
| `vTaskStartScheduler()` | Main | Start RTOS (never returns) |

---

## STM32F051C8 Peripheral Map

### Commonly Used Peripherals

| Peripheral | Base Address | IRQ | Description |
|-----------|-------------|-----|-------------|
| GPIO A | 0x48000000 | EXTI0_1, EXTI2_3, EXTI4_15 | Port A pins |
| GPIO B | 0x48000400 | Same as above | Port B pins |
| GPIO C | 0x48000800 | Same as above | Port C pins |
| USART1 | 0x40013800 | USART1_IRQn (27) | Debug UART |
| USART2 | 0x40004400 | USART2_IRQn (28) | Secondary UART |
| I2C1 | 0x40005400 | I2C1_IRQn (23) | Sensor bus |
| SPI1 | 0x40013000 | SPI1_IRQn (25) | SPI master |
| TIM2 | 0x40000000 | TIM2_IRQn (15) | General purpose timer (32-bit) |
| TIM3 | 0x40000400 | TIM3_IRQn (16) | General purpose timer (16-bit) |
| ADC1 | 0x40012400 | ADC1_IRQn (12) | 12-bit ADC |
| DMA1 | 0x40020000 | DMA1_Ch1_IRQn (9) | DMA controller |
| IWDG | 0x40003000 | - | Independent watchdog |
| RTC | 0x40002800 | RTC_IRQn (2) | Real-time clock |

### Clock Configuration

```
HSI (Internal) = 8 MHz
PLL multiplier = 6x
SYSCLK = 48 MHz
AHB = 48 MHz (HCLK)
APB = 48 MHz (PCLK)
SysTick = 48 MHz / 1000 = 1 ms tick
```

---

## Compiler and Linker Reference

### GCC Compiler Flags

```
Target Architecture:
  -mcpu=cortex-m0          Cortex-M0 instruction set
  -mthumb                  Thumb instruction set (required for M0)
  -mfloat-abi=soft         Software floating point (no FPU on M0)

Language:
  -std=c++14               C++14 standard
  -fno-exceptions          Disable C++ exceptions (saves ~10KB Flash)
  -fno-rtti                Disable RTTI (saves ~2KB Flash)
  -fno-threadsafe-statics  Disable thread-safe static init (FreeRTOS handles this)

Optimization:
  -Os                      Optimize for size (best for Flash-constrained targets)
  -ffunction-sections      Place each function in its own section
  -fdata-sections          Place each data item in its own section

Warnings:
  -Wall -Wextra -Werror    All warnings as errors
  -Wno-unused-parameter    Allow unused params (common in HAL callbacks)
```

### Linker Flags

```
  -Wl,--gc-sections        Remove unused sections (works with -ffunction-sections)
  -Wl,-Map=output.map      Generate memory map file
  -T STM32F051C8TX_FLASH.ld  Linker script
  --specs=nosys.specs       No system calls (bare metal)
  --specs=nano.specs        Newlib-nano (smaller printf/scanf)
  -lnosys                   No OS stubs
```

### Size Analysis Commands

```bash
# Overall size summary (text=Flash, data+bss=RAM)
arm-none-eabi-size build/*.elf

# Detailed section sizes
arm-none-eabi-size -A build/*.elf

# Symbol sizes sorted by size (find largest consumers)
arm-none-eabi-nm --size-sort --print-size build/*.elf | tail -20

# Show only C++ symbols (demangled)
arm-none-eabi-nm --size-sort --print-size -C build/*.elf | tail -20

# Flash usage by object file
arm-none-eabi-size build/Core/Src/*.o | sort -k1 -n -r

# Map file analysis (sections, symbols, memory regions)
# Look for: .text size, .bss size, .data size, stack usage
less build/output.map
```

---

## HAL Driver Quick Reference

### GPIO

```cpp
// Write pin
HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_SET);
HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_RESET);

// Toggle pin
HAL_GPIO_TogglePin(LED_GPIO_Port, LED_Pin);

// Read pin
GPIO_PinState state = HAL_GPIO_ReadPin(BTN_GPIO_Port, BTN_Pin);

// EXTI callback (override weak function)
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin) { /* ISR context */ }
```

### UART

```cpp
// Blocking transmit
HAL_UART_Transmit(&huart1, data, len, timeout_ms);

// Blocking receive
HAL_UART_Receive(&huart1, data, len, timeout_ms);

// Interrupt-driven receive (1 byte at a time)
HAL_UART_Receive_IT(&huart1, &rxByte, 1);
void HAL_UART_RxCpltCallback(UART_HandleTypeDef* huart) { /* ISR */ }

// DMA transmit
HAL_UART_Transmit_DMA(&huart1, data, len);
void HAL_UART_TxCpltCallback(UART_HandleTypeDef* huart) { /* ISR */ }
```

### I2C

```cpp
// Master transmit
HAL_I2C_Master_Transmit(&hi2c1, addr << 1, data, len, timeout);

// Master receive
HAL_I2C_Master_Receive(&hi2c1, addr << 1, data, len, timeout);

// Memory read (register access)
HAL_I2C_Mem_Read(&hi2c1, addr << 1, reg, I2C_MEMADD_SIZE_8BIT,
                  data, len, timeout);

// Memory write (register access)
HAL_I2C_Mem_Write(&hi2c1, addr << 1, reg, I2C_MEMADD_SIZE_8BIT,
                   data, len, timeout);
```

### Timer

```cpp
// Start timer
HAL_TIM_Base_Start(&htim2);

// Start with interrupt
HAL_TIM_Base_Start_IT(&htim2);
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef* htim) { /* ISR */ }

// PWM output
HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1);

// Set PWM duty cycle
__HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, dutyCycle);
```

### ADC

```cpp
// Single conversion (blocking)
HAL_ADC_Start(&hadc1);
HAL_ADC_PollForConversion(&hadc1, timeout);
uint32_t value = HAL_ADC_GetValue(&hadc1);
HAL_ADC_Stop(&hadc1);

// DMA continuous conversion
HAL_ADC_Start_DMA(&hadc1, (uint32_t*)adcBuffer, numChannels);
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc) { /* ISR */ }
```

### SysTick / Delay

```cpp
// Millisecond delay (blocking - uses SysTick)
HAL_Delay(100);  // WARNING: Do NOT use in FreeRTOS tasks - use vTaskDelay

// Get current tick (1ms resolution)
uint32_t tick = HAL_GetTick();  // Safe in both task and ISR context
```
