import json
import sys
from pathlib import Path
import pandas as pd
from pyteomics.mztab import MzTab

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

    df = pd.read_parquet(params["in"][0])

    df.insert(3, "MS2 annotation", "")

    if not df["MS2_native_specs"].any():
        print("No MS2 native spectra found for MS2 annotation.")

    def annotate(x, mztab_file, df_mztab):
        # get spec ids for the matching mztab file
        spec_ids = [spec[1] for spec in [spec.split("_") for spec in x["MS2_native_specs"].split(";")] if Path(spec[0]).stem == Path(mztab_file).stem]
        ann = x["MS2 annotation"]
        if spec_ids:
            for sid in spec_ids:
                if sid in df_mztab["native id"].values:
                    tmp_ann = df_mztab[df_mztab["native id"] == sid]["description"].values[0]
                    if ann:
                        ann += "; "
                    ann += tmp_ann
        return ann

    mztab_dir = Path(Path(params["in"][0]).parent.parent, "ms2-matches")
    for file in mztab_dir.iterdir():
        spectralmatch = MzTab(str(file), encoding="UTF8", table_format="df")
        spectralmatch.metadata
        df_mztab = spectralmatch.small_molecule_table
        df_mztab["native id"] = df_mztab["opt_spec_native_id"].str.split("=").str.get(-1)
        df["MS2 annotation"] = df.apply(annotate, args=(str(file), df_mztab), axis=1)
    
    df.to_parquet(params["in"][0])