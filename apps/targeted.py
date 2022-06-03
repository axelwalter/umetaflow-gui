import streamlit as st
import plotly.express as px
from pyopenms import *
from pymetabo.helpers import Helper
from pymetabo.core import FeatureFinderMetaboIdent
from pymetabo.dataframes import DataFrames
from pymetabo.plotting import Plot
import os
import pandas as pd
from utils.filehandler import get_files, get_dir

def app():
    results_dir = "results_targeted"
    if not os.path.exists(results_dir):
        os.mkdir(results_dir)
    if "viewing_targeted" not in st.session_state:
        st.session_state.viewing_targeted = False
    if "mzML_files_targeted" not in st.session_state:
        st.session_state.mzML_files_targeted = set(["example_data/mzML/standards_1.mzML",
                                        "example_data/mzML/standards_2.mzML"])
    if "library_options" not in st.session_state:
        st.session_state.library_options = [os.path.join("example_data", "FeatureFinderMetaboIdent", file) 
                                            for file in os.listdir(os.path.join("example_data", "FeatureFinderMetaboIdent"))]

    with st.sidebar:
        with st.expander("info", expanded=True):
            st.markdown("""
Workflow for targeted metabolmics with FeatureFinderMetaboIdent.
""")

    with st.expander("settings", expanded=True):
        col1, col2 = st.columns([9,1])
        with col1:
            mzML_files = st.multiselect("mzML files", st.session_state.mzML_files_targeted, st.session_state.mzML_files_targeted,
                                        format_func=lambda x: os.path.basename(x)[:-5])
        with col2:
            st.markdown("##")
            mzML_button = st.button("Add", help="Add new mzML files.")
        
        col1, col2 = st.columns([9,1])
        with col1:
            library = st.selectbox("select library", st.session_state.library_options)
        with col2:
            st.markdown("##")
            load_library = st.button("Add", help="Load a library file.")

        st.dataframe(pd.read_csv(library, sep="\t"))

        if mzML_button:
            files = get_files("Open mzML files", [("MS Data", ".mzML")])
            for file in files:
                st.session_state.mzML_files_targeted.add(file)
            st.experimental_rerun()

        if load_library:
            new_lib_files = get_files("Open library file(s)", [("Standards library", ".tsv")])
            for file in new_lib_files:
                st.session_state.library_options.insert(0, file)
            st.experimental_rerun()

        col1, col2, col3, col4 = st.columns([2,2,2,2])
        with col1:
            ffmid_mz = float(st.number_input("extract:mz_window", 0, 1000, 10))
        with col2:
            ffmid_peak_width = float(st.number_input("detect:peak_width", 1, 1000, 60))
        with col3:
            ffmid_n_isotopes = st.number_input("extract:n_isotopes", 2, 10, 2)
        with col4: 
            time_unit = st.radio("time unit", ["seconds", "minutes"])
            run_button = st.button("Extract Chromatograms!")

    if run_button:
        Helper().reset_directory(results_dir)
        for file in mzML_files:
            with st.spinner("Extracting from: " + file):

                FeatureFinderMetaboIdent().run(file,
                            os.path.join(results_dir,  os.path.basename(file[:-4]+"featureXML")), library,
                            params={"extract:mz_window": ffmid_mz,
                                    "detect:peak_width": ffmid_peak_width,
                                    "extract:n_isotopes": ffmid_n_isotopes})

                DataFrames().FFMID_chroms_to_df(os.path.join(results_dir, os.path.basename(file[:-4]+"featureXML")),
                                                os.path.join(results_dir,  os.path.basename(file[:-4]+"ftr")),
                                                time_unit=time_unit)

                DataFrames().FFMID_auc_to_df(os.path.join(results_dir,os.path.basename(file[:-4]+"featureXML")),
                                            os.path.join(results_dir,  os.path.basename(file[:-5]+"AUC.ftr")))

                DataFrames().FFMID_auc_combined_to_df(os.path.join(results_dir,  os.path.basename(file[:-5]+"AUC.ftr")),
                                                os.path.join(results_dir,  os.path.basename(file[:-5]+"AUC_combined.ftr")))

                os.remove(os.path.join(results_dir,  os.path.basename(file[:-4]+"featureXML")))


        st.session_state.viewing_targeted = True

    files = [f for f in os.listdir(results_dir) if f.endswith(".ftr") and "AUC" not in f and "summary" not in f]
    if st.session_state.viewing_targeted:
        all_files = sorted(st.multiselect("samples", files, files, format_func=lambda x: os.path.basename(x)[:-4]), reverse=True)

        DataFrames().get_auc_summary([os.path.join(results_dir, file[:-4]+"AUC.ftr") for file in all_files], os.path.join(results_dir, "summary.ftr"))
        DataFrames().get_auc_summary([os.path.join(results_dir, file[:-4]+"AUC_combined.ftr") for file in all_files], os.path.join(results_dir, "summary_combined.ftr"))

        col1, col2, _, col3, _, col4, col5 = st.columns([2,2,1,2,1,1,2])
        col1.markdown("##")
        num_cols = col3.number_input("show columns", 1, 5, 1)
        download_as = col4.radio("download as", [".xlsx", ".tsv"])
        col5.markdown("##")
        if col5.button("Download Selection", help="Select a folder where data from selceted samples and chromatograms gets stored."):
            new_folder = get_dir()
            if new_folder:
                for file in all_files:
                    df = pd.read_feather(os.path.join(results_dir, file))
                    path = os.path.join(new_folder, file[:-4])
                    if download_as == ".tsv":
                        df.to_csv(path+".tsv", sep="\t", index=False)
                    if download_as == ".xlsx":
                        df.to_excel(path+".xlsx", index=False)
                col5.success("Download done!")

        st.markdown("***")
        st.markdown("Summary with combined intensities")
        df_summary_combined = pd.read_feather(os.path.join(results_dir, "summary_combined.ftr"))
        df_summary_combined.index = df_summary_combined["index"]
        df_summary_combined = df_summary_combined.drop(columns=["index"])
        fig = Plot().FeatureMatrix(df_summary_combined)#, samples=[sample[:-4] for sample in all_files])
        st.plotly_chart(fig)
        st.dataframe(df_summary_combined)
        st.markdown("***")
        st.markdown("Summary with adduct intensities")
        df_summary = pd.read_feather(os.path.join(results_dir, "summary.ftr"))
        df_summary.index = df_summary["index"]
        df_summary = df_summary.drop(columns=["index"])
        fig = Plot().FeatureMatrix(df_summary, samples=[sample[:-4] for sample in all_files])
        st.plotly_chart(fig)
        st.dataframe(df_summary)
        st.markdown("***")
        cols = st.columns(num_cols)
        while all_files:
            for col in cols:
                try:
                    file = all_files.pop()
                except IndexError:
                    break
                df_chrom = pd.read_feather(os.path.join(results_dir, file))
                df_auc = pd.read_feather(os.path.join(results_dir, file[:-4]+"AUC.ftr")).drop(columns=["index"])
                df_auc_combined = pd.read_feather(os.path.join(results_dir, file[:-4]+"AUC_combined.ftr")).drop(columns=["index"])

                fig_chrom, fig_auc, fig_auc_combined = Plot().FFMID(df_chrom, df_auc=df_auc, df_auc_combined=df_auc_combined, time_unit=time_unit, title=file[:-4])
                col.plotly_chart(fig_chrom)
                col.plotly_chart(fig_auc)
                col.dataframe(df_auc)
                col.plotly_chart(fig_auc_combined)
                col.dataframe(df_auc_combined)

                col.markdown("***")