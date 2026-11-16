import pcbnew,sys
b=pcbnew.LoadBoard(sys.argv[1])
for ref in sys.argv[2:]:
    fp=b.FindFootprintByReference(ref)
    print(ref,fp.GetValue(),fp.GetFPIDAsString())
    print("  ",sorted([(p.GetNumber(),p.GetNetname()) for p in fp.Pads()],key=lambda x:(len(x[0]),x[0])))
