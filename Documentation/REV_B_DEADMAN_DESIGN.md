# REV_B_DEADMAN_DESIGN (proposal only; REV A unchanged)

Evidence labels: [DS] manufacturer datasheet read this session (TI TPS3431 SNVSB66A, SN74LVC1G74 SCES794G, SN74LVC1G08 SCES217AA, TPS3823 SLVS165O, TLV755P, TCA9555 SCPS200E, ESP32-C3 v2.4); [CALC] calculation (Hardware/build/deadman_calc.py); [SIM] logic-level host model of my reading of the datasheets (Hardware/build/deadman_sim.py), not hardware; [N] REV A netlist; [U] unverified; [MEAS] physical measurement: none exists for any item.

## 1. Proposed architecture
| Block | Part | Connections |
|---|---|---|
| Dead-man timer | TPS3431 (VSON-8 DRB, 3 x 3 mm) | VDD = 3V3 (100 nF); SET1 = 3V3; CWD = 10 k to 3V3 (preset 170/200/230 ms) or C0G capacitor (section 2); EN open (internal pull-up); WDI = the existing WDI net (supervisor pulse); WDO and ENOUT open-drain, each 10 k to 3V3 |
| Clear logic | SN74LVC1G08 | A = ENOUT, B = WDO, Y = CLR_N |
| Latch | SN74LVC1G74 (pins CLK 1, D 2, Q 3, GND 4, /Q 5, CLR 6, PRE 7, VCC 8 for DCT/DCU) | CLK = ARM; D = 3V3; PRE = 3V3; CLR = CLR_N; Q = PERMIT |
| Permit gate | SN74LVC1G08 | INTERLOCK_OK = INTERLOCK_OK_PRE AND PERMIT, placed where the AND chain now ends so the TCA9555 read-back of INTERLOCK_OK includes the permit |
| Second source cut | TLV755P (existing U4) | EN of the 3V3_RF LDO driven by INTERLOCK_OK instead of tied to VBUS_F (EN VHI 1.0 V min, VLO 0.3 V, startup 550 us typ, active output discharge [DS]) |
| Observation | second TCA9555 at 0x21 (A0 = 3V3) | inputs: PERMIT, WDO, ENOUT, RF1_VCC_SENSE, RF2_VCC_SENSE (section 7) |
Logic: PERMIT is cleared at power-up (ENOUT low) and whenever WDO asserts; set only by a rising edge of ARM while neither is asserted; stays low until ARM falls and rises again.

## 2. Timeout: calculated, not assumed
TPS3431 [DS]: preset CWD = 10 k to VDD, SET1 = 1: tWD 170 / 200 / 230 ms (min/typ/max, over -40..125 C). Capacitor mode: tWD(ms) = 77.4 x C(nF) + 55, +/-9.5 % for an ideal capacitor (Table 8-2), tested 100 pF-1 uF. [CALC] with an assumed +/-5 % C0G capacitor (assumption, no part selected):
| Option | min / typ / max (ms) | margin min/50 ms | exposure after a supervisor stall |
|---|---|---|---|
| Preset (10 k to VDD) | 170 / 200 / 230 [DS] | 3.4x | <= 230 ms |
| 1 nF | 116 / 132 / 149 | 2.3x | <= 149 ms |
| 2.2 nF | 196 / 225 / 256 | 3.9x | <= 256 ms |
| 3.3 nF | 269 / 310 / 354 | 5.4x | <= 354 ms |
| 4.7 nF | 363 / 419 / 479 | 7.3x | <= 479 ms |
| 10 nF | 715 / 829 / 950 | 14.3x | <= 950 ms (no better than TPS3823 min) |
The "200 ms" figure is the typical value only. The bound that can be claimed is 230 ms plus latch/gate/switch delays of well under 1 us (SN74LVC1G08 tpd max 3.6 ns [DS]; SN74LVC1G74 max tpd 5.9 ns at 3.3 V [DS features line]; TPS22918 tOFF about 2 us [DS]) = about 0.23 s [CALC], versus 0.9-2.5 s today. Exposure runs from the last falling edge on WDI, so it is never longer than tWD max after the supervisor stops.
False-trip margin: the firmware now issues one WDI falling edge per supervisor pass (50 ms, a 5 us low pulse; TPS3823 requires >= 100 ns at WDI [DS], TPS3431 minimum WDI pulse 50 ns [DS]). Against tWD min 170 ms the supervisor may be late by about 120 ms before a trip (3.4x). Earlier firmware toggled a level every 50 ms, giving a falling edge only every 100 ms and a margin of 70 ms; that was corrected in this revision. The real worst-case supervisor delay (flash writes, interrupt latency) has NOT been measured [U]; a trip is the safe direction (nuisance).

## 3. Power-on reset
[DS] TPS3431: VPOR 0.8 V; for VPOR <= VDD < VDD(min) = 1.8 V WDO is asserted (low); after VDD >= 1.8 V a 300 us start-up delay, then ENOUT is released only tRST (170-230 ms) after EN is high, so ENOUT is low for >= 170 ms after power-up. CLR_N = ENOUT AND WDO is therefore low for >= 170 ms and PERMIT is forced 0. [SIM] an ARM rise inside that hold produces no permit (edge ignored). Below VPOR the TPS3431 outputs are undefined and the SN74LVC1G74 output state at power-up is not specified in the text read [U]; in that region the existing 10 k pull-down on each TPS22918 ON pin and the unpowered gate chain keep the switches off [N].

## 4. WDO pulse behaviour
[DS] WDO goes low for tRST (170-230 ms) after a timeout, then releases; WDI is ignored while WDO is low. With a static WDI the sequence repeats every tWD + tRST, i.e. WDO pulses. The pulses are not usable as a level, hence the latch: [SIM] after the first timeout PERMIT stays 0 through later WDO pulses, through WDO releasing, and when WDI toggling resumes, until an ARM edge. A WDI edge during a WDO pulse is ignored, so after a trip the first healthy WDI edges may need up to tRST before they count [DS].

## 5. Flip-flop set/reset logic
[DS] SN74LVC1G74: a low level at PRE or CLR sets or resets the outputs regardless of other inputs; with both inactive, D is transferred on the rising CLK edge. With D and PRE tied high, Q can only become 1 on a rising ARM edge while CLR_N is high. Setup/hold: D is static, no timing risk. ARM is a 10 k-pulled-down GPIO with fast edges; a noise spike on that high-impedance node while CLR_N is high could set PERMIT while ARM is low, which is harmless by itself (ARM is also required) but would remove the "re-arm needed" property; a 100 pF capacitor / series resistor option is left to the layout stage.

## 6. ARM rearming sequence
Trip: PERMIT 0 immediately; rails off even if ARM stays high; firmware reads INTERLOCK_OK low -> OPEN (the permit sits before the read-back). Recovery: disarm (ARM low) -> verified enables low -> arm request -> PRECHECK -> ARM rises -> if CLR_N is inactive at that edge, PERMIT = 1 [SIM]. If WDO is still pulsing at the edge it is lost, firmware reads INTERLOCK_OK low in ARMING and goes OPEN; retry is possible.

## 7. Brown-out and low-voltage logic levels
- 3V3 falling: TPS3823 /RESET asserts at VIT- 2.83-3.00 V (typ 2.93 V) with a 25 us delay [DS] -> EN low -> chain off.
- TPS3431: VDD(min) 1.8 V; below it WDI is ignored and ENOUT is driven low [DS] -> CLR active.
- Operating minimum VCC: SN74LVC1G08 1.65 V [DS], SN74LVC1G74 1.65 V [DS], TPS22918 VIN down to 1 V (ON VIH 1 V, VIL 0.5 V) [DS], TLV755P UVLO 1.21-1.44 V rising [DS].
- Between about 2.9 V and 1.8 V the chain is held off by the reset; below 1.65 V logic outputs are not specified [U]; the final fallback is the passive 10 k pull-down at each switch ON pin and, in REV B, the LDO EN gating (an unpowered 3V3 gate drives U4 EN low).
- Limited to what the datasheets state: no brown-out test was done.

## 8. Failure of the timeout circuit itself
| Failure | Effect | Detection | Result |
|---|---|---|---|
| TPS3431 missing/dead/unsoldered | open-drain outputs float to their pull-ups: CLR inactive, the latch behaves as a plain arm latch. The dead-man function is silently lost (fail-open) | proof test below | other protections remain; must be caught by test, not by the circuit |
| Latch Q stuck 1 | dead-man lost | proof test (PERMIT must be 0 after a forced timeout) | |
| Latch Q stuck 0 | permit never granted -> INTERLOCK_OK always low -> system cannot arm | found at first arm attempt | safe |
| CLR_N stuck low | same as Q stuck 0 | | safe |
| WDO/ENOUT shorted to GND | permanent clear | | safe |
| False trips (jitter) | rails drop, firmware goes OPEN | CLI status | safe, nuisance |
Proof test (firmware, before every arm; untested): with ARM low, stop WDI pulses for about 260 ms, read WDO via the second expander (must be low for 170-230 ms), read PERMIT (must be 0), resume pulses; total stoppage 0.26 s < TPS3823 ttout min 0.9 s [DS]. Then, during ARMING, confirm PERMIT = 1 after the ARM edge. Common-cause failure of the 3V3 rail turns everything off.

## 9. Rail feedback and stuck-ON detection (separate item)
REV A has no feedback: a stuck-ON switch (gate output stuck high, ON shorted to 3V3, switch shorted) is undetectable and unbounded (FAILURE_MODE_MATRIX.md row 8). Proposal: connect each RFx_VCC through 10 k to an input of the second TCA9555. Input thresholds [DS]: VIL 0.3 x VCC (0.99 V), VIH 0.7 x VCC (2.31 V), inputs tolerate up to 5.5 V. Expected = (PWR_ON asserted). Mismatch (rail high while switch commanded off, or low while on) -> FAULT. Limits: a module back-powered through its signal pins can present about 3 V and read high with the switch off (false "stuck-on", safe direction); a rail held between 0.99 and 2.31 V is indeterminate; the sense shows presence, not current. Response to a real stuck-ON: the redundant path is the LDO enable gating (section 1): INTERLOCK_OK low shuts U4, cutting the source for both modules. Only one failure at a time is covered; a stuck-ON switch that is also back-fed from another source is not.

## 10. Verification before layout (all open)
1. LCSC/JLCPCB availability, footprints and stock for TPS3431DRB (VSON-8), SN74LVC1G74 (SM8/US8), extra SN74LVC1G08, second TCA9555 [U].
2. Bench: measure supervisor pulse jitter on the target under NVS/SD activity; measure tWD with the chosen CWD option; verify WDI minimum pulse; scope PERMIT through power-up/brown-out ramps; characterise gate and latch outputs below 1.65 V.
3. Confirm the SN74LVC1G74 power-up state from the full datasheet/EVM or test with CLR held low during ramp.
4. Review ARM node noise susceptibility on the real layout.
5. Run the proof test and every row of FAILURE_MODE_MATRIX.md on the REV B prototype.
