> SUPERSEDED by ARM_RACE_FINAL_REVIEW.md (audit4 source analysis; its residual-risk statements are replaced).

# ARM_TRANSITION_RACE_ANALYSIS

Code reviewed: Firmware/src/{supervisor_core.c, interlock.c, expander.c}, include/supervisor_core.h. Tests: Firmware/tests/host (122 checks, 0 failures, host model). I2C driver behaviour read in ~/esp/esp-idf/components/driver/i2c/i2c.c (i2c_master_cmd_begin takes `cmd_mux` with the caller's timeout). No hardware run.

## State machine (supervisor_core.c, evaluated every 50 ms)
DISARMED --arm_request & guards--> ARMING --settle sample OK--> ARMED
ARMING --enables not low--> FAULT; --interlock open--> OPEN; --400 ms without settle sample--> FAULT
ARMED --invalid sample--> FAULT(I2C); stale sample (>400 ms)--> FAULT; output mismatch--> FAULT; interlock low--> OPEN
any --task stall--> FAULT; 3 consecutive bad samples--> FAULT
ARMING/ARMED --disarm_request--> DISARMED (ARM low, enables cleared)
OPEN/FAULT --disarm_request & tasks healthy & fresh valid sample & enables low & >= 3 good samples--> DISARMED
ARM output is high only in ARMING and ARMED.

## Required conditions before ARMED
| # | Requirement | Where enforced | Status |
|---|---|---|---|
| 1 | Task health valid | a failed `tasks_healthy` latches FAULT before the state switch, so DISARMED cannot accept arm | enforced; tested (T2) |
| 2 | TCA9555 output registers read back | sampler reads register 0x02 (expander_read_outputs) each cycle; arm needs `valid` and fresh | enforced; tested |
| 3 | Both module enables confirmed LOW | `enables_low` = output register bits low AND input-port (pin) bits low; needed at accept time and again in the settle sample | enforced since this revision (pin-level read added); tested (T5, T5b, T9) |
| 4 | Interlock input closed | settle sample `interlock_ok` (read after ARM has been high >= 60 ms, sample started after that instant) | enforced; tested (T7) |
| 5 | No fault latch | state must be DISARMED to accept arm; OPEN/FAULT refuse | enforced; tested |
| extra | >= 3 consecutive good samples | `good_streak` | added this revision; tested (T9) |

## Races found and their status
| ID | Race | Status |
|---|---|---|
| R1 | Sample timestamp was taken after the I2C reads, so a slow or failing cycle could look newer than it was and satisfy the 60 ms settle test with reads made before ARM was high | closed: time_ms is now the start of the cycle (conservative: sample is considered as old as its first transaction) |
| R2 | Arm accepted from a sample up to 400 ms old; an enable raised in between would power a module until the settle sample | narrowed, not removed: settle sample must show enables low or the state latches FAULT. Host model (T5b): rail powered ~150 ms. The CLI path clears enables and waits two sampler periods before requesting; nothing else in the firmware raises RFx_EN today |
| R3 | `enables_low` used only the output register; a pin held high by a fault (shorted pin, wrong direction) was not seen | closed: input-port bits are also required low |
| R4 | Non-atomic sample: input port and output register are separate I2C reads (<1 ms apart normally, up to ~100 ms with 50 ms timeouts) | accepted: all five conditions are re-evaluated in the settle sample; a change between reads is caught on the next cycle (<= 100 ms) |
| R5 | App writes RFx_EN between sampler's register read and shadow compare | closed: the read-back and the shadow comparison happen under the expander mutex (expander_read_outputs) |
| R6 | Concurrent I2C use: sampler, CLI (expander_write) | the IDF driver serialises with cmd_mux, but a caller waits at most its timeout (50 ms) and then gets ESP_ERR_TIMEOUT; a long transaction could therefore produce a false bad sample (fail-safe direction, one failure is not enough to latch outside ARMED; inside ARMED one invalid sample latches FAULT) |
| R7 | arm_request flag set by the CLI is consumed by the supervisor each pass; a request set while the state is not DISARMED is dropped | acceptable: the CLI polls state and returns failure |
| R8 | ARM goes high before the interlock can be read | by design: INTERLOCK_OK depends on ARM, so a settle time is required. During the 60 ms+ settle the rails can be on if RFx_EN is high — hence enables-low is required before ARM rises |
| R9 | Residual: the guard "enables low" is a firmware check, not hardware. A hardware condition (TCA9555 output state) cannot be interlocked with ARM by firmware alone | open; see REV_B_SAFETY_RECOMMENDATIONS.md |

## Residual exposure statement
Between a stale-but-acceptable sample and the settle sample, a module rail can be on for about 150 ms in the host model if an enable is raised by something other than the CLI path. This is a firmware window; it is not eliminated.
