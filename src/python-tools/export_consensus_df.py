import json
import sys
import pyopenms as poms
from pathlib import Path
import pandas as pd
import numpy as np

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
    {"key": "in", "value": [], "help": "consensusXML file", "hide": True},
    {"key": "out", "value": [], "help": "consensus df parquet file", "hide": True}
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
    consensus_map = poms.ConsensusMap()
    poms.ConsensusXMLFile().load(params["in"][0], consensus_map)
    df = consensus_map.get_df().drop(["sequence"], axis=1)
    for cf in consensus_map:
        if cf.metaValueExists("best ion"):
            df.insert(
                4, "adduct", [cf.getMetaValue(
                    "best ion") for cf in consensus_map]
            )
            break
    for cf in consensus_map:
        if cf.metaValueExists("label"):
            df["name"] = [cf.getMetaValue("label") for cf in consensus_map]
            break
    if "adduct" in df.columns:
        df.insert(
            0,
            "metabolite",
            [
                f"{round(mz, 4)}@{round(rt, 2)}@{adduct}"
                for mz, rt, adduct in zip(
                    df["mz"].tolist(), df["RT"].tolist(), df["adduct"].tolist()
                )
            ],
        )
    else:
        df.insert(
            0,
            "metabolite",
            [
                f"{round(mz, 4)}@{round(rt, 2)}"
                for mz, rt in zip(df["mz"].tolist(), df["RT"].tolist())
            ],
        )
    # annotate original feature IDs
    fnames = [Path(value.filename).name for value in consensus_map.getColumnHeaders().values()]

    ids = [[] for _ in fnames]

    for cf in consensus_map:
        fids = {f.getMapIndex(): f.getUniqueId() for f in cf.getFeatureList()}
        for i, fname in enumerate(fnames):
            if i in fids.keys():
                ids[i].append(str(fids[i]))
            else:
                ids[i].append(pd.NA)

    for i, f in enumerate(fnames):
        df[f"{fnames[i]}_IDs"] = ids[i]

    # annotate spectrum IDs for MS2 specs associated with feature
    df["MS2_native_specs"] = [";".join([f"{fnames[p.getMetaValue('map_index')]}_{p.getMetaValue('spectrum_index')+1}" for p in f.getPeptideIdentifications()]) for f in consensus_map]

    # set re-quantified
    if "ffmid" in params["out"][0]:
        df["re-quantified"] = True
    else:
        df["re-quantified"] = False

    # Rename columns to not show full file path
    df = df.rename(columns={col: Path(col).name for col in df.columns if Path(col).exists()})
    
    df = df.reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "id"

    path = Path(params["out"][0])
    df.to_parquet(path)
    # save additionally as tsv file
    df.to_csv(path.with_suffix(".tsv"), sep="\t")