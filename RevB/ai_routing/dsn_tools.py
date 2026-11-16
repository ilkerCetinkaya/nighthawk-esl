import os
import sys

import pcbnew


def export_dsn(pcb, dsn):
    os.makedirs(os.path.dirname(dsn), exist_ok=True)
    board = pcbnew.LoadBoard(pcb)
    ok = pcbnew.ExportSpecctraDSN(board, dsn)
    print("export", ok, os.path.getsize(dsn))


def import_ses(pcb, ses, out):
    board = pcbnew.LoadBoard(pcb)
    ok = pcbnew.ImportSpecctraSES(board, ses)
    pcbnew.SaveBoard(out, board)
    print("import", ok)


if __name__ == "__main__":
    {"export": lambda: export_dsn(sys.argv[2], sys.argv[3]), "import": lambda: import_ses(sys.argv[2], sys.argv[3], sys.argv[4])}[sys.argv[1]]()
