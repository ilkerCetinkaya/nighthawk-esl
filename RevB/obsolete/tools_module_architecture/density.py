import json
CY = {"0402": 1.82*0.92, "0603": 2.96*1.46, "0805": 3.4*1.9, "SOT23-5": 4.10*3.40, "SOT23-6": 4.10*3.40, "TSSOP24": 7.70*8.30,
      "QFN16_3x3": 4.26*4.26, "QFN32_5x5": 6.26*6.26, "DFN_TPS63802": 3.6*2.6, "L2016": 2.8*2.2, "XTAL3225": 4.0*3.3,
      "SOT5_DRL": 2.2*1.8, "PTC1206": 4.0*2.3, "VSON8_3x3": 3.9*3.9, "US8": 3.6*3.0, "PTS810": 5.70*3.70, "JST_SH4": 7.8*6.56, "LGA8_6x8": 7.0*9.0, "SOIC8_208": 9.3*5.8}
BLOCKS = {
 "USB_ESD": [("TPD2E2U06 DRL", "SOT5_DRL", 1), ("CC 5.1k", "0402", 2), ("PTC (1206, assumed)", "PTC1206", 1), ("VBUS 10uF", "0603", 1), ("VBUS 100nF", "0402", 1)],
 "CHG": [("BQ24074 VQFN-16", "QFN16_3x3", 1), ("ISET/ILIM/ITERM/TMR/TS R", "0402", 5), ("IN/OUT/BAT caps", "0603", 3)],
 "REG": [("TPS63802 DLA", "DFN_TPS63802", 1), ("0.47uH DFE201612E", "L2016", 1), ("Cin 10uF", "0603", 2), ("Cout 22uF", "0805", 2), ("FB divider", "0402", 2), ("TLV755P", "SOT23-5", 2), ("LDO caps 1uF", "0402", 4)],
 "NFC_IC": [("TRF7970A VQFN-32", "QFN32_5x5", 1), ("27.12 MHz xtal", "XTAL3225", 1), ("xtal caps", "0402", 2), ("matching C/L (C0G)", "0603", 8), ("EMC filter L", "0603", 2), ("decoupling", "0402", 5)],
 "DIG1": [("TCA9555 TSSOP-24", "TSSOP24", 2), ("decoupling", "0402", 2), ("INT pull-ups", "0402", 2), ("I2C pull-ups", "0402", 2), ("RFx_EN / PWR_ON pull-downs", "0402", 4), ("TPS22918 load switch", "SOT23-6", 2), ("load switch caps", "0402", 4)],
 "DIG2": [("TPS3823", "SOT23-5", 1), ("TPS3431 VSON-8", "VSON8_3x3", 1), ("SN74LVC1G74 US8", "US8", 1), ("SN74LVC1G08", "SOT23-5", 6), ("decoupling", "0402", 9), ("pull-ups/downs", "0402", 10), ("EN RC", "0402", 2)],
 "STOR": [("GD25Q32ESIGR SOP-8 208mil", "SOIC8_208", 1), ("VCC 100nF + 1uF", "0402", 2), ("pull-ups 10k CS#/WP#/HOLD#", "0402", 3), ("SCLK series R", "0402", 1)],
 "UI": [("buttons PTS810", "PTS810", 2), ("LEDs", "0603", 4), ("LED resistors", "0402", 4), ("interlock connector JST SH 4", "JST_SH4", 1)],
}
sol = json.load(open("manual_d.json"))
print("| Block | Block area mm^2 | Sum of courtyards mm^2 | Utilisation |")
print("|---|---|---|---|")
for k, parts in BLOCKS.items():
    s = sol[k]
    area = s["w"] * s["h"]
    used = sum(CY[p] * n for _, p, n in parts)
    print(f"| {k} | {area:.0f} | {used:.0f} | {used/area*100:.0f} % |")
