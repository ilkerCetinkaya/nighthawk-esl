SHEETS = ["01_MCU_STORAGE", "02_POWER", "03_CC1352R_RF", "04_NFC_TRF7970A", "05_IR_LINK", "06_INTERLOCK", "07_IO_UI_DEBUG"]

FP = {
    ("R", "0402"): "Resistor_SMD:R_0402_1005Metric",
    ("R", "0603"): "Resistor_SMD:R_0603_1608Metric",
    ("R", "0805"): "Resistor_SMD:R_0805_2012Metric",
    ("R", "1206"): "Resistor_SMD:R_1206_3216Metric",
    ("L", "1008"): "Inductor_SMD:L_1008_2520Metric",
    ("C", "0402"): "Capacitor_SMD:C_0402_1005Metric",
    ("C", "0603"): "Capacitor_SMD:C_0603_1608Metric",
    ("C", "0805"): "Capacitor_SMD:C_0805_2012Metric",
    ("L", "0402"): "Inductor_SMD:L_0402_1005Metric",
    ("L", "0603"): "Inductor_SMD:L_0603_1608Metric",
    ("L", "0805"): "Inductor_SMD:L_0805_2012Metric",
}
FP_TP = "TestPoint:TestPoint_Pad_D1.5mm"
FP_LED = "LED_SMD:LED_0603_1608Metric"
FP_SOT5 = "Package_TO_SOT_SMD:SOT-23-5"
FP_SOT6 = "Package_TO_SOT_SMD:SOT-23-6"
FP_SW = "Button_Switch_SMD:SW_SPST_PTS810"
FP_HDR4 = "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"

VERIFIED = {
    ("R", "0R", "0603"): ("C21189", "UNI-ROYAL", "0603WAF0000T5E"),
    ("R", "1k", "0603"): ("C21190", "UNI-ROYAL", "0603WAF1001T5E"),
    ("R", "4.7k", "0603"): ("C23162", "UNI-ROYAL", "0603WAF4701T5E"),
    ("R", "5.1k", "0603"): ("C23186", "UNI-ROYAL", "0603WAF5101T5E"),
    ("R", "10k", "0603"): ("C25804", "UNI-ROYAL", "0603WAF1002T5E"),
    ("C", "100n", "0603"): ("C108079", "YAGEO", "CC0603KRX7R7BB104"),
    ("C", "1u", "0603"): ("C15849", "Samsung Electro-Mechanics", "CL10A105KB8NNNC"),
    ("C", "10u", "0603"): ("C19702", "Samsung Electro-Mechanics", "CL10A106KP8NNNC"),
    ("C", "100p", "0603"): ("C14858", "Samsung Electro-Mechanics", "CL10C101JB8NNNC"),
}

PARTS = []
_cnt = {}


def add(ref, sym, fp, value, nets, sheet, lcsc="", mfr="", mpn="", desc="", dnp=False, ds=""):
    PARTS.append({"ref": ref, "sym": sym, "fp": fp, "value": value, "nets": nets, "sheet": sheet, "lcsc": lcsc,
                  "mfr": mfr, "mpn": mpn, "desc": desc, "dnp": dnp, "ds": ds})


def nxt(prefix):
    _cnt[prefix] = _cnt.get(prefix, 0) + 1
    return f"{prefix}{_cnt[prefix]}"


def passive(kind, value, a, b, sheet, pkg, dnp=False, desc="", mpn="", mfr="", lcsc=""):
    ref = nxt(kind)
    v = VERIFIED.get((kind, value, pkg))
    if v and not (mpn or lcsc):
        lcsc, mfr, mpn = v
    lib = {"R": ("Device", "R"), "C": ("Device", "C"), "L": ("Device", "L")}[kind]
    add(ref, lib, FP[(kind, pkg)], value, {"1": a, "2": b}, sheet, lcsc, mfr, mpn, desc or f"{kind} {value} {pkg}", dnp)
    return ref


def R(value, a, b, sheet, pkg="0603", **kw):
    return passive("R", value, a, b, sheet, pkg, **kw)


def C(value, a, b, sheet, pkg="0603", **kw):
    return passive("C", value, a, b, sheet, pkg, **kw)


def L(value, a, b, sheet, pkg="0603", **kw):
    return passive("L", value, a, b, sheet, pkg, **kw)


def TP(net, sheet):
    ref = nxt("TP")
    add(ref, ("Connector", "TestPoint"), FP_TP, f"TP_{net}", {"1": net}, sheet, desc="Test point pad 1.5 mm")
    return ref


def FB(a, b, sheet, value="600R@100MHz"):
    ref = nxt("FB")
    add(ref, ("Device", "FerriteBead"), "Inductor_SMD:L_0603_1608Metric", value, {"1": a, "2": b}, sheet, "C19330", "Murata", "BLM18AG601SN1D", "Ferrite bead 600 ohm 0603")
    return ref


def decouple(net, sheet, n=1, value="100n", pkg="0603"):
    for _ in range(n):
        C(value, net, "GND", sheet, pkg)


def AND(ref, a, b, y, sheet, desc):
    add(ref, ("NH_LOCAL", "SN74LVC1G08"), FP_SOT5, "SN74LVC1G08DBVR", {"1": a, "2": b, "3": "GND", "4": y, "5": "3V3"}, sheet,
        "C7666", "Texas Instruments", "SN74LVC1G08DBVR", desc)
    C("100n", "3V3", "GND", sheet)


S = "01_MCU_STORAGE"
add("U1", ("RF_Module", "ESP32-C3-WROOM-02"), "RF_Module:ESP32-C3-WROOM-02", "ESP32-C3-WROOM-02-N4", {
    "1": "3V3", "2": "EN", "IO0": "SPI_SCK", "IO1": "SPI_MISO", "IO2": "WDI", "IO3": "NFC_IRQ", "IO4": "SPI_MOSI",
    "IO5": "FLASH_CS", "IO6": "NFC_CS", "IO7": "I2C_SDA", "IO8": "I2C_SCL", "IO9": "BOOT", "IO10": "EXP_INT",
    "IO20/RXD": "CC_UART_TX", "IO21/TXD": "CC_UART_RX", "IO18": "USB_DN", "IO19": "USB_DP", "9": "GND", "19": "GND",
}, S, "C2934560", "Espressif", "ESP32-C3-WROOM-02-N4", "ESP32-C3 module, 4 MB flash, PCB antenna")
C("10u", "3V3", "GND", S)
C("100n", "3V3", "GND", S)
R("10k", "3V3", "EN", S)
C("1u", "EN", "GND", S)
R("10k", "3V3", "WDI", S)
R("10k", "3V3", "BOOT", S)
R("4.7k", "3V3", "I2C_SDA", S)
R("4.7k", "3V3", "I2C_SCL", S)
R("10k", "3V3", "EXP_INT", S)
add("U2", ("Memory_Flash", "W25Q32JVSS"), "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm", "GD25Q32ESIGR", {
    "1": "FLASH_CS", "2": "SPI_MISO", "3": "FLASH_WP", "4": "GND", "5": "SPI_MOSI", "6": "SPI_SCK", "7": "FLASH_HOLD", "8": "3V3",
}, S, "C2832998", "GigaDevice", "GD25Q32ESIGR", "32 Mbit SPI NOR flash (package to be confirmed)")
C("100n", "3V3", "GND", S)
R("10k", "3V3", "FLASH_CS", S)
R("10k", "3V3", "FLASH_WP", S)
R("10k", "3V3", "FLASH_HOLD", S)
R("10k", "3V3", "NFC_CS", S)
for n in ("SPI_SCK", "SPI_MOSI", "SPI_MISO", "I2C_SDA", "I2C_SCL"):
    TP(n, S)

S = "02_POWER"
add("J1", ("Connector", "USB_C_Receptacle_USB2.0_16P"), "NH_REVB:HRO_TYPE-C-31-M-12_DS", "TYPE-C-31-M-12", {
    "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
    "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DN", "B7": "USB_DN", "SH": "GND",
}, S, "C165948", "Korean Hroparts Elec", "TYPE-C-31-M-12", "USB-C receptacle 16-pin SMT")
R("5.1k", "CC1", "GND", S)
R("5.1k", "CC2", "GND", S)
add("D1", ("Power_Protection", "USBLC6-2SC6"), FP_SOT6, "USBLC6-2SC6", {"1": "USB_DP", "6": "USB_DP", "3": "USB_DN", "4": "USB_DN", "2": "GND", "5": "VBUS"},
    S, "C7519", "STMicroelectronics", "USBLC6-2SC6", "USB ESD protection")
add("F1", ("Device", "Polyfuse"), "Fuse:Fuse_1812_4532Metric", "MF-MSMF050-2", {"1": "VBUS", "2": "VBUS_F"}, S, "C17313", "Bourns", "MF-MSMF050-2", "PTC 0.5 A hold 1812")
C("100n", "VBUS", "GND", S)
C("10u", "VBUS_F", "GND", S)
add("U3", ("Battery_Management", "BQ24074RGT"), "Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm", "BQ24074RGTR", {
    "1": "BQ_TS", "2": "VBAT", "3": "VBAT", "4": "GND", "5": "SYS", "6": "GND", "7": "PGOOD_N", "8": "GND", "9": "CHG_N",
    "10": "SYS", "11": "SYS", "12": "BQ_ILIM", "13": "VBUS_F", "14": "BQ_TMR", "15": "BQ_ITERM", "16": "BQ_ISET", "17": "GND",
}, S, "C54313", "Texas Instruments", "BQ24074RGTR", "USB charger with power path, 4.4 V OUT, adjustable ITERM")
R("10k", "BQ_TS", "GND", S, desc="TS fixed 10k (equals 10k NTC at 25 C); battery NTC not used")
R("3.09k", "BQ_ILIM", "GND", S, desc="ILIM: 1550/3.09k = 0.50 A input limit")
R("1.78k", "BQ_ISET", "GND", S, desc="ISET: 890/1.78k = 0.50 A fast charge")
R("68k", "BQ_TMR", "GND", S, desc="TMR: max charge time about 9.1 h")
R("2.94k", "BQ_ITERM", "GND", S, desc="ITERM = 0.03 x 2.94k/1.78k = 50 mA")
R("10k", "3V3", "PGOOD_N", S)
R("10k", "3V3", "CHG_N", S)
C("1u", "VBUS_F", "GND", S)
C("10u", "SYS", "GND", S)
C("10u", "VBAT", "GND", S)
add("J2", ("Connector_Generic", "Conn_01x02"), "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal", "BATT", {"1": "VBAT", "2": "GND"}, S,
    "C295747", "JST", "S2B-PH-SM4-TB(LF)(SN)", "Battery connector (user-supplied pack)")
add("U4", ("NH_LOCAL", "TPS63802DLA"), "NH_REVB:TPS63802DLA_VSON-10_3x2mm", "TPS63802DLAR", {
    "1": "BB_EN", "2": "BB_MODE", "3": "GND", "4": "BB_FB", "5": "BB_PG", "6": "3V6", "7": "BB_L2", "8": "GND", "9": "BB_L1", "10": "SYS",
}, S, "C2845237", "Texas Instruments", "TPS63802DLAR", "2 A buck-boost converter, adjustable")
L("0.47u", "BB_L1", "BB_L2", S, "0805", desc="Buck-boost inductor 0.47 uH, Isat >= 4 A, 4x4 mm class; footprint to be set to the chosen part (datasheet reference XFL4015-471ME, LCSC C18221164 for -471MEC at US$4.27)", mfr="Coilcraft", mpn="XFL4015-471MEC", lcsc="C18221164")
C("10u", "SYS", "GND", S)
C("10u", "SYS", "GND", S)
C("22u", "3V6", "GND", S, "0805")
C("22u", "3V6", "GND", S, "0805")
R("100k", "SYS", "BB_EN", S)
R("562k", "3V6", "BB_FB", S, desc="FB upper, 3.6 V output (datasheet table 10-5)")
R("91k", "BB_FB", "GND", S, desc="FB lower")
R("100k", "3V6", "BB_PG", S)
R("0R", "3V6", "BB_MODE", S, desc="MODE high = forced PWM")
R("0R", "BB_MODE", "GND", S, dnp=True, desc="MODE low = power save (alternative)")
for ref, out in (("U5", "3V3"), ("U6", "3V3_RF")):
    add(ref, ("Regulator_Linear", "TLV75533PDBV"), FP_SOT5, "TLV75533PDBVR", {"1": "3V6", "2": "GND", "3": "3V6", "5": out},
        S, "C404027", "Texas Instruments", "TLV75533PDBVR", f"3.3 V 500 mA LDO ({out})")
    C("10u", "3V6", "GND", S)
    C("10u", out, "GND", S)
FB("3V3_RF", "3V3_A", S)
C("10u", "3V3_A", "GND", S)
FB("3V6", "3V6_NFC", S)
C("10u", "3V6_NFC", "GND", S)
for n in ("VBUS_F", "VBAT", "SYS", "3V6", "3V3", "3V3_RF", "3V3_A", "BB_PG"):
    TP(n, S)
TP("GND", S)

S = "03_CC1352R_RF"
add("U7", ("NH_LOCAL", "CC1352R1F3RGZ"), "Package_DFN_QFN:Texas_RGZ0048A_VQFN-48-1EP_7x7mm_P0.5mm_EP5.15x5.15mm", "CC1352R1F3RGZR", {
    "1": "RF24_P", "2": "RF24_N", "3": "RFSUB_P", "4": "RFSUB_N", "5": "RX_TX", "6": "X32K_Q1", "7": "X32K_Q2",
    "46": "X48M_N", "47": "X48M_P", "48": "VDDR", "45": "VDDR", "44": "3V3_RF", "13": "3V3_RF", "22": "3V3_RF", "34": "3V3_RF",
    "33": "DCDC_SW", "23": "DCOUPL", "35": "CC_RESET_N", "24": "CC_TMSC", "25": "CC_TCKC", "49": "GND",
    "8": "CC_UART_RX", "9": "CC_UART_TX", "10": "IR_MOD", "11": "CC_RF_BUSY", "12": "ESP_RF_QUIET", "14": "CC_IRQ", "15": "IR_RX", "21": "CC_BSL", "26": "CC_TDO", "27": "CC_TDI",
}, S, "C2151581", "Texas Instruments", "CC1352R1F3RGZR", "SimpleLink dual-band wireless MCU, sub-1 GHz + 2.4 GHz")
for _ in range(4):
    C("100n", "3V3_RF", "GND", S)
C("10u", "3V3_RF", "GND", S)
C("10u", "3V3_RF", "GND", S)
L("10u", "DCDC_SW", "VDDR", S, "0805", desc="DC/DC inductor 10 uH (TI reference value, to be confirmed)")
C("22u", "VDDR", "GND", S, "0805", desc="22 uF on VDDR per CC1352R datasheet note")
C("100n", "VDDR", "GND", S)
C("100n", "VDDR", "GND", S)
C("1u", "DCOUPL", "GND", S, desc="DCOUPL decoupling (value to be confirmed against TI reference)")
add("Y1", ("Device", "Crystal_GND24"), "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", "48MHz", {"1": "X48M_N", "3": "X48M_P", "2": "GND", "4": "GND"}, S,
    "C2925606", "HCI", "XC32M4-48.000-F08NLDT", "48 MHz crystal 8 pF, 40 ohm, +-10 ppm (CC1352R requires CL 5-9 pF, ESR <= 60 ohm)")
C("12p", "X48M_N", "GND", S, "0402", dnp=True, desc="optional external load capacitor")
C("12p", "X48M_P", "GND", S, "0402", dnp=True, desc="optional external load capacitor")
add("Y2", ("Device", "Crystal"), "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm", "32.768kHz", {"1": "X32K_Q1", "2": "X32K_Q2"}, S,
    "C48615", "Epson", "Q13FC13500002", "32.768 kHz crystal 7 pF, 70 kohm, +-20 ppm (CC1352R requires CL 6-12 pF, ESR <= 100 kohm)")
C("12p", "X32K_Q1", "GND", S, "0402", dnp=True, desc="optional external load capacitor")
C("12p", "X32K_Q2", "GND", S, "0402", dnp=True, desc="optional external load capacitor")
add("U8", ("NH_LOCAL", "JTI0900PC15A0036"), "NH_REVB:Johanson_0900PC15A0036_2.0x1.25mm", "0900PC15A0036001E", {
    "1": "ANT24_IPC", "2": "GND", "3": "GND", "4": "ANTSUB_IPC", "5": "RX_TX", "6": "RFSUB_N", "7": "RFSUB_P", "8": "RF24_N", "9": "RF24_P", "10": "GND",
}, S, "", "Johanson Technology", "0900PC15A0036001E", "Integrated balun filter for CC1352R/P, 862-928 MHz and 2.4-2.5 GHz")
C("100p", "RX_TX", "GND", S, "0402", desc="C41 per SWRA629A figure 3 (RX_TX external bias decoupling)")
C("100p", "ANTSUB_IPC", "ANTSUB_DC", S, "0402", desc="C51 per SWRA629A figure 3 (series DC block, sub-GHz port)")
R("0R", "ANT24_IPC", "ANT24_FEED", S, "0402", desc="2.4 GHz port to on-board antenna (select)")
R("0R", "ANT24_FEED", "UFL24_C", S, "0402", dnp=True, desc="U.FL J3 tap on the antenna feed node (fit for VNA/conducted tests only)")
C("1p", "ANT24_FEED", "GND", S, "0402", dnp=True, desc="IFA shunt tuning")
L("1n", "ANT24_FEED", "ANT24_A", S, "0402", dnp=True, desc="IFA series tuning (0R default)")
R("0R", "ANT24_FEED", "ANT24_A", S, "0402", desc="IFA series link")
add("ANT1", ("Device", "Antenna_Chip"), "NH_REVB:IFA_AN043_15.2x5.7", "2.4GHz IFA", {"1": "ANT24_A", "2": "GND"}, S, desc="TI AN043 (SWRA117D) 15.2 x 5.7 mm inverted-F antenna; pad 1 feed, pad 2 short-stub via to ground; reference PCB thickness unknown, tune on VNA")
R("0R", "ANTSUB_DC", "ANTSUB_FEED", S, "0402", desc="Sub-GHz port to chip antenna (select)")
R("0R", "ANTSUB_FEED", "UFLSUB_C", S, "0402", dnp=True, desc="U.FL J4 tap on the antenna feed node (fit for VNA/conducted tests only)")
C("3.9p", "ANTSUB_FEED", "GND", S, "0402", dnp=True, desc="Johanson 0868AT43A0020 matching: 3.9 pF shunt (JTI 500R07S3R9BV4T)", mfr="Johanson Technology", mpn="500R07S3R9BV4T")
L("18n", "ANTSUB_FEED", "ANTSUB_A", S, "0402", dnp=True, desc="Johanson 0868AT43A0020 matching: 18 nH series (JTI L-07C18NJV6T)", mfr="Johanson Technology", mpn="L-07C18NJV6T")
C("0.3p", "ANTSUB_A", "GND", S, "0402", dnp=True, desc="Johanson 0868AT43A0020 matching: 0.3 pF shunt (JTI 500R07S0R3BV4T)", mfr="Johanson Technology", mpn="500R07S0R3BV4T")
R("0R", "ANTSUB_FEED", "ANTSUB_A", S, "0402", dnp=True, desc="alternative link (antenna without matching network)")
add("ANT2", ("Device", "Antenna_Chip"), "NH_REVB:Johanson_0868AT43A0020", "0868AT43A0020E", {"1": "ANTSUB_A"}, S, "C3284550", "Johanson Technology", "0868AT43A0020E",
    "868 MHz chip antenna", dnp=True)
for ref, net in (("J3", "UFL24_C"), ("J4", "UFLSUB_C")):
    add(ref, ("Connector", "Conn_Coaxial"), "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical", "U.FL", {"1": net, "2": "GND"}, S,
        "C598199", "Hirose", "U.FL-R-SMT-1(01)", "U.FL receptacle RF test port", dnp=True)
add("SH1", ("NH_LOCAL", "SHIELD_FRAME"), "RF_Shielding:Wuerth_36103205_20x20mm", "36103205S", {"1": "GND"}, S, "", "Wurth Elektronik", "36103205S", "WE-SHC shield frame 20x20 mm")
add("SH1C", ("NH_LOCAL", "SHIELD_COVER"), "", "36003200S", {}, S, "", "Wurth Elektronik", "36003200S", "WE-SHC shield cover 20x20 mm (BOM only)")
add("J5", ("Connector", "Conn_ARM_JTAG_SWD_10"), "Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD", "CC1352R JTAG", {
    "1": "3V3_RF", "2": "CC_TMSC", "3": "GND", "4": "CC_TCKC", "5": "GND", "6": "CC_TDO", "8": "CC_TDI", "9": "GND", "10": "CC_RESET_N",
}, S, desc="cJTAG/JTAG programming header 2x5 1.27 mm")
R("1k", "CC_RESET_G", "CC_RESET_N", S, desc="series between interlock gate and RESET_N (allows debugger override)")
for n in ("CC_UART_TX", "CC_UART_RX", "CC_IRQ", "CC_RESET_N", "IR_MOD", "IR_RX", "VDDR"):
    TP(n, S)

S = "04_NFC_TRF7970A"
add("U9", ("NH_LOCAL", "TRF7970ARHB"), "Package_DFN_QFN:Texas_RHB0032E_VQFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm", "TRF7970ARHBR", {
    "1": "NFC_VDDA", "2": "3V6_NFC", "3": "NFC_VDDRF", "4": "NFC_VDDRF", "5": "NFC_TXOUT", "6": "GND", "7": "GND", "8": "NFC_RX1", "9": "NFC_RX2", "10": "GND",
    "11": "NFC_BG", "12": "NFC_ASKOOK", "13": "NFC_IRQ", "15": "GND", "16": "3V3", "17": "NFC_IO0", "18": "NFC_IO1", "19": "NFC_IO2", "21": "NFC_CS",
    "23": "SPI_MISO", "24": "SPI_MOSI", "25": "NFC_EN2", "26": "SPI_SCK", "28": "NFC_EN_G", "29": "GND", "30": "NFC_OSC_OUT", "31": "NFC_OSC_IN",
    "32": "NFC_VDDX", "33": "GND",
}, S, "C117004", "Texas Instruments", "TRF7970ARHBR", "13.56 MHz NFC/RFID transceiver, SPI with SS")
C("2.2u", "3V6_NFC", "GND", S, "0603")
C("10n", "3V6_NFC", "GND", S)
C("2.2u", "NFC_VDDA", "GND", S, "0603")
C("10n", "NFC_VDDA", "GND", S)
C("2.2u", "NFC_VDDRF", "GND", S, "0603")
C("10n", "NFC_VDDRF", "GND", S)
C("2.2u", "NFC_VDDX", "GND", S, "0603")
C("10n", "NFC_VDDX", "GND", S)
C("100n", "3V3", "GND", S)
C("2.2u", "NFC_BG", "GND", S, "0603", desc="band-gap decoupling (value to be confirmed against TRF7970A EVM)")
R("10k", "3V3", "NFC_IO2", S)
R("10k", "3V3", "NFC_IO1", S)
R("10k", "NFC_IO0", "GND", S)
R("10k", "NFC_EN2", "GND", S)
R("10k", "NFC_ASKOOK", "GND", S)
R("10k", "NFC_EN_G", "GND", S)
add("Y3", ("Device", "Crystal_GND24"), "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", "27.12MHz", {"1": "NFC_OSC_IN", "3": "NFC_OSC_OUT", "2": "GND", "4": "GND"}, S,
    "C29975", "YXC", "X32252712MMB4SI", "27.12 MHz crystal CL 10 pF, 50 ohm, +-10 ppm")
C("15p", "NFC_OSC_IN", "GND", S, "0402", desc="load capacitor for CL 10 pF with about 3 pF stray (to be trimmed)")
C("15p", "NFC_OSC_OUT", "GND", S, "0402", desc="load capacitor for CL 10 pF with about 3 pF stray (to be trimmed)")
C("1.5n", "NFC_TXOUT", "NFC_T1", S, "0402", desc="TI TRF7970A application schematic: C13 (3 nF as two 1.5 nF)")
C("1.5n", "NFC_TXOUT", "NFC_T1", S, "0402")
L("150n", "NFC_T1", "NFC_N1", S, "0603", desc="TI TRF7970A application schematic: L1")
C("1.2n", "NFC_N1", "NFC_RXM1", S, "0402", desc="divider top (C15)")
C("1.2n", "NFC_RXM1", "GND", S, "0402", desc="divider bottom (C16)")
C("680p", "NFC_N1", "GND", S, "0402", desc="C17")
L("330n", "NFC_N1", "NFC_N2", S, "0603", desc="TI TRF7970A application schematic: L2")
C("10p", "NFC_N1", "NFC_N2", S, "0402", desc="C18 across L2")
C("220p", "NFC_N2", "NFC_RXM2", S, "0402", desc="divider top (C19)")
C("680p", "NFC_RXM2", "GND", S, "0402", desc="divider bottom (C20)")
C("100p", "NFC_N2", "GND", S, "0402", desc="C21")
C("27p", "NFC_N2", "GND", S, "0402", desc="C22")
R("0R", "NFC_N2", "NFC_ANT", S, "0402", desc="R5 test-port link")
R("0R", "NFC_RXM1", "NFC_RX1", S, "0402", desc="RX_IN1 link")
R("0R", "NFC_RXM2", "NFC_RX2", S, "0402", desc="RX_IN2 link")
C("47p", "NFC_ANT", "NFC_COIL_A", S, "0402", desc="Cs part 1 (47 pF + 12 pF = 59 pF; calculated 60.1 pF for the 1.43 uH coil, retune on VNA)")
C("12p", "NFC_ANT", "NFC_COIL_A", S, "0402", desc="Cs part 2 (second pad for fine tuning, SLOA241C 2.3)")
R("845", "NFC_COIL_A", "GND", S, "1206", desc="Rp Q damping: X*Q = 122 ohm x 7 = 854 ohm, E96 845 ohm; dissipation up to about 100 mW, 1206 250 mW")
C("39p", "NFC_COIL_A", "GND", S, "0402", desc="Cp part 1: calculated 39.7 pF for the 1.43 uH coil, retune on VNA")
C("2.2p", "NFC_COIL_A", "GND", S, "0402", dnp=True, desc="Cp part 2 (trim pad, DNP)")
add("ANT3", ("Device", "Antenna_Loop"), "NH_REVB:NFC_COIL_18x16_6T", "NFC coil", {"1": "NFC_COIL_A", "2": "GND"}, S, desc="On-board 13.56 MHz coil 18 x 16 mm outer, 6 turns, 0.25 mm trace, 0.10 mm gap, F.Cu with B.Cu underpass; calculated 1.43 uH (SLOA241C eq. 2), not measured")
add("J8", ("Connector", "Conn_Coaxial"), "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical", "U.FL NFC", {"1": "NFC_ANT", "2": "GND"}, S, "C598199", "Hirose", "U.FL-R-SMT-1(01)", "VNA access to the coil tank (SLOA241C 2.3): remove R39 0 ohm to isolate the TRF7970A network", dnp=True)
for n in ("NFC_IRQ", "NFC_EN_G", "NFC_TXOUT", "NFC_ANT", "NFC_RX1", "NFC_RX2", "NFC_VDDX"):
    TP(n, S)

S = "05_IR_LINK"
add("D2", ("Device", "LED"), "NH_REVB:VSMB10940_SideView_3x2", "VSMB10940", {"2": "IR_LED_A", "1": "IR_LED_K"}, S, "C4749241", "Vishay", "VSMB10940", "940 nm IR emitter, side view")
R("20", "IR_VCC", "IR_LED_A", S, "0805", desc="LED current limit, about 95 mA at 3.3 V (to be verified)")
add("Q1", ("Transistor_FET", "AO3400A"), "Package_TO_SOT_SMD:SOT-23", "AO3400A", {"1": "IR_GATE", "2": "GND", "3": "IR_LED_K"}, S, "C20917", "Alpha & Omega", "AO3400A", "N-MOSFET LED switch")
R("22", "IR_GATE_DRV", "IR_GATE", S, "0603", desc="gate series resistor")
R("100k", "IR_GATE", "GND", S)
add("U10", ("NH_LOCAL", "TPS22918"), FP_SOT6, "TPS22918DBVR", {"1": "3V3", "2": "GND", "3": "IR_PWR_ON", "6": "IR_VCC"}, S,
    "C131941", "Texas Instruments", "TPS22918DBVR", "Load switch, IR LED supply gate")
C("1u", "3V3", "GND", S)
C("10u", "IR_VCC", "GND", S)
C("100n", "IR_VCC", "GND", S)
R("10k", "IR_PWR_ON", "GND", S)
add("D3", ("Device", "D_Photo"), "NH_REVB:VEMD10940F_SideView_3x2", "VEMD10940F", {"1": "PD_BIAS", "2": "TIA_IN"}, S, "C3211032", "Vishay", "VEMD10940F", "940 nm PIN photodiode, side view")
R("100", "3V3_A", "PD_BIAS", S, "0603", desc="photodiode bias filter")
C("1u", "PD_BIAS", "GND", S)
add("U11", ("Amplifier_Operational", "OPA356xxDBV"), FP_SOT5, "OPA356AIDBVR", {"1": "TIA_OUT", "2": "GND", "3": "VREF", "4": "TIA_IN", "5": "3V3_A"}, S,
    "C183100", "Texas Instruments", "OPA356AIDBVR", "200 MHz CMOS op-amp, TIA")
R("10k", "TIA_IN", "TIA_OUT", S, "0603", desc="TIA feedback Rf")
C("1.5p", "TIA_IN", "TIA_OUT", S, "0402", desc="TIA feedback Cf, about 10.6 MHz")
C("100n", "3V3_A", "GND", S)
R("6.8k", "3V3_A", "VREF", S)
R("10k", "VREF", "GND", S)
C("1u", "VREF", "GND", S)
C("100n", "TIA_OUT", "CMP_IN", S, desc="AC coupling")
R("100k", "CMP_IN", "VREF", S)
add("U12", ("Comparator", "TLV3501AIDBV"), FP_SOT6, "TLV3501AIDBVR", {"1": "VREF", "2": "GND", "3": "CMP_IN", "4": "3V3_A", "5": "IR_RX", "6": "GND"}, S,
    "", "Texas Instruments", "TLV3501AIDBVR", "4.5 ns comparator, IR detector output; not found on LCSC: source from DigiKey/Farnell")
C("100n", "3V3_A", "GND", S)
for n in ("TIA_OUT", "CMP_IN", "IR_LED_K", "IR_GATE", "VREF"):
    TP(n, S)

S = "06_INTERLOCK"
add("U13", ("Power_Supervisor", "TPS3823-xxDBV"), FP_SOT5, "TPS3823-33DBVR", {"1": "EN", "2": "GND", "3": "RESET_BTN", "4": "WDI", "5": "3V3"}, S,
    "C7719", "Texas Instruments", "TPS3823-33DBVR", "Supervisor with watchdog, 2.93 V threshold")
C("100n", "3V3", "GND", S)
AND("U14", "ARM", "EN", "ARM_WDG", S, "AND: ARM and ESP32 running")
AND("U15", "LOOP_OK", "ENCL_OK", "LOOPS_OK", S, "AND: interlock loops")
AND("U16", "ARM_WDG", "LOOPS_OK", "INTERLOCK_OK", S, "AND: interlock chain")
AND("U17", "INTERLOCK_OK", "CC_RUN", "CC_RESET_G", S, "AND: CC1352R run permit")
AND("U18", "INTERLOCK_OK", "NFC_EN", "NFC_EN_G", S, "AND: TRF7970A enable permit")
AND("U19", "INTERLOCK_OK", "IR_EN", "IR_PWR_ON", S, "AND: IR LED supply permit")
AND("U20", "INTERLOCK_OK", "IR_MOD", "IR_GATE_DRV", S, "AND: IR gate buffer with interlock permit")
R("10k", "LOOP_OK", "GND", S)
R("10k", "ENCL_OK", "GND", S)
R("10k", "ARM", "GND", S)
R("10k", "CC_RUN", "GND", S)
R("10k", "NFC_EN", "GND", S)
R("10k", "IR_EN", "GND", S)
R("1k", "3V3", "ILK_SRC1", S)
R("1k", "3V3", "ILK_SRC2", S)
add("J6", ("Connector_Generic", "Conn_01x04"), FP_HDR4, "INTERLOCK", {"1": "ILK_SRC1", "2": "LOOP_OK", "3": "ILK_SRC2", "4": "ENCL_OK"}, S,
    "C2691448", "XFCN", "PZ254V-11-04P", "1x4 2.54 mm header, interlock loops")
TP("INTERLOCK_OK", S)
TP("ARM", S)

S = "07_IO_UI_DEBUG"
for ref, addr in (("U21", "GND"), ("U22", "3V3")):
    add(ref, ("Interface_Expansion", "TCA9555PWR"), "Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm", "TCA9555PWR", {
        "1": "EXP_INT", "2": "GND", "3": "GND", "21": addr, "22": "I2C_SCL", "23": "I2C_SDA", "24": "3V3", "12": "GND",
    }, S, "C465732", "Texas Instruments", "TCA9555PWR", f"16-bit I2C GPIO expander, address pin A0={addr}")
    C("100n", "3V3", "GND", S)
for p, net in (("4", "CC_RUN"), ("5", "CC_BSL"), ("6", "CC_IRQ"), ("7", "NFC_EN"), ("8", "IR_EN"), ("9", "ARM"), 
               ("13", "LED_STATUS"), ("14", "LED_FAULT"), ("15", "BTN1"), ("16", "BTN2"), ("17", "CHG_N"), ("18", "PGOOD_N"), ("19", "INTERLOCK_OK"), ("20", "EN")):
    [x for x in PARTS if x["ref"] == "U21"][0]["nets"][p] = net
for p, net in (("4", "LOOP_OK"), ("5", "ENCL_OK"), ("6", "ESP_RF_QUIET"), ("7", "CC_RF_BUSY"),
               ):
    [x for x in PARTS if x["ref"] == "U22"][0]["nets"][p] = net
add("SW1", ("Switch", "SW_Push"), FP_SW, "RESET", {"1": "RESET_BTN", "2": "GND"}, S, "C221895", "C&K", "PTS810SJG250SMTRLFS", "Tactile switch reset")
add("SW2", ("Switch", "SW_Push"), FP_SW, "BOOT", {"1": "BOOT", "2": "GND"}, S, "C221895", "C&K", "PTS810SJG250SMTRLFS", "Tactile switch boot")
add("SW3", ("Switch", "SW_Push"), FP_SW, "BTN1", {"1": "BTN1", "2": "GND"}, S, "C221895", "C&K", "PTS810SJG250SMTRLFS", "Tactile switch user 1")
add("SW4", ("Switch", "SW_Push"), FP_SW, "BTN2", {"1": "BTN2", "2": "GND"}, S, "C221895", "C&K", "PTS810SJG250SMTRLFS", "Tactile switch user 2")
add("J7", ("Connector_Generic", "Conn_01x04"), FP_HDR4, "DEBUG", {"1": "GND", "2": "3V3", "3": "EN", "4": "BOOT"}, S,
    "C2691448", "XFCN", "PZ254V-11-04P", "1x4 2.54 mm header, ESP32 reset/boot")
_cnt["D"] = 3
_led = {"green": ("C51933293", "Guiguang light", "GL0603UG01"), "white": ("C51933297", "Guiguang light", "GL0603UW01"), "red": ("C2286", "KENTO", "KT-0603R")}
for color, net in (("green", "3V3"), ("green", "INTERLOCK_OK"), ("white", "LED_STATUS"), ("red", "LED_FAULT")):
    anode = f"LEDA_{net}"
    R("1k", net, anode, S)
    l, m, p = _led[color]
    add(nxt("D"), ("Device", "LED"), FP_LED, color.upper(), {"1": "GND", "2": anode}, S, l, m, p, f"LED 0603 {color}")

C("1p", "ANT24_A", "GND", "03_CC1352R_RF", "0402", dnp=True, desc="IFA pi network: second shunt pad at the antenna side")
R("10k", "ESP_RF_QUIET", "GND", "07_IO_UI_DEBUG", "0603", desc="fail-safe: ESP_RF_QUIET defaults low (not quiet) because TCA9555 pins power up as inputs with pull-ups")
import passive_data as _pd
GENERIC_REFS = set()
for _p in PARTS:
    if _p["lcsc"] or _p["ref"][0] not in "RCL" or _p["ref"][:2] in ("TP", "SH", "FB"):
        continue
    _k = (_p["ref"][0], _p["value"])
    if _p["ref"][0] == "R" and _p["value"] == "0R":
        _k = ("R", "0R402")
    if _p["ref"] in _pd.BY_REF:
        _code = _pd.BY_REF[_p["ref"]]
        _pkg = _pd.REF_PKG.get(_p["ref"], "0402")
    elif _k in _pd.BY_KEY:
        _pkg, _code = _pd.BY_KEY[_k]
    else:
        continue
    _d = _pd.DATA[_code]
    _p["lcsc"], _p["mpn"], _p["mfr"] = _code, _d[0], _d[1]
    _p["ds"] = _d[5]
    _p["fp"] = FP[(_p["ref"][0], _pkg)]
    GENERIC_REFS.add(_p["ref"])

for _p in PARTS:
    if _p["lcsc"] in _pd.SWAPS:
        _code, _pkg, _kind = _pd.SWAPS[_p["lcsc"]]
        _d = _pd.DATA[_code]
        _p["lcsc"], _p["mpn"], _p["mfr"], _p["ds"] = _code, _d[0], _d[1], _d[5]
        _p["fp"] = FP[(_kind, _pkg)]
        GENERIC_REFS.add(_p["ref"])

for _p in PARTS:
    if _p["ref"] == "L1":
        _d = _pd.DATA["C703140"]
        _p["lcsc"], _p["mpn"], _p["mfr"], _p["ds"] = "C703140", _d[0], _d[1], _d[5]
        _p["fp"] = FP[("L", "1008")]
        _p["desc"] = "Buck-boost inductor 0.47 uH +-20%, Isat 4.9 A, 23 mohm, 2.5x2.0 mm (replaces Coilcraft XFL4015-471MEC at US$4.27)"
        GENERIC_REFS.add("L1")

_refs = [p["ref"] for p in PARTS]
assert len(_refs) == len(set(_refs)), "duplicate refs"
