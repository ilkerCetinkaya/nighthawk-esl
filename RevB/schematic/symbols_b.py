from sch_helpers import parse

CC1352R = [
    ("1", "RF_P_2_4GHZ", "passive", "L"), ("2", "RF_N_2_4GHZ", "passive", "L"), ("3", "RF_P_SUB_1GHZ", "passive", "L"),
    ("4", "RF_N_SUB_1GHZ", "passive", "L"), ("5", "RX_TX", "passive", "L"), ("6", "X32K_Q1", "passive", "L"),
    ("7", "X32K_Q2", "passive", "L"), ("46", "X48M_N", "passive", "L"), ("47", "X48M_P", "passive", "L"),
    ("35", "RESET_N", "input", "L"), ("24", "JTAG_TMSC", "bidirectional", "L"), ("25", "JTAG_TCKC", "input", "L"),
    ("44", "VDDS", "power_in", "T"), ("13", "VDDS2", "power_in", "T"), ("22", "VDDS3", "power_in", "T"), ("34", "VDDS_DCDC", "power_in", "T"),
    ("45", "VDDR", "power_in", "T"), ("48", "VDDR_RF", "power_in", "T"), ("33", "DCDC_SW", "passive", "T"), ("23", "DCOUPL", "passive", "T"),
    ("49", "EGP", "power_in", "B"),
] + [(str(n), f"DIO_{d}", "bidirectional", "R") for n, d in [
    (8, 3), (9, 4), (10, 5), (11, 6), (12, 7), (14, 8), (15, 9), (16, 10), (17, 11), (18, 12), (19, 13), (20, 14), (21, 15),
    (26, 16), (27, 17), (28, 18), (29, 19), (30, 20), (31, 21), (32, 22), (36, 23), (37, 24), (38, 25), (39, 26), (40, 27),
    (41, 28), (42, 29), (43, 30)]]

TRF7970A = [
    ("2", "VIN", "power_in", "L"), ("16", "VDD_I/O", "power_in", "L"), ("1", "VDD_A", "power_out", "L"), ("3", "VDD_RF", "power_out", "L"),
    ("4", "VDD_PA", "power_in", "L"), ("32", "VDD_X", "power_out", "L"), ("11", "BAND_GAP", "passive", "L"), ("30", "OSC_OUT", "output", "L"),
    ("31", "OSC_IN", "input", "L"), ("28", "EN", "input", "L"), ("25", "EN2", "input", "L"), ("12", "ASK/OOK", "bidirectional", "L"),
    ("5", "TX_OUT", "passive", "R"), ("8", "RX_IN1", "input", "R"), ("9", "RX_IN2", "input", "R"), ("26", "DATA_CLK", "input", "R"),
    ("24", "I/O_7_MOSI", "bidirectional", "R"), ("23", "I/O_6_MISO", "bidirectional", "R"), ("21", "I/O_4_SS", "bidirectional", "R"),
    ("22", "I/O_5", "bidirectional", "R"), ("20", "I/O_3", "bidirectional", "R"), ("19", "I/O_2", "bidirectional", "R"),
    ("18", "I/O_1", "bidirectional", "R"), ("17", "I/O_0", "bidirectional", "R"), ("13", "IRQ", "output", "R"), ("14", "MOD", "bidirectional", "R"),
    ("27", "SYS_CLK", "output", "R"),
    ("6", "VSS_PA", "power_in", "B"), ("7", "VSS_RX", "power_in", "B"), ("10", "VSS", "power_in", "B"), ("15", "VSS_A", "power_in", "B"),
    ("29", "VSS_D", "power_in", "B"), ("33", "PAD", "power_in", "B"),
]

TPS63802 = [
    ("10", "VIN", "power_in", "L"), ("1", "EN", "input", "L"), ("2", "MODE", "input", "L"), ("4", "FB", "input", "L"),
    ("6", "VOUT", "power_out", "R"), ("9", "L1", "passive", "R"), ("7", "L2", "passive", "R"), ("5", "PG", "open_collector", "R"),
    ("3", "AGND", "power_in", "B"), ("8", "GND", "power_in", "B"),
]

JTI = [
    ("9", "RF_P_2.4GHz", "passive", "L"), ("8", "RF_N_2.4GHz", "passive", "L"), ("7", "RF_P_SubGHz", "passive", "L"),
    ("6", "RF_N_SubGHz", "passive", "L"), ("5", "RX_TX", "passive", "L"),
    ("1", "ANT_2.4GHz", "passive", "R"), ("4", "ANT_SubGHz", "passive", "R"),
    ("2", "GND", "passive", "B"), ("3", "GND", "passive", "B"), ("10", "GND", "passive", "B"),
]

AND2 = [("1", "A", "input", "L"), ("2", "B", "input", "L"), ("4", "Y", "output", "R"), ("3", "GND", "power_in", "B"), ("5", "VCC", "power_in", "T")]
TPS22918 = [("1", "VIN", "power_in", "L"), ("3", "ON", "input", "L"), ("2", "GND", "power_in", "B"), ("4", "CT", "passive", "R"),
            ("5", "QOD", "passive", "R"), ("6", "VOUT", "power_out", "R")]
SHIELD = [("1", "GND", "passive", "L")]
SHIELD_COVER = []

CUSTOM = {
    "CC1352R1F3RGZ": ("U", "Package_DFN_QFN:Texas_RGZ0048A_VQFN-48-1EP_7x7mm_P0.5mm_EP5.15x5.15mm", CC1352R, 17.78),
    "TRF7970ARHB": ("U", "Package_DFN_QFN:Texas_RHB0032E_VQFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm", TRF7970A, 17.78),
    "TPS63802DLA": ("U", "NH_REVB:TPS63802DLA_VSON-10_3x2mm", TPS63802, 12.7),
    "JTI0900PC15A0036": ("U", "NH_REVB:Johanson_0900PC15A0036_2.0x1.25mm", JTI, 15.24),
    "SN74LVC1G08": ("U", "Package_TO_SOT_SMD:SOT-23-5", AND2, 12.7),
    "TPS22918": ("U", "Package_TO_SOT_SMD:SOT-23-6", TPS22918, 12.7),
    "SHIELD_FRAME": ("SH", "RF_Shielding:Wuerth_36103205_20x20mm", SHIELD, 10.16),
    "SHIELD_COVER": ("SH", "", SHIELD_COVER, 10.16),
}


def custom_symbol(name):
    refp, fpid, pins, w = CUSTOM[name]
    sides = {s: [p for p in pins if p[3] == s] for s in "LRTB"}
    h = max(len(sides["L"]), len(sides["R"]), 2) * 2.54 + 2.54
    w = max(w, max(len(sides["T"]), len(sides["B"]), 1) * 2.54 * 3)
    lines = [f'(symbol "NH_LOCAL:{name}" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)',
             f'(property "Reference" "{refp}" (at 0 {h / 2 + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))',
             f'(property "Value" "{name}" (at 0 {-h / 2 - 5.08:.2f} 0) (effects (font (size 1.27 1.27))))',
             f'(property "Footprint" "{fpid}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
             '(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
             f'(symbol "{name}_1_1"',
             f'(rectangle (start {-w / 2:.2f} {h / 2:.2f}) (end {w / 2:.2f} {-h / 2:.2f}) (stroke (width 0.254) (type default)) (fill (type background)))']

    def pin(typ, x, y, ang, num, pname):
        lines.append(f'(pin {typ} line (at {x:.2f} {y:.2f} {ang}) (length 5.08) (name "{pname}" (effects (font (size 1.27 1.27)))) (number "{num}" (effects (font (size 1.27 1.27)))))')

    for i, (num, pname, typ, _) in enumerate(sides["L"]):
        pin(typ, -w / 2 - 5.08, h / 2 - 2.54 - i * 2.54, 0, num, pname)
    for i, (num, pname, typ, _) in enumerate(sides["R"]):
        pin(typ, w / 2 + 5.08, h / 2 - 2.54 - i * 2.54, 180, num, pname)
    n = len(sides["T"])
    for i, (num, pname, typ, _) in enumerate(sides["T"]):
        pin(typ, (i - (n - 1) / 2) * 7.62, h / 2 + 5.08, 270, num, pname)
    n = len(sides["B"])
    for i, (num, pname, typ, _) in enumerate(sides["B"]):
        pin(typ, (i - (n - 1) / 2) * 7.62, -h / 2 - 5.08, 90, num, pname)
    lines.append(")")
    lines.append(")")
    return parse("\n".join(lines))
