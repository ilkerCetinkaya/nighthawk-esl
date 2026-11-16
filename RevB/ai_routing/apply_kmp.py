import os, sys, shutil
H = os.path.dirname(os.path.abspath(__file__))
d = sys.argv[1]
os.environ["KICAD_MCP_PROJECT_DIR"] = d
os.environ["KICAD_MCP_WORKSPACE_ROOT"] = d
os.environ["KICAD_MCP_PCB_FILE"] = f"{d}/subset.kicad_pcb"
os.environ["KICAD_MCP_KICAD_CLI"] = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
from kicad_mcp.tools.routing_ses_apply import _default_dependencies
r = _default_dependencies().service.apply(sys.argv[2])
print(str(r)[:800])
