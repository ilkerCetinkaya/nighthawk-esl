import json
import os
import select
import subprocess
import time

JAVA = "/Users/ilkercetinkaya/Desktop/PCB_design_claude/GPace copy/build/tools/jre25/jdk-25.0.4.1+1-jre/Contents/Home/bin/java"
HERE = __file__.rsplit("/", 1)[0]


class FR:
    def __init__(self):
        self.p = subprocess.Popen(
            ["/bin/sh", "-c", 'exec "$0" "$@"', JAVA, "-jar", f"{HERE}/freerouting-2.5.0.jar", "--api_server.enabled=true", "--api_server.authentication.enabled=false",
             "--mcp_server.enabled=true", "--mcp_server.authentication.enabled=false", "--mcp_server.stdio=true", "--gui.enabled=false"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
        self.buf = b""
        self.i = 0
        self.rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "nighthawk", "version": "1"}}, 240)
        self.p.stdin.write((json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n").encode())
        self.p.stdin.flush()

    def rpc(self, method, params, timeout=60):
        self.i += 1
        self.p.stdin.write((json.dumps({"jsonrpc": "2.0", "id": self.i, "method": method, "params": params}) + "\n").encode())
        self.p.stdin.flush()
        end = time.time() + timeout
        while time.time() < end:
            while b"\n" in self.buf:
                line, self.buf = self.buf.split(b"\n", 1)
                line = line.strip()
                if not line:
                    continue
                msg = json.loads(line)
                if msg.get("id") == self.i:
                    return msg
            r, _, _ = select.select([self.p.stdout], [], [], 1)
            if r:
                chunk = os.read(self.p.stdout.fileno(), 65536)
                if not chunk:
                    raise EOFError("freerouting closed stdout")
                self.buf += chunk
        raise TimeoutError(method)

    def call(self, tool, args=None, timeout=60):
        msg = self.rpc("tools/call", {"name": tool, "arguments": args or {}}, timeout)
        if "error" in msg:
            return {"error": msg["error"]}
        res = msg["result"]
        if res.get("structuredContent"):
            return res["structuredContent"]
        text = "".join(c.get("text", "") for c in res.get("content", []))
        try:
            return json.loads(text)
        except Exception:
            return text

    def tools(self):
        return self.rpc("tools/list", {}, 60)["result"]["tools"]

    def close(self):
        self.p.kill()
