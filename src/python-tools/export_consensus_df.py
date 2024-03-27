import json
import sys
import pyopenms as poms
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
    {"key": "in", "value": [], "help": "consensusXML file", "hide": True},
    {"key": "in_ms", "value": [], "help": "SIRIUS ms dir", "hide": True},
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
    # annotate original feature IDs which are in the Sirius .ms files
    if params["in_ms"]:
        path = params["in_ms"][0]
        ms_files = Path(path).glob("*.ms")
        map = {
            Path(value.filename).stem: key
            for key, value in consensus_map.getColumnHeaders().items()
        }
        for file in ms_files:
            if file.exists():
                key = map[file.stem]
                id_list = []
                content = file.read_text()
                for cf in consensus_map:
                    # get a map with map index and feature id for each consensus feature -> get the feature id key exists
                    f_map = {
                        fh.getMapIndex(): fh.getUniqueId()
                        for fh in cf.getFeatureList()
                    }
                    if key in f_map.keys():
                        f_id = str(f_map[key])
                    else:
                        f_id = ""
                    if f_id and f_id in content:
                        id_list.append(f_id)
                    else:
                        id_list.append("")
                df[file.stem + "_SiriusID"] = id_list
    df = df.rename(columns={col: Path(col).name for col in df.columns if Path(col).exists()})
    if "second-feature-map.mzML" in df.columns:
        df = df.drop(columns=["second-feature-map.mzML"])
    path = Path(params["out"][0])
    df.to_parquet(path)
    # save additionally as tsv file
    df.to_csv(path.with_suffix(".tsv"), sep="\t")