import os
import sys
from pathlib import Path

sys.path.insert(0, '../')
from script_generator import *

BASE_LIST = ['base', 'ndp', 'cache', 'nearest', 'infinite']

# DATASET = ["sift1M", "gist1M"]
DATASET = ["sift10M"]
SEARCH_L = ["16", "32", "64", "128", "256", "512"]
# TYPE = ["base", "cache", "ndp", "nearest", "disk", "distributed", "infinite"]
TYPE = ["base", "cache", "ndp", "nearest", "disk", "distributed", "infinite"]
OMP_NUM_THREADS = ["1"]
CACHE_BUDGET = ["1600"]

NUM_DISTRIBUTED = 3
NUM_NDP = 8

gen = ScriptGenerator(f"one_template.sh")

gen.options = {"DATASET": DATASET, "SEARCH_L": SEARCH_L, "TYPE": TYPE, "OMP_NUM_THREADS": OMP_NUM_THREADS, "CACHE_BUDGET": CACHE_BUDGET}

experiments, scripts = gen.generate()

for i, (exp, sc) in enumerate(zip(experiments, scripts)):
    SCRIPT_DIR = f"/root/git/guitar/workload/script-generator/scripts/overall_sift10M_evaluation/{exp['DATASET']}/{exp['TYPE']}"
    Path(SCRIPT_DIR).mkdir(parents=True, exist_ok=True)

    if exp['TYPE'] == 'distributed':
        file_name = f"{exp['DATASET']}_{exp['SEARCH_L']}_{exp['TYPE']}_{NUM_DISTRIBUTED}.sh"
    elif exp['TYPE'] in BASE_LIST:
        file_name = f"{exp['DATASET']}_{exp['SEARCH_L']}_{exp['TYPE']}_{NUM_NDP}.sh"
    else:
        file_name = f"{exp['DATASET']}_{exp['SEARCH_L']}_{exp['TYPE']}_1.sh"
    filepath = os.path.join(SCRIPT_DIR, file_name)
    print(filepath)

    with open(filepath, "w") as f:
        f.write(sc)

print(f"generated {len(experiments)} experiment scripts")
