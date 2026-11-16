import asyncio, logging, sys
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
from mcp_client import Session
async def main():
    async with Session("freerouting") as s:
        try:
            r = await asyncio.wait_for(s.cs.call_tool("get_system_status", {}), 25)
            print("OK", str(r)[:200])
        except Exception as e:
            print("EXC", type(e).__name__, str(e)[:400])
asyncio.run(main())
