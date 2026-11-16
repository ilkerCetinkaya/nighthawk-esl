# WATCHDOG_TASK_HEALTH_MATRIX (firmware REV A.1)

Replaces the previous design (a `health_task` counter incremented by a task whose only job was to increment it). That design proved only that the counter task ran; it is removed. Sources: Firmware/src/{health_core.c, supervisor_core.c, health.c, interlock.c, cli.c, storage.c, main.c}.

## Architecture
- One supervisor task (interlock.c `supervisor_task`, 50 ms period) is the only code that touches PIN_WDI (grep `PIN_WDI`: interlock.c lines for gpio_config and the single gpio_set_level) and the only code that drives PIN_ARM after init.
- The supervisor never generates a heartbeat for anything. It reads progress records written by other tasks (health.c, spinlock-protected) and a sample record written by the sampler.
- The supervisor never performs I2C, SD or ADC operations, so it cannot be blocked by them. Enable clearing is requested through a flag and executed by the sampler.
- If the supervisor itself stalls, nobody toggles WDI and the TPS3823 hardware watchdog acts (host test T3).
- Decision logic is in supervisor_core.c / health_core.c (pure C, no ESP calls) and is what the host tests compile.

## Critical task list and health matrix
| Task | Why critical | What counts as progress (reported by that task) | Allowed silence | Mode |
|---|---|---|---|---|
| sampler (interlock.c `sampler_task`) | only source of INTERLOCK_OK and enable read-back | one complete cycle: optional enable clear, read of TCA9555 input port, read of output port; progress is reported after the cycle ends, whether the transactions succeeded or returned an error. A blocked I2C call does not reach the report. | 500 ms (cycle = 100 ms period + up to 3 I2C transactions at 50 ms timeout = 250 ms worst case) | always BUSY |
| CLI (main task / cli.c) | executes commands incl. arm/disarm, SD and ADC access | boot: after expander init, after ADC init, after storage init; commands: each rf-monitor sample (100 ms), each line of a log export, each poll in arm/disarm waits | boot 10 s; each command 5 s since last progress | IDLE while waiting for input (no deadline), BUSY during a command |
| supervisor | decides WDI/ARM | not self-reported; covered by the hardware TPS3823 | ttout 0.9 / 1.6 / 2.5 s (min/typ/max) | n/a |
Other tasks (ADC, storage, device DB) run only inside CLI commands and are therefore covered by the CLI command deadline. There is no separate Wi-Fi/BT task (not initialised).

Both required tasks must be registered: `hc_evaluate(..., expected_tasks = 2)` fails if fewer are registered. Registration happens in health_init() before the tasks start; the CLI starts BUSY with a 10 s boot deadline, so a CLI that never reaches its input loop is detected.

## What "progress" means for the sampler (three separate things)
1. Execution progress: the cycle ran to completion within its deadline, even if transactions returned errors. Required to keep WDI serviced (otherwise a blocked task would be indistinguishable from a dead MCU, and a reset cannot repair an unplugged expander).
2. Successful acquisition: the cycle returned valid data. Required to stay ARMED (one invalid sample latches FAULT) and to arm.
3. Peripheral health: streak counters. 3 consecutive failures latch FAULT (reason I2C) in any state; arming and recovery require 3 consecutive good samples. Repeated I2C failures are therefore never reported as healthy; the system stays safe (ARM low) and visible via `interlock status`, but the MCU is not reset repeatedly.

## Timeout assumptions
| Parameter | Value | Origin |
|---|---|---|
| WDI toggle period when healthy | 50 ms (every supervisor pass) | firmware |
| TPS3823 watchdog time-out ttout | 0.9 / 1.6 / 2.5 s | TI SLVS165O |
| TPS3823 reset delay td | 120 / 200 / 300 ms | TI SLVS165O |
| Sampler period | 100 ms | firmware |
| Sampler deadline | 500 ms | derived above |
| Sample max age while ARMED | 400 ms | firmware |
| Arm settle time | 60 ms, arm timeout 400 ms | firmware |
| CLI command deadline | 5000 ms; boot 10000 ms | firmware choice |
A single SD write or long ADC loop that does not report progress for more than 5 s will be treated as a stall (ARM low, WDI stops, MCU resets).

## Behaviour on faults (from supervisor_core.c, verified by host tests)
| Event | ARM | WDI | State | Recovery |
|---|---|---|---|---|
| critical task misses deadline | low immediately | serviced no longer | FAULT (task stall) | hardware reset after ttout; MCU boots DISARMED, ARM low |
| sample older than 400 ms while ARMED | low | still serviced until sampler deadline | FAULT (stale) | disarm command |
| expander read error | low | serviced (task alive, error reported) | FAULT (I2C) | disarm command, needs fresh valid sample with both enables read back low |
| INTERLOCK_OK low while ARMED | low | serviced | OPEN | disarm command |
| module enable read back high while arming | low | serviced | FAULT (enables) | disarm command |
| WDI/supervisor stall | stays as last driven (high if armed) | none | n/a | hardware watchdog reset after ttout; exposure is up to ttout (T3) |
Recovery from OPEN/FAULT requires an explicit disarm request AND tasks healthy AND a fresh valid sample showing both module enables low. Arm is accepted only from DISARMED with a fresh sample showing enables low.

## What firmware cannot guarantee
A stall of the supervisor or a hung MCU leaves ARM at its last level until the TPS3823 resets the MCU: rails can stay on for up to ttout (0.9-2.5 s) (host test T3 shows 845-2485 ms in the model). Only the hardware (EN reset, loop/enclosure gates) acts without firmware. A firmware change does not remove this exposure.
