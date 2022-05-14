import streamlit as st
import plotly.express as px
from pyopenms import *
import os
import pandas as pd
from pymetabo.helpers import Helper
from filehandler.filehandler import get_mzML_files, get_result_dir


# TODO deal with multiple file inputs (only problem on Windows?)
# TODO how to enter path in Windows? raw string? conversion? works with Linux also?


def app():
    if "viewing" not in st.session_state:
        st.session_state.viewing = False
    if "mzML_files" not in st.session_state:
        st.session_state.mzML_files = set(["/home/axel/dev/easy-MS/example_data/mzML/standards_1.mzML",
                                        "/home/axel/dev/easy-MS/example_data/mzML/standards_2.mzML"])
    if "results_dir" not in st.session_state:
        st.session_state.results_dir = "results"

    with st.sidebar:
        st.markdown("""
### Extract Ion Chromatograms

Here you can get extracted ion chromatograms `EIC` from mzML files. A base peak chromatogram `BPC`
will be automatically generated as well. Select the mass tolerance according to your data either as
absolute values `Da` or relative to the metabolite mass in parts per million `ppm`.

As input you can add `mzML` files and select which ones to use for the chromatogram extraction.
The results will be stored in the specified folder. Each time you run the extraction the old results will be deleted and newly generated.

You can enter the exact masses of your metabolites each in a new line. Optionally you can label them separated by an equal sign e.g.
`222.0972=GlcNAc`. To store the list of metabolites for later use you can download them as a text file. Simply
copy and paste the content of that file into the input field.

The results will be displayed as one graph per sample. Choose the samples and chromatograms to display. 
To get the resulting data as a table check the results folder.
""")

    with st.expander("Parameters", expanded=True):
        col1, col2 = st.columns(2)
        mzML_button = col1.button("Add mzML Files")
        if mzML_button:
            files = get_mzML_files()
            for file in files:
                st.session_state.mzML_files.add(file)
        mzML_files = col1.multiselect("mzML files", st.session_state.mzML_files, st.session_state.mzML_files,
                                    format_func=lambda x: os.path.basename(x)[:-5])
        if col2.button("Select Results", help="Select a folder where your results will be stored."):
            result = get_result_dir()
            if result:
                st.session_state.results_dir = result
        alternative_results = col2.text_input("current results folder", st.session_state.results_dir)
        if os.path.isdir(alternative_results):
            st.session_state.results_dir = alternative_results
        else:
            st.warning("The specified results folder does not exists!")
        col1, col2, col3 = st.columns(3)
        unit = col2.radio("mass tolerance unit", ["ppm", "Da"])
        if unit == "ppm":
            tolerance = col1.number_input("mass tolerance", 1, 100, 10)
        elif unit == "Da":
            tolerance = col1.number_input("mass tolerance", 0.01, 10.0, 0.02)
        time_unit = col3.radio("time unit", ["seconds", "minutes"])

        col1, col2 = st.columns(2)
        masses_input = col1.text_area("masses", "222.0972=GlcNAc\n294.1183=MurNAc",
                    help="Add one mass per line and optionally label it with an equal sign e.g. 222.0972=GlcNAc.")
        col2.markdown("##")
        col2.markdown("##")
        col2.download_button("Download Masses",
                            masses_input,
                            "masses.txt",
                            "text/txt",
                            key='download-txt',
                            help="Download mass list as a text file.")
    _, col2, _, _, col1, _ = st.columns(6)
    if col1.button("Extract Data"):
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

    if col2.button("View Results") or st.session_state.viewing:
        st.session_state.viewing = True

        all_files = sorted(st.multiselect("Samples", [f[:-4] for f in os.listdir(st.session_state.results_dir) if f.endswith(".tsv")], 
                                [f[:-4] for f in os.listdir(st.session_state.results_dir) if f.endswith(".tsv")]), reverse=True)
        all_chroms = st.multiselect("Chromatograms", pd.read_csv(os.path.join(st.session_state.results_dir, os.listdir(st.session_state.results_dir)[0]),
                                                                sep="\t").drop(columns=["time"]).columns.tolist(), 
                                    pd.read_csv(os.path.join(st.session_state.results_dir, os.listdir(st.session_state.results_dir)[0]),
                                                sep="\t").drop(columns=["time"]).columns.tolist())
        st.markdown("##")
        col1, _, _, _, _, _ = st.columns(6)
        num_cols = col1.number_input("number of columns", 1, 5, 2)
        cols = st.columns(num_cols)
        while all_files:
            for col in cols:
                try:
                    file = all_files.pop()
                except IndexError:
                    break
                df = pd.read_csv(os.path.join(st.session_state.results_dir, file+".tsv"), sep="\t")
                if time_unit == "minutes":
                    time = df["time"]/60
                    time_label = "time (minutes)"
                else:
                    time = df["time"]
                    time_label = "time (seconds)"
                
                fig = px.line(df, x=time, y=all_chroms)
                fig.update_layout(title=file, xaxis=dict(title=time_label), yaxis=dict(title="intensity (cps)"))
                col.plotly_chart(fig)
                # col.download_button(
                # "Download",
                # df.to_csv(sep="\t").encode("utf-8"),
                # file+".tsv",
                # "text/tsv",
                # key='download-tsv'
                # )