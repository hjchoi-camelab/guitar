from string import Template
from typing import Dict, List, Tuple
import itertools


class PercentTemplate(Template):
    delimiter = "%"


class ScriptGenerator:
    template_path: str  # path to template
    template: PercentTemplate
    options: Dict[str, List]  # dict of options to experiment

    def __init__(self, template_path):
        self.template_path = template_path

        with open(template_path) as f:
            template_str = f.read()

        self.template = PercentTemplate(template_str)

        self.options = {}

    def generate(self) -> Tuple[List[Dict], List[str]]:
        if len(self.options) == 0:
            print("set options before generation")
            exit(1)

        keys = list(self.options.keys())

        # generate combination of option idxs
        num_options = [len(self.options[k]) for k in keys]
        option_idxs = [list(range(n)) for n in num_options]

        idx_combination = itertools.product(*option_idxs)

        # generate all set of option
        experiments = []
        for comb in idx_combination:
            exp = {}
            for i, key in enumerate(keys):
                exp[key] = self.options[key][comb[i]]
            experiments.append(exp)

        # generate script
        scripts = []
        for exp in experiments:
            scripts.append(self.template.substitute(exp))

        return experiments, scripts
