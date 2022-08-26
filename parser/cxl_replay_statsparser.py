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

for (path, dir, files) in os.walk("/home/hjchoi/result/gem5-ARM-SPEC-CPU2006/replay/replay_403.gcc"):
    csv_f = open(f"{path.split('/')[-1]}.csv", 'w', newline='')
    wr = csv.writer(csv_f)
    wr.writerow(['Addr Mapping (str)', 'Addr Mapping (idx)', \
                'Ctrl Num', 'Device Num', 'Switch Num', 'Sim Ticks',])

    for filename in files:
        if "stats" not in filename:
            continue
        splitted_filename = filename[:-10].split('_')
        addr_mapping_idx = int(splitted_filename[2])
        addr_mapping_num = addr_mapping_table[addr_mapping_idx]
        addr_mapping_str = ''
        for num in addr_mapping_num:
            addr_mapping_str += addr_mapping_num2str[num]
        
        row = []
        row.append(addr_mapping_str)
        row.append(addr_mapping_idx)
        row.append(splitted_filename[3])
        row.append(1)
        row.append(0)

        f = open(f'{path}/{filename}', 'r')
        for i, line in enumerate(f):
            if i == 3:
                sim_ticks = line.split()[1]
                row.append(sim_ticks)
            elif i > 4:
                break
        print(f'{filename} | {row}')
        wr.writerow(row)
        f.close()

csv_f.close()