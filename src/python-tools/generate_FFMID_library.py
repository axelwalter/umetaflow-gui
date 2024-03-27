import json
import sys
from pathlib import Path
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
    {"key": "in", "value": [], "help": "feature matrix parquet", "hide": True},
    {"key": "out", "value": [], "help": "FFMID library tsv", "hide": True}
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
    # Select columns ending with ".mzML"
    mzml_columns = df.filter(like='.mzML')
    # Create a boolean mask for rows with zero values in these columns
    mask = (mzml_columns == 0).any(axis=1)
    # Filter the DataFrame using this mask
    print(df.head())
    print(df.shape)
    df = df[mask]
    print(df.head())
    print(df.shape)
    
    lib = pd.DataFrame(
        {
            "CompoundName": df["metabolite"],
            "SumFormula": "",
            # calculate neutral mass if charge is not zero, else assume charge = 1
            "Mass": df.apply(lambda x: x["mz"] * x["charge"] - x["charge"] * 1.007825 if x["charge"] else x["mz"] - 1.007825, axis=1),
            "Charge": df["charge"],
            "RetentionTime": df["RT"],
            "RetentionTimeRange": 0,
            "IsoDistribution": 0,
        }
    )
    lib.to_csv(params["out"][0], sep="\t", index=False)
    print(lib.head())
    print(lib.shape)
    