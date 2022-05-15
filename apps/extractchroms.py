import streamlit as st
import plotly.express as px
from pyopenms import *
import os
import pandas as pd
from pymetabo.helpers import Helper
from filehandler.filehandler import get_mzML_files, get_result_dir
import shutil

# TODO deal with multiple file inputs (only problem on Windows?)
# TODO how to enter path in Windows? raw string? conversion? works with Linux also?


def app():
    if "viewing" not in st.session_state:
        st.session_state.viewing = False
    if "mzML_files" not in st.session_state:
        st.session_state.mzML_files = set(["example_data/mzML/standards_1.mzML",
                                        "example_data/mzML/standards_2.mzML"])
    if "results_dir" not in st.session_state:
        st.session_state.results_dir = "results"

    with st.sidebar:
        with st.expander("info", expanded=False):
            st.markdown("""
Here you can get extracted ion chromatograms `EIC` from mzML files. A base peak chromatogram `BPC`
will be automatically generated as well. Select the mass tolerance according to your data either as
absolute values `Da` or relative to the metabolite mass in parts per million `ppm`.

As input you can add `mzML` files and select which ones to use for the chromatogram extraction.
Download the results of single samples or all as `tsv` files that can be opened in Excel.

You can enter the exact masses of your metabolites each in a new line. Optionally you can label them separated by an equal sign e.g.
`222.0972=GlcNAc`. To store the list of metabolites for later use you can download them as a text file. Simply
copy and paste the content of that file into the input field.

The results will be displayed as one graph per sample. Choose the samples and chromatograms to display.
""")

    with st.expander("settings", expanded=True):
        col1, col2 = st.columns([9,1])
        col2.markdown("##")
        mzML_button = col2.button("Add", "Add new mzML files.")
        if mzML_button:
            files = get_mzML_files()
            for file in files:
                st.session_state.mzML_files.add(file)
        mzML_files = col1.multiselect("mzML files", st.session_state.mzML_files, st.session_state.mzML_files,
                                    format_func=lambda x: os.path.basename(x)[:-5])

        col1, col2, _, col3 = st.columns([4, 1, 0.5, 1.5])
        unit = col3.radio("mass tolerance unit", ["ppm", "Da"])
        if unit == "ppm":
            tolerance = col3.number_input("mass tolerance", 1, 100, 10)
        elif unit == "Da":
            tolerance = col3.number_input("mass tolerance", 0.01, 10.0, 0.02)
        time_unit = col3.radio("time unit", ["seconds", "minutes"])

        masses_input = col1.text_area("masses", "222.0972=GlcNAc\n294.1183=MurNAc",
                    help="Add one mass per line and optionally label it with an equal sign e.g. 222.0972=GlcNAc.",
                    height=250)

        col2.markdown("##")
        col2.download_button("Download",
                            masses_input,
                            "masses.txt",
                            "text/txt",
                            key='download-txt',
                            help="Download mass list as a text file.")
        run_button = col3.button("Extract Chromatograms!")

    if run_button:
        Helper().reset_directory(st.session_state.results_dir)
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
            df.to_csv(os.path.join(st.session_state.results_dir, os.path.basename(file)[:-5]+".tsv"), sep="\t", index=False)
        st.session_state.viewing = True


    if st.session_state.viewing:
        all_files = st.multiselect("samples", [f for f in os.listdir(st.session_state.results_dir) if f.endswith(".tsv")], 
                                [f for f in os.listdir(st.session_state.results_dir) if f.endswith(".tsv")], format_func=lambda x: os.path.basename(x)[:-4])
        all_files = sorted(all_files, reverse=True)
        col1, col2 = st.columns([9,1])
        all_chroms = col1.multiselect("chromatograms", pd.read_csv(os.path.join(st.session_state.results_dir, os.listdir(st.session_state.results_dir)[0]),
                                                                sep="\t").drop(columns=["time"]).columns.tolist(), 
                                    pd.read_csv(os.path.join(st.session_state.results_dir, os.listdir(st.session_state.results_dir)[0]),
                                                sep="\t").drop(columns=["time"]).columns.tolist())

        num_cols = col2.number_input("columns", 1, 5, 1)

        _, col1 = st.columns([9, 1])
        if col1.button("Download", help="Select a folder where data from all samples gets stored."):
            results_folder = get_result_dir()
            for file in all_files:
                shutil.copy(os.path.join(st.session_state.results_dir, file), os.path.join(results_folder, os.path.basename(file)))
        cols = st.columns(num_cols)
        while all_files:
            for col in cols:
                try:
                    file = all_files.pop()
                except IndexError:
                    break
                df = pd.read_csv(os.path.join(st.session_state.results_dir, file), sep="\t")

                fig = px.line(df, x=df["time"], y=all_chroms)
                fig.update_layout(xaxis=dict(title="time"), yaxis=dict(title="intensity (cps)"))
                col.download_button(file[:-4],
                                    df.to_csv(sep="\t").encode("utf-8"),
                                    file,
                                    "text/tsv",
                                    key='download-tsv', help="Download file.")
                col.plotly_chart(fig)