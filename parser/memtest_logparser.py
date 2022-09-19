import csv

f = open("/root/git/cxl-sim/m5out/debug_dram_0_1_1_50.log", 'r')
csv_f = open("/root/tmp/dram_breakdown.csv", 'w', newline='')
wr = csv.writer(csv_f)

stages_str = [
    'l1rreq',
    'l2Brreq',
    'l2rreq',
    'MBrreq',
    'Maccess',
    'Mcmd',
    'MBrres',
    'l2rres',
    'l2sres',
    'l2Brres',
    'l1rres',
    'l1sres',
    'end',
]

stages = zip(stages_str, [range(len(stages_str))])

delete_cmd = [
    'CleanEvict',
    'WritebackDirty',
    'CxlWritebackDirty',
    'CxlWriteResp',
]

tmp_results = {}
results = []
final_results = []

while True:
    line = f.readline()[:-1]
    if not line:
        break
    line = line.split(": ")

    stage = line[2]
    addr = int(line[3], 16)
    timestamp = int(line[4])
    cmd = line[5]

    if cmd in delete_cmd:
        continue

    if stage == 'l1rreq':
        tmp_results[addr] = [timestamp]
    elif stage == 'end':
        tmp_results[addr].append(timestamp)
        tmp_result = tmp_results.pop(addr, None)
        tmp_result.append(addr)
        results.append(tmp_result)
    else:
        tmp_results[addr].append(timestamp)

for res in results:
    addr = res.pop()
    final_result = [time - res[i-1] for i, time in enumerate(res)][1:]
    final_result.append(res[-1] - res[0])
    final_result.append(addr)

    final_results.append(final_result)

for res in final_results:
    wr.writerow(res)

f.close()
csv_f.close()