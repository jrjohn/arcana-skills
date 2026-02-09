# Production Readiness Checklist

## Pre-Release Checklist

### CRITICAL (Must Pass)
- [ ] **No heap allocation** - `grep -rn "malloc\|new \|std::vector\|std::string" Core/`
- [ ] **Build clean** - `make -j$(nproc)` with zero warnings (`-Werror`)
- [ ] **RAM < 75%** - `arm-none-eabi-size build/*.elf` (< 6,144 bytes)
- [ ] **Flash < 90%** - `arm-none-eabi-size build/*.elf` (< 58,982 bytes)
- [ ] **Stack overflow detection** - `configCHECK_FOR_STACK_OVERFLOW = 2`
- [ ] **ISR uses FromISR APIs** - No `publish()` in interrupt context
- [ ] **Observer count <= 4** - Per Observable instance
- [ ] **All models POD** - `static_assert(is_trivially_copyable<T>)` on every model
- [ ] **Error callback set** - `dispatcher.setErrorCallback()` called before scheduler start
- [ ] **portYIELD_FROM_ISR** - Called after every `*FromISR()` queue operation

### IMPORTANT (Should Pass)
- [ ] **Volatile on ISR-shared vars** - All variables shared with ISR marked `volatile`
- [ ] **Critical sections** - Multi-task shared data protected
- [ ] **Task stack verified** - Each task stack sized for worst-case call depth
- [ ] **No floating point in ISR** - Cortex-M0 has no FPU
- [ ] **Observer callbacks < 100us** - No blocking in callbacks
- [ ] **Watchdog configured** - IWDG with appropriate timeout
- [ ] **Hard fault handler** - Debug output on fault

### RECOMMENDED (Nice to Have)
- [ ] **Power management** - `__WFI()` in idle task
- [ ] **Debug UART** - Printf retargeting functional
- [ ] **Performance metrics** - Event latency measured
- [ ] **Error statistics** - Dropped event counters active

---

## Memory Budget Verification

| Resource | Budget | Actual | Status |
|----------|--------|--------|--------|
| RAM | < 6,144 B (75%) | ___ B | [ ] |
| Flash | < 58,982 B (90%) | ___ B | [ ] |
| Task stacks (total) | < 2,048 B | ___ B | [ ] |
| Queue storage | < 512 B | ___ B | [ ] |

---

## Stack Analysis

```bash
# Measure actual stack usage
arm-none-eabi-size -A build/*.elf | grep -E "stack|\.bss|\.data"

# Check each task stack (from map file)
grep -A2 "taskStack" build/output.map
```

| Task | Allocated | Worst Case | Margin | Status |
|------|-----------|------------|--------|--------|
| Dispatcher | 512 B | ___ B | ___ B | [ ] |
| Timer | 512 B | ___ B | ___ B | [ ] |
| Counter | 512 B | ___ B | ___ B | [ ] |
| Idle | 256 B | ___ B | ___ B | [ ] |

---

## ISR Safety Verification

```bash
# All ISR publish calls must use FromISR variant
grep -rn "\.publish(" Core/Src/ | grep -vi "FromISR"
# Above must NOT match any lines inside IRQHandler or Callback functions

# Verify portYIELD_FROM_ISR present after all FromISR calls
grep -B2 -A2 "FromISR" Core/Src/*.c Core/Src/*.cpp
```

---

## Build Verification

```bash
# Clean build
make clean && make -j$(nproc) 2>&1

# Size check
arm-none-eabi-size build/*.elf

# Symbol analysis (find largest functions)
arm-none-eabi-nm --size-sort --print-size -C build/*.elf | tail -10
```

---

## Flash and Test

```bash
# Flash via ST-Link
st-flash write build/*.bin 0x08000000

# Or via OpenOCD
openocd -f interface/stlink.cfg -f target/stm32f0x.cfg \
  -c "program build/*.elf verify reset exit"

# Monitor debug UART output
screen /dev/ttyUSB0 115200
```
