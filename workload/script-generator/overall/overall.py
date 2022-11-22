import os
import sys
from pathlib import Path

sys.path.insert(0, '../')
from script_generator import *

# DATASET = ["sift1M", "gist1M"]
DATASET = ["sift1M"]
SEARCH_L = ["16", "32", "64", "128", "256", "512"]
TYPE = ["base", "cache", "ndp", "nearest", "disk", "distributed", "infinite"]

gen = ScriptGenerator(f"one_template.sh")

gen.options = {"DATASET": DATASET, "SEARCH_L": SEARCH_L, "TYPE": TYPE}

experiments, scripts = gen.generate()

for i, (exp, sc) in enumerate(zip(experiments, scripts)):
    SCRIPT_DIR = f"/root/git/guitar/workload/script-generator/scripts/overall_evaluation/{exp['DATASET']}/{exp['TYPE']}"
    Path(SCRIPT_DIR).mkdir(parents=True, exist_ok=True)

    file_name = f"{exp['DATASET']}_{exp['SEARCH_L']}_{exp['TYPE']}.sh"
    filepath = os.path.join(SCRIPT_DIR, file_name)
    print(filepath)

    with open(filepath, "w") as f:
        f.write(sc)

print(f"generated {len(experiments)} experiment scripts")
