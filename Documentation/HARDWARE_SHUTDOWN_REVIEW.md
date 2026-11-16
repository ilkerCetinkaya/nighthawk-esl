# HARDWARE_SHUTDOWN_REVIEW (REV A, focused review)

Scope: can the RF module rails be disabled independently of ESP32 firmware, and is an extra hardware timeout needed. Evidence levels: [D] read in a datasheet this session, [N] read from the REV A netlist/PCB, [S] host simulation (a model, not physical evidence), [A] assumption, [U] unverified. Nothing here was measured on hardware. REV A files were not modified: no electrical defect was identified; the finding is a latency limit of the REV A design.

## 1. Power path to the module rails (from the netlist [N])
3V3_RF (LDO U4) -> TPS22918 U5/U6 (VIN) -> RFx_VCC -> ferrite -> connector. Each switch ON pin = RFx_PWR_ON = AND(INTERLOCK_OK, RFx_EN) (U11/U12). INTERLOCK_OK = AND(AND(ARM, EN), AND(LOOP_OK, ENCL_OK)) (U8, U9, U10). EN is the ESP32 EN net driven by the TPS3823 /RESET. ARM is ESP32 GPIO10 with a 10 k pull-down. RFx_EN comes from TCA9555 with a 10 k pull-down. RFx_PWR_ON has a 10 k pull-down. LOOP_OK / ENCL_OK have 10 k pull-downs.

## 2. Component behaviour that matters
| Item | Fact | Source |
|---|---|---|
| TPS3823-33 /RESET | push-pull, active low; asserts if no WDI falling edge within ttout 0.9 / 1.6 / 2.5 s (min/typ/max); held low td 120 / 200 / 300 ms; VDD->RESET delay 25 us; /MR->RESET 0.1 us; VIT- 2.83-3.00 V (typ 2.93 V) | [D] SLVS165O |
| TPS3823 WDI floating | "If left floating, the device generates pulses internally to prevent watchdog reset" | [D] SLVS165O Table 5-1 |
| ESP32-C3 GPIO10 (ARM) at reset and after reset | IE only: input enabled, no internal pull (hi-Z) | [D] ESP32-C3 datasheet v2.4 Table 2-1 (pin "GPIO10": IE / IE) |
| ESP32-C3 GPIO7 (WDI, MTDO) at reset | IE: hi-Z. GPIO9 has WPU. Internal weak pull resistors, when enabled, are 45 kOhm typ | [D] same |
| Consequence | In reset and early boot ARM is held low only by the external 10 k pull-down; WDI is hi-Z, so TPS3823 sees a floating WDI and self-pulses: the watchdog is effectively disarmed while the MCU is not driving WDI. Safe only because ARM is low until firmware drives it. | [D]+[N] reasoning |
| ARM level seen by gates if a 45 k pull-up were enabled on GPIO10 | 3.3 V x 10 k / 55 k = 0.60 V vs SN74LVC1G08 VIL max 0.8 V (VCC 3.0-3.6 V): thin margin; GPIO10 has no default pull-up so not the case today | [D] SCES217 + ESP datasheet; computed |
| TCA9555 | no reset pin; power-on reset only; outputs retained across MCU reset; I/O inputs have internal pull-up (datasheet figure shows 100 k) | [D] SCPS200E; 100 k is read from a figure, [A] typical |
| RFx_EN with TCA absent/unpowered/POR state | pin sits at 10 k pull-down vs internal pull-up -> about 0.3 V, below gate VIL 0.8 V -> LOW | computed from [D]/[A] |
| SN74LVC1G08 | VIL max 0.8 V, VIH min 2 V at 3.0-3.6 V; max tpd 3.6 ns at 3.3 V | [D] SCES217 |
| TPS22918 | ON: VIH min 1 V, VIL max 0.5 V, "do not leave floating"; tOFF about 2 us typ (RL 10 ohm test); QOD tied to VOUT gives output pull-down RPD ~24 ohm (table value at VIN 5 V) | [D] SLVSD76C |

## 3. Which events remove module power without firmware
| Event | Mechanism | Latency (derived) | Level |
|---|---|---|---|
| Reset button / TPS3823 /RESET (watchdog, brown-out, /MR) | EN low -> U8 -> chain -> switch OFF | 25 us (TPS3823 VDD path) or 0.1 us (/MR) + 4 gates x 3.6 ns + ~2 us switch; output decays through module load / QOD | hardware [D]+[N], not measured |
| Loop or enclosure opened | LOOP_OK/ENCL_OK low -> U9/U10 chain | ~tens of ns + ~2 us | hardware |
| ARM low (any reason incl. MCU in reset or boot) | pull-down on ARM | same | hardware |
| TCA9555 missing / not configured / I2C dead | RFx_EN pulled low | same | hardware (passive default) |
| Supervisor / MCU hung with ARM high and WDI static | only the TPS3823 time-out | up to ttout: 0.9 / 1.6 / 2.5 s | hardware but slow; [S] shows 845-2485 ms exposure |

## 4. Can a single MCU task prevent shutdown?
- Supervisor task: yes. If it stalls (or interrupts/scheduler are blocked, CPU halted by a debugger, spinlock held) ARM keeps its last GPIO level and the rails stay on until the TPS3823 times out (<= 2.5 s). Only this task and a whole-MCU hang have that property.
- Sampler or CLI stall: not by themselves; the supervisor drops ARM (software, <= 500 ms / 5 s). This depends on the supervisor being alive.
- No task can keep power on through a reset, loop-open, enclosure-open or when ARM is low: those are hardware paths. No task can raise ARM during reset/boot.
- Firmware cannot override the AND chain: ARM and RFx_EN are only two of the six inputs.
Conclusion: apart from the supervisor-stall exposure, shutdown does not depend on firmware.

## 5. Is an independent hardware timeout required?
Judgement, not a measurement: the REV A requirement ("watchdog timeout disables both rails through hardware") is met, with a worst case of 2.5 s. Whether 2.5 s is acceptable depends on what will be plugged into the expansion connectors, which is not defined (no module chosen). For a platform that is meant to power unknown RF modules, a 0.9-2.5 s window with ARM latched high is the largest remaining single-task exposure. Recommendation: add an independent dead-man timeout in REV B, sized to about 0.2-0.5 s, and keep REV A as is. A REV A rework is not recommended (hand-wiring a latch onto a 4-layer SOT-23 board adds more risk than it removes).

## 6. Options evaluated (no circuit is implemented)
| Option | What was verified | What is not verified | Verdict |
|---|---|---|---|
| A. TPS3431 (programmable watchdog) + SN74LVC1G74 latch + 1 AND gate | TPS3431 [D] SNVSB66A: VDD 1.8-6.5 V, open-drain WDO active low, WDI falling-edge, tWD with CWD = 10 k to VDD and SET1 = 1: 170 / 200 / 230 ms; tRST 170-230 ms WDO pulse; ENOUT low until tRST after power-up; capacitor option 100 pF-1 uF (62.74 ms typ at 0.1 nF, 77.45 s at 1000 nF). WDO is only a pulse (tRST), so it needs a latch: SN74LVC1G74 [D] SCES794G: edge-triggered D flip-flop, active-low CLR and PRE, 1.65-5.5 V | Equation 1 coefficients (not extractable here; a two-point fit suggests tWD ~ 77.4 ms/nF x C + 55 ms, unverified); LCSC part numbers, stock and footprints; behaviour of WDI when MCU is hi-Z at boot; power-up state of the flip-flop output | Preferred: timing is fully characterised by the manufacturer |
| B. SN74LVC1G123 retriggerable monostable | [D] SCES586E: edge triggered, retriggerable to 100 % duty, CLR terminates the pulse; tw about 1.0-1.1 ms at 3.3 V for Rext 10 k, Cext 0.1 uF; Rext >= 1 k at VCC >= 3 V; Rext/Cext must not be tied to rails | tw for tens-of-ms to 500 ms needs a large RC (e.g. 100 k x 2 uF); datasheet characterises only the 10 k points, so tolerance (including capacitor DC-bias loss) is unknown; no latch: normal operation resumes when WDI resumes | Possible, requires bench characterisation first |
| C. Charge-pump (AC-coupled heartbeat) | nothing | all | Rejected |
| D. Keep TPS3823 only | [D] timing above | n/a | Acceptable for REV A, not for unknown modules |

## 7. Requirements any added circuit must meet (to be checked on the bench before layout)
1. Power-up state: permit output must be LOW until firmware has toggled and then re-armed.
2. Recovery: after a trip, permit must stay LOW until ARM goes low and rises again (satisfies "recovery needs a safe disarmed state").
3. It must not rely on the same GPIO state that fails: it must observe the supervisor's toggling (WDI), not the ARM level.
4. False-trip margin: with one WDI falling edge every 50 ms (firmware pulse, changed in the latest revision; the earlier level toggle gave an edge every 100 ms) vs tWD min 170 ms leaves 120 ms; NVS or flash operations that stall the CPU for longer would trip it (safe direction, nuisance). Measure worst-case supervisor jitter on the target before choosing 200 ms vs a capacitor-set value.
5. Unconnected or hi-Z WDI during boot must not cause chatter on the permit path (permit is held low anyway).
6. The 3V3 logic rail is shared with the existing chain; behaviour of every gate at low VCC is not characterised in the datasheets read here [U].
