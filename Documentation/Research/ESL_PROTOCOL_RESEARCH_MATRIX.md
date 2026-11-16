# ESL Protocol Research Matrix

Date: 2026-11-07. Desk research only. **Nothing here was measured by NIGHTHAWK.** Confidence tags: **[V]** read in a source (named), **[S]** stated by a source, not checked, **[H]** hypothesis, **[U]** unknown / not documented.

Primary sources: Furrtek ESL page (`furrtek.org/?a=esl`, brand table + Pricer IR sections), PrecIR repo (code), TagTinker repo (code + README).

## 1. Vendor / family matrix

| Vendor / family | Display link | Detail stated | Source | Confidence | NIGHTHAWK relevance |
|---|---|---|---|---|---|
| **Pricer** (IR) | Infrared 940 nm, PPM, 1.25 MHz carrier; uplink carrier 1.245 MHz | Bidirectional; "no encryption whatsoever, 16-bit key with default value" | Furrtek | [S] (author's analysis) | IR module target #1 |
| Pricer-type graphic + segment tags (PrecIR/TagTinker targets) | IR, PP4 and PP16 | Frame `[VER 0x84/0x85][PLID][CMD][...][KEY][CRC16]`; code reproduces it | PrecIR, TagTinker code | [V] (code) | IR module |
| **SES-imagotag / VUSION** | Proprietary 2.4 GHz radio; TI CC2510; hardware AES-128 on chip | Bidirectional; security "mentioned in brochures", whether used unknown | Furrtek | [S] | RF target (class: 2.4 GHz); TagTinker README adds BLE announced 2023 [S] |
| **Hanshow** | "Proprietary 2.4GHz radio" (Furrtek); Stellar Pro-266 / Nebular Pro-346 "documented as RF devices working at 2402–2480 MHz" (TagTinker README citing Hanshow pages) | Security unknown | Furrtek; TagTinker README | [S] both; cited pages **not fetched** | RF target (class: 2.4 GHz) |
| Altierre | Proprietary 2.4 GHz | Bidirectional / security unknown | Furrtek | [S] | RF |
| Samsung | Zigbee 2.4 GHz | Bidirectional yes | Furrtek | [S] | RF (standard stack, 802.15.4 class) [H] |
| Digi (Teraoka Seiko) | "Radio" | TODO on page | Furrtek | [S] | unknown |
| NCR | Proprietary UHF radio | very old, TODO | Furrtek | [S] | unknown |
| ZKong | "Radio" | Asia | Furrtek | [S] | unknown |
| DisplayData | Proprietary 920 MHz | bidirectional unknown | Furrtek | [S] | RF (sub-GHz) |
| Store Electronic Systems (legacy) | Proprietary LF 38 kHz, radiating cable | one-way | Furrtek | [S] | out of scope [H] |
| Generic Alibaba systems | "Probably generic 2.4GHz or BLE" | stated as probable | Furrtek | [H] (author's guess) | RF/BLE |

**Gap [V]:** the Furrtek page has *no* RF protocol section: no modulation, data rate, CRC, packet or ID format for any RF vendor.

## 2. IR physical layer (documented)

| Parameter | Furrtek | PrecIR (code) | TagTinker (code) | Status |
|---|---|---|---|---|
| Wavelength | 940 nm | LED part [U] | Flipper LED, wavelength [U] | [S] |
| Carrier | 1.25 MHz square; ESL passband ≈ ±10 kHz | 1.25 MHz (ATtiny2313 @10 MHz, OC0A, "10/2/(3+1)") | ≈1.25 MHz **[H]** (51 ticks of an unconfirmed 64 MHz clock) | agree |
| Uplink carrier | 1.245 MHz (TRX section) | not implemented | not implemented | [S] |
| PP4 burst | 40 µs ("1.3t") | ≈39 µs | ≈40.3 µs | agree |
| PP4 symbol timing | base t=30.52 µs; symbols 2t/4t/6t/8t = 61/122/183/244 µs (Gray: 00,01,11,10) | burst 39 µs + pause {56, 237, 117, 178} µs for values {0,1,2,3} | burst 40.3 + gap {60, 242, 121, 181} µs for values {0,1,2,3} | **Unresolved:** the three do not map onto each other in an obvious way (symbol ordering of values 1 vs 2 differs, and Furrtek's totals do not equal burst+PrecIR gap). Needs a scope capture. |
| PP4 bit order | LSB pair first | LSB pair first | LSB pair first | agree |
| PP4 data rate | public docs "10 kbps"; author's calc avg 13.1 kbps | – | – | [S] |
| PP16 | t=4 µs, burst 21 µs, 16 symbols 27–147 µs; header `00 00 00 40`; "38 kbps" public / 52 kbps author avg | PP16 header `00 00 00 40` prepended; ESL Blaster FW02+ | **not in files read** | header agrees; timing table only in Furrtek [S] |
| CRC | CRC16 poly 0x8408, init 0x8408, over VER onward | same | same | [V] ×3 agree |
| Segment tags + PP16 | – | "None of the segment-based ESLs tested support PP16" | – | [S] |

## 3. Frame commands seen (IR family)

| Command | Meaning | Furrtek | PrecIR | TagTinker |
|---|---|---|---|---|
| `0x17` (proto 0x85) | wake/ping | yes (loop up to ~4 s) | yes (400 repeats) | wake `0x17`, plus ping `0x97` |
| `0x34` + sub-cmd `0x05` | image parameters | yes | yes | yes |
| `0x34` + `0x20` | image data, 20 B/frame | yes | yes | yes |
| `0x34` + `0x01` | refresh/final | yes | yes | yes |
| `0x3A`/`0xBA` (proto 0x84) | segment update | yes (`0x3A`) | `0xBA` | – (not read) |
| `0xAB` (proto 0x84) | segment page change | yes | – | – |
| `0x06` | broadcast page | – | – | yes |
| Image types | 0 raw, 2 RLE; B/W/red = two blocks; 4-colour unconfirmed | 0/2 | 0/2 | 0/2 |

Unknowns stated by Furrtek [S]: purpose of one wake-up byte; meaning of `00 00 09 00` in segment update; per-model segment mapping; 4-colour format; whether broadcast returns the ID.

## 4. Identification inputs (how an ESL declares itself)

| Input | What it can tell you | What it cannot tell you | Status |
|---|---|---|---|
| Printed 17-char barcode (Code128) | PLID, type code (chars 13–16) | link technology | [V] decode rules in Furrtek, PrecIR, TagTinker |
| NFC NDEF URI (NTAG/Ultralight) | ID/model hint; imagotag host hint | IR vs RF (README says so explicitly) | [V] |
| NFC UID / chip type | tag-IC family | display link | [H] |
| Passive 2.4 GHz survey | presence of periodic emissions near tag | which tag emitted, protocol | [H] |
| Optical (photodiode) survey | IR uplink bursts, carrier ≈1.245 MHz | – | [H] derived from Furrtek uplink statement |
| Teardown | chips (CC2510 for SES-imagotag per Furrtek); IR photodiode + LED present? | – | [S] |

## 5. Research questions that remain open (must be answered by measurement)

1. Which exact tags will NIGHTHAWK own/test? (**Hardware choices are blocked on this.**)
2. For each: IR present (photodiode window/LED)? RF chip marking? Antenna type?
3. RF carrier frequency, channel plan, modulation, data rate, preamble/sync, CRC, addressing: **no public values accepted without capture**.
4. Does the radio family use encryption in practice? (Furrtek: unknown for Hanshow/SES-imagotag.)
5. PP4 symbol timing ambiguity (Section 2).
6. Hanshow documented frequency range (2402–2480 MHz, per TagTinker README citing Hanshow) — verify from the cited manufacturer pages or by measurement.
