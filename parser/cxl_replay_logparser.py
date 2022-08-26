import csv

f = open("/root/git/cxl-sim/m5out/replay_454.calculix_1_0_2_0_1_debug.log", 'r')
csv_f = open("parsed_log.csv", 'w', newline='')
wr = csv.writer(csv_f)

stages = {
    'rpReq': 0,
    't3Req': 1,
    'mcReq': 2,
    't3Resp': 3,
    'rpResp': 4,
}

tmp_results = {}
results = []
final_results = []

# i = 0
while True:
    # i += 1
    # if i == 200: break
    line = f.readline()[:-1]
    if not line: break
    line = line.split(": ")
    
    timestamp = int(line[0])
    stage = stages[line[2]]
    addr = int(line[4], 16)

    if stage == 0:
        # if addr in tmp_results:
        #     tmp_results.pop(addr, None)
        #     tmp_results[addr] = [timestamp]
        # else:
        tmp_results[addr] = [timestamp]
    elif stage == 1:
        tmp_results[addr].append(timestamp)
    elif stage == 2:
        tmp_results[addr].append(timestamp)
    elif stage == 3:
        tmp_results[addr].append(timestamp)
    elif stage == 4:
        tmp_results[addr].append(timestamp)
        tmp_result = tmp_results.pop(addr, None)
        tmp_result.append(line[4])
        results.append(tmp_result)
    else:
        print("Something wrong")
        exit()

for res in results:
    addr = res.pop()
    final_result = [time - res[i-1] for i, time in enumerate(res)][1:]
    final_result.append(res[-1] - res[0])
    final_result.append(addr)

    final_results.append(final_result)

for res in final_results:
    # print(res)
    wr.writerow(res)

f.close()
csv_f.close()