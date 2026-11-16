import collections
import design_b as d
import passive_data as pd
from bom_b import pkg, price

sel = [p for p in d.PARTS if p["ref"] in d.GENERIC_REFS]
groups = collections.OrderedDict()
for p in sel:
    groups.setdefault((p["lcsc"], p["dnp"]), []).append(p)
lines = []
A = lines.append
A("| Refs | Value | Pkg | Manufacturer / MPN | LCSC | Stock | JLC class | 1st-tier / bulk USD | Datasheet |")
A("|---|---|---|---|---|---|---|---|---|")
for (code, dnp), ps in groups.items():
    p = ps[0]
    dd = pd.DATA[code]
    lad = dd[4]
    A(f"| {', '.join(x['ref'] for x in ps)}{' (DNP)' if dnp else ''} | {p['value']} | {pkg(p['fp'])} | {dd[1]} {dd[0]} | {code} | {dd[2]:,} | {'Basic' if dd[3] else 'Extended'} | {lad[0][1]} @{lad[0][0]}+ / {lad[-1][1]} @{lad[-1][0]:,}+ | [pdf]({dd[5]}) |")
table = "\n".join(lines)
pop = [p for p in sel if not p["dnp"]]
by_code = collections.Counter(p["lcsc"] for p in pop)
tot = {n: sum(price(c, q * n) * q * n for c, q in by_code.items()) for n in (1, 5, 50, 500)}
ext = sorted({p["lcsc"] for p in pop if not pd.DATA[p["lcsc"]][3]})
extdnp = sorted({p["lcsc"] for p in sel if p["dnp"] and not pd.DATA[p["lcsc"]][3]} - set(ext))
cost_lines = ["| Boards | Passive parts (68 lines, populated only) | Per board | Extended-part loading fee (upper bound, $3.07 x %d) |" % len(ext), "|---|---|---|---|"]
for n in (1, 5, 50, 500):
    cost_lines.append(f"| {n} | US${tot[n]:.2f} | US${tot[n] / n:.3f} | US${3.07 * len(ext):.2f} per order |")
cost = "\n".join(cost_lines)

doc = f"""# REV B passive component selection (68 lines: the 67 generic passives plus the buck-boost inductor)

Date: 2026-11-08. Scope: only part numbers, packages and footprint fields changed. No net, value or architecture change (netlist compared before/after: identical, 175 nets). No PCB layout touched. Source data: LCSC pages read 2026-11-08 (stock, price ladder, datasheet link); datasheet numbers read from the PDFs where stated. Labels: [LCSC] listing, [DS] datasheet, [CALC], [A] assumption, [U] not verified.

Files: `schematic/BOM_REVB_schematic.csv` (full BOM with LCSC, stock, class, datasheet, prices, 5/50/500-board cost, RF flag), `schematic/RF_CRITICAL_PASSIVES.csv`, `schematic/passive_data.py` (selection data), `schematic/gen_passive_report.py` (this report's tables).

## 1. Result
- All 68 lines have an exact MPN and an LCSC number; nothing was left generic. 54 parts are populated, 14 are DNP tuning/option parts.
- 31 unique part numbers are populated: 7 JLC Basic, 24 Extended. Eight more Extended numbers appear only if the DNP parts are fitted.
- Cost of the 68 passive lines: about US$0.84 per board (1-5 boards), US$0.73 at 50 boards, US$0.68 at 500 [LCSC ladder prices]. The JLCPCB loading fee for Extended parts (US$3.07 per unique Extended part on Economic assembly, Basic and "Preferred" parts free; see sources) is about US$74 per order for these 24 parts and dominates the part cost for small runs. Whether any of my Extended parts count as "Preferred" (fee-free) was not checked.
- Package decisions: resistors with <= 31 mW moved 0603 to 0402 (area on an 80 x 50 board); three power-limited resistors moved up (section 5); L1 moved to a 1008 inductor. Existing REV A verified 0603 parts (10k, 1k, 4.7k, 5.1k, 100n, 1u, 10u, 100p 0603, 0R 0603) were not touched.

## 2. Selection table (grouped by part number)
{table}

## 3. Changes against the schematic (documented engineering reasons)
| Item | Before | After | Reason |
|---|---|---|---|
| 20 ohm LED resistor R43 | 0805 | **1206** 250 mW (C17955) | 93 mW average [CALC, `ir_driver_calcs_output.txt`]; a 125 mW 0805 would run at 74 % load |
| 680 ohm tank damping R42 | 0603 | **0805** 125 mW (C17798) | estimated 40-90 mW at 0.38 uH coil and 50-100 mW TX [CALC/A]; 0603 100 mW too tight |
| Buck-boost inductor L1 | Coilcraft XFL4015-471MEC (C18221164, US$4.27) | **Murata DFE252012F-R47M** (C703140, US$0.15), footprint 1008 | cost; datasheet formula (section 6) needs Isat >= 1.7 A for 0.8 A load, DFE252012F is rated 4.9 A [LCSC listing] |
| DC/DC inductor L2 10 uH | 10 uH 0805, no part chosen (candidate TDK MLZ2012M100WT000 rejected: Isat 150 mA) | **cjiang FTC201212S100MBCA** (C53436344, 1.4 A / 1.2 A, 500 mohm) | TDK part saturates at 150 mA [DS]; the CC1352R DC/DC peak current is not given in the datasheet I read, so margin was chosen |
| 10 nF NFC decoupling | 0603 | 0402 X7R 50 V (Basic) | area, same performance at 3.3 V |
| 22 ohm, 100, 6.8k, 100k, 91k, 562k, 68k, 3.09k, 1.78k, 2.94k | 0603 | 0402 1 % 62.5 mW | dissipation below 1 mW each (section 5) |
| 22 ohm gate resistor R44 | (UNI-ROYAL 0402 22R is a Basic part but stock 0) | Yageo RC0402FR-0722RL (C114765) | stock |
Electrical values are unchanged in every case.

## 4. Capacitor verification (dielectric, voltage, tolerance, bias)
| Part | Used for | Dielectric / V / tol | Applied V | DC-bias effect | Verdict |
|---|---|---|---|---|---|
| CL21A226MPQNNNE 22u 0805 (C29277) x3 | 3V6 output (2), VDDR (1) | X5R 10 V +-20 % | 3.6 V (36 %); VDDR 1.68 V (17 %) | X5R 0805 22 uF at 36 % of rating typically keeps 55-70 % [A, Samsung curves not read] = 12-15 uF each. TPS63802 needs **>= 7 uF effective** with a single 22 uF recommended for Vo <= 3.6 V [DS 8.3, 10.2.2.3]; two parts give margin. VDDR: CC1352R datasheet requires "22 uF" (no effective value given); with +-20 % and bias about 17 uF effective | OK for 3V6; VDDR marginal but TI-consistent, verify with TI reference [U] |
| CL10B225KP8NNNC 2.2u 0603 (C100082) x5 | TRF7970A VIN, VDD_A, VDD_RF, VDD_X, BG | X7R 10 V +-10 % | 3.3-3.4 V (33 %); BG about 1.6 V | X7R 0603 2.2 uF: typically -25 to -35 % at 33 % of rating, about 1.5 uF effective [A]. TRF7970A datasheet requires bypass caps "per reference schematic" (2.2 uF + 10 nF) with no effective value | OK, moves to 0805 only if TRF EVM data shows noise [U] |
| CL05B103KB5NNNC 10n 0402 (C15195) x4 | TRF7970A HF bypass | X7R 50 V +-10 % | 3.4 V (7 %) | under 10 % | OK |
| GRM1555C1H101JA01D 100p (C77177) x3 | IPC C41/C51 (868 MHz-2.4 GHz), NFC C21 | **C0G 50 V +-5 %** | up to a few V (RX_TX bias); NFC node about 2-3 Vrms | none (C0G) | OK; SRF of the 0402 100 pF (about 1.5-2 GHz range) is **[U]**: C41 is a decoupling and C51 a series DC block at 868 MHz, so SRF must be checked in Murata SimSurfing before layout |
| CL05C... C0G 12p/15p/10p/27p/68p/220p/330p/680p | crystal loads, NFC matching | C0G 50 V +-5 % | NFC tank peak about 11 V (est. [CALC/A], 100 mW into R_parallel about 580 ohm) | none | OK; 330 pF carries about 0.3 A pk circulating current [CALC/A], within 0402 C0G capability but ESR should be checked at 13.56 MHz [U] |
| GRM1555C1H122JA01D 1.2n, GRM1555C1H152JA01D 1.5n (Murata) | NFC series and divider | C0G 50 V +-5 % | series 3 nF carries about 0.2 A RMS | none | OK; only Murata parts had stock |
| GJM1555C1H1R0BB01D 1p, GJM1555C1H3R9BB01D 3.9p, GJM1555C1HR30BB01D 0.3p (DNP) | IFA / 868 MHz antenna tuning | C0G 50 V, **+-0.1 pF** (high-Q GJM) | RF | none | OK as tuning footprints; Johanson specifies its own 500R07 parts for 868 MHz [DS], listed as DigiKey alternatives |
| GRM1555C1H1R5BA01D 1.5p (C76957) | TIA feedback Cf | C0G 50 V +-0.1 pF | up to 3.3 V | none | OK; tolerance matters: 0.1 pF is 7 % of 1.5 pF, TIA bandwidth about 10.6 MHz +-4 % [CALC] |
| 0402CG1R0C500NT 1p, 0402CG2R0C500NT 2p (FH) | NFC trim (DNP) | C0G 50 V +-0.25 pF | 13.56 MHz | none | OK, low-frequency trim only |
Existing verified REV A caps (10u/1u/100n 0603): TPS63802 CIN 2 x 10 uF at 4.4 V (44 %) keeps about 40-50 % = 8-10 uF effective vs required 4-5 uF [DS 8.3, A]; BQ24074 OUT/BAT 10 uF within the 4.7-47 uF range [DS]; OPA356 bypass: datasheet recommends 10 uF minimum, present as C18 (3V3_A) [DS].

## 5. Resistor power and current check
| Refs | Value | Part rating | Dissipation | Load |
|---|---|---|---|---|
| R14 3.09k, R15 1.78k, R16 68k, R17 2.94k | BQ24074 ILIM/ISET/TMR/ITERM | 62.5 mW | < 1 mW (pin voltages about 1-2 V across kohm values) | < 2 % |
| R20, R23, R45, R51 100k | pullups, AC bias | 62.5 mW | 0.13 mW at 3.6 V | 0.2 % |
| R21 562k, R22 91k | TPS63802 FB divider | 62.5 mW | 20 uW | 0.03 % |
| R49 6.8k | VREF divider | 62.5 mW | 0.3 mW | 0.5 % |
| R47 100 | photodiode bias filter | 62.5 mW | 0.1 mW at 1 mA | 0.2 % |
| R44 22 | AO3400A gate | 62.5 mW | about 8 mW (21 mW gate charge power x 22/58) | 13 % |
| R43 20 | IR LED limit | 1206 250 mW | 93 mW | 37 % |
| R42 680 | NFC tank damping | 0805 125 mW | 40-90 mW est. | 32-72 % [A: depends on coil Q and TX power; check on the bench] |
| 0R x9 | RF path links, NFC links | 0402 0 ohm | negligible (rated about 1 A [A]) | - |
Resistor tolerance 1 % throughout; set-point resistors (FB divider, ILIM, ISET, ITERM, TMR) keep the exact values computed from datasheet formulas. Low-stock items: 3.09k (C11460, 800 pcs), 1.78k (4,600), 2.94k (8,500), 562k (9,100): enough for prototypes, check before larger runs. E24 alternatives that are Basic parts were not checked.

## 6. Inductor verification
| Ref | Part | Check |
|---|---|---|
| L1 0.47 uH | Murata DFE252012F-R47M (C703140), +-20 %, DCR 23 mohm, Isat 4.9 A / 7.4 A [LCSC listing] | TPS63802 inductor-current formula: IL,max = Iout/(eta(1-D)) + Vin*D/(2 L f). At Vin 3.0 V, Vout 3.6 V (D = 0.167), 0.8 A load, 2.1 MHz, L = 0.37 uH (datasheet minimum effective) and eta 0.9: 1.07 + 0.32 = 1.39 A; x1.2 = 1.67 A [CALC]. At 2 A load: 3.0 A x1.2 = 3.6 A, still below 4.9 A. Stock only 1,090 pieces (Murata DFE201610E-R47M is an alternate via LCSC other suppliers); datasheet list names Coilcraft XFL4015 and Toko DFE201612E, so this part is an equivalent not on TI's list [U: effective inductance versus bias not read] |
| L2 10 uH | cjiang FTC201212S100MBCA (C53436344): 1.4 A Isat, 1.2 A Itemp, 500 mohm [LCSC] | CC1352R DC/DC current not stated in the datasheet text I read; at most a few tens of mA in the standard modes [A]. TDK MLZ2012M100WT000 rejected (Isat 150 mA [DS]). TI's DC/DC inductor tolerance/DCR requirement not read [U] |
| L5 150 nH (NFC L1) | APV AHW1608C-R15GTF (C56333414): Q 28, SRF 990 MHz, DCR 0.92 ohm, Irms 280 mA [DS] | estimated TX current about 0.17-0.19 A RMS [CALC/A, 4 ohm source into a matched load]; 0.92 ohm DCR dissipates about 30 mW (loss about 20 % of 140 mW). Murata LQW18ANR15J00D rejected (160 mA, 1.5 ohm); Coilank HWF1608KR15DS (1 A, 0.15 ohm) is better but stock is 0. **Re-select when stock returns** |
| L6 330 nH (NFC L2) | Coilank HWF1608KR33DS (C54534874): SRF 725 MHz, 0.32 ohm, Irms 600 mA, Q 12 at 7.9 MHz [DS] | 50 ohm-side current about 50-65 mA; loss about 1 mW. Tolerance +-10 % (TI figure does not state a tolerance [U]); VNA tuning required |
| L3 1 nH (DNP) | Murata LQG15HS1N0S02D (C18222): 300 mA, 70 mohm, Q 8 at 100 MHz, SRF 10 GHz [DS] | IFA tuning only; Q is low at 2.4 GHz. Murata LQP15MN1N0B02D (high-Q) has 0 stock at LCSC; buy from DigiKey if populated |
| L4 18 nH (DNP) | Murata LQW15AN18NG0ZD (C7519796): +-2 %, Q 25 at 250 MHz, SRF 4.5 GHz, 0.27 ohm, 370 mA [DS] | Johanson specifies L-07C18NJV6T (DigiKey); this is a similar wirewound alternative, **not identical**: retune with a VNA |

## 7. Decoupling placement requirements (from the datasheets)
| IC | Datasheet statement | Schematic status |
|---|---|---|
| TPS63802 | place input and output capacitors as close as possible to VIN/VOUT and PGND; short wide traces; separate ground nodes for power and control, joined near a ground pin; FB trace away from L1/L2 [DS 10.2.2, 12.1] | CIN 2 x 10 uF, COUT 2 x 22 uF present |
| BQ24074 | IN and OUT capacitors as close as possible with short traces to the thermal pad; BAT 4.7-47 uF, OUT 4.7-47 uF [DS] | IN 1 uF + 10 uF (VBUS_F), OUT 10 uF, BAT 10 uF |
| TLV755P | input and output capacitors as close as possible; CIN >= 1 uF, COUT >= 1 uF (effective > 0.47 uF) [DS] | 10 uF each |
| OPA356 | bypass at the V+ pin, short signal traces; 10 uF minimum ceramic bypass [DS] | 100 nF at pin plus 10 uF C18 on 3V3_A |
| TLV3501 | bypass capacitors close to the supply pins [DS] | 100 nF |
| TRF7970A | external bypass on VIN, VDD_A, VDD_RF, VDD_X per the reference schematic; short SPI lines, solid ground, isolate RF lines [DS 7.1] | 2.2 uF + 10 nF on each |
| CC1352R | 22 uF on the DC/DC output (VDDR); VDDS pins all supplied; per-pin placement rules are in TI's PCB design note, not in the datasheet text read [U] | 100 nF per VDDS pin, 22 uF + 2 x 100 nF on VDDR, 1 uF DCOUPL |
These are layout rules for the PCB phase; nothing was placed.

## 8. Duplicate values sharing one part number (BOM reduction)
0R 0402 x9 (C17168); 100k x4 (C25741); 100p C0G x3 (C77177, one line for IPC and NFC); 22u 0805 x3 (C29277, 3V6 and VDDR); 2.2u x5 (C100082); 10n x4 (C15195); 12p x4 DNP (C26406; the four crystal load pads); 15p x2; 1.2n x2; 1.5n x2; 680p x2. Merges that would change a value were rejected (for example 91k to 100k would give 3.31 V instead of 3.59 V on the 3.6 V rail).

## 9. Cost estimate
{cost}
Per-line prices are in the BOM CSV. Prices are LCSC tier prices (not JLCPCB assembly quotes); the REV A verified 0603 lines are not included.

## 10. Parts that cannot be sourced economically through LCSC
- Johanson IPC 0900PC15A0036001E: 0 LCSC stock (DigiKey about CHF 0.73).
- Würth shield frames 36103205S x2 and covers 36003200S x2: not found on LCSC (DigiKey/Farnell).
- TLV3501AIDBVR comparator: not found on LCSC (DigiKey).
- Johanson 868 MHz matching parts (500R07S3R9BV4T, 500R07S0R3BV4T, L-07C18NJV6T) if the exact Johanson parts are wanted (DigiKey); LCSC Murata equivalents are listed.
- Coilank HWF1608KR15DS (better NFC L1) 0 stock; Murata LQP15MN1N0B02D 0 stock.
- Single-supplier or low-stock items to watch: 3.09k (800), L1 DFE252012F (1,090).

## 11. RF-critical passives (strict specification control)
See `RF_CRITICAL_PASSIVES.csv`. Rule: no substitution without VNA or Murata SimSurfing/TI reference check. The list: IPC C41 and C51 (C34, C35); IFA tuning C36, L3, link resistors R26-R31; 868 MHz matching C37, L4, C38; the whole NFC network (L5, L6, C51-C61 except decoupling, R42, C63, C49, C50, R39-R41); crystal load capacitors C30-C33, C49, C50; TIA Cf C69. Requirements: C0G only, +-5 % (0.1 pF below 3 pF), 50 V, 0402 from one supplier lot per build; inductors with Q, SRF and DCR from the datasheet as in section 6; no X7R/X5R in these nets.

## 12. ERC after the change
kicad-cli ERC, all severities: **0 errors, 1 warning**, identical to before (`lib_symbol_mismatch` for AO3400A). Netlist before/after: identical (175 nets, same pins); 20 footprint-field changes listed in section 3 (the 19 resistor/capacitor package moves and L1), no value changes. Report: `ERC_REPORT.rpt`.

## 13. Open items
1. Samsung/Murata DC-bias curves were not read; bias numbers are typical values [A]. Verify with Samsung EPS / Murata SimSurfing before layout.
2. SRF/ESR of the RF-critical 0402 capacitors not checked [U].
3. NFC L1 should be replaced by the 1 A, 0.15 ohm Coilank part when it is back in stock.
4. TI reference-design values for the CC1352R passives (L2 DC/DC inductor, DCOUPL) remain unconfirmed.
5. Which of the 24 Extended parts are fee-free "Preferred" parts on JLCPCB was not checked.

Sources: JLCPCB fee rules https://jlcpcb.com/help/article/pcb-assembly-faqs , https://jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype ; LCSC product pages read 2026-11-08; TPS63802 SLVSEU9D sections 8.3, 10.2.2, 12.1; BQ24074, OPA356, TLV755P, TLV3501, TRF7970A and CC1352R datasheets in the research folder.
"""
open("../REV_B_PASSIVE_SELECTION.md", "w").write(doc)
print(len(doc))
