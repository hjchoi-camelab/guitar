import csv
import os
import re
import numpy as np
import pandas as pd
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

line_txt = [
    'simTicks',
    'system.l2.overallAvgMissLatency::total',
    'system.type_three.cxl_mem_ctrls0.readReqs',
    'system.type_three.cxl_mem_ctrls0.writeReqs',
    'system.type_three.cxl_mem_ctrls0.dram.readRowHitRate',
    'system.type_three.cxl_mem_ctrls0.dram.writeRowHitRate',
    'system.type_three.cxl_mem_ctrls0.dram.pageHitRate',
    'system.type_three.cxl_mem_ctrls1.readReqs',
    'system.type_three.cxl_mem_ctrls1.writeReqs',
    'system.type_three.cxl_mem_ctrls1.dram.readRowHitRate',
    'system.type_three.cxl_mem_ctrls1.dram.writeRowHitRate',
    'system.type_three.cxl_mem_ctrls1.dram.pageHitRate',
]

rankAct_txt = r'system\.type_three\.cxl_mem_ctrls\d+\.dram\.rank\d+\.pwrStateTime::ACT'
bankRdBurst_txt = r'system\.type_three\.cxl_mem_ctrls\d+\.dram\.perBankRdBursts::\d+'
bankWrBurst_txt = r'system\.type_three\.cxl_mem_ctrls\d+\.dram\.perBankWrBursts::\d+'

avgGap = []
rankAct = {}
bankRdBurst = {}
bankWrBurst = {}

TYPE="single"
OUTPUT_DIR=f"/home/hjchoi/replay/{TYPE}"
SELECTED_WORKLOAD=[
    '429.mcf.csv',
    '433.milc.csv',
    '434.zeusmp.csv',
    '437.leslie3d.csv',
    '445.gobmk.csv',
    '453.povray.csv',
    '459.GemsFDTD.csv',
    '470.lbm.csv',
    '471.omnetpp.csv',
]
COLUMNS = [
    'Workload',
    'Addr Mapping (str)', 'Addr Mapping (idx)',
    'Sim Ticks',
    'L2 Miss Latency',
    'Read Reqs 0', 'Write Reqs 0',
    'Read Row Hit Rate 0', 'Write Row Hit Rate 0',
    'Row Hit Rate 0',
    'Read Reqs 1', 'Write Reqs 1',
    'Read Row Hit Rate 1', 'Write Row Hit Rate 1',
    'Row Hit Rate 1',
    'Bank Rd Burst Std 0', 'Bank Wr Burst Std 0',
    'Bank Rd Burst Std 1', 'Bank Wr Burst Std 1',
    'Requests 0', 'Requests 1', 'Request Ratio',
    'Rank Act Ratio 0', 'Rank Act Ratio 1',
    'Bank Burst Std 0', 'Bank Burst Std 1',
    'Ctrl Num', 'Device Num', 'Switch Num',
]
INT_COLUMNS=[
    'Sim Ticks',
    'Read Reqs 0', 'Write Reqs 0',
    'Read Reqs 1', 'Write Reqs 1',
]

for (path, dir, files) in os.walk(f"/home/hjchoi/result/gem5-ARM-SPEC-CPU2006/replay/{TYPE}"):
    if path.split('/')[-1] == f"{TYPE}":
        continue
    output_filename = f"{path.split('/')[-1]}"
    if output_filename[7:] not in SELECTED_WORKLOAD:
        continue
    print(output_filename)
    row_list = []

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
        
        # Workload, Addr Mapping (str), Addr Mapping (idx)
        row = [output_filename[7:], addr_mapping_str, addr_mapping_idx]

        f = open(f'{path}/{filename}', 'r')
        for i, line in enumerate(f):
            if line == '\n':
                continue
            splitted_line = line.split()
            if splitted_line[0] in line_txt:
                if splitted_line[0] in INT_COLUMNS:
                    item = int(splitted_line[1])
                else:
                    item = float(splitted_line[1])
                row.append(item)
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

        row.append(bankRdBurst_std0)                            # Bank Rd Burst Std 0
        row.append(bankWrBurst_std0)                            # Bank Wr Burst Std 0
        row.append(bankRdBurst_std1)                            # Bank Rd Burst Std 1
        row.append(bankWrBurst_std1)                            # Bank Wr Burst Std 1
        row.append(row[5] + row[6])                             # Requests 0
        row.append(row[10] + row[11])                           # Requests 1
        row.append(get_ratio([row[-1], row[-2]]))               # Request Ratio
        row.append(get_ratio(rankAct['0']))                     # Rank Act Ratio 0
        row.append(get_ratio(rankAct['1']))                     # Rank Act Ratio 1
        row.append((bankRdBurst_std0 + bankWrBurst_std0) / 2)   # Bank Burst std 0
        row.append((bankRdBurst_std1 + bankWrBurst_std1) / 2)   # Bank Burst std 1
        row.append(splitted_filename[3])                        # Ctrl Num
        row.append(1)                                           # Device Num
        row.append(0)                                           # Switch Num

        row_list.append(dict(zip(COLUMNS, row)))
        f.close()
    
    df = pd.DataFrame(row_list, columns=COLUMNS)
    df.to_csv(f"{OUTPUT_DIR}/csv/original/{output_filename}.csv", index=False)
    df.to_excel(f"{OUTPUT_DIR}/xlsx/original/{output_filename}.xlsx", index=False)
