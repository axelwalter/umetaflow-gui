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

st.set_page_config(page_title="UmetaFlow", page_icon="resources/icon.png", layout="wide", initial_sidebar_state="auto", menu_items=None)

def open_df(path):
    if os.path.isfile(path):
        df = pd.read_csv(path, sep="\t")
    else:
        return
    return df

try:
    st.title("Metabolomics")

    # setting results directory
    results_dir = "results_metabolomics"
    if not os.path.exists(results_dir):
        os.mkdir(results_dir)

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

    st.markdown("**Map Alignment**")
    col1, col2, col3 = st.columns(3)
    with col1:
        ma_mz_max = float(st.number_input("pairfinder:distance_MZ:max_difference", 0.01, 1000.0, 10.0, step=1.,format="%.2f"))
    with col2:
        ma_mz_unit = st.radio("pairfinder:distance_MZ:unit", ["ppm", "Da"])
    with col3:
        ma_rt_max = float(st.number_input("pairfinder:distance_RT:max_difference", 1, 1000, 100))

    st.markdown("##")
    use_requant = st.checkbox("**Re-Quantification**", True, help="Go back into the raw data to re-quantify consensus features that have missing values.")

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

    use_sirius_manual = st.checkbox("**Export files for SIRIUS**", True, help="Export files for formula and structure predictions. Run Sirius with these pre-processed .ms files, can be found in results -> SIRIUS -> sirius_files.")

    use_gnps = st.checkbox("**Export files for GNPS**", True, help="Run GNPS Feature Based Molecular Networking and Ion Identity Molecular Networking with these files, can be found in results -> GNPS.")
    if use_gnps:
        annotate_gnps_library = st.checkbox("annotate features with GNPS library", True)

    st.markdown("**Feature Linking**")
    col1, col2, col3 = st.columns(3)
    with col1:
        fl_mz_tol = float(st.number_input("link:mz_tol", 0.01, 1000.0, 10.0, step=1.,format="%.2f"))
    with col2:
        fl_mz_unit = st.radio("mz_unit", ["ppm", "Da"])
    with col3:
        fl_rt_tol = float(st.number_input("link:rt_tol", 1, 200, 30))

    annotate_ms1 = st.checkbox("**MS1 annotation by m/z and RT**", value=False, help="Annotate features on MS1 level with known m/z and retention times values.")
    if annotate_ms1:
        ms1_annotation_file_upload = st.file_uploader("Select library for MS1 annotations.", type=["tsv"])
        if not ms1_annotation_file_upload:
            st.warning("No MS1 library selected.")
        c1, c2 = st.columns(2)
        annoation_rt_window_sec = c1.number_input("retention time window for annotation in seconds", 1, 240, 60, 10, help="Checks around peak apex, e.g. window of 60 s will check left and right 30 s.")
        annotation_mz_window_ppm = c2.number_input("mz window for annotation in ppm", 1, 100, 10, 1)

    annotate_ms2 = st.checkbox("**MS2 annotation via fragmentation patterns**", value=False, help="Annotate features on MS2 level based on their fragmentation patterns. The library has to be in mgf file format.")
    if annotate_ms2:
        use_gnps = True
        ms2_annotation_file = "example_data/ms2-libraries/peptidoglycan-soluble-precursors-positive.mgf"
        ms2_annotation_file_upload = st.file_uploader("Select library for MS2 annotations", type=["mgf"])
        if not ms2_annotation_file_upload:
            st.warning("No MS2 library selected.")


    mzML_dir = "mzML_files"
    _, _, c3 = st.columns(3)
    run_button = c3.button("**Run Workflow!**")
    if  run_button and any(Path(mzML_dir).iterdir()):
        st.session_state.viewing_untargeted = True
        interim = Helper().reset_directory(os.path.join(results_dir, "interim"))

        # upload annotation libraries or use default
        library_dir = os.path.join(interim, "annotation_libraries")
        Helper().reset_directory(library_dir)
        if annotate_ms1:
            if ms1_annotation_file_upload:
                ms1_annotation_file = os.path.join(library_dir, ms1_annotation_file_upload.name)
                with open(ms1_annotation_file, "wb") as f:
                    f.write(ms1_annotation_file_upload.getbuffer())
            else:
                ms1_annotation_file = ""#"example_data/ms1-libraries/peptidoglycan-soluble-precursors-positive.tsv"
        if annotate_ms2:
            if ms2_annotation_file_upload:
                ms2_annotation_file = os.path.join(library_dir, ms2_annotation_file_upload.name)
                with open(ms2_annotation_file, "wb") as f:
                    f.write(ms2_annotation_file_upload.getbuffer())
            else:
                ms2_annotation_file = ""#"example_data/ms2-libraries/peptidoglycan-soluble-precursors-positive.mgf"

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

        if use_sirius_manual: # export only sirius ms files to use in the GUI tool
            with st.spinner("Exporting files for Sirius..."):
                Sirius().run(mzML_dir, featureXML_dir, os.path.join(results_dir, "SIRIUS"), "", True,
                            {"-preprocessing:feature_only": "true"})
            sirius_ms_dir = os.path.join(results_dir, "SIRIUS", "sirius_files")
        else:
            sirius_ms_dir = ""

        DataFrames().create_consensus_table(os.path.join(interim, "FeatureMatrix.consensusXML"), os.path.join(results_dir, "FeatureMatrix.tsv"), sirius_ms_dir)
        GNPSExport().export_metadata_table_only(os.path.join(interim, "FeatureMatrix.consensusXML"), os.path.join(results_dir, "MetaData.tsv"))

        if use_gnps:
            with st.spinner("Exporting files for GNPS..."):
                # create interim directory for MS2 ids later (they are based on the GNPS mgf file)
                Helper().reset_directory(os.path.join(interim, "mztab_ms2"))
                GNPSExport().run(os.path.join(interim, "FeatureMatrix.consensusXML"), mzML_dir, os.path.join(results_dir, "GNPS"))
                output_mztab = os.path.join(interim, "mztab_ms2", "GNPS.mzTab")
                mgf_file = os.path.join(results_dir, "GNPS", "MS2.mgf")
                database = "example_data/ms2-libraries/GNPS-LIBRARY.mgf"
                SpectralMatcher().run(database, mgf_file, output_mztab)
                DataFrames().annotate_ms2(mgf_file, output_mztab,os.path.join(results_dir, "FeatureMatrix.tsv"), "GNPS library match")

        if annotate_ms1:
            with st.spinner("Annotating feautures on MS1 level by m/z and RT"):
                if ms1_annotation_file:
                    DataFrames().annotate_ms1(os.path.join(results_dir, "FeatureMatrix.tsv"), ms1_annotation_file, annotation_mz_window_ppm, annoation_rt_window_sec)
                    DataFrames().save_MS_ids(os.path.join(results_dir, "FeatureMatrix.tsv"), os.path.join(results_dir, "MS1-annotations"), "MS1 annotation")

        if annotate_ms2:
            with st.spinner("Annotating features on MS2 level by fragmentation patterns..."):
                if ms2_annotation_file:
                    output_mztab = os.path.join(interim, "mztab_ms2", "MS2.mzTab")
                    SpectralMatcher().run(ms2_annotation_file, mgf_file, output_mztab)
                    DataFrames().annotate_ms2(mgf_file, output_mztab, os.path.join(results_dir, "FeatureMatrix.tsv"), "MS2 annotation", overwrite_name=True)
                    DataFrames().save_MS_ids(os.path.join(results_dir, "FeatureMatrix.tsv"), os.path.join(results_dir, "MS2-annotations"), "MS2 annotation")

        # re-quantification
        # get missing values before re-quant
        df = open_df(os.path.join(results_dir, "FeatureMatrix.tsv"))
        st.session_state.missing_values_before = sum([(df[col] == 0).sum() for col in df.columns])
        if use_requant:
            with st.spinner("Re-Quantification..."):
                Requantifier().run(os.path.join(interim, "FeatureMatrix.consensusXML"), os.path.join(results_dir, "FeatureMatrix.tsv"), mzML_dir, featureXML_dir, ffm_mass_error)
            df = open_df(os.path.join(results_dir, "FeatureMatrix.tsv"))
            st.session_state.missing_values_after = sum([(df[col] == 0).sum() for col in df.columns])
        else:
            st.session_state.missing_values_after = None

        if use_sirius_manual:
            shutil.make_archive(os.path.join(interim, "ExportSirius"), 'zip', sirius_ms_dir)
        if use_gnps:
            shutil.make_archive(os.path.join(interim, "ExportGNPS"), 'zip', os.path.join(results_dir, "GNPS"))

        st.success("Complete!")


    elif run_button:
        st.warning("Please upload some mzML files.")

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