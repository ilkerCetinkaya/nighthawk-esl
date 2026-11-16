import json,subprocess,time,select,os,sys
c=json.load(open('/Users/ilkercetinkaya/Desktop/PCB_design_claude/.mcp.json'))['mcpServers']['kicad-pro']
drop=sys.argv[1].split(",") if len(sys.argv)>1 and sys.argv[1] else []
env=dict(os.environ); env.update({k:v for k,v in c['env'].items() if k not in drop})
t=time.time()
p=subprocess.Popen([c['command']]+c['args'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=env,bufsize=0)
p.stdin.write((json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"1"}}})+"\n").encode())
buf=b""
while time.time()-t<45:
    r,_,_=select.select([p.stdout],[],[],1)
    if r:
        buf+=os.read(p.stdout.fileno(),65536)
        if b"\n" in buf: break
print("drop",drop,"->",round(time.time()-t,1),"s",buf[:60])
p.kill()
