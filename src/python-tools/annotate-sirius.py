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
    {"key": "in", "value": [], "help": "Feature Matrix parquet file", "hide": True},
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
    sirius_projects_dir = Path(Path(params["in"][0]).parent.parent, "sirius-projects")
    if sirius_projects_dir.exists():
        for result_directory in sirius_projects_dir.iterdir():
            if result_directory.is_dir():
                for tool, annotation_file, cols in zip(
                    ["CSI:FingerID", "SIRIUS", "CANOPUS"],
                    [
                        "compound_identifications.tsv",
                        "formula_identifications.tsv",
                        "canopus_compound_summary.tsv",
                    ],
                    [
                        ["molecularFormula", "name", "InChI", "smiles"],
                        ["molecularFormula"],
                        [
                            "NPC#pathway",
                            "NPC#superclass",
                            "NPC#class",
                            "ClassyFire#most specific class",
                        ],
                    ],
                ):
                    file = Path(result_directory, annotation_file)
                    if file.exists():
                        df_tmp = pd.read_csv(file, sep="\t")
                        df_tmp["id"] = df_tmp["id"].apply(
                            lambda x: x.split("_0_")[1].split("-")[0]
                        )
                        for col in cols:
                            df[
                                f"{tool}_{result_directory.name}_{col.replace('NPC#', '').replace('ClassyFire#', '')}"
                            ] = df[f"{result_directory.name}.mzML_IDs"].map(
                                df_tmp.set_index("id")[col].to_dict()
                            )

        df.to_parquet(params["in"][0])
        df.to_csv(Path(params["in"][0]).with_suffix(".tsv"), sep="\t")