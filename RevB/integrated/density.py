from layout import B
CY = {"0402": 1.82*0.92, "0603": 2.96*1.46, "0805": 3.4*1.9, "SOT23-5": 4.10*3.40, "SOT23-6": 4.10*3.40, "SOT23": 4.1*3.4,
      "TSSOP24": 7.70*8.30, "QFN16": 4.26**2, "QFN32": 6.26**2, "QFN48": 8.26**2, "DFN_63802": 3.6*2.6, "L2016": 2.8*2.2,
      "X2520": 3.3*2.8, "X3215": 4.0*2.3, "X3225": 4.0*3.3, "SOT5_DRL": 2.2*1.8, "PTC1206": 4.0*2.3, "VSON8": 3.9**2, "US8": 3.6*3.0,
      "PTS810": 5.70*3.70, "JST_SH4": 7.8*6.56, "SOIC8W": 9.3*5.8, "LED_IR": 3.8*2.8, "PD": 3.0*2.6, "L0805": 3.4*1.9, "TC2030": 8.0*4.0}
P = {
 "RF_SOC": [("CC1352R1F3 VQFN-48", "QFN48", 1), ("48 MHz xtal", "X2520", 1), ("32.768 kHz xtal", "X3215", 1), ("DC/DC 10 uH", "L0805", 1),
            ("decoupling", "0402", 14), ("2.4 GHz balun/match", "0402", 7), ("sub-GHz match/LPF", "0402", 10), ("RF path 0R selects", "0402", 4)],
 "NFC_IC": [("TRF7970A VQFN-32", "QFN32", 1), ("27.12 MHz xtal", "X3225", 1), ("xtal caps", "0402", 2), ("matching C0G", "0603", 8), ("EMC filter L", "0603", 2), ("decoupling", "0402", 6)],
 "IR": [("VSMB10940 LED", "LED_IR", 1), ("VEMD10940F photodiode", "PD", 1), ("OPA356 TIA", "SOT23-5", 1), ("LED MOSFET", "SOT23", 1), ("TIA R/C + bias", "0402", 8), ("LED R", "0603", 1)],
 "UI_T": [("RESET/BOOT PTS810", "PTS810", 2), ("LEDs", "0603", 4), ("LED R", "0402", 4)],
 "DIG1": [("TCA9555 x2", "TSSOP24", 2), ("TPS22918 x3", "SOT23-6", 3), ("caps/pulls", "0402", 16)],
 "DIG2": [("TPS3823", "SOT23-5", 1), ("TPS3431", "VSON8", 1), ("SN74LVC1G74", "US8", 1), ("SN74LVC1G08 x7", "SOT23-5", 7), ("caps/pulls", "0402", 20)],
 "UI_B": [("interlock JST SH 4", "JST_SH4", 1), ("CC1352 cJTAG TC2030 pads", "TC2030", 1)],
 "REG": [("TPS63802", "DFN_63802", 1), ("0.47 uH", "L2016", 1), ("caps", "0805", 2), ("caps", "0603", 2), ("TLV755P x2", "SOT23-5", 2), ("caps/FB", "0402", 6)],
 "CHG": [("BQ24074", "QFN16", 1), ("R", "0402", 5), ("C", "0603", 3)],
 "USB_ESD": [("TPD2E2U06", "SOT5_DRL", 1), ("CC R", "0402", 2), ("PTC", "PTC1206", 1), ("C", "0603", 1), ("C", "0402", 1)],
 "STOR": [("GD25Q32E SOP-8 208mil", "SOIC8W", 1), ("C", "0402", 2), ("pull-ups", "0402", 3), ("SCLK R", "0402", 1)],
}
print("| Block | Area mm^2 | Courtyards mm^2 | Fill |\n|---|---|---|---|")
for k, parts in P.items():
    a = B[k][2] * B[k][3]
    u = sum(CY[p] * n for _, p, n in parts)
    print(f"| {k} | {a:.0f} | {u:.0f} | {u/a*100:.0f} % |")
