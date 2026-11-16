import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design
import gen_sch
import make_board as mb

by_ref = {p["ref"]: p for p in design.PARTS}
board = pcbnew.LoadBoard(mb.PCB)
linked = 0
for fp in board.GetFootprints():
    p = by_ref.get(fp.GetReference())
    if not p:
        continue
    fp.SetPath(pcbnew.KIID_PATH(f"/{gen_sch.ROOT_UUID}/{gen_sch.SHEET_UUID[p['sheet']]}/{gen_sch.uid('sym', p['ref'])}"))
    for key, val in (("LCSC", p["lcsc"]), ("MPN", p["mpn"]), ("Manufacturer", p["mfr"])):
        if val:
            fp.SetField(key, val)
            fp.GetFieldByName(key).SetVisible(False)
    linked += 1
pcbnew.SaveBoard(mb.PCB, board)
print("linked", linked)
