# TagTinker Technical Review (for NIGHTHAWK)

Date: 2026-11-07. Status: desk review of public sources. **No hardware was built, flashed or tested; no tag was transmitted to.**

## 0. How to read this document

Every claim carries one tag:

| Tag | Meaning |
|---|---|
| **[V]** | Verified: read directly in a source file/page during this review (source named) |
| **[S]** | Stated by a project's README or article but not independently checked (e.g. cited external pages, author opinions) |
| **[H]** | Hypothesis / inference. Must be tested before design decisions rely on it |
| **[U]** | Unknown / not read |

Sources read: TagTinker `README.md`, `LICENSE`, `Makefile`, `ir/tagtinker_ir.c`, `protocol/tagtinker_proto.{c,h}`, `nfc/tagtinker_nfc.c`, `web-image-prep/index.html`, `shared/tt_wifi_proto_fap.h`, directory listings. PrecIR: README, LICENSE, `tools_python/*.py`, `hardware/ir_tx_serial/ir_tx_serial.c`, directory listings. Furrtek: the single page `furrtek.org/?a=esl`.
**Not read [U]:** `tagtinker_app.c`, `scenes/`, `views/`, `wifi/*.c`, `esp32-wifi-fw/main/*.c`, `esp32-wifi-fw/shared/tt_wifi_proto.h`, `cloud-plugins/`, NFC poller, FAP-side BMP reader, PrecIR ESL Blaster firmware FW01–FW03S, PriceHax Android source, VB6 tool, and every external page the READMEs link to (Hanshow, VUSION, TagTinker issue #51).

## 1. What TagTinker is

- **[V]** A Flipper Zero application (FAP) that transmits **infrared only**, through the Flipper's built-in IR LED, to infrared ESLs. README: it works with IR ESLs whose type code is in the app's profile table.
- **[V]** README states it "has no way to drive ESLs that are updated over radio, whatever their barcode or NFC tag says."
- **[V]** Credits furrtek's ESL research and PrecIR as the reference implementation; credits `7h30th3r0n3` for NFC decoding.
- **[V]** The README says protocol is "simple enough to drive from other cheap microcontroller hardware, such as an ESP32 and an IR LED", but the repo contains only the Flipper implementation.

## 2. Architecture (as read)

| Module | Path | Role | Status |
|---|---|---|---|
| IR transmitter | `ir/tagtinker_ir.c` | Carrier + symbol timing | [V] read |
| Protocol | `protocol/tagtinker_proto.c/.h` | Profile table, CRC16, frame builders, image payload encoders | [V] read |
| NFC | `nfc/tagtinker_nfc.c` | NDEF URI extraction, 17-char ID decode | [V] read |
| Web image prep | `web-image-prep/index.html` | Browser-side image → 1bpp BMP (mono or mono+accent) | [V] read |
| App/UI | `tagtinker_app.c`, `scenes/`, `views/` | Flipper UI | [U] |
| Wi-Fi glue | `wifi/`, `esp32-wifi-fw/`, `cloud-plugins/` | ESP32-S2 board + cloud rendering worker | [U] mostly |

Clean layering worth copying conceptually: **transport (IR) → protocol (frames/CRC) → payload encoding (image) → UI**, with the protocol header carrying `SPDX-License-Identifier: GPL-3.0-only` **[V]**.

## 3. Hardware interface

- **[V]** TIM1 CH3N drives the Flipper's IR LED carrier; DWT cycle counter (`CYCCNT`) times symbols; each frame is sent inside a critical section (`FURI_CRITICAL_ENTER`). Comment: "~1-2ms per frame".
- **[V]** `CARRIER_ARR = 51-1`, `CARRIER_CCR = 25`, prescaler 0. Source comments reference 64 MHz.
- **[H]** If TIM1 runs at 64 MHz the carrier is ≈1.25 MHz (64/51). Consistent with Furrtek's stated 1.25 MHz carrier, but TIM1's clock was not confirmed from the source.
- **[V]** Modulation: OOK of the carrier; symbol = burst (`PP4_BURST_CYCLES 2581` ≈ 40.3 µs @64 MHz) + gap from a 4-entry table.
- **[V]** Gap table `{3871, 15483, 7741, 11612}` cycles ≈ 60 / 242 / 121 / 181 µs, indexed by the raw 2-bit value, low pair first.
- **[V] Discrepancy:** source comments label index 1 as "symbol 3 ~242 µs" and index 3 as "symbol 1 ~181 µs", but the code indexes by raw value. Code and comments disagree; the code is what runs.
- **[V]** Only **PP4** is implemented in the IR file read. PP16 (the faster mode in PrecIR/Furrtek) is not in `tagtinker_ir.c`. **[H]** TagTinker is therefore slower than PrecIR's ESL Blaster FW02+ for large images.
- **[V]** Repeat handling: `len` 1–255, `repeats & 0x7FFF`, inter-repeat gap `delay * 32000` cycles (comment: 500 µs/unit).
- **[U]** Physical Flipper pin number for the IR LED (only the name `gpio_infrared_tx` is in source).

## 4. Protocol layer

- **[V]** Frame: `[proto][PLID×4][cmd]...[CRC16 lo][CRC16 hi]`; proto `0x85` = dot-matrix, `0x84` = segment; max frame 96 bytes; image data 20 bytes/frame.
- **[V]** CRC16: reflected, polynomial `0x8408`, **initial value written as `0x8408`** (not 0/0xFFFF). PrecIR's `pr.py` does the same, and Furrtek's page states "Both the initial value and the polynomial are 0x8408". Three independent statements agree.
- **[V]** PLID from the 17-char barcode: `id = (chars[2..6] as 5-digit) << 16 | chars[7..11]`, bytes LSB first. PrecIR `get_plid()` computes the same layout.
- **[V]** Frames present: ping (`0x97`), wake (`0x17`), refresh (MCU cmd `0x01`), image parameters (MCU cmd `0x05`), image data (MCU cmd `0x20`), broadcast page (`0x06`), broadcast debug.
- **[V]** Type code = barcode characters 13–16; 39-entry profile table (width/height/kind/colour/model name). Some entries duplicate model names (1317/1322, 1353/1354).
- **[V]** The README says type 1626 (SmartTAG Color 2.6) accepts only up to 24 KB; the enforcing code was **[U]**.

## 5. Image-processing concepts (what is actually there)

- **[V] Web tool pipeline:** compose (fit/fill/stretch, rotate, flip) → tone/colour (sRGB→linear, saturation, contrast, brightness; ACES-like curve strength 0.35 for accent profiles) → unsharp → **Oklab nearest-colour quantisation** against {white, black, accent} → dither (Floyd–Steinberg serpentine default, Atkinson, Bayer 8×8, threshold) → 1bpp BMP (accent profiles = two stacked 1-bit planes).
- **[V]** Firmware payload: raw 1bpp (MSB-first) or **RLE** with Elias-gamma-style run codes (first pixel value 1 bit, then runs; alternate implicitly); `Auto` picks RLE only if smaller; zero-padded to 160-bit (20-byte) multiples.
- **[V]** Colour tags: second plane; `color_clear` fills it with 1s.
- **[V]** PrecIR `img2dm.py` uses the same RLE idea but a simpler threshold (luma `0.21r+0.72g+0.07b < 0.5`), no dithering. **[V]** Observation from reading (not run): its final run is only stored if `run_count > 1`, so a trailing single-pixel run may be dropped.
- **[U]** Bit polarity on real tags (1 = ink?) is not confirmed in the code read.

## 6. NFC feature: what it does and does not do

- **[V]** Reads NTAG/Ultralight pages; checks the capability container (`0xE1`), finds NDEF TLV `0x03`, requires a short, well-known URI record (`'U'`), takes the last path segment (10 chars from a custom base64-like alphabet), derives an 18-digit value, checks `barcode[1]=='4'` and a checksum.
- **[V]** The checksum adds **ASCII values** (lower-case folded) of 16 characters, mod 10, and compares with character 17. Furrtek's page gives the same ASCII-sum-mod-10 rule for the printed barcode.
- **[V]** Result classes: Unreadable / Unrecognized / Decoded / ImagotagLink. `ImagotagLink` = host `nfc.imagotag.com`; UI shows "Likely radio tag".
- **[V]** README: the scan "cannot sense whether the display listens for infrared or radio." It yields an ID/model hint only.
- **[H]** The imagotag-link → "radio" heuristic is a *guess about vendor behaviour*; not validated here.
- **[V]** Furrtek: the NFC sticker on an IR (Pricer-type) tag is **not electrically connected** to the board, so NFC presence tells you nothing about the display link.

## 7. ESP32-S2 Wi-Fi board

- **[V]** README: a Flipper WiFi Dev Board (ESP32-S2) unlocks "live, network-rendered tag designs" (crypto cards, weather tiles, identicons); new plugins live on a cloud worker (Cloudflare, TypeScript). Firmware: ESP-IDF v5.2, target esp32s2, talks to `CONFIG_TT_CLOUD_URL`.
- **[U]** Flipper↔ESP32 transport, wire protocol, pins, worker API, default URL.
- **[H]** The ESP32 is a *content source*, not an RF ESL interface; it adds no radio-ESL capability. For NIGHTHAWK the useful idea is the separation "renderer/content service ↔ transmitter".

## 8. Limitations / what is dangerous

- **[V]** README warns: removing the battery or full discharge makes the tag lose all programming and become unresponsive. Matches Furrtek (**[V]** no flash found on die; firmware in volatile RAM). **Implication:** research on *spare, owned* tags only; never experiment with unknown frames on a tag you cannot afford to brick.
- **[V]** README disclaimer: prohibited for use on retail displays / hardware you do not legally own.
- **[V]** Source-first, no released `.fap`; `make lint` advisory, not a CI gate.
- **[V]** IR is line-of-sight; PrecIR FAQ: no known broadcast for display updates.

## 9. Reusable engineering concepts for NIGHTHAWK (ideas, not code)

1. Strict layering: transport / frame builder / payload encoder / UI.
2. Hardware-timed carrier + cycle-counter symbol timing → on ESP32-class MCUs use a timer/RMT peripheral **[H, must be checked against the chip's TRM]**.
3. Data-driven **profile table** keyed by type code (size, kind, colour, model).
4. Auto raw/RLE selection; padding to the frame payload size.
5. Perceptual (Oklab) quantisation + selectable dither as a *host-side* tool, outputting a neutral intermediate (1bpp planes), separate from firmware.
6. Honest result classes in the NFC step ("Decoded / Unrecognized / Unreadable") and a message that states what the check cannot prove.
7. Content-service/transmitter split (the ESP32/cloud idea).

## 10. Recommendations

- Treat TagTinker as a **reference for the IR path only**. Do not assume any of its profile entries, timings or commands are correct for a given tag until captured/measured on the NIGHTHAWK bench.
- Resolve the PP4 timing disagreement (Section 3 here and the matrix) by **oscilloscope/logic-analyser capture of a known-good transmitter**, not by choosing a source.
