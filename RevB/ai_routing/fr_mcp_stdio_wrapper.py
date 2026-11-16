import json
import os
import subprocess
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
JAVA = "/Users/ilkercetinkaya/Desktop/PCB_design_claude/GPace copy/build/tools/jre25/jdk-25.0.4.1+1-jre/Contents/Home/bin/java"
CMD = [JAVA, "-jar", f"{HERE}/freerouting-2.5.0.jar", "--api_server.enabled=true", "--api_server.authentication.enabled=false",
       "--mcp_server.enabled=true", "--mcp_server.authentication.enabled=false", "--mcp_server.stdio=true", "--gui.enabled=false"]

LOGP = f"{HERE}/results/fr_wrap.log" if os.path.exists(f"{HERE}/wraplog.enable") else None
proc = subprocess.Popen(CMD, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)


def pump_in():
    try:
        while True:
            chunk = os.read(sys.stdin.fileno(), 65536)
            if not chunk:
                break
            proc.stdin.write(chunk)
            if LOGP:
                open(LOGP, 'ab').write(b'>> ' + chunk)
    except Exception:
        pass
    try:
        proc.stdin.close()
    except Exception:
        pass


threading.Thread(target=pump_in, daemon=True).start()
buf = b""
out = sys.stdout.buffer
while True:
    chunk = os.read(proc.stdout.fileno(), 65536)
    if not chunk:
        break
    buf += chunk
    while b"\n" in buf:
        line, buf = buf.split(b"\n", 1)
        line = line.strip()
        if LOGP:
            open(LOGP, 'ab').write(b'<< ' + line + b'\n')
        if line.startswith(b"{"):
            if b'"tools"' in line and b"outputSchema" in line:
                try:
                    msg = json.loads(line)
                    for tool in msg.get("result", {}).get("tools", []):
                        tool.pop("outputSchema", None)
                    line = json.dumps(msg, separators=(",", ":")).encode()
                except Exception:
                    pass
            out.write(line + b"\n")
            out.flush()
sys.exit(proc.wait())
