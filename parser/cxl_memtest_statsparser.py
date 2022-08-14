import csv
import os
from itertools import permutations

# 0  | 1  | 2  | 3  | 4
# Ro | Ra | Ba | Co | Ch
addr_mapping_table = list(''.join(s) for s in permutations(['0', '1', '2', '3', '4'], 5))
addr_mapping_num2str = {
    '0': 'Ro',
    '1': 'Ra',
    '2': 'Ba',
    '3': 'Co',
    '4': 'Ch'
}

csv_f = open("sequential_cxl.csv", 'w', newline='')
wr = csv.writer(csv_f)

wr.writerow(['Type', 'Addr Mapping (idx)', 'Addr Mapping (str)', 'Ctrl Num', 'Random', 'Read (%)', 'Sim Ticks', 'Read Num', 'Read BW (MiB/s)', \
            'Write Num', 'Write BW (MiB/s)', 'Read Latency (ps)', 'Write Latency (ps)'])

for (path, dir, files) in os.walk("/root/gem5/m5out"):
    for filename in files:
        if "stats" not in filename:
            continue
        # path = "/root/gem5/m5out/0"
        # filename = "stats_dram_0_4_1_100.txt"
        f = open(f'{path}/{filename}', 'r')
        row = filename[6:-4].split('_')
        addr_mapping_num = addr_mapping_table[int(row[1])]
        addr_mapping_str = ''
        for num in addr_mapping_num:
            addr_mapping_str += addr_mapping_num2str[num]
        row.insert(1, addr_mapping_str)

        for i, line in enumerate(f):
            if i == 3:
                simTicks = int(line.split()[1])
                row.append(simTicks)
            elif i == 10:
                numReads = int(line.split()[1])
                readBW = (numReads * 64) / (simTicks / 1024 / 1024) # MiB/s
                row.append(numReads)
                row.append(readBW)
            elif i == 11:
                numWrites = int(line.split()[1])
                writeBW = (numWrites * 64) / (simTicks / 1024 / 1024) # MiB/s
                row.append(numWrites)
                row.append(writeBW)
            elif i == 14:
                readAvgLatency = line.split()[1] # pico second
                if readAvgLatency == 'nan':
                    readAvgLatency = 0
                row.append(readAvgLatency)
            elif i == 15:
                writeAvgLatency = line.split()[1] # pico second
                if writeAvgLatency == 'nan':
                    writeAvgLatency = 0
                row.append(writeAvgLatency)
            elif i > 15:
                break
        print(f'{filename} | {row}')
        wr.writerow(row)
        f.close()

csv_f.close()