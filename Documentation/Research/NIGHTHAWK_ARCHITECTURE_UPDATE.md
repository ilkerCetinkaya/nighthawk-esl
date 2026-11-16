# NIGHTHAWK Architecture Update

Date: 2026-11-07. Companion docs: `TAGTINKER_TECHNICAL_REVIEW.md`, `ESL_PROTOCOL_RESEARCH_MATRIX.md`, `REUSE_AND_LICENSE_AUDIT.md`. Tags: **[V]** verified in a source, **[S]** stated, **[H]** hypothesis, **[U]** unknown.

## 0. State of the existing design: read this first

- **[V]** `TOOLCHAIN_STATUS.md` (2026-11-07) says NIGHTHAWK **PCB design has not started** and is gated on a KiCad 10 DRC/ERC round trip on the Mac.
- **[V]** The project folder (`PCB_design_claude`) contains only the earlier **GNSS + IMU + ESP32-C3** board (`gnss_board.*`, `gnss-board-design.md`, `docs/notlar.md`). No file in it mentions NIGHTHAWK (the folder-wide search did not finish; the top-level and `docs/` files were read and contain no reference).
- **[U]** The earlier NIGHTHAWK architecture is therefore **not on disk**. This update does not rewrite it. It states constraints that any NIGHTHAWK architecture must satisfy, and flags the places that need İlker's existing decisions (Section 8). Nothing in the GNSS board was modified.

## 1. TagTinker vs NIGHTHAWK

| Aspect | TagTinker | NIGHTHAWK (intended, per brief) |
|---|---|---|
| Purpose | Flipper app to update **IR** ESLs [V] | Broader ESL **research platform**: identify, analyse, test [H from brief] |
| Link types | IR only; README: cannot drive radio ESLs [V] | IR + RF, modular |
| Hardware | Off-the-shelf Flipper Zero (+ optional ESP32-S2 dev board) [V] | Own board, KiCad (not started) [V] |
| Identification | Barcode / NFC decode → type code; NFC cannot tell IR vs RF [V] | Multi-evidence workflow incl. RF/IR observation (Section 4) |
| Receive path | None in files read (transmit only) [V] | Required for research (IR uplink listen, RF survey) |
| Security research | Not a goal; disclaimer forbids misuse [V] | Defensive/owned-device analysis; needs capture, logging, replay-safe tooling |
| Content pipeline | Web image prep + RLE + cloud renderer [V/U] | Reuse the *ideas* (Section 6) |
| Licence | GPL-3.0 [V] | Open decision (audit Section 4.5) |

## 2. What TagTinker does not solve

1. **RF ESL identification and control** (explicit in README).
2. IR-vs-RF determination (NFC step says it cannot).
3. Receive/observation: no IR uplink decoding, no RF sniffing, no capture tooling [V for files read].
4. Protocol verification: sources disagree on PP4 timing; no measurements published [see matrix].
5. Security analysis of any link (key defaults, replay, authentication). Furrtek claims weak/absent IR security for Pricer-type tags [S]; nothing equivalent exists for RF vendors.
6. Tag-family coverage beyond one IR family; the 39-entry profile table is unvalidated here.
7. Timing-robust transmit on a general-purpose OS; it relies on a critical section on a Flipper [V].
8. Test evidence: no test suite or reproducible measurement set seen [U].

## 3. Proposed modular architecture

```
                         ┌───────────────────────────┐
                         │  NIGHTHAWK CORE BOARD     │
                         │  MCU (ESP32-C3 class? H)  │
                         │  USB, power/charger, UI   │
                         │  microSD/log (H)          │
                         │  NFC reader slot (H)      │
                         └───┬────────┬────────┬─────┘
                  expansion A│        │B       │C
                 ┌───────────┘        │        └────────────┐
          ┌──────▼──────┐     ┌───────▼──────┐      ┌───────▼───────┐
          │ IR DAUGHTER │     │ RF MODULE    │      │ SPARE / SDR   │
          │ TX + RX     │     │ SLOT (empty  │      │ bridge/debug  │
          │ (specified, │     │ until tags   │      │ UART/SWD/GPIO │
          │ buildable)  │     │ verified)    │      └───────────────┘
          └─────────────┘     └──────────────┘
```

Principles:

- **Core board owns**: MCU, power, USB, storage, user interface, NFC front-end *or* a connector to one, the expansion connector(s), and timing-critical GPIO routing.
- **Every radio/optical function is a plug-in module** with: power rail(s), SPI (and/or UART/I²C), IRQ, 2–4 GPIO, reset, and an **ID/identification EEPROM or resistor-coded ID** so firmware knows what is attached **[H]**.
- **No transceiver part is selected.** Slot B defines only the electrical interface (3.3 V, SPI, IRQ, GPIO, an RF-quiet ground/keep-out zone, SMA or U.FL option) and leaves the part open.
- Until Slot B is filled, RF research uses an **external SDR / commercial receiver** feeding captures to the host **[H]**; this needs no board decision.
- **Isolation from the earlier GNSS design**: if the GNSS module is part of NIGHTHAWK, its noise rules apply (the earlier design flags 2.4 GHz coexistence and digital noise at 1.5 GHz). Whether GNSS belongs on NIGHTHAWK is **[U]**, a question for İlker.

### 3.1 Decision gate for the RF module (Slot B)

Do not choose an RF part until all are filled from **measured** evidence:

| Needed fact | Source | Status |
|---|---|---|
| Target tag models in hand | İlker | [U] |
| Carrier frequency and channel plan | SDR capture | [U] |
| Modulation, data rate, deviation | capture | [U] |
| Sync word/preamble, CRC, addressing | capture + decode | [U] |
| TX required or RX sufficient | scope decision + legal check | [U] |
| Chip identification (teardown) | photo of IC marking | [U]; Furrtek lists CC2510 for SES-imagotag [S] |

Candidate *classes* only after that (examples of classes, not choices): packet transceiver IC, sub-GHz transceiver, 2.4 GHz GFSK/802.15.4 transceiver, SDR-front-end module.

## 4. ESL identification workflow

```
S0 Visual/label    → barcode (17 chars), vendor, model, photo of back, chip marks
S1 NFC read        → UID, NDEF URI; decode ID/type (hint)          [cannot decide IR/RF]
S2 Optical check   → IR window? photodiode/LED visible? passive IR listen
S3 RF survey       → passive scan near tag over time (2.4 GHz first; sub-GHz if S0 suggests)
S4 Active probe    → ONLY on owned spare tags; IR addressed ping; RF none until module verified
S5 Teardown        → remove cover, identify ASIC/RF chip, antenna, IR parts
S6 Classify        → record link type + confidence + evidence IDs in tag database
```

Decision table:

| Evidence | Conclusion | Confidence |
|---|---|---|
| NFC decodes ID, nothing else | ID/type only | link type **unknown** |
| `nfc.imagotag.com` URL | vendor hint "likely radio" (TagTinker heuristic) | low [H] |
| IR photodiode + LED on PCB, and addressed IR ping gets a response/refresh | **IR** | high if response observed |
| RF IC (e.g. 2.4 GHz SoC) + antenna on PCB, and periodic emission in survey | **RF** | medium; protocol still unknown |
| Both IR parts and RF IC present | **Hybrid, test each separately** | [U] |
| Tag silent on all channels after wake | **Unclassified**; do not guess | – |

Each record stores: tag ID, evidence list with timestamps, raw captures, tool versions, confidence. A conclusion without a raw artifact is marked [H].

## 5. IR daughterboard decision

**Recommendation: yes, build IR as a separate daughterboard.** Reasons:

1. **Isolation.** A 1.25 MHz-class carrier burst driver and LED current pulses are noise sources next to RF receivers (and, if present, the GNSS front-end). Physical separation and a ribbon/connector distance help **[H]**.
2. **Optional.** Not needed for RF-only tags; keeps core cost/size lower.
3. **Mechanical.** The LED/photodiode need a clear line of sight and good aiming; a small board at the edge of the enclosure or on a short cable suits that.
4. **Iteration.** The least-documented parts (LED drive current, uplink receiver) can be revised without respinning the core.
5. **Fits the modular rule** (one connector, ID, own power switch).

IR daughterboard requirements (parameters to verify, not part selections):

| Requirement | Basis | Status |
|---|---|---|
| Wavelength ≈940 nm emitter | Furrtek | [S] |
| Carrier ≈1.25 MHz OOK, symbol timing in µs | Furrtek, PrecIR code | [V]/[S] |
| Driver fast enough for ~MHz switching with short pulses (PrecIR: transistor with no base resistor for max range) | PrecIR README | [S] |
| Optional receive: photodiode + amplifier/demod for ≈1.245 MHz uplink | Furrtek | [S]; needed to *observe* tag replies |
| IrDA/consumer-IR receivers/drivers unusable (carrier too high) | Furrtek page, ESL Blaster shop note, PrecIR FAQ | [S] |
| Timer/peripheral able to produce the carrier and µs symbol timing in the chosen MCU | Datasheet check | [H] (ESP32 family has RMT/LEDC; TRM must be checked) |
| Eye-safety / LED current budget | design calc | [U] |

Interface to core: 3.3 V, one carrier/modulation GPIO (hardware-timer driven), one RX analog or comparator-digital line, enable, ID.

## 6. Reuse plan (concepts only; code reuse blocked on licence decision)

| Module (NIGHTHAWK) | Idea taken from | Own work required |
|---|---|---|
| `transport/ir` | TIM carrier + cycle-timed symbols (TagTinker); serial-framed blaster (PrecIR) | New implementation on MCU peripheral; verify with scope |
| `protocol/pricer_ir` | CRC16 0x8408, frame layout, PLID derivation | Spec-first re-implementation; capture-verify |
| `protocol/…rf_*` | none | Empty until RF measured |
| `profiles` | type-code table | Rebuild from measured tags |
| `imaging` (host tool) | Oklab quantisation, dithering, RLE | Own tool producing neutral 1bpp planes |
| `identify` | NFC decode + honest result classes | Add IR/RF evidence stages |
| `content service` | ESP32/cloud split | Optional |

## 7. Documentation and process updates (done / to do)

- Done: the four documents in `docs/nighthawk/`.
- To do (needs İlker): add decisions to `docs/notlar.md` once Section 8 is answered; add the tag database schema.
- Verification practice: DOM/curl-style checks do not apply here; instead, **scope/logic-analyser captures and SDR captures with raw files saved in the repo**.

## 8. Decisions needed from İlker

1. Where is the original NIGHTHAWK architecture (chat, notes)? Share it so this update can be merged rather than assumed.
2. Does NIGHTHAWK include the GNSS/IMU functions of the existing board, or is it a separate board?
3. Which ESL models do you physically have or plan to buy? (Unblocks RF module.)
4. Licence option for the software: clean-room (a) or GPL-3.0 (b)?
5. Is the goal receive-only research, or also transmit/control of owned tags?

## 9. Next steps (ordered)

1. Pass the KiCad 10 DRC/ERC gate on the Mac (per `TOOLCHAIN_STATUS.md`).
2. Acquire/identify a few spare tags (owned), photograph, record barcodes.
3. Bench: NFC read + visual teardown + passive RF survey with an external SDR.
4. Capture a known IR transmitter's waveform (scope) to settle PP4 timing.
5. Freeze connector pin-out for Slots A/B/C; then schematic.
