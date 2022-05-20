import streamlit as st
import plotly.express as px
from pyopenms import *
from pymetabo.helpers import Helper
from pymetabo.core import FeatureFinderMetaboIdent
import os
import pandas as pd
from utils.filehandler import get_files

def app():
    if "viewing_targeted" not in st.session_state:
        st.session_state.viewing_targeted = False
    if "mzML_files_targeted" not in st.session_state:
        st.session_state.mzML_files_targeted = set(["example_data/mzML/standards_1.mzML",
                                        "example_data/mzML/standards_2.mzML"])
    if "library_options" not in st.session_state:
        st.session_state.library_options = [os.path.join("example_data", "FeatureFinderMetaboIdent", file) 
                                            for file in os.listdir(os.path.join("example_data", "FeatureFinderMetaboIdent"))]

    results_dir = "results_targeted"
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
        featureXML_dir = Helper().reset_directory(os.path.join(results_dir, "feature_maps"))
        for file in mzML_files:
            with st.spinner("Extracting from: " + file):
                exp = MSExperiment()
                MzMLFile().load(file, exp)
                df = pd.DataFrame()

                FeatureFinderMetaboIdent().run(file,
                            os.path.join(featureXML_dir,  os.path.basename(file[:-4]+"featureXML")), library,
                            params={"extract:mz_window": ffmid_mz,
                                    "detect:peak_width": ffmid_peak_width,
                                    "extract:n_isotopes": ffmid_n_isotopes})

                fm = FeatureMap()
        st.session_state.viewing_targeted = True


    if st.session_state.viewing_targeted:
        all_files = st.multiselect("samples", [f for f in os.listdir(results_dir) if f.endswith(".tsv")], 
                                [f for f in os.listdir(results_dir) if f.endswith(".tsv")], format_func=lambda x: os.path.basename(x)[:-4])
        all_files = sorted(all_files, reverse=True)
        col1, col2 = st.columns([9,1])
        all_chroms = col1.multiselect("chromatograms", pd.read_csv(os.path.join(results_dir, os.listdir(results_dir)[0]),
                                                                sep="\t").drop(columns=["time"]).columns.tolist(), 
                                    pd.read_csv(os.path.join(results_dir, os.listdir(results_dir)[0]),
                                                sep="\t").drop(columns=["time"]).columns.tolist())

        num_cols = col2.number_input("columns", 1, 5, 1)

        _, col1 = st.columns([9, 1])
        if col1.button("Download", help="Select a folder where data from all samples gets stored."):
            results_folder = get_result_dir()
            for file in all_files:
                shutil.copy(os.path.join(results_dir, file), os.path.join(results_folder, os.path.basename(file)))
        cols = st.columns(num_cols)
        while all_files:
            for col in cols:
                try:
                    file = all_files.pop()
                except IndexError:
                    break
                df = pd.read_csv(os.path.join(results_dir, file), sep="\t")

                fig = px.line(df, x=df["time"], y=all_chroms)
                fig.update_layout(xaxis=dict(title="time"), yaxis=dict(title="intensity (cps)"))
                col.download_button(file[:-4],
                                    df.to_csv(sep="\t").encode("utf-8"),
                                    file,
                                    "text/tsv",
                                    key='download-tsv', help="Download file.")
                col.plotly_chart(fig)