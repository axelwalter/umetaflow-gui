import streamlit as st
import plotly.express as px
import os
from pyopenms import *
import pandas as pd
from pymetabo.helpers import Helper

def app():
    st.markdown("""
# Chromatogram Extractor
Get BPCs and EICs from mzML files.
""")

    if "viewing" not in st.session_state:
        st.session_state.viewing = False
    mzML = st.text_area("mzML input", "/home/axel/Nextcloud/workspace/MetabolomicsWorkflowMayer/mzML")
    results_dir = st.text_input("results folder (will be deleted each time the workflow is started!)", "results")

    masses_input = st.text_area("masses", "222.0972=GlcNAc\n294.1183=MurNAc")
    col1, col2 = st.columns(2)

    col1, col2, col3 = st.columns(3)
    tolerance = col1.number_input("mass tolerance", 0.01, 100.0, 10.0)
    unit = col2.radio("mass tolerance unit", ["ppm", "Da"])
    time_unit = col3.radio("time unit", ["seconds", "minutes"])
    st.markdown("")

    if col2.button("Extract chromatograms"):
        Helper().reset_directory(results_dir)
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
                        if unit == "Da":
                            index_highest_peak_within_window = spec.findHighestInWindow(mass, tolerance, tolerance)
                        else:
                            index_highest_peak_within_window = spec.findHighestInWindow(mass,float((tolerance/1000000)*mass),float((tolerance/1000000)*mass))
                        if index_highest_peak_within_window > -1:
                            intensity.append(int(spec[index_highest_peak_within_window].getIntensity()))
                        else:
                            intensity.append(0)
                    df[str(mass)+"_"+name] = intensity
            df.to_csv(os.path.join(results_dir, os.path.basename(file)[:-5]+".tsv"), sep="\t", index=False)
        st.session_state.viewing = True

    if col3.button("View results") or st.session_state.viewing:
        st.session_state.viewing = True

        all_files = st.multiselect("Samples", [f[:-4] for f in os.listdir(results_dir) if f.endswith(".tsv")], 
                                [f[:-4] for f in os.listdir(results_dir) if f.endswith(".tsv")])
        all_chroms = st.multiselect("Chromatograms", pd.read_csv(os.path.join(results_dir, os.listdir(results_dir)[0]),
                                                                sep="\t").drop(columns=["time"]).columns.tolist(), 
                                    pd.read_csv(os.path.join(results_dir, os.listdir(results_dir)[0]),
                                                sep="\t").drop(columns=["time"]).columns.tolist())

        for file in sorted(all_files):
            df = pd.read_csv(os.path.join(results_dir, file+".tsv"), sep="\t")
            if time_unit == "minutes":
                time = df["time"]/60
                time_label = "time (minutes)"
            else:
                time = df["time"]
                time_label = "time (seconds)"
            
            fig = px.line(df, x=time, y=all_chroms)
            fig.update_layout(title=file, xaxis=dict(title=time_label), yaxis=dict(title="intensity (cps)"))
            col1, col2 = st.columns(2)
            col1.plotly_chart(fig)
            col2.download_button(
            "Download",
            df.to_csv(sep="\t").encode("utf-8"),
            file+".tsv",
            "text/tsv",
            key='download-tsv'
            )