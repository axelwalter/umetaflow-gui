import streamlit as st
import shutil
from pathlib import Path
from src.common.common import reset_directory
from .core import *
from .dataframes import DataFrames
class UmetaFlow:
    """
    Implements the steps for UmetaFlow in a reusable way.
    """

    def __init__(self, params, mzML_files, results_dir):
        self.params = params
        self.mzML_files = mzML_files
        self.results_dir = results_dir
        self.interim = Path(results_dir, "interim")
        reset_directory(self.interim)
        self.mzML_dir = Path(self.interim, "mzML_original")
        self.featureXML_dir = Path(self.interim, "FFM")
        self.consensusXML = Path(self.interim, "FeatureMatrix.consensusXML")
        self.consensus_tsv = Path(self.results_dir, "FeatureMatrix.tsv")

    def fetch_raw_data(self):
        reset_directory(self.mzML_dir)
        for file in self.mzML_files:
            shutil.copy(file, self.mzML_dir)

    def feature_detection(self):
        if self.params["ffm_single_traces"]:
            ffm_single_traces = "true"
        else:
            ffm_single_traces = "false"
        FeatureFinderMetabo().run(
            self.mzML_dir,
            os.path.join(self.interim, "FFM"),
            {
                "noise_threshold_int": float(self.params["ffm_noise"]),
                "chrom_fwhm": self.params["ffm_peak_width"],
                "chrom_peak_snr": self.params["ffm_snr"],
                "report_chromatograms": "true",
                "mass_error_ppm": self.params["ffm_mass_error"],
                "remove_single_traces": ffm_single_traces,
                "report_convex_hulls": "true",
                "min_fwhm": self.params["ffm_min_fwhm"],
                "max_fwhm": self.params["ffm_max_fwhm"],
            },
        )
        self.featureXML_dir = Path(self.interim, "FFM")

    def adduct_detection(self):
        if self.params["ad_ion_mode"] == "negative":
            negative_mode = "true"
        else:
            negative_mode = "false"
        adducts = [line.encode()
                   for line in self.params["ad_adducts"].split("\n")]
        MetaboliteAdductDecharger().run(
            self.featureXML_dir,
            Path(self.interim, "FFM_decharged"),
            {
                "potential_adducts": adducts,
                "charge_min": self.params["ad_charge_min"],
                "charge_max": self.params["ad_charge_max"],
                "charge_span_max": 1,
                "max_neutrals": len(adducts) - 1,
                "negative_mode": negative_mode,
                "retention_max_diff": float(self.params["ad_rt_max_diff"]),
                "retention_max_diff_local": float(self.params["ad_rt_max_diff"]),
            },
        )
        shutil.rmtree(self.featureXML_dir)
        Path(self.interim, "FFM_decharged").rename(Path(self.featureXML_dir))

    def align_feature_maps(self):
        MapAligner().run(
            self.featureXML_dir,
            os.path.join(self.interim, "FFM_aligned"),
            os.path.join(self.interim, "Trafo"),
            {
                "max_num_peaks_considered": -1,
                "superimposer:mz_pair_max_distance": 0.05,
                "pairfinder:distance_MZ:max_difference": self.params["ma_mz_max"],
                "pairfinder:distance_MZ:unit": self.params["ma_mz_unit"],
                "pairfinder:distance_RT:max_difference": float(self.params["ma_rt_max"]),
            },
        )
        self.featureXML_dir = Path(self.interim, "FFM_aligned")

    def feature_maps_to_df(self, requant=False):
        df_path = Path(self.featureXML_dir).name + "_df"
        reset_directory(Path(self.interim, df_path))
        for file in Path(self.featureXML_dir).iterdir():
            DataFrames().featureXML_to_ftr(
                file, Path(self.interim, df_path), requant=requant
            )

    def align_peak_maps(self):
        MapAligner().run(
            self.mzML_dir,
            Path(self.interim, "mzML_aligned"),
            Path(self.interim, "Trafo"),
        )
        self.mzML_dir = Path(self.interim, "mzML_aligned")

    def peak_maps_to_df(self):
        df_path = Path(self.mzML_dir).name + "_df"
        reset_directory(Path(self.interim, df_path))
        for file in Path(self.mzML_dir).iterdir():
            DataFrames().mzML_to_ftr(file, Path(self.interim, df_path))

    def map_MS2(self):
        MapID().run(
            self.mzML_dir,
            self.featureXML_dir,
            Path(self.interim, "FeatureMaps_ID_mapped"),
        )
        self.featureXML_dir = Path(self.interim, "FeatureMaps_ID_mapped")

    def link_feature_maps(self):
        FeatureLinker().run(
            self.featureXML_dir,
            str(self.consensusXML),
            {
                "link:mz_tol": self.params["fl_mz_tol"],
                "link:rt_tol": float(self.params["fl_rt_tol"]),
                "mz_unit": self.params["fl_mz_unit"],
            },
        )

    def consensus_df(self):
        DataFrames().create_consensus_table(
            str(self.consensusXML),
            self.consensus_tsv
        )

    def requantify_alternative(self):
        Requantifier().run(
            str(self.consensusXML),
            self.consensus_tsv,
            self.mzML_dir,
            self.featureXML_dir,
            self.params["ffm_mass_error"],
        )

    def requantify(self):
        FeatureMapHelper().FFMID_library_from_consensus_df(
            self.consensus_tsv, Path(self.interim, "FFMID.tsv")
        )
        FeatureFinderMetaboIdent().run(
            self.mzML_dir,
            str(Path(self.interim, "FFMID")),
            Path(self.interim, "FFMID.tsv"),
            {
                "detect:peak_width": self.params["ffm_peak_width"] * 2,
                "extract:mz_window": self.params["ffm_mass_error"],
                "extract:n_isotopes": 2,
            },
        )
        self.consensusXML = Path(
            self.interim, "FeatureMatrixRequantified.consensusXML")
        self.consensus_tsv = Path(
            self.results_dir, "FeatureMatrixRequantified.tsv")
        self.featureXML_dir = Path(self.interim, "FFMID")

    def additional_data_for_consensus_df(self):
        DataFrames().consensus_df_additional_annotations(
            self.consensus_tsv,
            Path(self.results_dir, "FeatureMatrix.ftr"),
            self.consensusXML,
        )


def run_umetaflow(params, mzML_files, results_dir):
    with st.status("Running UmetaFlow", expanded=True) as status:
        umetaflow = UmetaFlow(params, mzML_files, results_dir)

        st.write("Fetching input mzML files...")
        umetaflow.fetch_raw_data()

        st.write("Detecting features...")
        umetaflow.feature_detection()

        # return if no features have been detected
        if not any(Path(umetaflow.interim, "FFM").iterdir()):
            st.error("No features detected in all files")
            return

        if params["use_ad"] and not params["use_requant"]:
            st.write("Determining adducts...")
            umetaflow.adduct_detection()


        if params["use_ma"] and len(list(umetaflow.featureXML_dir.iterdir())) > 1:
            st.write("Aligning feature maps...")
            umetaflow.align_feature_maps()
            umetaflow.feature_maps_to_df()

            st.write("Aligning mzML files...")
            umetaflow.align_peak_maps()
            umetaflow.peak_maps_to_df()
        else:
            umetaflow.feature_maps_to_df()
            umetaflow.peak_maps_to_df()

        st.write("Linking features...")
        umetaflow.link_feature_maps()
        umetaflow.consensus_df()

        if params["use_requant"]:
            # for requant run FFMID and Feature Linking and optionally Adduct Decharging and Mapping MS2 data
            st.write("Re-quantification...")
            umetaflow.requantify()

            # return if no features have been detected
            if not any(Path(umetaflow.interim, "FFMID").iterdir()):
                st.error("No features detected in all files **after requantification**.")
                shutil.rmtree(results_dir)
                return

            st.write("Exporting re-quantified feature maps for visualization...")
            umetaflow.feature_maps_to_df(requant=True)

            if params["use_ad"]:
                st.write("Determining adducts...")
                umetaflow.adduct_detection()

            st.write("Linking re-quantified features...")
            umetaflow.link_feature_maps()
            umetaflow.consensus_df()

        # export metadata
        umetaflow.export_metadata()

        umetaflow.additional_data_for_consensus_df()

        status.update(label="UmetaFlow run complete!", state="complete", expanded=False)
        st.rerun()


METABO = {
    "main": """
This workflow includes the core UmetaFlow pipeline which results in a table of metabolic features.

- The most important parameter are marked as **bold** text. Adjust them according to your instrument.
- All the steps with checkboxes are optional.
""",
    "potential_adducts": """
Specify adducts and neutral additions/losses.\n
Format (each in a new line): adducts:charge:probability.\n
The summed up probability for all charged entries needs to be 1.0.\n

Good starting options for positive mode with sodium adduct and water loss:\n
H:+:0.9\n
Na:+:0.1\n
H-2O-1:0:0.4

Good starting options for negative mode with water loss and formic acid addition:\n
H-1:-:1\n
H-2O-1:0:0.5\n
CH2O2:0:0.5
    """,
    "ad_ion_mode": "Carefully adjust settings for each mode. Especially potential adducts and negative min/max charges for negative mode.",
    "ad_charge_min": "e.g. for negative mode -3, for positive mode 1",
    "ad_charge_max": "e.g. for negative mode -1, for positive mode 3",
    "ad_rt_diff": "Groups features with slightly different RT.",
    "re-quant": "Go back into the raw data to re-quantify consensus features that have missing values.",
}

HELP = """
This page lets you analyze mass spectrometry data for untargeted metabolomics.

Below are the main steps and options available in the tool:

#### 1. Pre-Processing

This step focuses on feature detection and data filtering.

**Feature Detection**

The most important parameters should be set according to your data:

*Mass Error ppm*: Specify the allowed mass error in parts per million (ppm).

*Noise Threshold*: Set the noise threshold to filter out low-intensity signals.

**Map Alignment**

If needed, you can perform map alignment to correct retention time differences between samples.

**Adduct Detection**

Optionally, you can perform adduct detection to identify potential ionization adducts and charge states for features.

#### 2. Re-Quantification
In this step, you have the option to re-quantify consensus features with missing values in the raw data.

Please use the checkboxes and input fields to customize the parameters according to your specific dataset and analysis needs. Remember to check the information and help provided for each option to understand its impact on your data analysis.
"""
