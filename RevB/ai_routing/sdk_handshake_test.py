import asyncio, json, time
from mcp_client import Session
async def main():
    t=time.time()
    async with Session("freerouting") as s:
        tl=await s.tools()
        print("tools",len(tl),"handshake+list",round(time.time()-t,1),"s")
        r=await s.call("get_system_status")
        print("get_system_status",json.dumps(r)[:200])
asyncio.run(main())
