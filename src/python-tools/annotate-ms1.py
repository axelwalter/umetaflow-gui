import json
import sys
from pathlib import Path
import zipfile
import pandas as pd

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
    {"key": "in", "value": [], "help": "Feature Matrix parquet file", "hide": True},
    {"key": "in_lib", "value": "", "help": "MS1 library for annotation", "hide": True},
    {"key": "ms1-annotation-rt-window", "name": "RT window for annotation", "value": 10, "min": 1, "max": 240, "step_size": 5, "help": "Checks around peak apex, e.g. window of 60 s will check left and right 30 s."},
    {"key": "ms1-annotation-mz-tolerance", "name": "m/z tolerance in ppm", "value": 10, "min": 1, "max": 100, "step_size": 5, "help": "Select m/z tolerance for MS1 feature annotation."}    
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
    df = pd.read_parquet(params["in"][0])
    library = pd.read_csv(params["in_lib"], sep="\t")
    df.insert(2, "MS1 annotation", "")

    df["mz"] = df["mz"].astype(float)

    for _, std in library.iterrows():
        delta_Da = abs(params["ms1-annotation-mz-tolerance"] * std["mz"] / 1000000)
        mz_lower = std["mz"] - delta_Da
        mz_upper = std["mz"] + delta_Da
        rt_lower = std["RT"] - params["ms1-annotation-rt-window"] / 2
        rt_upper = std["RT"] + params["ms1-annotation-rt-window"] / 2
        match = df.query(
            "mz > @mz_lower and mz < @mz_upper and RT > @rt_lower and RT < @rt_upper"
        )
        if not match.empty:
            for _, row in match.iterrows():
                if len(df.loc[df["metabolite"] == row["metabolite"], "MS1 annotation"]) > 1:
                    df.loc[df["metabolite"] == row["metabolite"], "MS1 annotation"] += (
                        ";" + std["name"]
                    )
                else:
                    df.loc[df["metabolite"] == row["metabolite"],
                            "MS1 annotation"] += std["name"]


    df.to_parquet(params["in"][0])
    df.to_csv(Path(params["in"][0]).with_suffix(".tsv"), sep="\t")