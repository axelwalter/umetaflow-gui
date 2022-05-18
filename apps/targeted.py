import streamlit as st
import plotly.express as px
from pyopenms import *
from pymetabo.helpers import Helper
import os
import pandas as pd
from utils.filehandler import get_files

def app():
    if "viewing_targeted" not in st.session_state:
        st.session_state.viewing_targeted = False
    if "mzML_files_targeted" not in st.session_state:
        st.session_state.mzML_files_targeted = set(["example_data/mzML/standards_1.mzML",
                                        "example_data/mzML/standards_2.mzML"])
    if "results_dir_targeted" not in st.session_state:
        st.session_state.results_dir_targeted = "results"
    
    if "library_options" not in st.session_state:
        st.session_state.library_options = [os.path.join("example_data", "FeatureFinderMetaboIdent", file) 
                                            for file in os.listdir(os.path.join("example_data", "FeatureFinderMetaboIdent"))]
    if "library" not in st.session_state:
        st.session_state.library = pd.read_csv([os.path.join("example_data", "FeatureFinderMetaboIdent", file) 
                                            for file in os.listdir(os.path.join("example_data", "FeatureFinderMetaboIdent"))][0], sep="\t")

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
            st.dataframe(st.session_state.library)
            select_library = st.selectbox("select library", st.session_state.library_options)

        with col2:
            st.markdown("##")
            mzML_button = st.button("Add", help="Add new mzML files.")
            st.markdown("##")
            load_library = st.button("Add", help="Load a library file.")

        if mzML_button:
            files = get_files("Open mzML files", ("MS Data", ".mzML"))
            for file in files:
                st.session_state.mzML_files_targeted.add(file)

        if select_library:
            st.session_state.library = pd.read_csv(select_library, sep='\t')

        if load_library:
            pass

        col1, col2, col3 = st.columns(3)
        with col1:
            unit = col2.radio("mass tolerance unit", ["ppm", "Da"])

        with col3: 
            time_unit = col2.radio("time unit", ["seconds", "minutes"])

        if unit == "ppm":
            tolerance = col2.number_input("mass tolerance", 1, 100, 10)
        elif unit == "Da":
            tolerance = col2.number_input("mass tolerance", 0.01, 10.0, 0.02)

        run_button = col2.button("Extract Chromatograms!")

    if run_button:
        Helper().reset_directory(st.session_state.results_dir_targeted)
        masses = []
        names = []
        for line in [line for line in masses_input.split('\n') if line != '']:
            if '=' in line:
                mass, name = line.split('=')
            else:
                mass = line
                name = ''
            masses.append(float(mass.strip()))
            names.append(name.strip())
        for file in mzML_files:
            with st.spinner("Extracting from: " + file):
                exp = MSExperiment()
                MzMLFile().load(file, exp)
                df = pd.DataFrame()
                # get BPC always
                time = []
                intensity = []
                for spec in exp:
                    _, intensities = spec.get_peaks()
                    rt = spec.getRT()
                    if time_unit == "minutes":
                        rt = rt/60
                    time.append(rt)
                    i = int(max(intensities))
                    intensity.append(i)
                df["time"] = time
                df["BPC"] = intensity
                # get EICs
                for mass, name in zip(masses, names):
                    intensity = []
                    for spec in exp:
                        _, intensities = spec.get_peaks()
                        if unit == "Da":
                            index_highest_peak_within_window = spec.findHighestInWindow(mass, tolerance, tolerance)
                        else:
                            index_highest_peak_within_window = spec.findHighestInWindow(mass,float((tolerance/1000000)*mass),float((tolerance/1000000)*mass))
                        if index_highest_peak_within_window > -1:
                            intensity.append(int(spec[index_highest_peak_within_window].getIntensity()))
                        else:
                            intensity.append(0)
                    df[str(mass)+"_"+name] = intensity
            df.to_csv(os.path.join(st.session_state.results_dir_targeted, os.path.basename(file)[:-5]+".tsv"), sep="\t", index=False)
        st.session_state.viewing_targeted = True


    if st.session_state.viewing_targeted:
        all_files = st.multiselect("samples", [f for f in os.listdir(st.session_state.results_dir_targeted) if f.endswith(".tsv")], 
                                [f for f in os.listdir(st.session_state.results_dir_targeted) if f.endswith(".tsv")], format_func=lambda x: os.path.basename(x)[:-4])
        all_files = sorted(all_files, reverse=True)
        col1, col2 = st.columns([9,1])
        all_chroms = col1.multiselect("chromatograms", pd.read_csv(os.path.join(st.session_state.results_dir_targeted, os.listdir(st.session_state.results_dir_targeted)[0]),
                                                                sep="\t").drop(columns=["time"]).columns.tolist(), 
                                    pd.read_csv(os.path.join(st.session_state.results_dir_targeted, os.listdir(st.session_state.results_dir_targeted)[0]),
                                                sep="\t").drop(columns=["time"]).columns.tolist())

        num_cols = col2.number_input("columns", 1, 5, 1)

        _, col1 = st.columns([9, 1])
        if col1.button("Download", help="Select a folder where data from all samples gets stored."):
            results_folder = get_result_dir()
            for file in all_files:
                shutil.copy(os.path.join(st.session_state.results_dir_targeted, file), os.path.join(results_folder, os.path.basename(file)))
        cols = st.columns(num_cols)
        while all_files:
            for col in cols:
                try:
                    file = all_files.pop()
                except IndexError:
                    break
                df = pd.read_csv(os.path.join(st.session_state.results_dir_targeted, file), sep="\t")

                fig = px.line(df, x=df["time"], y=all_chroms)
                fig.update_layout(xaxis=dict(title="time"), yaxis=dict(title="intensity (cps)"))
                col.download_button(file[:-4],
                                    df.to_csv(sep="\t").encode("utf-8"),
                                    file,
                                    "text/tsv",
                                    key='download-tsv', help="Download file.")
                col.plotly_chart(fig)