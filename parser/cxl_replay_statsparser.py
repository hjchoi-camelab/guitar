import csv
import os
import re
import numpy as np
from itertools import permutations

def get_ratio(two_elements):
    if len(two_elements) != 2:
        print("Elements are too many")
        exit(1)
    
    first = two_elements[0]
    second = two_elements[1]

    if first == 0 or second == 0:
        return 9999999

    if first <= second:
        return second / first
    else:
        return first / second

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

line_txt = ['simTicks', \
            'system.type_three.cxl_mem_ctrls0.dram.readRowHitRate', \
            'system.type_three.cxl_mem_ctrls0.dram.writeRowHitRate', \
            'system.type_three.cxl_mem_ctrls1.dram.readRowHitRate', \
            'system.type_three.cxl_mem_ctrls1.dram.writeRowHitRate']

avgGap_txt = r'system\.type_three\.cxl_mem_ctrls\d+\.avgGap'
rankAct_txt = r'system\.type_three\.cxl_mem_ctrls\d+\.dram\.rank\d+\.pwrStateTime::ACT'
bankRdBurst_txt = r'system\.type_three\.cxl_mem_ctrls\d+\.dram\.perBankRdBursts::\d+'
bankWrBurst_txt = r'system\.type_three\.cxl_mem_ctrls\d+\.dram\.perBankWrBursts::\d+'

avgGap = []
rankAct = {}
bankRdBurst = {}
bankWrBurst = {}

for (path, dir, files) in os.walk("/home/hjchoi/result/gem5-ARM-SPEC-CPU2006/replay"):
    csv_f = open(f"{path.split('/')[-1]}.csv", 'w', newline='')
    wr = csv.writer(csv_f)
    wr.writerow(['Addr Mapping (str)', 'Addr Mapping (idx)', \
                'Sim Ticks', \
                'Read Row Hit Rate 0', 'Write Row Hit Rate 0', \
                'Read Row Hit Rate 1', 'Write Row Hit Rate 1', \
                'Avg Gap Ratio', 'Rank Act Ratio 0', 'Rank Act Ratio 1', \
                'Bank Rd Burst Std 0', 'Bank Wr Burst Std 0', \
                'Bank Rd Burst Std 1', 'Bank Wr Burst Std 1', \
                'Ctrl Num', 'Device Num', 'Switch Num'])

    for filename in files:
        if "stats.txt" not in filename:
            continue
        splitted_filename = filename[:-10].split('_')
        addr_mapping_idx = int(splitted_filename[2])
        if addr_mapping_idx < 120:
            addr_mapping_num = addr_mapping_table[addr_mapping_idx]
            addr_mapping_str = ''
            for num in addr_mapping_num:
                addr_mapping_str += addr_mapping_num2str[num]
        else:
            addr_mapping_str = 'Skylake'
        
        avgGap = []
        rankAct['0'] = []
        rankAct['1'] = []
        bankRdBurst['0'] = []
        bankRdBurst['1'] = []
        bankWrBurst['0'] = []
        bankWrBurst['1'] = []
        
        row = []
        row.append(addr_mapping_str)        # Addr Mapping (str)
        row.append(addr_mapping_idx)        # Addr Mapping (idx)

        f = open(f'{path}/{filename}', 'r')
        for i, line in enumerate(f):
            if line == '\n':
                continue
            splitted_line = line.split()
            if splitted_line[0] in line_txt:
                row.append(splitted_line[1])
            elif re.fullmatch(avgGap_txt, splitted_line[0]):
                avgGap.append(float(splitted_line[1]))
            elif re.fullmatch(rankAct_txt, splitted_line[0]):
                ctrl_pos = splitted_line[0].find('ctrls')
                dot_pos = splitted_line[0].find('.', ctrl_pos)
                ctrl_num = splitted_line[0][ctrl_pos+5:dot_pos]
                rankAct[ctrl_num].append(int(splitted_line[1]))
            elif re.fullmatch(bankRdBurst_txt, splitted_line[0]):
                ctrl_pos = splitted_line[0].find('ctrls')
                dot_pos = splitted_line[0].find('.', ctrl_pos)
                ctrl_num = splitted_line[0][ctrl_pos+5:dot_pos]
                bankRdBurst[ctrl_num].append(int(splitted_line[1]))
            elif re.fullmatch(bankWrBurst_txt, splitted_line[0]):
                ctrl_pos = splitted_line[0].find('ctrls')
                dot_pos = splitted_line[0].find('.', ctrl_pos)
                ctrl_num = splitted_line[0][ctrl_pos+5:dot_pos]
                bankWrBurst[ctrl_num].append(int(splitted_line[1]))

        bankRdBurst_std0 = np.array(bankRdBurst['0']).std()
        bankWrBurst_std0 = np.array(bankWrBurst['0']).std()
        bankRdBurst_std1 = np.array(bankRdBurst['1']).std()
        bankWrBurst_std1 = np.array(bankWrBurst['1']).std()

        row.append(get_ratio(avgGap))       # Avg Gap Ratio
        row.append(get_ratio(rankAct['0'])) # Rank Act Ratio 0
        row.append(get_ratio(rankAct['1'])) # Rank Act Ratio 1
        row.append(bankRdBurst_std0)        # Bank Rd Burst Std 0
        row.append(bankWrBurst_std0)        # Bank Wr Burst Std 0
        row.append(bankRdBurst_std1)        # Bank Rd Burst Std 1
        row.append(bankWrBurst_std1)        # Bank Wr Burst Std 1
        row.append(splitted_filename[3])    # Ctrl Num
        row.append(1)                       # Device Num
        row.append(0)                       # Switch Num

        # print(f'{filename} | {row}')
        wr.writerow(row)
        f.close()

csv_f.close()