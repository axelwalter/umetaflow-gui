import streamlit as st
import pandas as pd
from src.core import *
from src.helpers import *
from src.dataframes import *
from src.sirius import *
from src.gnps import *
from src.spectralmatcher import *
from pathlib import Path
from datetime import datetime
import json

st.set_page_config(page_title="UmetaFlow", page_icon="resources/icon.png", layout="wide", initial_sidebar_state="auto", menu_items=None)

def open_df(path):
    if os.path.isfile(path):
        df = pd.read_csv(path, sep="\t")
    else:
        return
    return df

try:
    # create result dir if it does not exist already
    if "workspace" in st.session_state:
        results_dir = Path(str(st.session_state["workspace"]), "results-metabolomics")
    else:
        st.warning("No online workspace ID found, please visit the start page first (UmetaFlow tab).")
        st.experimental_rerun()
    if not os.path.exists(results_dir):
        os.mkdir(results_dir)

    with st.sidebar:
        # Removing files
        st.markdown("### Remove Files")
        c1, c2 = st.columns(2)
        if c1.button("⚠️ **All**"):
            try:
                if any(st.session_state["mzML_files"].iterdir()):
                    Helper().reset_directory(st.session_state["mzML_files"])
                    st.experimental_rerun()
            except:
                pass
        if c2.button("**Un**selected"):
            try:
                for file in [Path(st.session_state["mzML_files"], key) for key, value in st.session_state.items() if key.endswith("mzML") and not value]:
                    file.unlink()
                st.experimental_rerun()
            except:
                pass

        # show currently available mzML files
        st.markdown("### Uploaded Files")
        for f in sorted(st.session_state["mzML_files"].iterdir()):
            if f.name in st.session_state:
                checked = st.session_state[f.name]
            else:
                checked = True
            st.checkbox(f.name[:-5], checked, key=f.name)

    st.title("Metabolomics")

    if Path("params/metabolomics.json").is_file():
        with open("params/metabolomics.json") as f:
            params = json.loads(f.read())
    else:
        with open("params/metabolomics_defaults.json") as f:
            params = json.loads(f.read())


    st.markdown("**Feature Detection**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        params["ffm_mass_error"] = st.number_input("**mass_error_ppm**", 1.0, 1000.0, params["ffm_mass_error"])
    with col2:
        params["ffm_noise"] = float(st.number_input("**noise_threshold_int**", 10, 1000000000, int(params["ffm_noise"])))
    with col3:
        params["ffm_peak_width"] = float(st.number_input("**peak_width_at_FWHM**", 0.1, 120.0, params["ffm_peak_width"], 1.0))
    with col4:
        st.markdown("##")
        params["ffm_single_traces"] = st.checkbox("remove_single_traces", params["ffm_single_traces"])
        if params["ffm_single_traces"]:
            ffm_single_traces = "true"
        else:
            ffm_single_traces = "false"

    st.markdown("**Map Alignment**")
    col1, col2, col3 = st.columns(3)
    with col1:
        params["ma_mz_max"] = st.number_input("pairfinder:distance_MZ:max_difference", 0.01, 1000.0, params["ma_mz_max"], step=1.,format="%.2f")
    with col2:
        params["ma_mz_unit"] = st.radio("pairfinder:distance_MZ:unit", ["ppm", "Da"], ["ppm", "Da"].index(params["ma_mz_unit"]))
    with col3:
        params["ma_rt_max"] = float(st.number_input("pairfinder:distance_RT:max_difference", 1, 1000, int(params["ma_rt_max"]), 10))

    params["use_requant"] = st.checkbox("**Re-Quantification**", params["use_requant"], help="Go back into the raw data to re-quantify consensus features that have missing values.")

    if params["use_ad"]:
        use_ad = True
    else:
        use_ad = False
    params["use_ad"] = st.checkbox("**Adduct Detection**", use_ad)
    if params["use_ad"]:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            params["ad_ion_mode"] = st.radio("ionization mode", ["positive", "negative"])
            if params["ad_ion_mode"] == "positive":
                ad_ion_mode = "false"
            else:
                ad_ion_mode = "true"
                params["ad_adducts"] = "H:-:1.0"
        with col2:
            params["ad_adducts"] = st.text_area("potential_adducts", "H:+:0.9\nNa:+:0.1\nH-2O-1:0:0.4")
        with col3:
            params["ad_charge_min"] = st.number_input("charge_min", 1, 10, 1)
        with col4:
            params["ad_charge_max"] = st.number_input("charge_max", 1, 10, 3)

    params["use_sirius_manual"] = st.checkbox("**Export files for SIRIUS**", params["use_sirius_manual"], help="Export files for formula and structure predictions. Run Sirius with these pre-processed .ms files, can be found in results -> SIRIUS -> sirius_files.")
    params["use_gnps"] = st.checkbox("**Export files for GNPS**", params["use_gnps"], help="Run GNPS Feature Based Molecular Networking and Ion Identity Molecular Networking with these files, can be found in results -> GNPS.")
    if params["use_gnps"]:
        params["annotate_gnps_library"] = st.checkbox("annotate features with GNPS library", True)

    st.markdown("**Feature Linking**")
    col1, col2, col3 = st.columns(3)
    with col1:
        params["fl_mz_tol"] = float(st.number_input("link:mz_tol", 0.01, 1000.0, 10.0, step=1.,format="%.2f"))
    with col2:
        params["fl_mz_unit"] = st.radio("mz_unit", ["ppm", "Da"])
    with col3:
        params["fl_rt_tol"] = float(st.number_input("link:rt_tol", 1, 200, 30))

    params["annotate_ms1"] = st.checkbox("**MS1 annotation by m/z and RT**", value=params["annotate_ms1"], help="Annotate features on MS1 level with known m/z and retention times values.")
    if params["annotate_ms1"]:
        ms1_annotation_file_upload = st.file_uploader("Select library for MS1 annotations.", type=["tsv"])
        if ms1_annotation_file_upload:
            params["ms1_annotation_file"] = os.path.join(str(st.session_state["workspace"]), ms1_annotation_file_upload.name)
            with open(params["ms1_annotation_file"], "wb") as f:
                    f.write(ms1_annotation_file_upload.getbuffer())
        elif params["ms1_annotation_file"]:
            st.write("Currently selected MS1 library: " + Path(params["ms1_annotation_file"]).name)
        else:
            st.warning("No MS1 library selected.")
            params["ms1_annotation_file"] = ""
        c1, c2 = st.columns(2)
        params["annoation_rt_window_sec"] = c1.number_input("retention time window for annotation in seconds", 1, 240, 60, 10, help="Checks around peak apex, e.g. window of 60 s will check left and right 30 s.")
        params["annotation_mz_window_ppm"] = c2.number_input("mz window for annotation in ppm", 1, 100, 10, 1)

    params["annotate_ms2"] = st.checkbox("**MS2 annotation via fragmentation patterns**", value=params["annotate_ms2"], help="Annotate features on MS2 level based on their fragmentation patterns. The library has to be in mgf file format.")
    if params["annotate_ms2"]:
        params["use_gnps"] = True
        ms2_annotation_file_upload = st.file_uploader("Select library for MS2 annotations", type=["mgf"])
        if ms2_annotation_file_upload:
            params["ms2_annotation_file"] = os.path.join(str(st.session_state["workspace"]), ms2_annotation_file_upload.name)
            with open(params["ms2_annotation_file"], "wb") as f:
                f.write(ms2_annotation_file_upload.getbuffer())
        elif params["ms2_annotation_file"]:
            st.write("Currently selected MS2 library: " + Path(params["ms2_annotation_file"]).name)
        else:
            st.warning("No MS2 library selected.")
            params["ms2_annotation_file"] = ""


    c1, c2, _, c4 = st.columns(4)
    if c1.button("Load default parameters"):
        with open("params/metabolomics_defaults.json") as f:
            params = json.loads(f.read())
        with open(Path(st.session_state["workspace"], "metabolomics.json"), "w") as f:
            f.write(json.dumps(params, indent=4))
        st.experimental_rerun()
    if c2.button("**Save parameters**"):
        with open(Path(st.session_state["workspace"], "metabolomics.json"), "w") as f:
            f.write(json.dumps(params, indent=4))

    run_button =  c4.button("**Run Workflow!**")

    # check for mzML files 
    mzML_files = [str(Path(st.session_state["mzML_files"], key)) for key, value in st.session_state.items() if key.endswith("mzML") and value]

    if run_button and mzML_files:
        results_dir = Helper().reset_directory(results_dir)
        interim = Helper().reset_directory(os.path.join(results_dir, "interim"))

        with st.spinner("Detecting features..."):
            FeatureFinderMetabo().run(mzML_files, os.path.join(interim, "FFM"),
                                    {"noise_threshold_int": params["ffm_noise"],
                                    "chrom_fwhm": params["ffm_peak_width"],
                                    "mass_error_ppm": params["ffm_mass_error"],
                                    "remove_single_traces": ffm_single_traces,
                                    "report_convex_hulls": "true"})

        with st.spinner("Aligning feature maps..."):
            MapAligner().run(os.path.join(interim, "FFM"), os.path.join(interim, "FFM_aligned"),
                            os.path.join(interim, "Trafo"),
                            {"max_num_peaks_considered": -1,
                            "superimposer:mz_pair_max_distance": 0.05,
                            "pairfinder:distance_MZ:max_difference": params["ma_mz_max"],
                            "pairfinder:distance_MZ:unit": params["ma_mz_unit"],
                            "pairfinder:distance_RT:max_difference": params["ma_rt_max"]})

        with st.spinner("Aligning mzML files..."):
            MapAligner().run(mzML_files, os.path.join(interim, "mzML_aligned"),
            os.path.join(interim, "Trafo"))
            mzML_dir = os.path.join(interim, "mzML_aligned")

        if params["use_ad"]:
            with st.spinner("Determining adducts..."):
                MetaboliteAdductDecharger().run(os.path.join(interim, "FFM_aligned"), os.path.join(interim, "FeatureMaps_decharged"),
                            {"potential_adducts": [line.encode() for line in params["ad_adducts"].split("\n")],
                            "charge_min": params["ad_charge_min"],
                            "charge_max": params["ad_charge_max"],
                            "max_neutrals": 2,
                            "negative_mode": ad_ion_mode,
                            "retention_max_diff": 3.0,
                            "retention_max_diff_local": 3.0})
            featureXML_dir = os.path.join(interim, "FeatureMaps_decharged")
        else:
            featureXML_dir = os.path.join(interim, "FFM_aligned")
        
        with st.spinner("Mapping MS2 data to features..."):
            MapID().run(mzML_dir, featureXML_dir, os.path.join(interim, "FeatureMaps_ID_mapped"))
            featureXML_dir = os.path.join(interim, "FeatureMaps_ID_mapped")

        with st.spinner("Linking features..."):
            FeatureLinker().run(featureXML_dir,
                            os.path.join(interim,  "FeatureMatrix.consensusXML"),
                            {"link:mz_tol": params["fl_mz_tol"],
                                "link:rt_tol": params["fl_rt_tol"],
                                "mz_unit": params["fl_mz_unit"]})

        if params["use_sirius_manual"]: # export only sirius ms files to use in the GUI tool
            with st.spinner("Exporting files for Sirius..."):
                Sirius().run(mzML_dir, featureXML_dir, os.path.join(results_dir, "SIRIUS"), "", True,
                            {"-preprocessing:feature_only": "true"})
            sirius_ms_dir = os.path.join(results_dir, "SIRIUS", "sirius_files")
        else:
            sirius_ms_dir = ""

        DataFrames().create_consensus_table(os.path.join(interim, "FeatureMatrix.consensusXML"), os.path.join(results_dir, "FeatureMatrix.tsv"), sirius_ms_dir)
        GNPSExport().export_metadata_table_only(os.path.join(interim, "FeatureMatrix.consensusXML"), os.path.join(results_dir, "MetaData.tsv"))

        if params["use_gnps"]:
            with st.spinner("Exporting files for GNPS..."):
                # create interim directory for MS2 ids later (they are based on the GNPS mgf file)
                Helper().reset_directory(os.path.join(interim, "mztab_ms2"))
                GNPSExport().run(os.path.join(interim, "FeatureMatrix.consensusXML"), mzML_dir, os.path.join(results_dir, "GNPS"))
                output_mztab = os.path.join(interim, "mztab_ms2", "GNPS.mzTab")
                mgf_file = os.path.join(results_dir, "GNPS", "MS2.mgf")
                database = "example_data/ms2-libraries/GNPS-LIBRARY.mgf"
                SpectralMatcher().run(database, mgf_file, output_mztab)
                DataFrames().annotate_ms2(mgf_file, output_mztab,os.path.join(results_dir, "FeatureMatrix.tsv"), "GNPS library match")

        if params["annotate_ms1"]:
            with st.spinner("Annotating feautures on MS1 level by m/z and RT"):
                if params["ms1_annotation_file"]:
                    DataFrames().annotate_ms1(os.path.join(results_dir, "FeatureMatrix.tsv"), params["ms1_annotation_file"], params["annotation_mz_window_ppm"], params["annoation_rt_window_sec"])
                    DataFrames().save_MS_ids(os.path.join(results_dir, "FeatureMatrix.tsv"), os.path.join(results_dir, "MS1-annotations"), "MS1 annotation")

        if params["annotate_ms2"]:
            with st.spinner("Annotating features on MS2 level by fragmentation patterns..."):
                if params["ms2_annotation_file"]:
                    output_mztab = os.path.join(interim, "mztab_ms2", "MS2.mzTab")
                    SpectralMatcher().run(params["ms2_annotation_file"], mgf_file, output_mztab)
                    DataFrames().annotate_ms2(mgf_file, output_mztab, os.path.join(results_dir, "FeatureMatrix.tsv"), "MS2 annotation", overwrite_name=True)
                    DataFrames().save_MS_ids(os.path.join(results_dir, "FeatureMatrix.tsv"), os.path.join(results_dir, "MS2-annotations"), "MS2 annotation")

        # re-quantification
        # get missing values before re-quant
        df = open_df(os.path.join(results_dir, "FeatureMatrix.tsv"))
        st.session_state.missing_values_before = sum([(df[col] == 0).sum() for col in df.columns])
        if params["use_requant"]:
            with st.spinner("Re-Quantification..."):
                Requantifier().run(os.path.join(interim, "FeatureMatrix.consensusXML"), os.path.join(results_dir, "FeatureMatrix.tsv"), mzML_dir, featureXML_dir, params["ffm_mass_error"])
            df = open_df(os.path.join(results_dir, "FeatureMatrix.tsv"))
            st.session_state.missing_values_after = sum([(df[col] == 0).sum() for col in df.columns])
        else:
            st.session_state.missing_values_after = None

        if params["use_sirius_manual"]:
            shutil.make_archive(os.path.join(interim, "ExportSirius"), 'zip', sirius_ms_dir)
        if params["use_gnps"]:
            shutil.make_archive(os.path.join(interim, "ExportGNPS"), 'zip', os.path.join(results_dir, "GNPS"))

        st.success("Complete!")
    
    elif run_button:
            st.warning("Upload or select some mzML files first!")

    if any(Path(results_dir).iterdir()):
        st.markdown("***")
        df = open_df(os.path.join(results_dir, "FeatureMatrix.tsv"))
        st.markdown("#### Feature Matrix")
        st.markdown(f"**{df.shape[0]} rows, {df.shape[1]} columns**")
        st.dataframe(df)
        st.markdown("##")
        st.markdown("#### Metrics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("missing values", st.session_state.missing_values_before)
        col2.metric("missing values after re-quantification", st.session_state.missing_values_after)
        col3.metric("number of features", df.shape[0])
        col4.metric("number of samples", len([col for col in df.columns if "mzML" in col]))
        st.markdown("#### Downloads")
        col1, col2, col3, col4 = st.columns(4)
        col1.download_button("Feature Matrix", df.to_csv(sep="\t", index=False), f"FeatureMatrix-{datetime.now().strftime('%d%m%Y-%H-%M-%S')}.tsv")
        df_md = pd.read_csv(os.path.join(results_dir, "MetaData.tsv"), sep="\t")
        col2.download_button("Meta Data", df_md.to_csv(sep="\t", index=False), f"MetaData-{datetime.now().strftime('%d%m%Y-%H-%M-%S')}.tsv")
        if Path(results_dir, "interim", "ExportSirius.zip").is_file():
            with open(os.path.join(results_dir, "interim", "ExportSirius.zip"), "rb") as fp:
                btn = col3.download_button(
                    label="Files for Sirius",
                    data=fp,
                    file_name=f"ExportSirius-{datetime.now().strftime('%d%m%Y-%H-%M-%S')}.zip",
                    mime="application/zip"
                )
        if Path(results_dir, "interim", "ExportGNPS.zip").is_file():
            with open(os.path.join(results_dir, "interim", "ExportGNPS.zip"), "rb") as fp:
                btn = col4.download_button(
                    label="Files for GNPS",
                    data=fp,
                    file_name=f"ExportGNPS-{datetime.now().strftime('%d%m%Y-%H-%M-%S')}.zip",
                    mime="application/zip"
                )
except:
    st.warning("Something went wrong.")