import streamlit as st
import os
from pyopenms import *
import pandas as pd

def app():
    st.markdown("""
# Chromatogram Extractor
Get BPCs and EICs from mzML files. Input can be either a path to a folder or path to a mzML file (one per line).
""")
    mzML = st.text_area("mzML input", "/home/axel/Nextcloud/workspace/MetabolomicsWorkflowMayer/mzML")
    results_dir = st.text_input("results folder (will be deleted each time the workflow is started!)", "results")

    masses_input = st.text_area("masses", "222.08=GlcNAc\n260.05=GlcN6P")

    col1, col2, col3 = st.columns(3)
    tolerance = col1.number_input("mass tolerance", 0.01, 100.0, 10.0)
    unit = col2.radio("mass tolerance unit", ["ppm", "Da"])
    time_unit = col3.radio("time unit", ["seconds", "minutes"])

    if col2.button("Extract chromatograms"):
        if os.path.isdir(mzML):
            mzML_files = [os.path.join(mzML, file) for file in os.listdir(mzML)]
        else:
            mzML_files = [path.strip() for path in mzML.split("\n") if os.path.isfile(path) and path.endswith(".mzML")]
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
                        index_highest_peak_within_window = spec.findHighestInWindow(mass,0.02,0.02)
                        if index_highest_peak_within_window > -1:
                            intensity.append(int(spec[index_highest_peak_within_window].getIntensity()))
                        else:
                            intensity.append(0)
                    df[str(mass)+"_"+name] = intensity
            df.to_csv(os.path.join(results_dir, os.path.basename(file)[:-5]+".tsv"), sep="\t", index=False)

    if col3.button("View results"):
        if "all_files" not in st.session_state.keys():
            st.session_state["all_files"] = [f[:-4] for f in os.listdir(results_dir)]
        if "all_chroms" not in st.session_state.keys():
            pass
        dfs = []
        for file in os.listdir(results_dir):
            if file.endswith("tsv"):
                dfs.append(pd.read_csv(os.path.join(results_dir, file), sep="\t"))
        st.multiselect("Choose samples", os.listdir(results_dir), os.listdir(results_dir))