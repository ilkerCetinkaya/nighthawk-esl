import shutil
import pcbnew

SUBSET = ["FLASH_WP", "FLASH_CS", "FLASH_HOLD", "BB_EN", "BB_FB", "BB_MODE", "ARM_WDG", "LOOPS_OK", "RESET_BTN", "BQ_ISET", "BQ_ILIM", "BQ_ITERM", "BQ_TMR", "BQ_TS", "CC1", "CC2"]
SRC = "sandbox/NIGHTHAWK_REVB_baseline"
DST = "sandbox/subset"
for ext in ("kicad_pro", "kicad_dru"):
    shutil.copy(f"{SRC}.{ext}", f"{DST}.{ext}")
b = pcbnew.LoadBoard(f"{SRC}.kicad_pcb")
none = b.FindNet("")
cleared = 0
for f in b.GetFootprints():
    for p in f.Pads():
        n = p.GetNetname()
        if n and n not in SUBSET:
            p.SetNetCode(0)
            cleared += 1
pcbnew.SaveBoard(f"{DST}.kicad_pcb", b)
print("cleared pads", cleared)
