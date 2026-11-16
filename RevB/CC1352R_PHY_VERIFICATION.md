# CC1352R proprietary PHY verification against the TI technical reference manual

Date: 2026-11-08. Source: TI SWCU185G "CC13x2, CC26x2 SimpleLink Wireless MCU Technical Reference Manual" (Jan 2018, rev. Jun 2024), chapter 25 "Radio", sections 25.10 (proprietary radio commands) and Tables 25-175 / 25-183, plus the CC1352R datasheet SWRS196I. The TRM is common to the CC13x2/CC26x2 family; I assume it applies to the CC1352R and did not find any CC1352R-specific exception. Labels: [DS] datasheet/TRM statement, [CALC] arithmetic on those statements (`RevB/integrated/rf_calcs.py`, output `rf_calcs_output.txt`), [U] not found in the sources read, [FCC] FCC test report.

Nothing here was measured. No CC1352R hardware exists yet.

## 1. What the TRM says, item by item

| Requested item | TRM / datasheet statement | Result for NIGHTHAWK |
|---|---|---|
| **500 kHz channel spacing** | The synthesiser frequency is given by `frequency` (integer MHz) and `fractFreq` (16-bit); the tuned frequency is "as close as possible to (frequency + fractFreq/65536) MHz" (CMD_FS, Table 25-25). There is no channel-spacing parameter in the proprietary commands: the host chooses any frequency | 500 kHz = fractFreq 32768, exactly representable. The 2402–2480 MHz grid of the Hanshow Nebular Plus (157 channels, 0.5 MHz) is within the programmable range: **capable at command level**. Whether the real synthesiser lands within the tag's tolerance is [U] |
| **Synthesiser frequency resolution** | programming step 1/65536 MHz = 15.26 Hz [CALC] | the actual analogue synthesiser step, phase noise and settling are [U] in the text read. The TRM says only "as close as possible" |
| **Frequency accuracy** | depends on the 48 MHz crystal. The proprietary RX tolerance figures in the datasheet are 350 ppm frequency error and 1000 ppm symbol-rate error for the 802.15.4 PHY [DS SWRS196I §8.22]; crystal ppm requirement not extracted | accuracy of our board is set by the crystal chosen (not chosen yet) [U] |
| **GFSK data rate** | `fbaud = R × 48 MHz / (p × 2^21)`, R is a 21-bit rate word, prescaler p 4–255 (Eq. 15). `modType` 0 = FSK, 1 = GFSK | formula range reaches 12 MBaud, but the datasheet characterises only specific rates (e.g. BLE 1 and 2 Mbps, 802.15.4 250 kbps, sub-GHz up to 500 kbps class). Data rates outside characterised settings are [U] for sensitivity/modulation quality. Example: R = 170000, p = 4 → 972.7 kBaud; R = 350000, p = 4 → 2.0 MBaud [CALC] |
| **Frequency deviation** | 11-bit `deviation` × step size {15.625, 62.5, 250, 1000 Hz} → range up to 2047 kHz; "the accuracy of the deviation may be less than the programmed step size due to hardware limitations" (Table 25-175) | covers BLE (±250 kHz at 1M) and narrower. Exact deviation accuracy [U] |
| **RX filter bandwidth** | 45 programmable settings from 4.8 kHz to 4236 kHz; at 2432 MHz: 153 / 174 / 220 / 264 / 306 / 348 / 439 / 528 / 612 / 697 / 878 / 1056 / 1224 / 1393 / 1756 / 2111 kHz … (Table 25-183) | Hanshow 20 dB bandwidth 558–591 kHz [FCC] fits the 612 kHz setting; SoluM 99 % bandwidth 1.05 MHz [FCC] fits the 1056 kHz setting. Whether the tag's data rate and deviation give acceptable sensitivity with those filters is [U] |
| **Packet engine** | proprietary commands CMD_PROP_RX/TX/(ADV): preamble 1 bit to 32 bytes (`nPreamBytes`), `preamMode`, header 0–32 bits (`numHdrBits`), length field up to 16 bits with position and offset, optional address (size/position/list), 16-bit CRC with polynomial x^16+x^15+x^2+1 and initial value all-ones (CC1101-compatible); "other polynomials, lengths and initialisations can be obtained by parameter overrides"; whitening: none, CC1101/CC2500-compatible, PN9, IEEE 802.15.4g variants; Manchester or long-range FEC option | flexible, but a tag using a different CRC polynomial/seed or whitening needs override settings that I have **not** read [U] |
| **Sync word** | `nSwBits` 8–32 bits; `syncWord0` and optional `syncWord1`; bit/byte order flags (`bMsbFirst`, `bBitReversal`) | 8–32-bit sync words and two simultaneous words are supported. Sync words shorter than 8 bits or longer than 32 bits are not supported [DS] |

## 2. What this means for the target families

| Target | Parameters public | Parameters unknown | CC1352R status |
|---|---|---|---|
| **SoluM EL029H3WRT** | 2402–2480 MHz, GFSK, 40 channels at 2 MHz spacing, 6 dB BW 0.708 MHz, 99 % BW 1.05–1.06 MHz, 3.59 dBm [FCC] | data rate, deviation, sync word, CRC, whitening, hopping/schedule, framing | frequency plan and bandwidth are inside the CC1352R's native 2 Mbps/1 Mbps GFSK capability. **Compatibility is not claimed**: it depends on parameters not public |
| **Hanshow Nebular Plus-266F** | 2402–2480 MHz, GFSK, 157 channels at 0.5 MHz, 20 dB BW 0.558–0.591 MHz [FCC] | same list | the 0.5 MHz grid is programmable; the 20 dB bandwidth suggests a data rate below about 0.5 Mbit/s [H, my inference]. **Compatibility is not claimed** |
| **Pricer** | not RF | — | not applicable (infrared) |

**Statement:** the CC1352R proprietary mode has the *configurable ranges* needed to try to receive and (for owned devices) transmit on both vendors' channel plans. That is a hardware capability statement only. Hanshow and SoluM compatibility is **unknown** until a conducted capture decodes at least one packet from a known tag. This was not demonstrated.

## 3. What was not found or not read

- TRM statements on synthesiser phase noise, lock time, and frequency error budget.
- The override registers needed for non-default CRC/whitening.
- The 48 MHz crystal specification (frequency tolerance, load capacitance, ESR) in SWRS196I.
- SmartRF Studio settings for 2-GFSK at 500 kbps.
- The CC1352R sub-GHz behaviour for unused RF pins.

## 4. Verification plan (all [MEAS], not done)

1. Conducted spectrum capture of a known tag via the U.FL port with the antenna disconnected; record centre frequency, 20 dB BW, deviation, symbol rate.
2. Program the CC1352R with the measured parameters and attempt to decode.
3. Report PER versus level using a calibrated attenuator.
4. Only after a decode: update the compatibility matrix.
