import json
import sys
import pyopenms as poms
from pathlib import Path
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
    {"key": "in", "value": [], "help": "ffmid featureXML dir", "hide": True},
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
    out_path = Path(Path(params["in"][0]).parent.parent, "ffmid-df")
    if not out_path.exists():
        out_path.mkdir(exist_ok=True)
    for file in Path(params["in"][0]).parent.glob("*.featureXML"):
        fm = poms.FeatureMap()
        poms.FeatureXMLFile().load(str(file), fm)
        # Get DataFrame with meta values
        df = fm.get_df(export_peptide_identifications=False,
                    meta_values=[b"num_of_masstraces", 
                                    b"dc_charge_adducts",
                                    b"model_FWHM",
                                    b"label"])
        
        rts = []
        intys = []
        # for f in fm:
        #     rts.append([
        #         [float(x[0]) for x in sub.getConvexHulls()[0].getHullPoints()]
        #         for sub in f.getSubordinates()
        #     ])
        #     intys.append([
        #         [int(y[1]) for y in sub.getConvexHulls()[0].getHullPoints()]
        #         for sub in f.getSubordinates()
        #     ])
        for f in fm:
            rts.append([float(x[0]) for x in f.getSubordinates()[0].getConvexHulls()[0].getHullPoints()])
            intys.append([int(y[1]) for y in f.getSubordinates()[0].getConvexHulls()[0].getHullPoints()])
        df["chrom_RT"] = rts
        df["chrom_intensity"] = [[int(i) for i in chrom_int] for chrom_int in intys]

        df = df.rename(columns={
            "model_FWHM": "FWHM",
            "dc_charge_adducts": "adduct",
            "label": "metabolite"
        })
        
        df["FWHM"] = df["FWHM"].astype(float)
        
        df["re-quantified"] = True
        
        df["quality ranked"] = np.linspace(0, 1, len(df))  # Generate ranks
        
        df = df.sort_values("quality ranked", ascending=False)

        df.to_parquet(Path(out_path, file.stem + ".parquet"))