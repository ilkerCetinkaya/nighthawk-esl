import json, math, itertools

BW, BH = 80.0, 40.0
ANT_NOTCH = (0.0, 7.0, 6.0, 40.0)
ESP_ANT = (0.0, 22.0, 6.0, 40.0)
CABLE_NOTCH = (38.0, 0.0, 42.0, 3.0)
CABLE_KO = (37.0, 0.0, 43.0, 4.0)
NOTCH_R = 1.0

KEEPOUTS = {
    "ESP_CLEAR": ANT_NOTCH,
    "ANT24_KO": (63.8, 33.3, 80.0, 40.0),
    "SUB_KO": (69.0, 13.0, 80.0, 26.0),
    "CABLE_KO": CABLE_KO,
}

B = {
 "ESP32":    (6.0, 22.0, 14.0, 18.0, "T", "ESP32-C3-WROOM-02-N4 (host MCU, USB, supervisor)"),
 "USB":      (72.7, 0.0, 7.3, 9.4, "TB", "USB-C TYPE-C-31-M-12 (THT shell legs)"),
 "USB_ESD":  (65.0, 0.0, 7.2, 6.0, "T", "TPD2E2U06, CC 5.1k x2, PTC, VBUS caps"),
 "CHG":      (56.0, 0.0, 8.5, 7.5, "T", "BQ24074 linear charger + power path"),
 "REG":      (44.0, 0.0, 12.0, 10.0, "B", "TPS63802 buck-boost + 0.47uH, 2x TLV755P; shield can"),
 "STOR":     (8.0, 0.5, 12.0, 8.0, "T", "GD25Q32ESIGR 4 MB SPI NOR"),
 "IR":       (22.0, 0.5, 12.0, 8.0, "T", "Pricer IR: VSMB10940 LED + MOSFET, VEMD10940F + OPA356 TIA"),
 "BATT_CONN":(34.5, 4.0, 9.2, 10.2, "T", "JST PH 2-pin SMD S2B-PH-SM4-TB (battery)"),
 "NFC_IC":   (21.0, 9.5, 13.0, 16.5, "T", "TRF7970A + 27.12 MHz xtal + matching/EMC filter; shield can"),
 "COIL":     (21.0, 27.0, 24.0, 12.0, "T", "NFC coil window 24x12, no copper L2-L4, nothing either side"),
 "RF_SOC":   (50.5, 20.0, 17.5, 12.0, "T", "CC1352R1F3 + 48 MHz/32 kHz xtals + 2.4 GHz and sub-GHz matching; shield can"),
 "UFL24":    (68.5, 27.0, 3.5, 3.5, "T", "U.FL conducted test port, 2.4 GHz (0R select)"),
 "UFLSUB":   (68.5, 9.0, 3.5, 3.5, "T", "U.FL conducted test port, sub-GHz (0R select)"),
 "ANT24":    (64.8, 34.3, 15.2, 5.7, "T", "2.4 GHz PCB IFA per TI AN043 (15.2 x 5.7)"),
 "SUBANT":   (77.5, 16.0, 2.0, 7.0, "T", "868 MHz chip antenna 0868AT43A0020 (DNP until a sub-GHz target is verified)"),
 "UI_T":     (36.0, 14.7, 14.0, 9.5, "T", "RESET/BOOT buttons, 4 status LEDs"),
 "DIG1":     (21.0, 12.0, 21.0, 14.0, "B", "TCA9555 x2 (0x20, 0x21), TPS22918 x3 load switches, pull-ups"),
 "DIG2":     (6.0, 0.0, 14.0, 21.5, "B", "TPS3823, TPS3431, SN74LVC1G74, SN74LVC1G08 x7 (interlock)"),
 "UI_B":     (57.0, 0.5, 15.0, 8.0, "B", "interlock JST SH 4, CC1352 cJTAG pads"),
}
METAL = ["USB", "BATT_CONN", "RF_SOC", "NFC_IC", "REG", "COIL", "UFL24", "UFLSUB", "UI_T"]
ANTENNAS = {"ANT24": "ANT24_KO", "SUBANT": "SUB_KO"}

def R(k):
    x, y, w, h = B[k][:4]
    return (x, y, x + w, y + h)

def ov(a, b, m=0.0):
    return not (a[2] + m <= b[0] or b[2] + m <= a[0] or a[3] + m <= b[1] or b[3] + m <= a[1])

def dist(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)

def sides(k):
    return B[k][4]

def check():
    v = []
    for k in B:
        r = R(k)
        if r[0] < 0 or r[1] < 0 or r[2] > BW or r[3] > BH:
            v.append(f"{k}: outside the 80 x 40 outline")
        if k not in ("ANT24",) and ov(r, ANT_NOTCH):
            v.append(f"{k}: in the ESP32 antenna notch / clearance")
        if ov(r, CABLE_NOTCH):
            v.append(f"{k}: in the cable notch")
    for a, b in itertools.combinations(B, 2):
        if set(sides(a)) & set(sides(b)) and ov(R(a), R(b), 0.5):
            v.append(f"{a}/{b}: overlap (0.5 mm spacing)")
    for ko_name, ko in KEEPOUTS.items():
        if ko_name == "ESP_CLEAR":
            continue
        for k in B:
            if ANTENNAS.get(k) == ko_name:
                continue
            if ov(R(k), ko, 0.0):
                v.append(f"{k}: inside keepout {ko_name}")
    coil = R("COIL")
    for k in B:
        if k in ("COIL",):
            continue
        if ov(R(k), coil, 0.5):
            v.append(f"{k}: inside the NFC coil window (+0.5)")
    for k in B:
        if "B" in sides(k) and ov(R(k), R("ESP32")):
            v.append(f"{k}: bottom part under the ESP32 module")
        if "B" in sides(k) and ov(R(k), R("RF_SOC")):
            v.append(f"{k}: bottom part under the RF section (no digital beneath RF)")
    for k in METAL:
        if dist(R(k), ESP_ANT) < 15.0:
            v.append(f"{k}: metal within 15 mm of the ESP32 antenna ({dist(R(k), ESP_ANT):.1f})")
    for k in ("RF_SOC", "NFC_IC", "COIL", "IR"):
        if dist(R("REG"), R(k)) < 10.0:
            v.append(f"REG (switching) within 10 mm of {k} ({dist(R('REG'), R(k)):.1f})")
    for ko in ("ANT24_KO", "SUB_KO"):
        if dist(R("REG"), KEEPOUTS[ko]) < 10.0:
            v.append(f"REG within 10 mm of {ko}")
    if dist(R("RF_SOC"), R("ANT24")) > 6.0:
        v.append("RF_SOC farther than 6 mm from the 2.4 GHz antenna feed")
    if dist(R("RF_SOC"), KEEPOUTS["SUB_KO"]) > 6.0:
        v.append("RF_SOC farther than 6 mm from the sub-GHz antenna area")
    for u in ("UFL24", "UFLSUB"):
        if dist(R(u), R("RF_SOC")) > 12.0:
            v.append(f"{u} farther than 12 mm from RF_SOC")
    if dist(R("NFC_IC"), R("COIL")) > 6.0:
        v.append("NFC_IC farther than 6 mm from the coil")
    if dist(R("USB_ESD"), R("USB")) > 3.0:
        v.append("USB_ESD farther than 3 mm from USB")
    if dist(R("CHG"), R("USB")) > 12.0:
        v.append("CHG farther than 12 mm from USB")
    if dist(R("REG"), R("CHG")) > 30.0:
        v.append("REG farther than 30 mm from CHG")
    if dist(R("STOR"), R("ESP32")) > 30.0:
        v.append("STOR farther than 30 mm from ESP32")
    if dist(R("BATT_CONN"), CABLE_KO) > 3.0:
        v.append("battery connector farther than 3 mm from the cable notch")
    return v

def metrics():
    m = {}
    m["ESP antenna to 2.4 GHz IFA (edge to edge, mm)"] = round(dist(ESP_ANT, R("ANT24")), 1)
    m["ESP antenna to sub-GHz antenna (mm)"] = round(dist(ESP_ANT, R("SUBANT")), 1)
    m["2.4 GHz IFA to sub-GHz antenna (mm)"] = round(dist(R("ANT24"), R("SUBANT")), 1)
    m["NFC coil to 2.4 GHz IFA (mm)"] = round(dist(R("COIL"), R("ANT24")), 1)
    m["NFC coil to ESP antenna (mm)"] = round(dist(R("COIL"), ESP_ANT), 1)
    m["REG to RF_SOC (mm)"] = round(dist(R("REG"), R("RF_SOC")), 1)
    m["REG to IR receiver (mm)"] = round(dist(R("REG"), R("IR")), 1)
    m["USB to sub-GHz keepout (mm)"] = round(dist(R("USB"), KEEPOUTS["SUB_KO"]), 1)
    return m

if __name__ == "__main__":
    v = check()
    print(len(v), "violations")
    for x in v:
        print("  -", x)
    for k, val in metrics().items():
        print(f"  {k}: {val}")
    json.dump({k: dict(x=b[0], y=b[1], w=b[2], h=b[3], side=b[4], content=b[5]) for k, b in B.items()}, open("placement.json", "w"), indent=1)
