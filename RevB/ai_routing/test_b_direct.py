import os, sys, time, json
H = os.path.dirname(os.path.abspath(__file__))
os.environ["KICAD_MCP_PROJECT_DIR"] = H + "/sandbox/testB"
os.environ["KICAD_MCP_WORKSPACE_ROOT"] = H + "/sandbox/testB"
os.environ["KICAD_MCP_KICAD_CLI"] = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
from pathlib import Path
from kicad_mcp.utils.freerouting import FreeRoutingRunner
r = FreeRoutingRunner()
r._java_executable = "/Users/ilkercetinkaya/Desktop/PCB_design_claude/GPace copy/build/tools/jre25/jdk-25.0.4.1+1-jre/Contents/Home/bin/java"
t = time.time()
res = r.run_freerouting(Path(H + "/sandbox/testB/output/routing/subset.dsn"), Path(H + "/sandbox/testB/output/routing/subset_kmp.ses"), use_docker=False, freerouting_jar_path=Path(H + "/freerouting-2.5.0.jar"), max_passes=20, thread_count=4, timeout=900)
print("seconds", round(time.time() - t, 1))
print(res.mode, res.returncode, res.routed_pct, res.total_nets, res.unrouted_nets, res.pass_count, res.wall_seconds)
print(res.stdout_tail[-800:])
print(res.stderr[-500:])
