# NIGHTHAWK ESL Security Research Tool: Architecture (REV A)

Status: design validated by ERC and DRC. **Not built, not powered, not RF-tested.** No range, compatibility or frequency claim is made.

## Board
80 x 80 mm, 4 layers, 1.6 mm FR-4, JLCPCB JLC04161H-7628 stackup (L1 0.035 Cu, 0.2104 mm 7628 prepreg Er 4.4, L2 GND, 1.065 mm core Er 4.6, L3, 0.2104 mm prepreg, L4). USB-C, two edge-launch SMA, two keyed 15-pin module connectors, microSD, UART and DEBUG headers, 4 x M2.5 holes.

## Blocks (hierarchical schematic sheets)
| Sheet | Function |
|---|---|
| 01_MCU | ESP32-C3-WROOM-02-N4, TCA9555 I2C GPIO expander |
| 02_USB_C | USB-C receptacle, CC resistors, USBLC6 ESD, 0.5 A PTC fuse |
| 03_POWER | Two 3.3 V LDOs (digital, RF module rail), ferrite-filtered analog rail |
| 04_RF_INTERFACE | RF IN and RF TEST SMA, 100 pF DC block, pi-attenuator pads, 0 ohm links |
| 05_RF_MONITOR | RSSI input network (external detector output to MCU ADC) |
| 06/07_RF_EXPANSION_1/2 | Keyed module connector, TPS22918 load switch, ferrite-filtered supply |
| 08_HARDWARE_INTERLOCK | TPS3823 supervisor/watchdog, five AND gates, loop and enclosure inputs |
| 09_MICROSD | microSD socket, SPI mode, card detect |
| 10_DEBUG | UART and DEBUG headers, RESET and BOOT buttons |
| 11_STATUS_LEDS | Power, interlock-OK, status, fault LEDs |

## MCU
ESP32-C3-WROOM-02-N4 (Espressif datasheet v1.7). 15 usable GPIOs. The firmware never starts Wi-Fi or BLE (disabled in sdkconfig.defaults), so the integrated radio is off during measurements.

## RF architecture
No radio chipset is selected. The mainboard has two identical module slots (SPI shared bus, per-slot CS/IRQ/RST/IO from the expander, I2C for a module-ID EEPROM at slot-set address, switched and ferrite-filtered supply). The RF path on the board is passive: RF IN, DC block, optional pi attenuator, 0 ohm tee to RF TEST. There is no transmitter, amplifier or detector IC. RSSI_IN accepts the DC output of an external detector. Controlled RF generation uses external calibrated lab equipment.

## Hardware interlock (default RF off)
`INTERLOCK_OK = ARM AND WDG_OK AND LOOP_OK AND ENCL_OK`; module supply `RFx_PWR_ON = INTERLOCK_OK AND RFx_EN`; each load switch has a 10k pull-down on ON.
- Power-up / reset: ARM has a 10k pull-down and the MCU pin is high-Z, so ARM is low. TPS3823 holds RESET low during its delay.
- Firmware crash: WDI stops toggling, TPS3823 asserts RESET (EN low), which also removes WDG_OK.
- Supply fault: TPS3823 undervoltage threshold (3.3 V version) asserts RESET.
- Interlock loop or enclosure input open: 10k pull-downs force LOOP_OK / ENCL_OK low. With no jumper fitted on J6 the default is RF off.
Limits: the AND chain is only as safe as the gates' supply; gate behaviour below ~1 V VCC is not specified here, ARM pull-down covers it. The enclosure sensor is an external switch the user must wire.

## Pin assignment
See Pin_Assignment.xlsx. ESP32-C3: IO0 SPI_SCK, IO1 SPI_MOSI, IO2 I2C_SCL, IO3 SPI_MISO, IO4 RSSI (ADC1), IO5 SD_CS, IO6 EXP_INT, IO7 WDI, IO8 I2C_SDA, IO9 BOOT, IO10 ARM, IO18/19 USB, IO20/21 UART.

## Known compromises
- Module connector has no UART pins (15-pin limit of the stocked connector footprint); UART is on the UART header only.
- SPI bus is shared between modules and microSD (separate CS), not electrically independent.
- Module connector keying: JST SH housings are polarised by the mating housing; connector type was chosen for stock and KiCad footprint, not for board-to-board mating.
- No reverse-current diode (the Schottky candidate was not stocked at LCSC).
- No low-capacitance RF ESD device populated (no verified part).
