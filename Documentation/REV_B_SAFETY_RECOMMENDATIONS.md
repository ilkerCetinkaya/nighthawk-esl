# REV_B_SAFETY_RECOMMENDATIONS

Priority = my judgement. None of these changes was made to REV A.

## P0
1. Independent dead-man timeout (reduces the supervisor-stall exposure from <= 2.5 s to about 0.2-0.5 s). Preferred option: TPS3431 programmable watchdog (CWD = 10 k to VDD -> tWD 170/200/230 ms, or a capacitor for a longer value after the datasheet equation is checked) feeding a latch built from SN74LVC1G74, with permit = Q ANDed into the existing INTERLOCK_OK chain (HARDWARE_SHUTDOWN_REVIEW.md section 6/7). Latch semantics: cleared at power-up (ENOUT low) and whenever WDO asserts; set only by an ARM rising edge. Before layout: confirm LCSC parts/footprints/stock, TPS3431 equation 1, flip-flop CLK/D/CLR behaviour at power-up, WDI handling when the MCU is hi-Z, and measure supervisor jitter on the target.
2. Rail sensing: a divider (or comparator) from each RFx_VCC to a free ADC/expander input, so a stuck-on switch (matrix row 8) is visible. The REV A VMON divider was removed when pin 5 was needed for SD_CS; budget a pin.
3. Bus isolation for module connectors: series resistors (or a bus switch/buffer powered with the module rail) on SCK/MOSI/MISO/SDA/SCL/CS/RST/IRQ lines so that a gated-off module is not back-powered (row 15). Consider a separate SPI bus for the SD card.

- (P0, add to item 3) Make LOOP_OK and ENCL_OK individually readable by the MCU (second expander inputs, through series resistors), so PRECHECK can require both loops closed before ARM rises (`loops_observable` in sup_sample_t). On REV A an open loop can only be seen after ARM rises, where the chain keeps the rails off.

## P1
4. Make RFx_EN physically unable to float high at power-up: keep the 10 k pull-downs (present) and add a TCA9555 hardware reset or choose an expander with a RESET pin so outputs return to a known state on MCU reset (TCA9555 retains outputs).
5. Add a hardware-latched fault: a trip (watchdog, loop open) holds rails off until ARM goes low (part of option 1 for the watchdog; extend to loop/enclosure if required).
6. Defined WDI pull-down/pull-up so WDI is never floating while the MCU is in reset (TPS3823 self-pulses a floating WDI).
7. Decoupling: place a 100 nF within ~2-3 mm of every IC supply pin (REV A: 4-12 mm). Re-run the placement with the constraint instead of region auto-placement.
8. LDO headroom: the TLV75533PDBV in SOT-23-5 has RthetaJA 100.8 C/W (EVM) / 231.1 C/W (JEDEC); 500 mA from 5 V is not sustainable. Limit the module rail budget, consider a buck for 3V3_RF, or a larger package.

## P2
9. Replace the USB-C D+ stub (both A6/B6 tied) layout with a proper routed pair; add USB data-line ESD verified against the ST datasheet (not read in this project).
10. Obtain and file the datasheets for USBLC6-2SC6, TYPE-C-31-M-12, DM3AT-SF-PEJM5 (REV A could only check symbol-vs-PCB consistency).
11. Connector for UART on the module header, RF ESD device, reverse-current diode (carried over from REV A notes).

## Firmware to keep regardless of hardware
Only the supervisor toggles WDI; no timer/ISR may toggle it. Boot clears RFx_EN before any arm. Arm requires a verified-low read of both output register and pin. Add a rail-voltage check to the arm conditions when REV B has sensing.

## What would change the assessment
The choice of real RF modules (current, voltage, back-power tolerance), a bench measurement of supervisor jitter, the TPS3823 and gate behaviour at low VCC, and a physical test of every row of FAILURE_MODE_MATRIX.md.
