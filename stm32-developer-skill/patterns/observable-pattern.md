# Observable Pattern for STM32

Deep dive into the Observable/Observer pattern implementation for resource-constrained STM32 microcontrollers.

---

## Core Concept

The Observable pattern decouples event producers (publishers) from event consumers (observers) through an intermediate dispatcher. On STM32, this is implemented with:

- **FreeRTOS queues** for thread-safe event transport
- **Function pointers** instead of `std::function` (zero heap overhead)
- **Static arrays** instead of `std::vector` for observer storage
- **Dual-priority queues** for real-time responsiveness

---

## Architecture Diagram

```
    Publisher (Task/ISR)
         │
         │  publish(model) / publishFromISR(model)
         ▼
    ┌──────────────────────────────────────┐
    │         Observable<T>                │
    │  ┌──────────────────────────┐       │
    │  │ Observers[0..3]          │       │
    │  │  [callback+ctx]          │       │
    │  │  [callback+ctx]          │       │
    │  │  [callback+ctx]          │       │
    │  │  [callback+ctx]          │       │
    │  └──────────────────────────┘       │
    │                                      │
    │  Creates QueueItem, sends to         │
    │  dispatcher queue                    │
    └────────────────┬─────────────────────┘
                     │
                     ▼
    ┌──────────────────────────────────────┐
    │       ObservableDispatcher           │
    │                                      │
    │  High Queue: [H][H][H][H]           │
    │  Normal Queue: [N][N][N][N][N]...    │
    │                                      │
    │  Task loop:                          │
    │    1. Drain all high-priority items  │
    │    2. Process one normal item        │
    │    3. Block on queues if empty       │
    └────────────────┬─────────────────────┘
                     │
                     │  observable.notify(model)
                     ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │Observer 0│  │Observer 1│  │Observer 2│
    │ Service A│  │ Service B│  │ Service C│
    └──────────┘  └──────────┘  └──────────┘
```

---

## Why Not std::function / Virtual Dispatch

| Approach | Size per Observer | Heap | ISR-Safe | Flash Cost |
|----------|------------------|------|----------|------------|
| Function pointer + void* | 8 bytes | No | Yes | ~0 |
| std::function | 32+ bytes | Yes | No | ~2-4 KB |
| Virtual method | 12+ bytes | No* | Yes | ~1-2 KB |
| Signal/Slot (Qt-style) | 40+ bytes | Yes | No | ~5+ KB |

On STM32F051C8 with 8KB RAM and 64KB Flash, the function pointer approach is the only viable option that is both ISR-safe and heap-free.

---

## Observer Lifecycle

```
1. CREATION (static, before scheduler)
   Observer<TimeModel> observer;
   observer.callback = &MyService::onTimeUpdate;
   observer.context = this;

2. REGISTRATION (before scheduler or in task)
   bool ok = timeObservable.subscribe(&observer);
   // ok == false if MAX_OBSERVERS (4) already reached

3. EVENT RECEPTION (in dispatcher task context)
   // callback invoked: observer.callback(model, observer.context)
   // model is const reference - valid only during callback

4. UNREGISTRATION (optional, in task context)
   timeObservable.unsubscribe(&observer);

5. DESTRUCTION (static lifetime - destroyed at program end)
   // On embedded: program never ends, so no cleanup needed
```

---

## Publish Flow (Detailed)

```cpp
// Step 1: Publisher creates model on stack
TimeModel model;
model.hours = 12;
model.minutes = 30;
model.seconds = 45;
model.milliseconds = 0;

// Step 2: Observable wraps in QueueItem
// (inside publish() implementation)
QueueItem item;
item.type = ModelType::Time;
memcpy(&item.data.time, &model, sizeof(TimeModel));  // ONLY copy

// Step 3: QueueItem sent to FreeRTOS queue
// (inside dispatcher->enqueue())
xQueueSend(normalQueue_, &item, 0);  // Zero timeout, non-blocking

// Step 4: Dispatcher task receives from queue
// (inside dispatchTask())
QueueItem received;
xQueueReceive(normalQueue_, &received, portMAX_DELAY);

// Step 5: Dispatcher calls notify() on the correct Observable
// (routes by ModelType)
timeObservable_.notify(received.data.time);

// Step 6: notify() iterates observers
for (uint8_t i = 0; i < observerCount_; i++) {
    observers_[i]->callback(model, observers_[i]->context);
    // ^^^ const reference to queue storage - ZERO copy to observer
}
```

---

## Memory Cost Breakdown

| Component | Per Instance | Count | Total |
|-----------|-------------|-------|-------|
| Observable<T> | ~20 bytes | 2-3 | ~60 B |
| Observer<T> | 8 bytes | 4-8 | ~64 B |
| ObservableDispatcher | ~80 bytes | 1 | ~80 B |
| High Queue Storage | 4 * sizeof(QueueItem) | 1 | ~64 B |
| Normal Queue Storage | 8 * sizeof(QueueItem) | 1 | ~128 B |
| Queue Control Blocks | ~80 bytes each | 2 | ~160 B |
| Dispatcher Task Stack | 512 bytes | 1 | 512 B |
| Dispatcher Task TCB | 88 bytes | 1 | 88 B |
| **Total Observable Framework** | | | **~1,156 B** |

This is 14.1% of 8KB RAM -- an efficient foundation for event-driven architecture.

---

## Scaling Guidelines

| Scenario | MAX_OBSERVERS | Queue Sizes | Additional RAM |
|----------|--------------|-------------|----------------|
| Simple (2-3 services) | 4 | H:4, N:8 | Baseline |
| Medium (4-6 services) | 4 | H:4, N:16 | +128 B |
| Complex (6-8 services) | 8 | H:8, N:16 | +384 B |

**Warning**: Increasing MAX_OBSERVERS to 8 adds 8 bytes per observer slot per Observable instance. With 3 Observables, that is +48 bytes of RAM.

---

## Common Mistakes

### Mistake 1: Storing reference to model data
```cpp
// WRONG: model reference is invalid after callback returns
const TimeModel* savedModel;
void onTime(const TimeModel& model, void* ctx) {
    savedModel = &model;  // DANGLING after callback
}
```

### Mistake 2: Publishing from ISR without FromISR
```cpp
// WRONG: Will cause hard fault
void TIM2_IRQHandler(void) {
    observable.publish(model);  // CRASH: calls non-ISR-safe API
}
```

### Mistake 3: Blocking in observer callback
```cpp
// WRONG: Blocks the dispatcher, delays ALL observers
void onSensor(const SensorModel& model, void* ctx) {
    HAL_Delay(100);  // BLOCKS for 100ms
    HAL_UART_Transmit(&huart1, data, len, 1000);  // BLOCKS for up to 1s
}
```

### Mistake 4: Exceeding observer limit silently
```cpp
// WRONG: Not checking subscribe return value
timeObservable.subscribe(&obs1);
timeObservable.subscribe(&obs2);
timeObservable.subscribe(&obs3);
timeObservable.subscribe(&obs4);
timeObservable.subscribe(&obs5);  // Returns false - obs5 not subscribed!
```

### Correct Pattern
```cpp
bool ok = timeObservable.subscribe(&observer);
if (!ok) {
    // Handle: increase MAX_OBSERVERS or reduce observer count
    Error_Handler();
}
```
