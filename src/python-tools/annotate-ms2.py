import pandas as pd
import sys
from pyopenms import *
import pyteomics
from pyteomics import mztab
from pyteomics import mgf, auxiliary
from pathlib import Path
import json

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
    {
        "key": "in_mzTab",
        "value": [],
        "help": "input mzTab file with annotations",
        "hide": True,
    },
    {
        "key": "in_mzML",
        "value": [],
        "help": "mzML file converted from GNPS mgf file",
        "hide": True,
    },
    {"key": "in_mgf", "value": [], "help": "GNPS mgf file", "hide": True},
    {"key": "out", "value": [""], "help": "feature matrix parquet file", "hide": True},
]


def get_params():
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as f:
            return json.load(f)
    else:
        return {
            "in_mzTab": ["/home/amd64/dev/workspaces-umetaflow-gui/default/umetaflow/results/spectral-matcher/MS2-matches.mzTab"],
            "in_mzML": ["/home/amd64/dev/workspaces-umetaflow-gui/default/umetaflow/results/spectral-matcher/MS2.mzML"],
            "in_mgf": ["/home/amd64/dev/workspaces-umetaflow-gui/default/umetaflow/results/gnps-export/MS2.mgf"],
            "in_gnps_consensus": ["/home/amd64/dev/workspaces-umetaflow-gui/default/umetaflow/results/consensus-dfs/feature-matrix-gnps.parquet"],
            "out": ["/home/amd64/dev/workspaces-umetaflow-gui/default/umetaflow/results/consensus-dfs/feature-matrix.parquet"],
        }


if __name__ == "__main__":
    params = get_params()

    # MzML file with MS2 spectra
    exp = MSExperiment()
    MzMLFile().load(params["in_mzML"][0], exp)
    df = exp.get_df()
    df["index"] = [spec.getNativeID() for spec in exp]
    df["SCANS"] = [spec.getMetaValue("Scan_ID") for spec in exp]
    df["index"] = df["index"].str.replace(r"index=", "")

    # MGF File
    file = mgf.MGF(
        source=params["in_mgf"][0],
        use_header=True,
        convert_arrays=2,
        read_charges=True,
        read_ions=False,
        dtype=None,
        encoding=None,
    )
    parameters = []
    for spectrum in file:
        parameters.append(spectrum["params"])
    mgf_file = pd.DataFrame(parameters)
    mgf_file["feature_id"] = mgf_file["feature_id"].str.replace(r"e_", "")

    # Input Feature Matrix
    DF_features = pd.read_parquet(params["in_gnps_consensus"][0])

    # Spectral Matches from MzTab File
    spectralmatch = pyteomics.mztab.MzTab(
        params["in_mzTab"][0], encoding="UTF8", table_format="df"
    )
    spectralmatch.metadata
    spectralmatch_DF = spectralmatch.small_molecule_table
    spectralmatch_DF["opt_spec_native_id"] = spectralmatch_DF[
        "opt_spec_native_id"
    ].str.replace(r"index=", "")
    
    # Add Scan numbers to spectral match DF
    spectralmatch_DF["SCANS"] = ""
    for i, idx in zip(spectralmatch_DF.index, spectralmatch_DF["opt_spec_native_id"]):
        hits = []
        for (
            index,
            scan_number,
        ) in zip(df["index"], df["SCANS"]):
            if idx == index:
                hit = f"{scan_number}"
                if hit not in hits:
                    hits.append(hit)
        spectralmatch_DF.loc[i, "SCANS"] = " ## ".join(hits)

    # Add Scan numbers to feature DF
    scan_map = {}
    for metabolite, consensus_id in zip(DF_features.index, DF_features["consensus_feature_id"].astype(str)):
        hits = []
        for scan, mgf_id in zip(mgf_file["scans"], mgf_file["feature_id"]):
            if consensus_id == mgf_id:
                if metabolite in scan_map.keys():
                    scan_map[metabolite].append(scan)
                scan_map[metabolite] = [scan]
    
    # Output Feature Matrix
    DF_features = pd.read_parquet(params["out"][0])

    scans = []
    for metabolite in DF_features.index:
        if metabolite in scan_map:
            scans.append(scan_map[metabolite])
        else:
            scans.append([])
    DF_features["SCANS"] = scans

    DF_features["SpectralMatch"] = ""
    DF_features["SpectralMatch_smiles"] = ""

    for i, scans in zip(DF_features.index, DF_features["SCANS"]):
        hits_name = []
        hits_smiles = []
        hits_ppm_error = []
        hits_score = []
        for (
            name,
            smiles,
            scan_number,
            ppm_error,
            score
        ) in zip(
            spectralmatch_DF["description"],
            spectralmatch_DF["smiles"],
            spectralmatch_DF["SCANS"],
            spectralmatch_DF["opt_ppm_error"],
            spectralmatch_DF["opt_match_score"]
        ):
            if scan_number in scans:
                hits_name.append(str(name))
                hits_smiles.append(str(smiles))
                hits_ppm_error.append(str(ppm_error))
                hits_score.append(str(score))
        DF_features.loc[i, "SpectralMatch"] = " ## ".join(hits_name)
        DF_features.loc[i, "SpectralMatch_smiles"] = " ## ".join(hits_smiles)
        DF_features.loc[i, "SpectralMatch_ppm_error"] = " ## ".join(hits_ppm_error)
        DF_features.loc[i, "SpectralMatch_score"] = " ## ".join(hits_score)
    
    DF_features = DF_features.drop(columns=["SCANS"])

    DF_features.to_csv(
        Path(params["out"][0]).with_suffix(".tsv"), sep="\t", index=False
    )
    DF_features.to_parquet(params["out"][0])
