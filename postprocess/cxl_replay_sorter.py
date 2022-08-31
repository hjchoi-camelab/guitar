import os
import pandas as pd
import numpy as np
  
np_list = []
for (path, dir, files) in os.walk("/home/hjchoi/replay/csv/selected"):
    for f in files:
        if f[-3:] != 'csv':
            continue
        workload = f[7:-4]
        csv_data = pd.read_csv(f"{path}/{f}")
        csv_data.sort_values(["Sim Ticks"], 
                            axis=0,
                            ascending=[True], 
                            inplace=True)
        # print(csv_data[-50:])
        np_list.extend(csv_data["Addr Mapping (str)"][:10].values.tolist())
np_list = np.array(np_list)
unique, counts = np.unique(np_list, return_counts=True)

print (np.asarray((unique, counts)).T)