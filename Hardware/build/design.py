BOARD_W = 80.0
BOARD_H = 80.0
BOARD_CORNER = 2.0
HOLES = [(3.5, 3.5), (76.5, 3.5), (3.5, 76.5), (76.5, 76.5)]
RF_WIDTH = 0.36

SHEETS = [
    "01_MCU", "02_USB_C", "03_POWER", "04_RF_INTERFACE", "05_RF_MONITOR", "06_RF_EXPANSION_1",
    "07_RF_EXPANSION_2", "08_HARDWARE_INTERLOCK", "09_MICROSD", "10_DEBUG", "11_STATUS_LEDS",
]

FP = {
    "R": "Resistor_SMD:R_0603_1608Metric",
    "C": "Capacitor_SMD:C_0603_1608Metric",
    "L": "Inductor_SMD:L_0603_1608Metric",
    "LED": "LED_SMD:LED_0603_1608Metric",
    "FUSE": "Fuse:Fuse_1812_4532Metric",
    "SOT5": "Package_TO_SOT_SMD:SOT-23-5",
    "SOT6": "Package_TO_SOT_SMD:SOT-23-6",
    "TSSOP24": "Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm",
    "SW": "Button_Switch_SMD:SW_SPST_PTS810",
    "HDR4": "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
    "JST15": "Connector_JST:JST_SH_SM15B-SRSS-TB_1x15-1MP_P1.00mm_Horizontal",
    "SMA": "Connector_Coaxial:SMA_Samtec_SMA-J-P-H-ST-EM1_EdgeMount",
    "SD": "Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5",
    "ESP": "RF_Module:ESP32-C3-WROOM-02",
    "USBC": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
    "TP": "TestPoint:TestPoint_Pad_D1.5mm",
}

VAL = {
    "0R": ("0R", "C21189", "UNI-ROYAL", "0603WAF0000T5E", "0 ohm 0603 resistor"),
    "1k": ("1k", "C21190", "UNI-ROYAL", "0603WAF1001T5E", "1 kohm 1% 0603 resistor"),
    "4.7k": ("4.7k", "C23162", "UNI-ROYAL", "0603WAF4701T5E", "4.7 kohm 1% 0603 resistor"),
    "5.1k": ("5.1k", "C23186", "UNI-ROYAL", "0603WAF5101T5E", "5.1 kohm 1% 0603 resistor"),
    "10k": ("10k", "C25804", "UNI-ROYAL", "0603WAF1002T5E", "10 kohm 1% 0603 resistor"),
    "100n": ("100n", "C108079", "YAGEO", "CC0603KRX7R7BB104", "100 nF 16 V X7R 0603"),
    "1u": ("1u", "C15849", "Samsung Electro-Mechanics", "CL10A105KB8NNNC", "1 uF 0603 ceramic"),
    "10u": ("10u", "C19702", "Samsung Electro-Mechanics", "CL10A106KP8NNNC", "10 uF 10 V 0603 ceramic"),
    "100p": ("100p", "C14858", "Samsung Electro-Mechanics", "CL10C101JB8NNNC", "100 pF 50 V C0G 0603"),
}

PARTS = []
_counters = {}


def _add(ref, fp, value, nets, sheet, lcsc="", mfr="", mpn="", desc="", pos=None, rot=0, region=None, dnp=False, side="F", ds=""):
    PARTS.append({
        "ref": ref, "fp": fp, "value": value, "nets": nets, "sheet": sheet, "lcsc": lcsc, "mfr": mfr, "mpn": mpn,
        "desc": desc, "pos": pos, "rot": rot, "region": region, "dnp": dnp, "side": side, "ds": ds,
    })


def _next(prefix):
    _counters[prefix] = _counters.get(prefix, 0) + 1
    return f"{prefix}{_counters[prefix]}"


def R(value, a, b, sheet, region, pos=None, rot=0, dnp=False, note=""):
    v = VAL[value]
    ref = _next("R")
    _add(ref, FP["R"], v[0] if not dnp else (note or v[0]), {"1": a, "2": b}, sheet, "" if dnp else v[1], "" if dnp else v[2], "" if dnp else v[3], v[4], pos, rot, region, dnp)
    return ref


def C(value, a, b, sheet, region, pos=None, rot=0):
    v = VAL[value]
    ref = _next("C")
    _add(ref, FP["C"], v[0], {"1": a, "2": b}, sheet, v[1], v[2], v[3], v[4], pos, rot, region)
    return ref


def TP(net, sheet, region, pos=None):
    ref = _next("TP")
    _add(ref, FP["TP"], f"TP_{net}", {"1": net}, sheet, "", "", "", "Test point pad 1.5 mm", pos, 0, region)
    return ref


def LED(color, k, a, sheet, region):
    table = {
        "red": ("C2286", "KENTO", "KT-0603R"),
        "green": ("C51933293", "Guiguang light", "GL0603UG01"),
        "white": ("C51933297", "Guiguang light", "GL0603UW01"),
    }
    l, m, p = table[color]
    ref = _next("D")
    _add(ref, FP["LED"], color.upper(), {"1": k, "2": a}, sheet, l, m, p, f"LED 0603 {color}", None, 0, region)
    return ref


def FB(a, b, sheet, region):
    ref = _next("FB")
    _add(ref, FP["L"], "600R@100MHz", {"1": a, "2": b}, sheet, "C19330", "Murata", "BLM18AG601SN1D", "Ferrite bead 600 ohm 0603", None, 0, region)
    return ref


def decouple(net, sheet, region, value="100n"):
    return C(value, net, "GND", sheet, region)


S = "01_MCU"
_add("U1", FP["ESP"], "ESP32-C3-WROOM-02-N4", {
    "1": "3V3", "2": "EN", "3": "RSSI", "4": "SD_CS", "5": "EXP_INT", "6": "WDI", "7": "I2C_SDA", "8": "BOOT",
    "9": "GND", "10": "ARM", "11": "UART_RX", "12": "UART_TX", "13": "USB_DN", "14": "USB_DP", "15": "SPI_MISO",
    "16": "I2C_SCL", "17": "SPI_MOSI", "18": "SPI_SCK", "19": "GND",
}, S, "C2934560", "Espressif", "ESP32-C3-WROOM-02-N4", "ESP32-C3 module, 4 MB flash, PCB antenna", (40.0, 61.5), 0)
C("10u", "3V3", "GND", S, "mcu")
C("100n", "3V3", "GND", S, "mcu")
R("10k", "3V3", "EN", S, "mcu")
C("1u", "EN", "GND", S, "mcu")
R("4.7k", "3V3", "I2C_SDA", S, "mcu")
R("4.7k", "3V3", "I2C_SCL", S, "mcu")
R("10k", "3V3", "BOOT", S, "mcu")
R("10k", "ARM", "GND", "08_HARDWARE_INTERLOCK", "mcu")
_add("U2", FP["TSSOP24"], "TCA9555PWR", {
    "1": "EXP_INT", "2": "GND", "3": "GND", "4": "RF1_CS", "5": "RF1_IRQ", "6": "RF1_RST", "7": "RF1_EN",
    "8": "RF1_IO1", "9": "RF2_CS", "10": "RF2_IRQ", "11": "RF2_RST", "12": "GND", "13": "RF2_EN", "14": "RF2_IO1",
    "16": "SD_CD", "17": "INTERLOCK_OK", "18": "LED_STATUS", "19": "LED_FAULT", "20": "EXP_SPARE",
    "21": "GND", "22": "I2C_SCL", "23": "I2C_SDA", "24": "3V3",
}, S, "C465732", "Texas Instruments", "TCA9555PWR", "16-bit I2C GPIO expander TSSOP-24", (60.0, 49.0), 0)
C("100n", "3V3", "GND", S, "exp")
R("10k", "3V3", "EXP_INT", S, "exp")
TP("EXP_SPARE", S, "exp")
TP("EXP_INT", S, "exp")

S = "02_USB_C"
_add("J1", FP["USBC"], "TYPE-C-31-M-12", {
    "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
    "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DN", "B7": "USB_DN", "SH": "GND",
}, S, "C165948", "Korean Hroparts Elec", "TYPE-C-31-M-12", "USB-C receptacle 16-pin SMT", (24.0, 3.9), 0)
R("5.1k", "CC1", "GND", S, "usb")
R("5.1k", "CC2", "GND", S, "usb")
_add("D1", FP["SOT6"], "USBLC6-2SC6", {"1": "USB_DP", "6": "USB_DP", "3": "USB_DN", "4": "USB_DN", "2": "GND", "5": "VBUS"}, S, "C7519", "STMicroelectronics", "USBLC6-2SC6", "USB ESD protection", None, 0, "usb")
_add("F1", FP["FUSE"], "MF-MSMF050-2", {"1": "VBUS", "2": "VBUS_F"}, S, "C17313", "Bourns", "MF-MSMF050-2", "PTC resettable fuse 1812 0.5 A hold", None, 0, "usb")
C("100n", "VBUS", "GND", S, "usb")
C("10u", "VBUS_F", "GND", S, "usb")

S = "03_POWER"
_add("U3", FP["SOT5"], "TLV75533PDBVR", {"1": "VBUS_F", "2": "GND", "3": "VBUS_F", "5": "3V3"}, S, "C404027", "Texas Instruments", "TLV75533PDBVR", "3.3 V 500 mA LDO, digital rail", None, 0, "pwr")
C("10u", "VBUS_F", "GND", S, "pwr")
C("10u", "3V3", "GND", S, "pwr")
_add("U4", FP["SOT5"], "TLV75533PDBVR", {"1": "VBUS_F", "2": "GND", "3": "VBUS_F", "5": "3V3_RF"}, S, "C404027", "Texas Instruments", "TLV75533PDBVR", "3.3 V 500 mA LDO, RF module rail", None, 0, "pwr")
C("10u", "VBUS_F", "GND", S, "pwr")
C("10u", "3V3_RF", "GND", S, "pwr")
FB("3V3", "3V3_A", S, "pwr")
C("10u", "3V3_A", "GND", S, "pwr")
for net in ("3V3", "3V3_RF", "VBUS_F", "3V3_A"):
    TP(net, S, "pwr")
TP("GND", S, "pwr")

S = "04_RF_INTERFACE"
_add("J2", FP["SMA"], "RF IN", {"1": "RF_IN", "2": "GND"}, S, "C5199907", "Samtec", "SMA-J-P-H-ST-EM1", "SMA edge-mount 50 ohm", (2.6, 68.0), 180)
_add("J3", FP["SMA"], "RF TEST", {"1": "RF_TEST", "2": "GND"}, S, "C5199907", "Samtec", "SMA-J-P-H-ST-EM1", "SMA edge-mount 50 ohm", (2.6, 52.0), 180)
C("100p", "RF_IN", "RF_A", S, None, (8.5, 68.0), 0)
R("0R", "RF_A", "RF_B", S, None, (13.5, 68.0), 0)
R("0R", "RF_A", "GND", S, None, (11.0, 65.4), 90, dnp=True, note="ATT_SHUNT_DNP")
R("0R", "RF_B", "GND", S, None, (16.0, 70.6), 90, dnp=True, note="ATT_SHUNT_DNP")
R("0R", "RF_B", "RF_TEST", S, None, (16.0, 60.0), 270)

S = "05_RF_MONITOR"
R("10k", "RSSI_IN", "GND", S, "rssi")
R("1k", "RSSI_IN", "RSSI", S, "rssi")
C("100n", "RSSI", "GND", S, "rssi")
TP("RSSI_IN", S, "rssi")
TP("RSSI", S, "rssi")

for idx, (sheet, conn_pos, slot, pre, load) in enumerate([
    ("06_RF_EXPANSION_1", (76.6, 62.0), "GND", "RF1", "J4"),
    ("07_RF_EXPANSION_2", (76.6, 38.0), "3V3", "RF2", "J5"),
], start=1):
    region = f"rf{idx}"
    _add(load, FP["JST15"], f"EXT MODULE {idx}", {
        "1": f"{pre}_VCC", "2": f"{pre}_VCC_F", "3": "GND", "4": "SPI_SCK", "5": "SPI_MOSI", "6": "SPI_MISO",
        "7": f"{pre}_CS", "8": "GND", "9": f"{pre}_IRQ", "10": f"{pre}_RST", "11": f"{pre}_IO1", "12": "I2C_SDA",
        "13": "I2C_SCL", "14": slot, "15": "GND", "MP": "GND",
    }, sheet, "C160414", "JST", "SM15B-SRSS-TB(LF)(SN)", "Board-to-wire 15 pin 1 mm connector", conn_pos, 90)
    swref = "U5" if idx == 1 else "U6"
    _add(swref, FP["SOT6"], "TPS22918DBVR", {"1": "3V3_RF", "2": "GND", "3": f"{pre}_PWR_ON", "5": f"{pre}_VCC", "6": f"{pre}_VCC"}, sheet, "C131941", "Texas Instruments", "TPS22918DBVR", "Load switch, RF module supply gate", None, 0, region)
    C("1u", "3V3_RF", "GND", sheet, region)
    C("1u", f"{pre}_VCC", "GND", sheet, region)
    FB(f"{pre}_VCC", f"{pre}_VCC_F", sheet, region)
    C("10u", f"{pre}_VCC_F", "GND", sheet, region)
    R("10k", f"{pre}_PWR_ON", "GND", sheet, region)
    R("10k", f"{pre}_EN", "GND", sheet, region)
    TP(f"{pre}_PWR_ON", sheet, region)

S = "08_HARDWARE_INTERLOCK"
_add("U7", FP["SOT5"], "TPS3823-33DBVR", {"1": "EN", "2": "GND", "3": "RESET_BTN", "4": "WDI", "5": "3V3"}, S, "C7719", "Texas Instruments", "TPS3823-33DBVR", "Supervisor with watchdog, 2.93 V threshold", None, 0, "ilk")
C("100n", "3V3", "GND", S, "ilk")
gates = [
    ("U8", "ARM", "EN", "ARM_WDG"), ("U9", "LOOP_OK", "ENCL_OK", "LOOPS_OK"), ("U10", "ARM_WDG", "LOOPS_OK", "INTERLOCK_OK"),
    ("U11", "INTERLOCK_OK", "RF1_EN", "RF1_PWR_ON"), ("U12", "INTERLOCK_OK", "RF2_EN", "RF2_PWR_ON"),
]
for ref, a, b, y in gates:
    _add(ref, FP["SOT5"], "SN74LVC1G08DBVR", {"1": a, "2": b, "3": "GND", "4": y, "5": "3V3"}, S, "C7666", "Texas Instruments", "SN74LVC1G08DBVR", "Single 2-input AND gate", None, 0, "ilk")
    C("100n", "3V3", "GND", S, "ilk")
R("10k", "LOOP_OK", "GND", S, "ilk")
R("10k", "ENCL_OK", "GND", S, "ilk")
R("1k", "3V3", "ILK_SRC1", S, "ilk")
R("1k", "3V3", "ILK_SRC2", S, "ilk")
_add("J6", FP["HDR4"], "INTERLOCK", {"1": "ILK_SRC1", "2": "LOOP_OK", "3": "ILK_SRC2", "4": "ENCL_OK"}, S, "C2691448", "XFCN", "PZ254V-11-04P", "1x4 2.54 mm pin header", (7.0, 40.0), 0)
TP("INTERLOCK_OK", S, "ilk")
TP("ARM", S, "ilk")

S = "09_MICROSD"
_add("J7", FP["SD"], "microSD", {
    "1": "SD_DAT2", "2": "SD_CS", "3": "SPI_MOSI", "4": "3V3", "5": "SPI_SCK", "6": "GND", "7": "SPI_MISO",
    "8": "SD_DAT1", "9": "SD_CD", "10": "GND", "SH": "GND",
}, S, "C114218", "HRS", "DM3AT-SF-PEJM5", "microSD push-push socket with card detect", (64.0, 14.0), 0)
C("10u", "3V3", "GND", S, "sd")
C("100n", "3V3", "GND", S, "sd")
R("10k", "3V3", "SD_DAT2", S, "sd")
R("10k", "3V3", "SD_DAT1", S, "sd")
R("10k", "3V3", "SD_CS", S, "sd")
R("10k", "3V3", "SD_CD", S, "sd")

S = "10_DEBUG"
_add("J8", FP["HDR4"], "UART", {"1": "GND", "2": "3V3", "3": "UART_TX", "4": "UART_RX"}, S, "C2691448", "XFCN", "PZ254V-11-04P", "1x4 2.54 mm pin header", (33.0, 6.0), 90)
_add("J9", FP["HDR4"], "DEBUG", {"1": "GND", "2": "3V3", "3": "EN", "4": "BOOT"}, S, "C2691448", "XFCN", "PZ254V-11-04P", "1x4 2.54 mm pin header", (45.0, 6.0), 90)
_add("SW1", FP["SW"], "RESET", {"1": "RESET_BTN", "2": "GND"}, S, "C221895", "C&K", "PTS810SJG250SMTRLFS", "Tactile switch SMD", (58.0, 72.0), 0)
_add("SW2", FP["SW"], "BOOT", {"1": "BOOT", "2": "GND"}, S, "C221895", "C&K", "PTS810SJG250SMTRLFS", "Tactile switch SMD", (66.0, 72.0), 0)

S = "11_STATUS_LEDS"
_counters["D"] = 1
for color, net, label in [("green", "3V3", "led_pwr"), ("green", "INTERLOCK_OK", "led_ilk"), ("white", "LED_STATUS", "led_st"), ("red", "LED_FAULT", "led_f")]:
    anode = f"LEDA_{label}"
    R("1k", net, anode, S, "leds")
    LED(color, "GND", anode, S, "leds")

REGIONS = {
    "mcu": (21.0, 40.0, 29.5, 67.0),
    "exp": (52.0, 36.0, 72.0, 56.0),
    "usb": (6.0, 10.5, 20.0, 24.0),
    "pwr": (30.0, 12.0, 54.0, 32.0),
    "ilk": (10.5, 20.0, 30.0, 39.5),
    "rssi": (10.0, 41.0, 24.0, 48.5),
    "rf1": (58.0, 56.0, 72.0, 75.0),
    "rf2": (58.0, 26.0, 72.0, 44.0),
    "sd": (44.0, 10.0, 55.0, 30.0),
    "leds": (55.0, 65.0, 72.5, 79.0),
}


_refs = [p["ref"] for p in PARTS]
assert len(_refs) == len(set(_refs)), "duplicate references"
