> SUPERSEDED by UPDATED_FIRMWARE_TEST_REPORT.md.

# FIRMWARE_TEST_REPORT

## Method
Host-side simulation, not hardware. `Firmware/tests/host/test_main.c` compiles the production sources `src/health_core.c` and `src/supervisor_core.c` unchanged and drives them with a 1 ms tick model of (a) the firmware loop (sampler 100 ms, supervisor 50 ms, CLI states; the glue is a re-implementation of interlock.c, not the ESP code itself) and (b) the hardware: the AND-gate chain from INTERLOCK_TRUTH_TABLE.md, the TPS3823 watchdog/reset behaviour at ttout 0.9 / 1.6 / 2.5 s and td 200 ms (modelled from datasheet statements: no WDI falling edge within ttout -> /RESET low for td), 10 k pull-down on ARM while the MCU is in reset, and TCA9555 outputs retained across MCU reset (datasheet: only power-on reset). Faults are injected by flags. The ESP-specific glue (interlock.c, health.c, sampler, GPIO, I2C driver) is covered only by the ESP-IDF build, not by these tests.
Command: `cd Firmware/tests/host && make` (Apple clang 15, -Wall -Wextra -Werror). Output: Documentation/Validation/audit2/host_test_output.txt.

## Result: 122 checks, 0 failures (after sampler-semantics rework; was 113) (exit 0). Two earlier runs had failures that exposed a test-expectation error and one real supervisor weakness (see below).
| Test | Scenario | Measured in the model |
|---|---|---|
| T0 | health_core: deadline, progress, idle, missing task, re-busy, 32-bit wrap | pass |
| T1 All healthy | arm, rails on, 20 s | 0 resets, 200 WDI falling edges, stays ARMED |
| T2a Critical task stalled (sampler) | stall while armed and rail on, ttout 0.9/1.6/2.5 | ARM low and rails off 440 ms after stall (stale-sample check, limit 500); WDI stops after the 500 ms deadline; hardware reset follows; after reset DISARMED, ARM low, rails off for 2 s |
| T2b CLI stalled | command with no progress | ARM low 5040 ms after command start (deadline 5000); an 8 s command reporting progress stays ARMED |
| T3 Supervisor stalled | supervisor stops with ARM high, WDI stuck low and stuck high, ttout 0.9/1.6/2.5 | rails stay on 845-885 / 1545-1585 / 2445-2485 ms, then off by hardware reset; DISARMED afterwards |
| T4 I2C failure | read errors while armed | ARM low in 90 ms, FAULT/I2C, no reset; arm refused; disarm refused while I2C is down (stays safe); after I2C returns disarm succeeds, enables read back low, re-arm works |
| T5 MCU reset | reset button while armed | rails off in the same tick; TCA9555 enable bit still set after reset (retained); stays off, DISARMED; boot clears it. Variant: boot clear fails -> arm refused |
| T5b Enable race | enable bit set just after a stale sample | arm briefly accepted, rail on 150 ms, then FAULT/ENABLES_HIGH |
| T6 Watchdog timeout | WDI stops, ttout min/typ/max | exactly one reset, at 900 / 1600 / 2500 ms after last falling edge; rails off |
| T9 Sampler semantics | 3 consecutive failed I2C cycles while DISARMED; output-register mismatch while ARMED; enable pin reads high with output low | FAULT/I2C latched at the 3rd failure, no watchdog reset (task alive), arm refused, recovery needs 3 good samples + disarm; mismatch: ARM low in 90 ms; pin-high: arm refused |
| T7 Interlock open | loop, then enclosure, while armed | rails off at 0 ms (combinational gates); supervisor OPEN within 150 ms; closing the loop does not re-arm; arm refused until disarm |

## Findings from the test run
1. Test expectation was wrong: ARM drops at the 400 ms stale-sample limit, before the 500 ms task deadline, so WDI is still serviced for another ~60-100 ms. Safe; expectation corrected and documented.
2. Real weakness: arm could be accepted from a sample up to 400 ms old; an enable set in between would power a module for ~150 ms. Fixed in supervisor_core.c: the settle sample must show enables low or the supervisor latches FAULT (T5b). Residual exposure remains ~150 ms in that race; the CLI path avoids it by clearing enables and waiting two sampler periods before requesting arm.

## Not tested
Real timing on the ESP32-C3, real I2C/SD/ADC blocking behaviour, spinlock contention, TPS3823 and TCA9555 actual behaviour, gates and load switches on the PCB. No hardware test was run.
