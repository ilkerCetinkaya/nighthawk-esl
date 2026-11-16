# FAILURE_MODE_MATRIX

Legend. Guarantee: HW = no firmware needed, SW = depends on running firmware, HW(slow) = hardware but bounded by the TPS3823 time-out. Latencies are derived from datasheet numbers or from the host simulation ([S], a model); none were measured. ARM = GPIO10. "Rails" = RF module power rails.

| # | Fault | Detection | ARM state | Rails | Max shutdown latency | Guarantee |
|---|---|---|---|---|---|---|
| 1 | Supervisor task stalled (ARM high) | TPS3823 sees no WDI falling edge | stays high until reset | stay ON until reset, then OFF | ttout max 2.5 s (typ 1.6, min 0.9); [S]: 845-2485 ms | HW(slow). Largest exposure |
| 2 | Sampler task stalled / I2C call hung | supervisor: sample older than 400 ms | low | OFF | <= 400 ms + 50 ms (+ gate/switch microseconds); WDI stops at 500 ms; MCU reset follows | SW (needs supervisor alive); if supervisor also dead -> row 1 |
| 3 | CLI task stalled (command without progress) | supervisor: 5 s deadline | low | OFF | 5.05 s ([S] 5040 ms) | SW. Policy value; CLI stall does not itself keep rails on |
| 4 | I2C bus stuck LOW | read error (50 ms timeout) -> bad sample; one invalid sample while ARMED latches FAULT; 3 consecutive anywhere | low | OFF (ARM low) | <= ~150 ms ([S] 90 ms) | SW (ARM low), then HW gates. If the driver hangs instead of timing out -> row 2 |
| 5 | TCA9555 disconnected / unpowered | same as 4; additionally RFx_EN and INTERLOCK_OK read path lost | low | OFF; RFx_EN falls to its 10 k pull-down so the AND gates are low independent of firmware | pull-down: immediate (microseconds); firmware detection <= ~150 ms | HW for the rail default (RFx_EN low), SW for ARM |
| 6 | TCA9555 output register mismatch (bit flipped, shadow differs) | read-back vs shadow under mutex each 100 ms | low | OFF | <= ~150 ms ([S] 90 ms) | SW. Gap before this revision: no mismatch check while ARMED |
| 7 | TPS3823 reset (watchdog, /MR, brown-out) | n/a, hardware | low (hi-Z + 10 k pull-down in reset) | OFF | ~25 us (VDD path) / 0.1 us (/MR) + gates (3.6 ns each) + switch ~2 us | HW |
| 8 | Load-switch ON stuck HIGH (gate output stuck high, ON shorted to 3V3, switch failed short) | none: rail voltage is not sensed | low | stay ON | unbounded | NOT guaranteed; single point of failure. REV B: rail sense / series second switch |
| 9 | Interlock loop or enclosure input opened | LOOP_OK / ENCL_OK low; firmware also sees INTERLOCK_OK low | firmware drops ARM within ~150 ms | OFF immediately | gates + switch (microseconds); [S] 0 ms | HW; SW latches OPEN |
| 10 | ESP32 brown-out / 3V3 sag | TPS3823 threshold 2.83-3.00 V (typ 2.93 V) -> /RESET | low in reset | OFF | ~25 us + gates + switch | HW. Caveat: logic gates share the sagging 3V3 while 3V3_RF stays up (separate LDO); gate outputs below VCC 1.65 V are not characterised -> the 10 k pull-down on each switch ON pin is the fallback [U] |
| 11 | Reset button | /MR low | low | OFF | 0.1 us + gates + switch | HW |
| 12 | Firmware hung but still toggling WDI from a timer/ISR | not detected by hardware | stays high | stay ON | unbounded | Prevented in this firmware: only the supervisor toggles WDI; a hardware timer or ISR could still do it if added later |
| 13 | CPU halted by debugger | TPS3823 (no WDI) | stays at last level | ON until reset | up to 2.5 s | HW(slow) |
| 14 | Boot hang after reset | ARM hi-Z, 10 k pull-down; TPS3823 WDI floating self-pulses (no watchdog) | low | OFF | n/a | HW (default state) |
| 15 | Back-powering of an unpowered module through SPI/I2C lines | not detected | low | module may be partly powered via protection diodes | n/a | NOT guaranteed (shared SD bus, no isolation) |

[S] values come from Firmware/tests/host (122 checks). They test supervisor_core.c/health_core.c against a model; they are not evidence about the real board.
