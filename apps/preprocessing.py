import streamlit as st
import pandas as pd
from pymetabo.core import *
from pymetabo.helpers import *
from pymetabo.dataframes import *
import plotly.express as px
import time

def app():
    if "workflow" not in st.session_state.keys():
        st.session_state["workflow"] = False
    if "load data" not in st.session_state.keys():
        st.session_state["dataframes loaded"] = ""
    st.markdown("""
## Metabolomics Preprocessing
Generate a table with consesensus features and their quantities with optional re-quantification step.
### Parameters
#### Input mzML and results folder
""")

    mzML_dir = st.text_input("mzML files folder", "/home/axel/Nextcloud/workspace/MetabolomicsWorkflowMayer/mzML")
    results_dir = st.text_input("results folder (will be deleted each time the workflow is started!)", "results")

    st.markdown("#### Feature detection")
    col1, col2, col3 = st.columns(3)
    with col1:
        ffm_mass_error = float(st.number_input("mass_error_ppm", 1, 1000, 10))
    with col2:
        ffm_noise = float(st.number_input("noise_threshold_int", 10, 1000000000, 10000))
    with col3:
        ffm_single_traces = st.checkbox("remove_single_traces", True)
        if ffm_single_traces:
            ffm_single_traces = "true"
        else:
            ffm_single_traces = "false"

    st.markdown("#### Map alignment")
    col1, col2, col3 = st.columns(3)
    with col1:
        ma_mz_max = float(st.number_input("pairfinder:distance_MZ:max_difference", 0.01, 1000.0, 10.0, step=1.,format="%.2f"))
    with col2:
        ma_mz_unit = st.radio("pairfinder:distance_MZ:unit", ["ppm", "Da"])
    with col3:
        ma_rt_max = float(st.number_input("pairfinder:distance_RT:max_difference", 1, 1000, 100))

    st.markdown("#### Re-quantification (FeatureFinderMetaboIdent)")
    use_ffmid = st.checkbox("requantfiy features (time intensive)", True)
    if use_ffmid:
        col1, col2, col3 = st.columns(3)
        with col1:
            ffmid_mz = float(st.number_input("extract:mz_window", 0, 1000, 10))
        with col2:
            ffmid_peak_width = float(st.number_input("detect:peak_width", 1, 1000, 60))
        with col3:
            ffmid_n_isotopes = st.number_input("extract:n_isotopes", 2, 10, 2)


    st.markdown("#### Adduct detection")
    use_ad= st.checkbox("annotate feature adducts", False)
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
            ad_adducts = st.text_area("potential_adducts", "H:+:0.5\nNa:+:0.3\nH-1O-1:+:0.2")
        with col3:
            ad_charge_min = st.number_input("charge_min", 1, 10, 1)
        with col4:
            ad_charge_max = st.number_input("charge_max", 1, 10, 3)
            

    st.markdown("#### Map ID")
    use_map_id = st.checkbox("annotate MS2 spectra to features", False)
    

    st.markdown("#### Feature linking")
    col1, col2, col3 = st.columns(3)
    with col1:
        fl_mz_tol = float(st.number_input("link:mz_tol", 0.01, 1000.0, 10.0, step=1.,format="%.2f"))
    with col2:
        fl_mz_unit = st.radio("mz_unit", ["ppm", "Da"])
    with col3:
        fl_rt_tol = float(st.number_input("link:rt_tol", 1, 200, 30))


    col1, col2, col3 = st.columns(3)
    if col2.button("Run Workflow"):
        results = Helper().reset_directory(results_dir)
        interim = Helper().reset_directory(os.path.join(results, "interim"))

        with st.spinner("Detecting features..."):
            FeatureFinderMetabo().run(mzML_dir, os.path.join(interim, "FFM"),
                                    {"noise_threshold_int": ffm_noise,
                                    "mass_error_ppm": ffm_mass_error,
                                    "remove_single_traces": ffm_single_traces})

        with st.spinner("Aligning feature maps..."):
            MapAligner().run(os.path.join(interim, "FFM"), os.path.join(interim, "FFM_aligned"),
                            os.path.join(interim, "Trafo"),
                            {"max_num_peaks_considered": -1,
                            "superimposer:mz_pair_max_distance": 0.05,
                            "pairfinder:distance_MZ:max_difference": ma_mz_max,
                            "pairfinder:distance_MZ:unit": ma_mz_unit,
                            "pairfinder:distance_RT:max_difference": ma_rt_max})

        if use_ffmid:
            with st.spinner("Aligning mzML files..."):
                MapAligner().run(mzML_dir, os.path.join(interim, "mzML_aligned"),
                os.path.join(interim, "Trafo"))
                mzML_dir = os.path.join(interim, "mzML_aligned")

        if use_ad and not use_ffmid:
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
        
        if use_map_id and not use_ffmid:
                with st.spinner("Mapping MS2 data to features..."):
                    MapID().run(mzML_dir, featureXML_dir, os.path.join(interim, "FeatureMaps_ID_mapped"))
                    featureXML_dir = os.path.join(interim, "FeatureMaps_ID_mapped")

        with st.spinner("Linking features..."):
            FeatureLinker().run(featureXML_dir,
                            os.path.join(interim,  "FeatureMatrix.consensusXML"),
                            {"link:mz_tol": fl_mz_tol,
                                "link:rt_tol": fl_rt_tol,
                                "mz_unit": fl_mz_unit})
            DataFrames().create_consensus_table(os.path.join(interim, "FeatureMatrix.consensusXML"), 
                                                os.path.join(results_dir, "FeatureMatrix.tsv"))

        if use_ffmid:
            with st.spinner("Re-quantifying features with missing values..."):
                FeatureMapHelper().split_consensus_map(os.path.join(interim,  "FeatureMatrix.consensusXML"),
                                                    os.path.join(interim,  "FFM_complete.consensusXML"),
                                                    os.path.join(interim,  "FFM_missing.consensusXML"))

                FeatureMapHelper().consensus_to_feature_maps(os.path.join(interim,  "FFM_complete.consensusXML"),
                                                            os.path.join(interim, "FFM_aligned"),
                                                            os.path.join(interim, "FFM_complete"))

                FeatureFinderMetaboIdent().run(mzML_dir,
                                            os.path.join(interim,  "FFMID"),
                                            os.path.join(interim,  "FFM_missing.consensusXML"),
                                            {"detect:peak_width": ffmid_peak_width,
                                            "extract:mz_window": ffmid_mz,
                                            "extract:n_isotopes": ffmid_n_isotopes})

                FeatureMapHelper().merge_feature_maps(os.path.join(interim, "FeatureMaps_merged"), os.path.join(
                    interim, "FFM_complete"), os.path.join(interim, "FFMID"))

            if use_ad:
                with st.spinner("Determining adducts..."):
                    MetaboliteAdductDecharger().run(os.path.join(interim, "FeatureMaps_merged"), os.path.join(interim, "FeatureMaps_decharged"),
                                {"potential_adducts": [line.encode() for line in ad_adducts.split("\n")],
                                "charge_min": ad_charge_min,
                                "charge_max": ad_charge_max,
                                "max_neutrals": 2,
                                "negative_mode": ad_ion_mode,
                                "retention_max_diff": 3.0,
                                "retention_max_diff_local": 3.0})
                featureXML_dir = os.path.join(interim, "FeatureMaps_decharged")
            else:
                featureXML_dir = os.path.join(interim, "FeatureMaps_merged")
            
            if use_map_id:
                with st.spinner("Mapping MS2 data to features..."):
                    MapID().run(mzML_dir, featureXML_dir, os.path.join(interim, "FeatureMaps_ID_mapped"))
                    featureXML_dir = os.path.join(interim, "FeatureMaps_ID_mapped")

            with st.spinner("Linking re-quantified features..."):
                FeatureLinker().run(featureXML_dir,
                                os.path.join(interim, "FeatureMatrix_requant.consensusXML"),
                                {"link:mz_tol": fl_mz_tol,
                                "link:rt_tol": fl_rt_tol,
                                "mz_unit": fl_mz_unit})
                DataFrames().create_consensus_table(os.path.join(interim, "FeatureMatrix_requant.consensusXML"), 
                                                    os.path.join(results_dir, "FeatureMatrix_requant.tsv"))
        st.session_state["workflow"] = True
        st.session_state["dataframes loaded"] = False
        st.success("Complete!")
    if col3.button("Display old results"):
        st.session_state["workflow"] = True
        st.session_state["dataframes loaded"] = "false"

    @st.cache
    def load_df(path):
        print("was not cached"+path)
        if os.path.isfile(path):
            return pd.read_csv(path, sep="\t")
        else:
            return pd.DataFrame()

    if st.session_state["workflow"]:
        df = load_df(os.path.join(results_dir, "FeatureMatrix.tsv"))
        df_requant = load_df(os.path.join(results_dir, "FeatureMatrix_requant.tsv"))
        st.markdown("#### Feature Matrix")
        st.download_button(
        "Download",
        df.to_csv(sep="\t").encode("utf-8"),
        "FeatureMatrix.tsv",
        "text/tsv",
        key='download-tsv'
        )
        
        if "q_threshold" not in st.session_state:
            st.session_state["q_threshold"] = min(df["quality"])
        st.session_state["q_threshold"] = st.slider('feature quality filter', min(df["quality"]), max(df["quality"]),
                                                    st.session_state["q_threshold"], step=0.02)
        for column in df.columns:
            if column.endswith(".mzML"):
                df = df.rename(columns={column: column[:-5]})
        st.dataframe(df.drop(columns=["id"])[df["quality"] > st.session_state["q_threshold"]])
        df["index"] =df.index
        hover = df.columns.drop("id")
        fig = px.scatter(df[df["quality"] > st.session_state["q_threshold"]], x="RT", y="mz", color="quality", hover_data=hover)
        st.plotly_chart(fig)

        if use_ffmid:
            st.markdown("#### Feature Matrix re-quantified")
            for column in df_requant.columns:
                if column.endswith(".mzML"):
                    df_requant = df_requant.rename(columns={column: column[:-5]})
            st.dataframe(df_requant.drop(columns=["id"]))
            st.download_button(
            "Download requantified Feature Matrix (as tsv file)",
            df_requant.to_csv(sep="\t").encode("utf-8"),
            "FeatureMatrix_requant.tsv",
            "text/tsv",
            key='download-tsv'
            )
            df_requant["index"] =df_requant.index
            hover = df.columns.drop("id")
            fig = px.scatter(df_requant[df_requant["quality"] > 0.01], x="RT", y="mz", color="quality", hover_data=hover)
            st.plotly_chart(fig)


        

        