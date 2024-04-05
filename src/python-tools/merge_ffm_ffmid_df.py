import json
import sys
import pyopenms as poms
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
    {"key": "in", "value": [], "help": "feature matrix parquet file", "hide": True},
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
    in_path = params["in"][0]
    # output directory for merged dfs
    out_dir = Path(Path(in_path).parent.parent, "feature-dfs")
    if not out_dir.exists():
        out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(in_path)

    # For each file in col which ends with mzML
    for file in [col for col in df.columns if col.endswith(".mzML")]:
        # Open the ffm df
        df_ffm = pd.read_parquet(
            Path(
                Path(in_path).parent.parent,
                "ffm-df",
                Path(file).stem + ".parquet",
            )
        )
        # Keep only rows in df_ffm where index is in df[file+"_IDs"]
        df_ffm = df_ffm.loc[df_ffm.index.isin(df[file + "_IDs"])]
        # Open the ffmid df
        df_ffmid = pd.read_parquet(
            Path(
                Path(in_path).parent.parent,
                "ffmid-df",
                Path(file).stem + ".parquet",
            )
        )
        # Concat both dataframes
        df_merged = pd.concat([df_ffm, df_ffmid])
        # Save dataframe
        df_merged.to_parquet(
            Path(
                out_dir,
                Path(file).stem + ".parquet",
            )
        )