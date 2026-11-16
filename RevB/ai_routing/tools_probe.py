import json,subprocess,time,select,os
c=json.load(open('/Users/ilkercetinkaya/Desktop/PCB_design_claude/.mcp.json'))['mcpServers']['kicad-pro']
env=dict(os.environ); env.update(c['env'])
p=subprocess.Popen([c['command']]+c['args'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=env,bufsize=0)
buf=b""
def rpc(i,m,params,limit=90):
    global buf
    p.stdin.write((json.dumps({"jsonrpc":"2.0","id":i,"method":m,"params":params})+"\n").encode())
    t=time.time()
    while time.time()-t<limit:
        while b"\n" in buf:
            l,buf=buf.split(b"\n",1)
            if l.strip():
                m_=json.loads(l)
                if m_.get("id")==i: return m_,time.time()-t
        r,_,_=select.select([p.stdout],[],[],1)
        if r: buf+=os.read(p.stdout.fileno(),1<<20)
    return None,limit
r,t=rpc(1,"initialize",{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"1"}}); print("init",round(t,1))
p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
for k in range(3):
    r,t=rpc(10+k,"tools/list",{}); n=len(r["result"]["tools"]) if r else None; print("tools/list",k,round(t,1),"s ->",n)
    if n: break
    time.sleep(10)
p.kill()
