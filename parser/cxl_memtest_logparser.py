import csv

f = open("../gem5/m5out/cxl_262144.log", 'r')
csv_f = open("cxl_read.csv", 'w', newline='')
wr = csv.writer(csv_f)

stages = {
    'l1m': 0,
    'l2m': 1,
    'uti': 2,
    'utp': 3,
    'dsp': 4,
    't3s': 5,
    'dti': 6,
    'dtp': 7,
    'usp': 8,
    'l2r': 9,
    'l1r': 10,
    'l1h': 11,
    'l2h': 12
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

    if line[2] != 'l1m' and line[3] == 'WRITE':
        continue
    
    timestamp = int(line[0])
    stage = stages[line[2]]
    addr = int(line[4], 16)
    
    # if addr == 411593792:
    #     print(f"stage = {stage}")
    #     breakpoint()

    if stage == 0:
        if addr in tmp_results:
            tmp_results.pop(addr, None)
            tmp_results[addr] = [timestamp]
        else:
            tmp_results[addr] = [timestamp]
    elif stage == 1:
        tmp_results[addr].append(timestamp)
    elif stage == 2:
        tmp_results[addr].append(timestamp)
    elif stage == 3:
        tmp_results[addr].append(timestamp)
    elif stage == 4:
        tmp_results[addr].append(timestamp)
    elif stage == 5:
        tmp_results[addr].append(timestamp)
    elif stage == 6:
        tmp_results[addr].append(timestamp)
    elif stage == 7:
        tmp_results[addr].append(timestamp)
    elif stage == 8:
        tmp_results[addr].append(timestamp)
    elif stage == 9:
        tmp_results[addr].append(timestamp)
    elif stage == 10:
        if addr in tmp_results:
            tmp_results[addr].append(timestamp)
            tmp_result = tmp_results.pop(addr, None)
            tmp_result.append(line[4])
            results.append(tmp_result)
        else:
            continue
    elif stage == 11:
        continue
    elif stage == 12:
        tmp_results.pop(addr, None)
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