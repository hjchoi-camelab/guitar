#!/usr/bin/env python

import os
import operator
import pandas as pd
import numpy as np

rankings = {}
max_rankings = {}
file_count = 0
for (path, dir, files) in os.walk("/home/hjchoi/replay/multi/csv/original"):
    for f in files:
        if f[-3:] != 'csv':
            continue
        file_count += 1
        workload = f[7:-4]
        csv_data = pd.read_csv(f"{path}/{f}")
        csv_data.sort_values(["Sim Ticks"], 
                            axis=0,
                            ascending=[True], 
                            inplace=True)
        ranking_list = csv_data["Addr Mapping (str)"].values.tolist()
        for ranking, addr_mapping in enumerate(ranking_list):
            rankings[addr_mapping] = rankings.get(addr_mapping, 0) + ranking
            max_rankings[addr_mapping] = max(max_rankings.get(addr_mapping, 0), ranking)

for ranking in rankings:
    rankings[ranking] = int(rankings[ranking] / file_count)

sorted_rankings = sorted(rankings.items(), key=operator.itemgetter(1))
sorted_max_rankings = sorted(max_rankings.items(), key=operator.itemgetter(1))

print(sorted_rankings[:10])
print(sorted_max_rankings)