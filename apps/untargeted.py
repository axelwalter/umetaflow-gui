import shutil
import streamlit as st
import pandas as pd
from pymetabo.core import *
from pymetabo.helpers import *
from pymetabo.dataframes import *
import plotly.express as px
import matplotlib.pyplot as plt
from utils.filehandler import get_files, get_dir

# @st.cache(suppress_st_warning=True)
def display_df(path, name):
    if os.path.isfile(path):
        df = pd.read_csv(path, sep="\t")
        df.index = df["Unnamed: 0"]
        df = df.drop(columns=["Unnamed: 0"])
    else:
        return
    for column in df.columns:
        if column.endswith(".mzML"):
            df = df.rename(columns={column: column[:-5]})
    st.download_button(
    name,
    df.to_csv(sep="\t").encode("utf-8"),
    name+".tsv",
    "text/tsv",
    )
    st.dataframe(df)
    # # calculate some metrics
    total_missing = sum([(df[col] == 0).sum() for col in df.columns])
    # mean_quality = df["quality"].mean()
    # median_quality = df["quality"].median()
    # st.dataframe(df)
    # hover = df.columns
    # fig = px.scatter(df, x="RT", y="mz", color="quality", hover_data=hover)
    # st.plotly_chart(fig)
    col1, col2, col3 = st.columns(3)
    col1.metric("total missing values", total_missing)
    # col2.metric("mean quality", str(mean_quality)[:6])
    # col3.metric("median quality", str(median_quality)[:6])


def display_FFM_info(path):
    col1, col2 = st.columns(2)
    names = []
    num_features = []
    fig, ax = plt.subplots()
    for file in os.listdir(path):
        names.append(file[:-11])
        fm = FeatureMap()
        FeatureXMLFile().load(os.path.join(path, file), fm)
        num_features.append(fm.size())
        df = fm.get_df()
        ax.plot(df["intensity"], df["quality"], label=file[:-11], marker="X")
        ax.ticklabel_format(axis='x',style='sci',scilimits=(0,0),useMathText=True)
        ax.set_xlabel("intensity")
        ax.set_ylabel("quality")
    col1.markdown("**Intensity to quality for each Feature Map**")
    col1.pyplot(fig)
    fig, ax = plt.subplots()
    ax.bar(names, num_features)
    ax.set_xticklabels(names, rotation=45, ha='right')
    col2.markdown("**Number of features per sample**")
    col2.pyplot(fig)

def app():
    # set all other viewing states to False
    st.session_state.viewing_extract = False
    # set untargeted specific states
    if "viewing_untargeted" not in st.session_state:
        st.session_state.viewing_untargeted = False
    if "mzML_files_untargeted" not in st.session_state:
        st.session_state.mzML_files_untargeted = set(['example_data/mzML/MarY_C.mzML', 'example_data/mzML/MraY_T.mzML'])
    if "results_dir_untargeted" not in st.session_state:
        st.session_state.results_dir_untargeted = "results_untargeted"

    
    with st.sidebar:
        with st.expander("info"):
            st.markdown("""
        Generate a table with consesensus features and their quantities with optional re-quantification step.
        """)

    with st.expander("settings", expanded=True):
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
        results_dir = col1.text_input("results folder (will be deleted each time the workflow is started!)", st.session_state.results_dir_untargeted)


        st.markdown("feature detection")
        col1, col2, col3 = st.columns(3)
        with col1:
            ffm_mass_error = float(st.number_input("mass_error_ppm", 1, 1000, 10))
        with col2:
            ffm_noise = float(st.number_input("noise_threshold_int", 10, 1000000000, 10000))
        with col3:
            st.markdown("##")
            ffm_single_traces = st.checkbox("remove_single_traces", True)
            if ffm_single_traces:
                ffm_single_traces = "true"
            else:
                ffm_single_traces = "false"

        st.markdown("map alignment")
        col1, col2, col3 = st.columns(3)
        with col1:
            ma_mz_max = float(st.number_input("pairfinder:distance_MZ:max_difference", 0.01, 1000.0, 10.0, step=1.,format="%.2f"))
        with col2:
            ma_mz_unit = st.radio("pairfinder:distance_MZ:unit", ["ppm", "Da"])
        with col3:
            ma_rt_max = float(st.number_input("pairfinder:distance_RT:max_difference", 1, 1000, 100))

        use_ffmid = st.checkbox("re-quantification", False, help="Use FeatureFinderMetaboIdent to re-quantify consensus features that have missing values.")
        if use_ffmid:
            col1, col2, col3 = st.columns(3)
            with col1:
                ffmid_mz = float(st.number_input("extract:mz_window", 0, 1000, 10))
            with col2:
                ffmid_peak_width = float(st.number_input("detect:peak_width", 1, 1000, 60))
            with col3:
                ffmid_n_isotopes = st.number_input("extract:n_isotopes", 2, 10, 2)

        use_ad= st.checkbox("adduct detection", True)
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
                ad_adducts = st.text_area("potential_adducts", "H:+:0.9\nNa:+:0.1\nH-2O-1:0:0.4\nH-4O-2:0:0.1")
            with col3:
                ad_charge_min = st.number_input("charge_min", 1, 10, 1)
            with col4:
                ad_charge_max = st.number_input("charge_max", 1, 10, 3)
                

        use_map_id = st.checkbox("map MS2 spectra to features", True)
        

        st.markdown("feature linking")
        col1, col2, col3 = st.columns(3)
        with col1:
            fl_mz_tol = float(st.number_input("link:mz_tol", 0.01, 1000.0, 10.0, step=1.,format="%.2f"))
        with col2:
            fl_mz_unit = st.radio("mz_unit", ["ppm", "Da"])
            view_button = st.button("View Other Results!", help="Show results that are in the currently specified results folder.")
        with col3:
            fl_rt_tol = float(st.number_input("link:rt_tol", 1, 200, 30))
            run_button = st.button("Run Workflow!")

        

    col1, col2, col3 = st.columns(3)
    if run_button:
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
        st.success("Complete!")

    if view_button or st.session_state.viewing_untargeted:
        st.session_state.viewing_untargeted = True
        display_df(os.path.join(results_dir, "FeatureMatrix.tsv"), "Feature Matrix")
        # display_FFM_info(os.path.join(results_dir, "interim", "FFM"))
        display_df(os.path.join(results_dir, "FeatureMatrix_requant.tsv"), "Feature Matrix requantified")


