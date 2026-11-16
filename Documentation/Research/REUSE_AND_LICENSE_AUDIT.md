# Reuse and License Audit

Date: 2026-11-07. **This is an engineering risk review, not legal advice.** Have a lawyer confirm before distributing anything.

## 1. Inventory

| Source | License | Evidence | Copyright holder | Notes |
|---|---|---|---|---|
| TagTinker (`i12bp8/TagTinker`) | GPL-3.0 | README: "GNU General Public License v3.0"; `LICENSE` = GPLv3 text; `protocol/tagtinker_proto.h` has `SPDX-License-Identifier: GPL-3.0-only` | **[U]** `LICENSE` has only the FSF template line; no holder named in files read | Other files read have no header. "GPL-3.0-only" in one header: do not assume "or later" |
| PrecIR (`furrtek/PrecIR`) | GPL-3.0 | `LICENSE` = standard GPLv3; GitHub shows GPL-3.0; headers "furrtek - furrtek.org, See LICENSE" | **[U]** not stated in LICENSE; source headers name furrtek (2018/2019) | Covers software **and** hardware design files in the repo (applicability of GPL to hardware files is less settled **[H]**) |
| Furrtek ESL article | **No licence or usage statement found** | page read | the author | Default: all rights reserved for the text/figures. Facts and measurements are not copyrightable; the expression is |
| Furrtek-cited patent WO0209322 | n/a | cited on page | – | A patent is a separate issue from copyright; implementation of a patented method is not cleared by GPL or by this review **[U]** |
| TagTinker dependencies (ufbt, Flipper SDK, ESP-IDF 5.2, Node, wrangler) | **[U]** not checked | Makefile/README | – | Matter only if NIGHTHAWK adopts them |
| Flipper-specific code | tied to Flipper SDK | – | – | Not portable to ESP32 anyway |

## 2. What GPL-3.0 means for NIGHTHAWK

- **Copying or adapting code** (even translating C→another language, or porting a function) creates a derivative work. If NIGHTHAWK firmware/software is then **conveyed** (distributed, shipped with hardware, published), the **entire combined work** must be licensed GPL-3.0, with corresponding source offered.
- Private, never-distributed internal use does not trigger the source obligation (GPLv3 §2 allows private modification and use), but any later sale of boards with firmware, or publication, does. Because the plan is a future web agency, assume distribution will happen.
- Linking with code that has an incompatible licence (proprietary SDK blobs, non-GPL-compatible licences) is a problem. ESP-IDF is Apache-2.0 (my recollection, **[U]** not checked in this review), generally GPL-3.0-compatible.
- GPLv3 includes a patent licence grant from contributors and "anti-tivoization" terms for consumer products; relevant only if NIGHTHAWK ships as a consumer product.
- Two different GPL-3.0 repos can be combined with each other, but the result must be GPL-3.0. TagTinker's own header says "GPL-3.0-only".

## 3. What can be reused, by risk

| Item | Reuse mode | Risk | Recommendation |
|---|---|---|---|
| Protocol **facts** (frame layout, CRC parameters, PLID derivation, command bytes, timings as *observed values*) | Re-implement from the documented facts, then **verify by capture** | Low (facts / functional interfaces). Verify no verbatim table copying | OK, after independent verification |
| Furrtek page text/diagrams | Cite and link; don't copy | Medium if copied | Link only |
| Algorithms (RLE with Elias-gamma runs, Oklab quantisation, dithering) | Write own implementation from the general technique | Low | OK; Floyd–Steinberg, Atkinson, Bayer, Oklab are public techniques |
| `tagtinker_ir.c`, `tagtinker_proto.c`, `img2dm.py`, `pr.py`, `ir_tx_serial.c` source | Verbatim or close adaptation | **High → forces GPL-3.0 on NIGHTHAWK distribution** | Do **not** copy. Read for understanding only |
| Profile table (39 type codes with models/sizes) | Data copy | Medium: a compilation of facts, but selection/arrangement may be protected **[H]**; entries also contain duplicates and **unverified** names | Do not import wholesale. Rebuild a table from tags NIGHTHAWK actually measures; cite upstream as leads |
| `web-image-prep/index.html` | Copy | High (GPL) | Write own tool |
| PrecIR `hardware/` (schematics, enclosure, firmware) | Copy/derive | High; hardware-licence ambiguity | Design own IR daughterboard from requirements |
| ESP32-S2 / cloud worker idea | Concept | None | Free to adopt the idea |

## 4. Clean-room policy for NIGHTHAWK (recommended)

1. **Spec first.** Write a NIGHTHAWK-owned protocol spec from the Furrtek description and from our own captures. The spec states values, not code.
2. **Separation.** The person who implements should work from the spec and measurements; avoid having upstream source open while writing. For a one-person project, record that code was written from the spec (a dated line in `docs/notlar.md`).
3. **Verify against hardware**, not against upstream code. Where upstream sources disagree (PP4 timing), our capture decides.
4. **Attribution without copying:** list TagTinker, PrecIR and Furrtek in a `CREDITS` file as research references.
5. **Licence choice (open decision for İlker):**
   - (a) Clean-room, NIGHTHAWK under a licence of your choosing (including proprietary), or
   - (b) Adopt GPL-3.0 for NIGHTHAWK software, which allows direct reuse of TagTinker/PrecIR code with attribution and compliance.
   The architecture works with either; only the reuse table above changes.
6. Hardware files (KiCad) written by us are ours; choose a hardware licence deliberately before publishing.
7. If code is ever copied: keep original notices, add the modification notice, keep the GPL text, record the upstream commit hash.

## 5. Use-and-law considerations (non-copyright)

- Both projects restrict use to hardware you own (TagTinker README disclaimer **[V]**). NIGHTHAWK documentation should say the same and the tool should refuse bulk/broadcast modes on foreign tags by design. Testing on shop displays you do not own is unauthorised access in many jurisdictions **[H]**.
- Bricking risk (volatile firmware, **[V]** README + Furrtek): label bench tags as consumable.
- RF transmission is regulated (band, power, duty cycle). Passive receive hardware has far fewer constraints than transmit hardware; the RF module should be receive-only until legal bench conditions are confirmed **[H]**.
- Patent WO0209322 cited by Furrtek: unreviewed.

## 6. Open items

- Confirm copyright holder identities for TagTinker and PrecIR (not stated in files read).
- Check dependency licences before adopting any of them.
- Decide licence option (a) or (b) in §4.5.
