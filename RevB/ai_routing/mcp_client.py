import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

JAVA = "/Users/ilkercetinkaya/Desktop/PCB_design_claude/GPace copy/build/tools/jre25/jdk-25.0.4.1+1-jre/Contents/Home/bin/java"
HERE = __file__.rsplit("/", 1)[0]
SERVERS = {
    "freerouting": StdioServerParameters(command=f"{HERE}/.venv/bin/python", args=[f"{HERE}/fr_mcp_stdio_wrapper.py"]),
    "kicad": StdioServerParameters(
        command=f"{HERE}/.venv/bin/kicad-mcp-pro",
        args=["--transport", "stdio", "--project-dir", __import__("os").environ.get("KPROJ", f"{HERE}/sandbox"), "--profile", __import__("os").environ.get("KPROFILE", "pcb_layout"), "--mode", __import__("os").environ.get("KMODE", "write"), "--no-telemetry"],
        env={"KICAD_MCP_WORKSPACE_ROOT": __import__("os").environ.get("KPROJ", f"{HERE}/sandbox"), "KICAD_MCP_KICAD_CLI": "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"},
    ),
}


class Session:
    def __init__(self, name):
        self.name = name

    async def __aenter__(self):
        self.cm = stdio_client(SERVERS[self.name])
        r, w = await self.cm.__aenter__()
        self.cs = ClientSession(r, w)
        await self.cs.__aenter__()
        await self.cs.initialize()
        return self

    async def __aexit__(self, *a):
        await self.cs.__aexit__(*a)
        await self.cm.__aexit__(*a)

    async def tools(self):
        return (await self.cs.list_tools()).tools

    async def call(self, tool, args=None):
        res = await self.cs.call_tool(tool, args or {})
        if getattr(res, "structuredContent", None):
            return res.structuredContent
        return "\n".join(getattr(c, "text", str(c)) for c in res.content)


async def main():
    name = sys.argv[1]
    async with Session(name) as s:
        tl = await s.tools()
        names = sys.argv[2:]
        if names:
            for t in tl:
                if t.name in names:
                    print(t.name, json.dumps(t.inputSchema.get("properties", {}))[:1000], "REQ", t.inputSchema.get("required"))
                    print("   ", (t.description or "")[:500].replace("\n", " "))
            return
        print(len(tl), "tools")
        for t in tl:
            print(t.name, "-", (t.description or "").split("\n")[0][:110])


if __name__ == "__main__":
    asyncio.run(main())
