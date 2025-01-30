import sys
import json

import pandas as pd
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
    {"key": "in", "value": "", "help": "umetaflow results dir", "hide": True},
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
    dir = params["in"]

    fm_dir = Path(dir, "feature-maps-recreated")
    if not fm_dir.exists():
        fm_dir.mkdir(exist_ok=True)
    fm_df_dir = Path(dir, "feature-dfs")

    # For each fm in df dir, re-create a feature map in featureXML format and save to fm_dir
    for f_df in fm_df_dir.iterdir():
        df = pd.read_parquet(f_df)
        # Create a new feature map
        fm = poms.FeatureMap()
        fm.setPrimaryMSRunPath([str(f_df.stem + ".mzML").encode()])
        for i, row in df.iterrows():
            # Create a new feature
            f = poms.Feature()
            # Set the position of the feature
            f.setRT(row["RT"])
            f.setMZ(row["mz"])
            # Set the intensity of the feature
            f.setIntensity(row["intensity"])
            # Set the quality of the feature
            f.setOverallQuality(row["quality"])
            # Set the charge state of the feature
            f.setCharge(row["charge"])
            # Set the adduct of the feature
            if row["adduct"] != "nan":
                f.setMetaValue("dc_charge_adducts", row["adduct"])
            # Set num masstraces
            f.setMetaValue("num_of_masstraces", row["num_of_masstraces"])
            # Set the unique id of the feature
            f.setUniqueId(int(i))
            # Set hull points
            hull = poms.ConvexHull2D()
            hull.addPoint([row["RTstart"], row["MZstart"]])
            hull.addPoint([row["RTend"], row["MZend"]])
            hull.addPoint([row["RTend"], row["MZstart"]])
            hull.addPoint([row["RTstart"], row["MZend"]])
            f.setConvexHulls([hull])
            # Add the feature to the feature map
            fm.push_back(f)
        # Save the feature map to featureXML format
        poms.FeatureXMLFile().store(str(Path(fm_dir, Path(f_df).stem + ".featureXML")), fm)