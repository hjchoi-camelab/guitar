#!/usr/bin/env python

import os
import pandas as pd
import numpy as np

DIRECTORY = '/home/hjchoi/result/anns/sift1M/CXL'
output = DIRECTORY.split('/')[-1] + '_distance_calculation'

out_list = []

for (path, dir, files) in os.walk(DIRECTORY):
    for f in files:
        if path[-3:] != 'CXL':
            continue
        if f[-24:] != 'distance_calculation.csv':
            continue
        print(f"{path}/{f}")
        search_l = int(f.split('_')[0])
        memory_size = f.split('_')[1]

        csv_data = pd.read_csv(f"{path}/{f}")
        mean = csv_data.mean().to_frame().T
        mean['search_l'] = search_l
        mean['memory_size'] = memory_size
        print(mean)

        out_list.append(mean)

df = pd.concat(out_list, axis=0, ignore_index=True)
df.sort_values(["search_l"],
    axis=0,
    ascending=[True],
    inplace=True)
print(f'\n{DIRECTORY}/{output}')
print(df)

df.to_csv(f'{DIRECTORY}/{output}.csv', index=False)
df.to_excel(f'{DIRECTORY}/{output}.xlsx', index=False)
