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
    {"key": "in", "value": [], "help": "ffm featureXML dir", "hide": True},
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
    out_path = Path(Path(params["in"][0]).parent.parent, "ffm-df")
    if not out_path.exists():
        out_path.mkdir(exist_ok=True)
    for file in Path(params["in"][0]).parent.glob("*.featureXML"):
        fm = poms.FeatureMap()
        poms.FeatureXMLFile().load(str(file), fm)
        # Get DataFrame with meta values
        df = fm.get_df(export_peptide_identifications=False,
                    meta_values=[b"num_of_masstraces", 
                                    b"dc_charge_adducts",
                                    b"FWHM"])
        # Read in chromatogram values
        chrom_path = Path(file.parent.parent, "ffm-chroms", file.stem + ".mzML")
        exp = poms.MSExperiment()
        poms.MzMLFile().load(str(chrom_path), exp)
        chroms = exp.getChromatograms()
        # Collect all chromatogram data in two arrays with dicts
        rts = []
        intys = []
        # Get chrom data for each feature
        for f in fm:
            f_chroms = [c for c in chroms if int(c.getNativeID().split("_")[0]) == f.getUniqueId()]
            tmp_rt = []
            tmp_inty = []
            for fc in f_chroms:
                iso = int(fc.getNativeID().split("_")[1])
                if iso == 0:
                    chrom_rts, chrom_intys = fc.get_peaks()
                    rts.append(chrom_rts)
                    intys.append(chrom_intys)

        df["chrom_RT"] = rts
        df["chrom_intensity"] = [[int(i) for i in chrom_int] for chrom_int in intys]
        
        df = df.rename(columns={
            "dc_charge_adducts": "adduct",
        })
        
        df["FWHM"] = df["FWHM"].astype(float)

        df.insert(12, "metabolite", df.apply(lambda x: f"{round(x['mz'], 4)}@{round(x['RT'], 2)}@{x['adduct']}", axis=1))

        df["re-quantified"] = False

        df["quality ranked"] = np.linspace(0, 1, len(df))  # Generate ranks
        
        df = df.sort_values("quality ranked", ascending=False)

        df.to_parquet(Path(out_path, file.stem + ".parquet"))
        