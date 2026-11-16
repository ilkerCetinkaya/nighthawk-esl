import re,sys,glob
pins={}
for f in sorted(glob.glob('*.kicad_sch')):
    s=open(f).read()
    for m in re.finditer(r'\(symbol "([^"]+:[^"]+)"',s):
        pass
    i=s.find('(lib_symbols')
    if i<0: continue
    depth=0;j=i
    while True:
        c=s[j]
        if c=='(':depth+=1
        elif c==')':
            depth-=1
            if depth==0:break
        j+=1
    blk=s[i:j]
    for sm in re.finditer(r'\n\t\t\(symbol "([^"]+:[^"]+)"',blk):
        name=sm.group(1)
        k=sm.start()+1;d=0;e=k
        while True:
            c=blk[e]
            if c=='(':d+=1
            elif c==')':
                d-=1
                if d==0:break
            e+=1
        body=blk[k:e]
        pl=re.findall(r'\(pin (\w+) \w+.*?\(name "([^"]*)".*?\(number "([^"]*)"',body,re.S)
        pins[name]=pl
want=sys.argv[1:]
for n,pl in pins.items():
    if any(w in n for w in want):
        print(n,sorted([(p[2],p[1]) for p in pl],key=lambda x:(len(x[0]),x[0])))
