import sys
sys.path.insert(0, "../schematic")
import pcbnew
from pcbnew import ToMM
import design_b as d
SUPPORT = "/Applications/KiCad/KiCad.app/Contents/SharedSupport"
LOCAL = "/Users/ilkercetinkaya/Desktop/PCB_design_claude/NIGHTHAWK_ESL/RevB/schematic/NH_REVB.pretty"
seen = {}
for p in d.PARTS:
    if not p["fp"] or p["fp"] in seen:
        continue
    lib, name = p["fp"].split(":")
    path = LOCAL if lib == "NH_REVB" else f"{SUPPORT}/footprints/{lib}.pretty"
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        seen[p["fp"]] = None
        print("MISSING", p["fp"])
        continue
    bb = fp.GetBoundingBox(False)
    cy = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    seen[p["fp"]] = (ToMM(bb.GetWidth()), ToMM(bb.GetHeight()), ToMM(cy.GetWidth()), ToMM(cy.GetHeight()), len(list(fp.Pads())))
    print(f'{p["fp"]:90s} bbox {ToMM(bb.GetWidth()):.1f}x{ToMM(bb.GetHeight()):.1f} crtyd {ToMM(cy.GetWidth()):.1f}x{ToMM(cy.GetHeight()):.1f} pads {len(list(fp.Pads()))}')
