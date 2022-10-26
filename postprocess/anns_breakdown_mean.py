import os
import pandas as pd

DIRECTORY = '/root/git/anns/faiss-experiments/results/test'

for (path, dir, files) in os.walk(DIRECTORY):
    for file in files:
        if file[-3:] != 'csv':
            continue
        workload = file[:-4]
        csv_data = pd.read_csv(f"{DIRECTORY}/{file}")
        mean = csv_data.mean()
        print(file)
        print(mean)
        print('\n')