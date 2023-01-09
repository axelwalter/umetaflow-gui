import shutil
import streamlit as st
import pandas as pd
from src.core import *
from src.helpers import *
from src.dataframes import *
from src.sirius import *
from src.gnps import *
from src.spectralmatcher import *
from utils.filehandler import get_file, get_files, get_dir

def open_df(path):
    if os.path.isfile(path):
        df = pd.read_csv(path, sep="\t")
    else:
        return
    for column in df.columns:
        if column.endswith(".mzML"):
            df = df.rename(columns={column: column[:-5]})
    return df

# set all other viewing states to False
st.session_state.viewing_extract = False
if "mzML_files_untargeted" not in st.session_state:
    st.session_state.mzML_files_untargeted = set()
if "results_dir_untargeted" not in st.session_state:
    st.session_state.results_dir_untargeted = "results_untargeted"

st.title("Metabolomics")
with st.expander("Quickstart"):
    st.markdown("""
    1. select mzML files
    2. select an existing folder to store your results
    3. Set the noise treshold and mass error for feature detection according to your instrument
    """)
st.markdown("**File Selection**")
col1, col2 = st.columns([9,1])
with col1:
    if st.session_state.mzML_files_untargeted:
        mzML_files = col1.multiselect("mzML files", st.session_state.mzML_files_untargeted, st.session_state.mzML_files_untargeted,
                                    format_func=lambda x: os.path.basename(x)[:-5])
    else:
        mzML_files = col1.multiselect("mzML files", [], [])
with col2:
    st.markdown("##")
    mzML_button = st.button("Add", help="Add new mzML files.")
if mzML_button:
    files = get_files("Open mzML files", [("MS Data", ".mzML")])
    for file in files:
        st.session_state.mzML_files_untargeted.add(file)
    st.experimental_rerun()

col1, col2 = st.columns([9,1])
col2.markdown("##")
result_dir_button = col2.button("Select", help="Choose a folder for your results.")
if result_dir_button:
    st.session_state.results_dir_untargeted = get_dir("Open folder for your results.")
results_dir = col1.text_input("results folder", st.session_state.results_dir_untargeted)

st.markdown("##")
st.markdown("**Feature Detection**")
col1, col2, col3 = st.columns(3)
with col1:
    ffm_mass_error = float(st.number_input("**mass_error_ppm**", 1, 1000, 10))
with col2:
    ffm_noise = float(st.number_input("**noise_threshold_int**", 10, 1000000000, 1000))
with col3:
    st.markdown("##")
    ffm_single_traces = st.checkbox("remove_single_traces", True)
    if ffm_single_traces:
        ffm_single_traces = "true"
    else:
        ffm_single_traces = "false"

st.markdown("##")
st.markdown("**Map Alignment**")
col1, col2, col3 = st.columns(3)
with col1:
    ma_mz_max = float(st.number_input("pairfinder:distance_MZ:max_difference", 0.01, 1000.0, 10.0, step=1.,format="%.2f"))
with col2:
    ma_mz_unit = st.radio("pairfinder:distance_MZ:unit", ["ppm", "Da"])
with col3:
    ma_rt_max = float(st.number_input("pairfinder:distance_RT:max_difference", 1, 1000, 100))

st.markdown("##")
use_ffmid = st.checkbox("**Re-Quantification**", False, help="Use FeatureFinderMetaboIdent to re-quantify consensus features that have missing values.")
if use_ffmid:
    col1, col2, col3 = st.columns(3)
    with col1:
        ffmid_mz = float(st.number_input("extract:mz_window", 0, 1000, 10))
    with col2:
        ffmid_peak_width = float(st.number_input("detect:peak_width", 1, 1000, 60))
    with col3:
        ffmid_n_isotopes = st.number_input("extract:n_isotopes", 2, 10, 2)

st.markdown("##")
use_ad = st.checkbox("**Adduct Detection**", True)
if use_ad:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ad_ion_mode = st.radio("ionization mode", ["positive", "negative"])
        if ad_ion_mode == "positive":
            ad_ion_mode = "false"
        elif ad_ion_mode == "negative":
            ad_ion_mode = "true"
            ad_adducts = "H:-:1.0"
    with col2:
        ad_adducts = st.text_area("potential_adducts", "H:+:0.9\nNa:+:0.1\nH-2O-1:0:0.4")
    with col3:
        ad_charge_min = st.number_input("charge_min", 1, 10, 1)
    with col4:
        ad_charge_max = st.number_input("charge_max", 1, 10, 3)

st.markdown("##")
use_sirius_manual = st.checkbox("**Export files for SIRIUS**", True, help="Export files for formula and structure predictions. Run Sirius with these pre-processed .ms files, can be found in results -> SIRIUS -> sirius_files.")

st.markdown("##")
use_gnps = st.checkbox("**Export files for GNPS**", True, help="Run GNPS Feature Based Molecular Networking and Ion Identity Molecular Networking with these files, can be found in results -> GNPS.")
if use_gnps:
    annotate_gnps_library = st.checkbox("annotate features with GNPS library", True)

st.markdown("##")
st.markdown("**Feature Linking**")
col1, col2, col3 = st.columns(3)
with col1:
    fl_mz_tol = float(st.number_input("link:mz_tol", 0.01, 1000.0, 10.0, step=1.,format="%.2f"))
with col2:
    fl_mz_unit = st.radio("mz_unit", ["ppm", "Da"])
with col3:
    fl_rt_tol = float(st.number_input("link:rt_tol", 1, 200, 30))

st.markdown("##")
annotate_ms1 = st.checkbox("**MS1 annotation by m/z and RT**", value=True, help="Annotate features on MS1 level with known m/z and retention times values.")
if annotate_ms1:
    c1, c2, c3 = st.columns(3)
    annotation_mz_window_ppm = c1.number_input("mz window for annotation in ppm", 1, 100, 10, 1)
    annoation_rt_window_sec = c2.number_input("retention time window for annotation in seconds", 1, 240, 60, 10, help="Checks around peak apex, e.g. window of 60 s will check left and right 30 s.")
    c1, c2 = st.columns([9,1])
    c2.markdown("##")
    ms1_annotation_file = "example_data/ms1-libraries/peptidoglycan-soluble-precursors-positive.tsv"
    if c2.button("Select", help="Choose a library for MS1 identification."):
        ms1_annotation_file = get_file("Select library for MS1 annotations.", type=[("Table file", "*.tsv")])
    ms1_annotation_file = c1.text_input("select a library for MS1 annotations", ms1_annotation_file)

st.markdown("##")
annotate_ms2 = st.checkbox("**MS2 annotation via fragmentation patterns**", value=True, help="Annotate features on MS2 level based on their fragmentation patterns. The library has to be in mgf file format.")
if annotate_ms2:
    use_gnps = True
    c1, c2 = st.columns([9,1])
    c2.markdown("##")
    ms2_annotation_file = "example_data/ms2-libraries/peptidoglycan-soluble-precursors-positive.mgf"
    if c2.button("Select", help="Choose a library for MS2 identification."):
        ms2_annotation_file = get_file("Select library for MS2 annotations.", type=[("Mascot Generic File", "*.mgf")])
    ms2_annotation_file = c1.text_input("select a library for MS2 annotations", ms2_annotation_file)

st.markdown("##")
_, c2, _ = st.columns(3)
if c2.button("**Run Workflow!**"):
    st.session_state.viewing_untargeted = True
    interim = Helper().reset_directory(os.path.join(results_dir, "interim"))

    with st.spinner("Fetching mzML file data..."):
        mzML_dir = os.path.join(interim, "mzML_original")
        Helper().reset_directory(mzML_dir)
        for file in mzML_files:
            shutil.copy(file, mzML_dir)

    with st.spinner("Detecting features..."):
        FeatureFinderMetabo().run(mzML_dir, os.path.join(interim, "FFM"),
                                {"noise_threshold_int": ffm_noise,
                                "mass_error_ppm": ffm_mass_error,
                                "remove_single_traces": ffm_single_traces,
                                "report_convex_hulls": "true"})

    with st.spinner("Aligning feature maps..."):
        MapAligner().run(os.path.join(interim, "FFM"), os.path.join(interim, "FFM_aligned"),
                        os.path.join(interim, "Trafo"),
                        {"max_num_peaks_considered": -1,
                        "superimposer:mz_pair_max_distance": 0.05,
                        "pairfinder:distance_MZ:max_difference": ma_mz_max,
                        "pairfinder:distance_MZ:unit": ma_mz_unit,
                        "pairfinder:distance_RT:max_difference": ma_rt_max})

    with st.spinner("Aligning mzML files..."):
        MapAligner().run(mzML_dir, os.path.join(interim, "mzML_aligned"),
        os.path.join(interim, "Trafo"))
        mzML_dir = os.path.join(interim, "mzML_aligned")

    if use_ad:
        with st.spinner("Determining adducts..."):
            MetaboliteAdductDecharger().run(os.path.join(interim, "FFM_aligned"), os.path.join(interim, "FeatureMaps_decharged"),
                        {"potential_adducts": [line.encode() for line in ad_adducts.split("\n")],
                        "charge_min": ad_charge_min,
                        "charge_max": ad_charge_max,
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
                        {"link:mz_tol": fl_mz_tol,
                            "link:rt_tol": fl_rt_tol,
                            "mz_unit": fl_mz_unit})

    sirius_featureXML_dir = featureXML_dir

    if use_ffmid:
        with st.spinner("Re-quantifying features with missing values..."):
            FeatureMapHelper().split_consensus_map(os.path.join(interim,  "FeatureMatrix.consensusXML"),
                                                os.path.join(interim,  "FFM_complete.consensusXML"),
                                                os.path.join(interim,  "FFM_missing.consensusXML"))

            FeatureMapHelper().consensus_to_feature_maps(os.path.join(interim,  "FFM_complete.consensusXML"),
                                                        featureXML_dir,
                                                        os.path.join(interim, "FFM_complete"))

            FeatureFinderMetaboIdent().run(mzML_dir,
                                        os.path.join(interim,  "FFMID"),
                                        os.path.join(interim,  "FFM_missing.consensusXML"),
                                        {"detect:peak_width": ffmid_peak_width,
                                        "extract:mz_window": ffmid_mz,
                                        "extract:n_isotopes": ffmid_n_isotopes,
                                        "extract:rt_window": ffmid_peak_width})


            FeatureMapHelper().merge_feature_maps(os.path.join(interim, "FeatureMaps_merged"), os.path.join(
                interim, "FFM_complete"), os.path.join(interim, "FFMID"))

        if use_ad:
            with st.spinner("Determining adducts..."):
                print([line.encode() for line in ad_adducts.split("\n")])
                MetaboliteAdductDecharger().run(os.path.join(interim, "FeatureMaps_merged"), os.path.join(interim, "FeatureMaps_decharged"),
                            {"potential_adducts": [line.encode() for line in ad_adducts.split("\n")],
                            "charge_min": ad_charge_min,
                            "charge_max": ad_charge_max,
                            "max_neutrals": 2,
                            "negative_mode": ad_ion_mode,
                            "retention_max_diff": 4.0,
                            "retention_max_diff_local": 4.0})
            featureXML_dir = os.path.join(interim, "FeatureMaps_decharged")
        else:
            featureXML_dir = os.path.join(interim, "FeatureMaps_merged")

        with st.spinner("Mapping MS2 data to re-quantified features..."):
            MapID().run(mzML_dir, featureXML_dir, os.path.join(interim, "FeatureMaps_ID_mapped"))
            featureXML_dir = os.path.join(interim, "FeatureMaps_ID_mapped")

        with st.spinner("Linking re-quantified features..."):
            FeatureLinker().run(featureXML_dir,
                            os.path.join(interim, "FeatureMatrixRequantified.consensusXML"),
                            {"link:mz_tol": fl_mz_tol,
                            "link:rt_tol": fl_rt_tol,
                            "mz_unit": fl_mz_unit})
        sirius_featureXML_dir = featureXML_dir

    if use_sirius_manual: # export only sirius ms files to use in the GUI tool
        with st.spinner("Exporting files for Sirius..."):
            Sirius().run(mzML_dir, sirius_featureXML_dir, os.path.join(results_dir, "SIRIUS"), "", True,
                        {"-preprocessing:feature_only": "true"})
        sirius_ms_dir = os.path.join(results_dir, "SIRIUS", "sirius_files")
    else:
        sirius_ms_dir = ""
    
    if use_ffmid:
        DataFrames().create_consensus_table(os.path.join(interim, "FeatureMatrixRequantified.consensusXML"),
                                        os.path.join(results_dir, "FeatureMatrixRequantified.tsv"), sirius_ms_dir)
        DataFrames().create_consensus_table(os.path.join(interim, "FeatureMatrix.consensusXML"), 
                                            os.path.join(results_dir, "FeatureMatrix.tsv"), "")
        GNPSExport().export_metadata_table_only(os.path.join(interim, "FeatureMatrixRequantified.consensusXML"), os.path.join(results_dir, "MetaData.tsv"))
    else:
        DataFrames().create_consensus_table(os.path.join(interim, "FeatureMatrix.consensusXML"), 
                                            os.path.join(results_dir, "FeatureMatrix.tsv"), sirius_ms_dir)
        GNPSExport().export_metadata_table_only(os.path.join(interim, "FeatureMatrix.consensusXML"), os.path.join(results_dir, "MetaData.tsv"))
    
    if use_ffmid:
        feature_matrix_df_file = os.path.join(results_dir, "FeatureMatrixRequantified.tsv")
    else:
        feature_matrix_df_file = os.path.join(results_dir, "FeatureMatrix.tsv")

    if use_gnps:
        with st.spinner("Exporting files for GNPS..."):
            # create interim directory for MS2 ids later (they are based on the GNPS mgf file)
            Helper().reset_directory(os.path.join(interim, "mztab_ms2"))
            if use_ffmid:
                consensusXML_file = os.path.join(interim, "FeatureMatrixRequantified.consensusXML")
            else:
                consensusXML_file = os.path.join(interim, "FeatureMatrix.consensusXML")
            GNPSExport().run(consensusXML_file, mzML_dir, os.path.join(results_dir, "GNPS"))
            output_mztab = os.path.join(interim, "mztab_ms2", "GNPS.mzTab")
            mgf_file = os.path.join(results_dir, "GNPS", "MS2.mgf")
            database = "example_data/ms2-libraries/GNPS-LIBRARY.mgf"
            SpectralMatcher().run(database, mgf_file, output_mztab)
            DataFrames().annotate_ms2(mgf_file, output_mztab,feature_matrix_df_file, "GNPS library match")

    if annotate_ms1:
        with st.spinner("Annotating feautures on MS1 level by m/z and RT"):
            DataFrames().annotate_ms1(feature_matrix_df_file, ms1_annotation_file, annotation_mz_window_ppm, annoation_rt_window_sec)
            DataFrames().save_MS_ids(feature_matrix_df_file, os.path.join(results_dir, "MS1-annotations"), "MS1 annotation")

    if annotate_ms2:
        with st.spinner("Annotating features on MS2 level by fragmentation patterns..."):
            output_mztab = os.path.join(interim, "mztab_ms2", "MS2.mzTab")
            SpectralMatcher().run(ms2_annotation_file, mgf_file, output_mztab)
            DataFrames().annotate_ms2(mgf_file, output_mztab, feature_matrix_df_file, "MS2 annotation", overwrite_name=True)
            DataFrames().save_MS_ids(feature_matrix_df_file, os.path.join(results_dir, "MS2-annotations"), "MS2 annotation")

    st.success("Complete!")

    df = open_df(os.path.join(results_dir, "FeatureMatrix.tsv"))
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("missing values", sum([(df[col] == 0).sum() for col in df.columns]))
    if use_ffmid:
        df_requant = open_df(os.path.join(results_dir, "FeatureMatrixRequantified.tsv"))
        col2.metric("missing values after requantification", sum([(df_requant[col] == 0).sum() for col in df_requant.columns]))
        st.dataframe(df_requant)
    else:
        st.dataframe(df)
