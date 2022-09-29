import numpy as np
import pandas as pd

DIRECTORY_BEFORE = '/home/hjchoi/result/anns'
DIRECTORY_AFTER = 'sift1M/16'

INPUTS = [
    'atomic-dram16G',
    'atomic-simple16G',
    'timing-dram16G',
    'timing-simple16G'
]

FILE = 'system.terminal'

COLUMNS = [
    1,
    2,
    3,
    4
]

for input_dir in INPUTS:
    row_list = []
    print(f'{DIRECTORY_BEFORE}/{input_dir}/{DIRECTORY_AFTER}/{FILE}')
    f = open(f'{DIRECTORY_BEFORE}/{input_dir}/{DIRECTORY_AFTER}/{FILE}', 'r')
    lines = f.read().splitlines()
    for line in lines:
        if line[:9] != "BREAKDOWN":
            continue
        row = line[18:].split(' ')
        row_list.append(dict(zip(COLUMNS, row)))
    
    df = pd.DataFrame(row_list, columns=COLUMNS).astype(int)
    df.to_csv(f"{DIRECTORY_BEFORE}/{input_dir}.csv", index=True, header=False)
    df.to_excel(f"{DIRECTORY_BEFORE}/{input_dir}.xlsx", index=True, header=False)
    f.close()