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
        with st.expander("info", expanded=False):
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

                DataFrames().FFMID_chroms_to_df(os.path.join(results_dir,  os.path.basename(file[:-4]+"featureXML")), os.path.join(results_dir,  os.path.basename(file[:-4]+"ftr")))

                os.remove(os.path.join(results_dir,  os.path.basename(file[:-4]+"featureXML")))

        st.session_state.viewing_targeted = True

    files = [f for f in os.listdir(results_dir) if f.endswith(".ftr") and "AUC" not in f]
    if st.session_state.viewing_targeted:
        all_files = sorted(st.multiselect("samples", files, files, format_func=lambda x: os.path.basename(x)[:-4]), reverse=True)

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
        cols = st.columns(num_cols)
        while all_files:
            for col in cols:
                try:
                    file = all_files.pop()
                except IndexError:
                    break
                df = pd.read_feather(os.path.join(results_dir, file))

                col.markdown(file[:-4])
                col.plotly_chart(Plot().FFMID_chroms_from_df(df))

                # if use_auc:
                #     auc = pd.DataFrame()
                #     for chrom in all_chroms:
                #         if chrom != "AUC baseline" and chrom != "BPC":
                #             auc[chrom] = [int(np.trapz([x for x in df[chrom] if x > baseline]))]
                #     auc.index = ["AUC"]
                #     fig_auc = px.bar(x=auc.columns.tolist(), y=auc.loc["AUC", :].values.tolist())
                #     fig_auc.update_traces(width=0.1)
                #     fig_auc.update_layout(xaxis=dict(title=""), yaxis=dict(title="area under curve (counts)"))
                #     col.plotly_chart(fig_auc)
                #     auc.reset_index().to_feather(os.path.join(results_dir, file[:-4]+"_AUC.ftr"))

                col.markdown("***")