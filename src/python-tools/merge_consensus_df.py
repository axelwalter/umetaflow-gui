import json
import sys
import pandas as pd
from pathlib import Path

############################
# default paramter values #
###########################
#
# Mandatory keys for each parameter
# key: a unique identifier
# value: the default value
#
# Optional keys for each parameter
# name: the name of the parameter
# hide: don't show the parameter in the parameter section (e.g. for input/output files)
# options: a list of valid options for the parameter
# min: the minimum value for the parameter (int and float)
# max: the maximum value for the parameter (int and float)
# step_size: the step size for the parameter (int and float)
# help: a description of the parameter
# widget_type: the type of widget to use for the parameter (default: auto)
# advanced: whether or not the parameter is advanced (default: False)

DEFAULTS = [
    {"key": "in", "value": [], "help": "consensus df ffm complete, consensus df ffmid", "hide": True},
    {"key": "out", "value": [], "help": "consensus df merged parquet file", "hide": True}
]

def get_params():
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as f:
            return json.load(f)
    else:
        return {}

if __name__ == "__main__":
    params = get_params()
    # Add code here:
    df_ffm = pd.read_parquet(params["in"][0])
    df_ffmid = pd.read_parquet(params["in"][1])
    
    df = pd.concat([df_ffm, df_ffmid]).reset_index(drop=True)
    df.index.name = "id"
    
    path = Path(params["out"][0])
    df.to_parquet(path)
    # save additionally as tsv file
    df.to_csv(path.with_suffix(".tsv"), sep="\t")