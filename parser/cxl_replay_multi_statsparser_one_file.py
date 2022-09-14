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

TYPE="multi"
OUTPUT_DIR=f"."
OUTPUT_FILENAME="multi_one"
SELECTED_WORKLOAD=[
    '434.zeusmp-445.gobmk-459.GemsFDTD-470.lbm',
    '429.mcf-434.zeusmp-445.gobmk-453.povray',
    '429.mcf-453.povray-459.GemsFDTD-470.lbm',
    '433.milc-434.zeusmp-445.gobmk-471.omnetpp',
    '429.mcf-434.zeusmp-437.leslie3d-470.lbm',
    '429.mcf-433.milc-434.zeusmp-445.gobmk',
]
SELECTED_ADDR_MAPPING=[
    # TOP 5
    'RoChRaBaCo', 'RoChBaRaCo', 'RoRaChBaCo', 'RaRoChBaCo', 'Skylake', # 18, 20, 4, 28, 999
    'RaRoBaCoCh', # 24 [Rank Act Ratio]
    'BaRoRaCoCh', # 48 [Bank Burst Std]
    'CoRoRaBaCh', # 72 [Row Hit Rate]
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
    'Bank Rd Burst CV 0', 'Bank Wr Burst CV 0',
    'Bank Rd Burst CV 1', 'Bank Wr Burst CV 1',
    'Requests 0', 'Requests 1', 'Request Ratio',
    'Rank Act Ratio 0', 'Rank Act Ratio 1',
    'Bank Burst CV 0', 'Bank Burst CV 1',
    'Ctrl Num', 'Device Num', 'Switch Num',
]
INT_COLUMNS=[
    'Sim Ticks',
    'Read Reqs 0', 'Write Reqs 0',
    'Read Reqs 1', 'Write Reqs 1',
]
one_row_list=[]

for (path, dir, files) in os.walk(f"/home/hjchoi/result/gem5-ARM-SPEC-CPU2006/replay/{TYPE}"):
    if path.split('/')[-1] == f"{TYPE}":
        continue
    processing_file = f"{path.split('/')[-1]}"
    if processing_file[7:] not in SELECTED_WORKLOAD:
        continue
    print(processing_file)
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
        
        if addr_mapping_str not in SELECTED_ADDR_MAPPING:
            continue

        avgGap = []
        rankAct['0'] = []
        rankAct['1'] = []
        bankRdBurst['0'] = []
        bankRdBurst['1'] = []
        bankWrBurst['0'] = []
        bankWrBurst['1'] = []
        
        # Workload, Addr Mapping (str), Addr Mapping (idx)
        row = [processing_file[7:], addr_mapping_str, addr_mapping_idx]

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

        cv = lambda x: np.std(x) / np.mean(x)
        bankRdBurst_cv0 = np.apply_along_axis(cv, axis=0, arr=np.array(bankRdBurst['0']))
        bankWrBurst_cv0 = np.apply_along_axis(cv, axis=0, arr=np.array(bankWrBurst['0']))
        bankRdBurst_cv1 = np.apply_along_axis(cv, axis=0, arr=np.array(bankRdBurst['1']))
        bankWrBurst_cv1 = np.apply_along_axis(cv, axis=0, arr=np.array(bankWrBurst['1']))

        row.append(bankRdBurst_cv0)                             # Bank Rd Burst CV 0
        row.append(bankWrBurst_cv0)                             # Bank Wr Burst CV 0
        row.append(bankRdBurst_cv1)                             # Bank Rd Burst CV 1
        row.append(bankWrBurst_cv1)                             # Bank Wr Burst CV 1
        row.append(row[5] + row[6])                             # Requests 0
        row.append(row[10] + row[11])                           # Requests 1
        row.append(get_ratio([row[-1], row[-2]]))               # Request Ratio
        row.append(get_ratio(rankAct['0']))                     # Rank Act Ratio 0
        row.append(get_ratio(rankAct['1']))                     # Rank Act Ratio 1
        row.append((bankRdBurst_cv0 + bankWrBurst_cv0) / 2)     # Bank Burst CV 0
        row.append((bankRdBurst_cv1 + bankWrBurst_cv1) / 2)     # Bank Burst CV 1
        row.append(int(splitted_filename[3]))                   # Ctrl Num
        row.append(1)                                           # Device Num
        row.append(0)                                           # Switch Num

        row_list.append(dict(zip(COLUMNS, row)))
    
    base_tick = 0
    for row in row_list:
        if row['Addr Mapping (str)'] == SELECTED_ADDR_MAPPING[0]:
            base_tick = int(row['Sim Ticks'])
            base_latency = float(row['L2 Miss Latency'])
    for row in row_list:
        row['Sim Ticks'] = float(int(row['Sim Ticks']) / base_tick)
        row['L2 Miss Latency'] = float(float(row['L2 Miss Latency']) / base_latency)
        one_row_list.append(row)
    
df = pd.DataFrame(one_row_list, columns=COLUMNS)
df.sort_values(["Addr Mapping (idx)"], 
                axis=0,
                ascending=[True], 
                inplace=True)
df.to_csv(f"{OUTPUT_DIR}/{OUTPUT_FILENAME}.csv", index=False)
df.to_excel(f"{OUTPUT_DIR}/{OUTPUT_FILENAME}.xlsx", index=False)
    
