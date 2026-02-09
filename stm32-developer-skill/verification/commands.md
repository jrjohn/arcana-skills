# Verification Commands

Quick reference for diagnosing common issues in Arcana Embedded STM32 projects.

---

## Quick Diagnosis Table

| Symptom | Command | Expected |
|---------|---------|----------|
| Hard fault | `arm-none-eabi-size -A build/*.elf` | Stack/RAM within budget |
| Events dropped | Check `getStats().dropped` | Zero in normal operation |
| ISR crash | `grep -rn "\.publish(" Core/Src/` in ISR | Only `FromISR` variants |
| Flash overflow | `arm-none-eabi-size build/*.elf` | text < 58,982 |
| RAM overflow | `arm-none-eabi-size build/*.elf` | data+bss < 6,144 |
| Observer not called | Check `subscribe()` return value | true |
| Build error | `make -j$(nproc) 2>&1` | Zero errors/warnings |

---

## 1. Memory Analysis

### Overall memory usage
```bash
arm-none-eabi-size build/*.elf
# text = Flash, data + bss = RAM (approximate)
```

### Detailed section sizes
```bash
arm-none-eabi-size -A build/*.elf
```

### Largest symbols (find memory hogs)
```bash
arm-none-eabi-nm --size-sort --print-size -C build/*.elf | tail -20
```

### Per-object file sizes
```bash
arm-none-eabi-size build/Core/Src/*.o | sort -k1 -n -r
```

---

## 2. Heap Allocation Check (MUST be empty)

### Application code heap usage
```bash
grep -rn "malloc\|calloc\|realloc\|free\b" Core/Inc/ Core/Src/
```

### C++ heap usage
```bash
grep -rn "new \|delete \|std::vector\|std::string\|std::map\|std::list" Core/
```

### Smart pointer usage
```bash
grep -rn "shared_ptr\|unique_ptr\|make_shared\|make_unique" Core/
```

---

## 3. ISR Safety Check

### Find non-ISR publish in interrupt context
```bash
# Look for publish() calls that should be publishFromISR()
grep -rn "\.publish(" Core/Src/ | grep -i "irq\|handler\|callback"
```

### Verify portYIELD_FROM_ISR after FromISR calls
```bash
grep -B1 -A3 "FromISR" Core/Src/*.c Core/Src/*.cpp
```

### Check for forbidden ISR operations
```bash
grep -rn "vTaskDelay\|xSemaphoreTake\|printf\|HAL_Delay" Core/Src/ | \
  grep -i "irq\|handler\|callback"
```

---

## 4. Observer and Model Verification

### Count observer subscriptions
```bash
grep -rn "subscribe(" Core/Src/*.cpp | wc -l
```

### Verify model static_assert
```bash
grep -rn "static_assert" Core/Inc/Models.hpp
```

### Check model sizes
```bash
grep -rn "sizeof(" Core/Inc/Models.hpp
```

---

## 5. FreeRTOS Configuration Check

### Stack overflow detection
```bash
grep -rn "configCHECK_FOR_STACK_OVERFLOW" Core/Inc/FreeRTOSConfig.h
# Must be 2
```

### Malloc failed hook
```bash
grep -rn "configUSE_MALLOC_FAILED_HOOK" Core/Inc/FreeRTOSConfig.h
# Must be 1
```

### Heap size
```bash
grep -rn "configTOTAL_HEAP_SIZE" Core/Inc/FreeRTOSConfig.h
```

### Task stack sizes
```bash
grep -rn "StackType_t.*\[" Core/Inc/ Core/Src/
```

---

## 6. Build Verification

### Clean build
```bash
make clean && make -j$(nproc) 2>&1 | tail -20
```

### Check for warnings (should be zero with -Werror)
```bash
make -j$(nproc) 2>&1 | grep -i "warning\|error"
```

### Verify compiler flags
```bash
grep -E "fno-exceptions|fno-rtti|Os|cortex-m0" Makefile
```

---

## 7. Flash and Debug

### Flash via ST-Link
```bash
st-flash write build/*.bin 0x08000000
```

### Flash via OpenOCD
```bash
openocd -f interface/stlink.cfg -f target/stm32f0x.cfg \
  -c "program build/*.elf verify reset exit"
```

### Debug via GDB
```bash
# Terminal 1: Start OpenOCD
openocd -f interface/stlink.cfg -f target/stm32f0x.cfg

# Terminal 2: Connect GDB
arm-none-eabi-gdb build/*.elf -ex "target remote :3333" -ex "monitor reset halt"
```

### Monitor debug UART
```bash
screen /dev/ttyUSB0 115200
# Or
minicom -D /dev/ttyUSB0 -b 115200
```

---

## 8. Complete Verification Script

```bash
#!/bin/bash
set -e

echo "=== STM32 Embedded Verification ==="

echo "1. Checking for heap allocation..."
HEAP=$(grep -rn "malloc\|new \|std::vector\|std::string" Core/Inc/ Core/Src/ || true)
if [ -n "$HEAP" ]; then
    echo "FAIL: Found heap allocation:"
    echo "$HEAP"
    exit 1
fi
echo "   PASS: No heap allocation"

echo "2. Checking ISR safety..."
ISR_UNSAFE=$(grep -rn "\.publish(" Core/Src/ | grep -vi "FromISR" | \
  grep -i "irq\|handler\|callback" || true)
if [ -n "$ISR_UNSAFE" ]; then
    echo "WARN: Possible non-ISR-safe publish in ISR context:"
    echo "$ISR_UNSAFE"
fi

echo "3. Building..."
make clean && make -j$(nproc) 2>&1 | tail -5

echo "4. Memory analysis..."
arm-none-eabi-size build/*.elf

echo "5. Checking model static_asserts..."
ASSERTS=$(grep -c "static_assert" Core/Inc/Models.hpp || echo 0)
echo "   Found $ASSERTS static_assert checks"

echo "6. Checking FreeRTOS safety hooks..."
STACK_CHECK=$(grep "configCHECK_FOR_STACK_OVERFLOW" Core/Inc/FreeRTOSConfig.h || true)
echo "   $STACK_CHECK"

echo "=== Verification Complete ==="
```

Save as `scripts/verify.sh` and run with `bash scripts/verify.sh`
