f = open("/home/hjchoi/data/git/cxl-sim/m5out/coherentXbar_simout2", 'r')

results = {
    "req": set(),
    "resp": set(),
    "snoop_req": set(),
    "snoop_resp": set(),
    "forward": set(),
}

while True:
    line = f.readline()[:-1]
    if not line:
        break
    line = line.split(": ")
    
    timestamp = int(line[0])
    func_name = line[2]
    cmd = line[4]

    if func_name == "recvTimingReq":
        results['req'].add(cmd)
    elif func_name == "recvTimingResp":
        results['resp'].add(cmd)
    elif func_name == "recvTimingSnoopReq":
        results['snoop_req'].add(cmd)
    elif func_name == "recvTimingSnoopResp":
        results['snoop_resp'].add(cmd)
    elif func_name == "forwardTiming":
        results['forward'].add(cmd)

f.close()

print(results)
