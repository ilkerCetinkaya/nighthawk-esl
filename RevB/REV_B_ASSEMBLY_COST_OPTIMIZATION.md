# REV B assembly cost optimization (JLCPCB/LCSC)

Date: 2026-11-08. Data: LCSC product pages read 2026-11-08 (stock, price ladder); JLCPCB fee rules from its help pages (sources at the end). Script: `schematic/cost_opt.py`, output `integrated/cost_opt_output.txt`. Excluded: PCB fabrication, JLCPCB base assembly/setup fees, stencil, shipping, duties, DigiKey parts, any RF validation cost. Prices are LCSC tier prices at the total quantity (qty per board x boards); JLCPCB assembly part prices can differ.

## 1. Correction of the earlier fee estimate
The earlier "24 Extended parts, about US$74" covered only the 67 generic passives. For the **whole board** there are 67 unique LCSC lines populated (DNP excluded). Of these 17 are Basic (current resistor values, 10 pF, 10 nF, 100 nF, 1 uF, 2.2 uF, 10 uF, 22 uF); the ICs, connectors, crystals, diodes and most RF passives are Extended, or were not individually checked and are **counted as Extended (upper bound)**. Before this stage: 53 Extended numbers (US$162.7 per order at US$3.07); after the swaps below: 50 (US$153.5). Per JLCPCB's current rules Basic and "Preferred Extended" parts carry no fee on Economic assembly; which of my ICs are Preferred was not checked, so the real fee can only be lower.

## 2. Applied Basic substitutions (no electrical change beyond the stated)
| Before | After | Why it is safe |
|---|---|---|
| 24 x 100 nF 0603 Yageo CC0603KRX7R7BB104 (C108079, Extended) | Samsung CL05B104KO5NNNC 0402 (C1525, **Basic**, 3.5 M in stock) | same value, X7R, 16 V; supply decoupling only; also saves area |
| 5 x 2.2 uF 0603 X7R 10 V CL10B225KP8NNNC (C100082, Extended) | Samsung CL10A225KO8NNNC (C23630, **Basic**, X5R 16 V) | 16 V rating means less DC-bias loss at 3.3 V than the 10 V part |
| 3 x 22 uF 0805 X5R 10 V CL21A226MPQNNNE (C29277, Extended) | Samsung CL10A226MQ8NRNC 0603 (C59461, **Basic**, 6.3 V, 716 k in stock) | 22 uF 6.3 V 0603 is the class TI lists for the TPS63802 output (SLVSEU9D table 10-3); effective capacitance at 3.6 V is lower (about 10 uF each, [A]), still above the 7 uF minimum with two parts; for VDDR (1.68 V) the effective value is lower than with the 0805 part: verify against the TI CC1352R reference [U] |
Net result: 3 fewer Extended numbers, 32 parts moved to Basic, part cost slightly lower.

## 3. Substitutions considered and NOT applied (they change a value or touch RF)
| Part | Alternative | Why not applied |
|---|---|---|
| 6.8k (C25917, Ext) | 10k Basic | changes VREF from 1.96 V to 1.65 V (TIA headroom) |
| 91k, 562k (TPS63802 FB) | E24 Basic values | would move the 3.6 V rail (91k -> 100k gives 3.31 V) |
| 3.09k, 1.78k, 2.94k, 68k (BQ24074) | 3.0k, 1.8k, 3.0k, 68k | changes input limit 0.50 -> 0.52 A, charge 0.50 -> 0.49 A, termination 50 -> 51 mA; allowed if the user accepts it, and if a Basic part exists at that value (not checked) |
| all RF/NFC C0G capacitors and RF inductors | Basic generics | RF-critical, strict control (see `RF_CRITICAL_PASSIVES.csv`); never changed for fee reasons |
| 22 ohm gate resistor (C114765, Ext) | UNI-ROYAL 0402 22 ohm C25092 (Basic) | stock 0 today; switch when restocked |

## 4. Parts not on LCSC (cannot be priced here)
IPC Johanson 0900PC15A0036001E (DigiKey about CHF 0.73), Wuerth shield frames 36103205S x2 and covers 36003200S x2 (DigiKey/Farnell, price not read), TLV3501AIDBVR (price not read). DNP RF parts (Johanson 868 MHz match parts, antenna, U.FL) are not in the order.

## 5. Manual assembly candidates (hand-solder, no JLCPCB Extended line)
Large 0603-1206 parts that are easy to hand-solder: the four LED lines (3 unique Extended), the headers J6/J7 (through-hole), PTC F1 and the two ferrite beads, the four tactile switches. Shield covers (all) are manual by nature; shield frames can be hand-reflowed or assembled by JLCPCB only if supplied as consigned parts. IPC (0.5 mm pitch, 10 terminals, 2 x 1.25 mm) and TLV3501 (SOT-23-6) can be hand-soldered but the IPC needs hot-air and care; the ground vias Johanson requires must stay under the part.

## 6. Parts suitable for consignment
IPC, shield frames and TLV3501 (no LCSC stock). JLCPCB terms read: accepted with a JLC part number or engineer review; loose-part fee quoted at US$0.142 per piece; overseas consignment adds import VAT and a 2 % handling fee (minimum US$10); agent fee US$85 (1-50 part numbers) on one page and US$45/85 on another: confirm before shipping. For 1-5 boards the fixed fees exceed the benefit: hand-soldering is cheaper. From about 50 boards consignment of the 4 SMT pieces (400 pieces at 100 boards, about US$57 loose fee) becomes reasonable, plus the fixed fees.

## 7. Cost comparison (assembly parts + Extended loading fee only; per order and per board)
| Boards | Before swaps (53 Ext) | After Basic swaps (50 Ext) | After swaps + hand-solder 4 groups of Section 5 (43 Ext) |
|---|---|---|---|
| 1 | US$188.02 (188.02/board) | US$178.45 | US$155.30 |
| 5 | US$287.85 (57.57/board) | US$276.82 (55.36/board) | US$247.03 (49.41/board) |
| 50 | US$1,138.24 (22.76/board) | US$1,116.23 (22.32/board) | US$1,032.63 (20.65/board) |
| 100 | US$1,944.49 (19.44/board) | US$1,910.11 (19.10/board) | US$1,767.45 (17.67/board) |
Composition at 1 board: parts about US$25 (CC1352R US$5.61, BQ24074 US$2.14, TRF7970A US$2.95, ESP32 module US$3.32, TPS63802 US$0.92 ...) plus the fee. **For 1-5 boards the Extended loading fee is 85 % of the assembly-parts cost**; the realistic way to cut it for prototypes is to have JLCPCB assemble only the parts that need it (ICs, small RF parts) and hand-place the rest, or to accept the fee. For 100 boards the fee is under 8 %.
Not included: DigiKey parts, JLCPCB setup fee, PCB.

## 8. Rules followed
No RF specification was relaxed; no netlist change; no value change (Section 2 swaps keep the value). Risks: the 22 uF and 2.2 uF swaps depend on typical DC-bias behaviour [A]; fee classes of non-passive lines are an upper bound.

Sources: https://jlcpcb.com/help/article/pcb-assembly-faqs , https://jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype , https://jlcpcb.com/help/article/consignment-part-terms-conditions .
