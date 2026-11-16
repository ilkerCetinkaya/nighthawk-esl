# UPDATED_FIRMWARE_TEST_REPORT

Date 2026-11-07. Supersedes FIRMWARE_TEST_REPORT.md. Result labels: [SIM] host simulation, [BUILD] ESP-IDF build, [SRC] review. No physical measurement was made.

## Commands
- Host tests: `cd Firmware/tests/host && make` (cc = Apple clang 15, `-std=c11 -Wall -Wextra -Werror`, sources health_core.c, supervisor_core.c, test_main.c). Output: Validation/audit2/host_test_output.txt. Result: exit 0, 750 checks, 0 failures (audit6; was 720).
- ESP-IDF: `Firmware/build_idf.sh` equivalent: `idf.py -B <scratch>/fwbuild -D SDKCONFIG=<scratch>/fwbuild/sdkconfig -D IDF_TARGET=esp32c3 build` with ESP-IDF v5.4, riscv32-esp-elf gcc 14.2.0 (toolchain extracted from the cached tarball because the installed copy is incomplete; see FIRMWARE_BUILD_REPORT.md). Result: exit 0, 0 errors, 0 warnings, nighthawk.bin 0x58530 bytes, 65 % of the app partition free (audit6 build). Log: Validation/audit2/firmware_build_full_log_rev5.txt. Not flashed.
- Dead-man models: `python3 Hardware/build/deadman_calc.py`, `python3 Hardware/build/deadman_sim.py` (outputs in Validation/audit2/). These are a calculation and a logic model of the REV B proposal, not tests of anything built.

## What the host tests are
supervisor_core.c and health_core.c are compiled unchanged. Everything else is a model: sampler and supervisor loops (a re-implementation of the glue in interlock.c), the AND-gate chain, TPS3823 timing (ttout 0.9/1.6/2.5 s, td 200 ms), pull-downs, TCA9555 output retention across MCU reset, the enable permit. interlock.c, expander.c, health.c, GPIO, I2C, spinlocks and mutexes are NOT executed by these tests; they are covered only by the build and by FREERTOS_CONCURRENCY_REVIEW.md.

## Tests and results [SIM]
| Test | What | Result |
|---|---|---|
| T0 | health_core: deadlines, idle/busy, missing task, 32-bit wrap | pass |
| T1 | all healthy, armed 20 s | 0 resets; 400 WDI falling edges (one per 50 ms pass now) |
| T2a | sampler stalled while armed, ttout 0.9/1.6/2.5 | ARM low 440 ms after stall (stale-sample limit), WDI stops after the 500 ms task deadline, hardware reset follows, DISARMED afterwards |
| T2b | CLI command blocked | ARM low 5040 ms after command start; 8 s command with progress stays ARMED |
| T3 | supervisor stalled with ARM high, WDI idle-high and stalled mid-pulse (low) | rails on 845-885 / 1545-1585 / 2445-2485 ms (idle high) and 900 / 1600 / 2500 ms (low) until the TPS3823 resets |
| T4 | I2C failure | ARM low in 90 ms, FAULT/I2C, no reset; arm refused; recovery only via disarm with good samples |
| T5 | MCU reset while armed; boot clear impossible | rails off in the same tick; retained TCA bit stays set; arming ABORTED in PRECHECK and ARM never rose |
| T5b | non-firmware enable raised at offsets 0..800 ms (7 ms steps) around the ARM transition | raised before ARMED -> never ended ARMED; worst module power exposure 98 ms |
| T5c | firmware enable path | refused in DISARMED/PRECHECK/ARMING, accepted in ARMED, refused after OPEN; stale enable cleared |
| T6 | watchdog timeout | one reset at 900 / 1600 / 2500 ms after the last falling edge; rails off |
| T7 | loop / enclosure open | rails off at 0 ms; OPEN within 150 ms; no auto re-arm; arm after disarm works |
| T9 | sampler semantics | 3 consecutive failures latch FAULT/I2C while DISARMED without a reset; output-register mismatch: ARM low in 90 ms; enable pin high with output low: arm refused |
| T10 | synthetic samples against supervisor_core | same sample forever -> aborted, ARM never high; pre-request sample ignored; duplicate acquisition counted once; sample acquired before settle ignored; invalid / enable-high / over-age sample aborts; arm + disarm together -> disarm wins; arm refused in PRECHECK, ARMING, ARMED, OPEN, FAULT; failed boot verification -> FAULT and never arms |
| T12 | PRECHECK validation (audit6): 7 conditions x 3 sample positions (invalid, enable high, output mismatch, interlock HIGH with ARM low, loop observable and open, stale, future timestamp); 3 fully valid samples; wraparound; future timestamp in ARMING/ARMED | 21 mutations all abort with ARM never high; valid triple reaches ARMING; wrap-safe; future timestamps rejected |
| T13 | integrated PRECHECK on the REV A model | enable pin HIGH and output mismatch: ARM never rose; open loop on REV A: caught in ARMING (OPEN, rails off) |
| T11 | integrated: stalled sampler before request; sampler dying mid-PRECHECK | ARM never rose; never ARMED |

## Findings during this work (all fixed unless stated)
1. audit4 accepted arm from pre-request samples (CURRENT_SOURCE_VS_REPORT.md) - fixed, tested T10/T11.
2. Unsynchronised `volatile` request flags - replaced; review only, not testable on the host.
3. Sampler task could start before the expander mutex existed - fixed by ordering.
4. The sampler cleared enables before reading, hiding a raised enable from the arming checks - changed to read first, then clear (found by T5b).
5. WDI was toggled as a level every 50 ms, giving a falling edge only every 100 ms; now one 5 us low pulse per pass (edge every 50 ms). This changes the false-trip margin for any 170 ms dead-man from 70 ms to 120 ms. The 5 us pulse width and its on-target jitter are not measured [U].

## Not tested
Real timing on the ESP32-C3; GPIO pulse width actually produced by `esp_rom_delay_us(5)`; I2C collisions; spinlock/mutex behaviour; flash/NVS stalls of the supervisor; any hardware behaviour (TPS3823, gates, load switches, TCA9555).

## audit6 addendum
- Defect reported by independent review: PRECHECK did not check `interlock_ok` and `outputs_match`; `age_ok()` accepted negative ages. Both fixed in supervisor_core.c; interlock.c now reads the clock inside the critical section after copying the sample (needed so a just-published sample is never "from the future").
- Interlock condition deviation (REV A cannot show INTERLOCK_OK HIGH before ARM rises): explained in ARM_RACE_FINAL_REVIEW.md; implemented as "must read LOW with ARM low" plus a loops-observable hook for REV B. Not the literal requirement.
- Regression: all earlier tests (T0-T11) still pass unchanged except the synthetic samples in T10, which now set `interlock_ok` explicitly because PRECHECK samples must read it LOW. The old-code check above shows the new tests detect the original defect.
- Build: `idf.py build` exit 0, 0 warnings. Host: `make` with `-Wall -Wextra -Werror`, 750 checks. Nothing was run on hardware; the sampler's `loops_observable = false` on REV A and the timestamp-in-critical-section change are covered by the build and review only.
