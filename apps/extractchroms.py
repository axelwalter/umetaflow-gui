import streamlit as st
import plotly.express as px
from pyopenms import *
import os
import pandas as pd
import numpy as np
from pymetabo.helpers import Helper
from utils.filehandler import get_files, get_dir, get_file

def app():
    # set all other viewing states to False
    st.session_state.viewing_untargeted = False
    # set extract specific session states
    if "viewing_extract" not in st.session_state:
        st.session_state.viewing_extract = False
    if "mzML_files_extract" not in st.session_state:
        st.session_state.mzML_files_extract = set(["example_data/mzML/standards_1.mzML",
                                        "example_data/mzML/standards_2.mzML"])
    if "masses_text_field" not in st.session_state:
        st.session_state.masses_text_field = "222.0972=GlcNAc\n294.1183=MurNAc"
    with st.sidebar:
        with st.expander("info", expanded=False):
            st.markdown("""
Here you can get extracted ion chromatograms `EIC` from mzML files. A base peak chromatogram `BPC`
will be automatically generated as well. Select the mass tolerance according to your data either as
absolute values `Da` or relative to the metabolite mass in parts per million `ppm`.

As input you can add `mzML` files and select which ones to use for the chromatogram extraction.
Download the results of selected samples and chromatograms as `tsv` or `xlsx` files.

You can enter the exact masses of your metabolites each in a new line. Optionally you can label them separated by an equal sign e.g.
`222.0972=GlcNAc`. To store the list of metabolites for later use you can download them as a text file. Simply
copy and paste the content of that file into the input field.

The results will be displayed as one graph per sample. Choose the samples and chromatograms to display.
""")

    results_dir = "results_extractchroms"
    with st.expander("settings", expanded=True):
        col1, col2 = st.columns([9,1])
        col2.markdown("##")
        mzML_button = col2.button("Add", "Add new mzML files.")
        if mzML_button:
            files = get_files("Add mzML files", [("MS Data", ".mzML")])
            if files:
                for file in files:
                    st.session_state.mzML_files_extract.add(file)
        mzML_files = col1.multiselect("mzML files", st.session_state.mzML_files_extract, st.session_state.mzML_files_extract,
                                    format_func=lambda x: os.path.basename(x)[:-5])

        col1, col2, col3, _ = st.columns([4, 1, 1.5, 0.5])
        unit = col3.radio("mass tolerance unit", ["ppm", "Da"])
        if unit == "ppm":
            tolerance = col3.number_input("mass tolerance", 1, 100, 10)
        elif unit == "Da":
            tolerance = col3.number_input("mass tolerance", 0.01, 10.0, 0.02)
        time_unit = col3.radio("time unit", ["seconds", "minutes"])

        col2.markdown("##")
        upload_mass_button = col2.button("Upload", help="Upload a mass list file.")
        if upload_mass_button:
            mass_file = get_file("Open mass file for chromatogram extraction", [("Mass File", ".txt")])
            if mass_file:
                with open(mass_file, "r") as f:
                    st.session_state.masses_text_field = f.read()

        masses_input = col1.text_area("masses", st.session_state.masses_text_field,
                    help="Add one mass per line and optionally label it with an equal sign e.g. 222.0972=GlcNAc.",
                    height=250)

        col2.download_button("Download",
                            masses_input,
                            "masses.txt",
                            "text/txt",
                            key='download-txt',
                            help="Download mass list as a text file.")
        run_button = col3.button("Extract Chromatograms!")


    if run_button:
        Helper().reset_directory(results_dir)
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
            df.to_feather(os.path.join(results_dir, os.path.basename(file)[:-5]+".ftr"))
        st.session_state.viewing_extract = True

    files = [f for f in os.listdir(results_dir) if f.endswith(".ftr") and "AUC" not in f]
    chroms = pd.read_feather(os.path.join(results_dir, files[0])).drop(columns=["time"]).columns.tolist()

    if st.session_state.viewing_extract:
        all_files = sorted(st.multiselect("samples", files, files, format_func=lambda x: os.path.basename(x)[:-4]), reverse=True)
        all_chroms = st.multiselect("chromatograms", chroms, chroms) 

        col1, col2, _, col3, _, col4, col5 = st.columns([2,2,1,2,1,1,2])
        col1.markdown("##")
        use_auc = col1.checkbox("calculate AUC", True)
        if use_auc:
            baseline = col2.number_input("AUC baseline", 0, 1000000, 5000, 1000)
        num_cols = col3.number_input("show columns", 1, 5, 1)
        download_as = col4.radio("download as", [".xlsx", ".tsv"])
        col5.markdown("##")
        if col5.button("Download Selection", help="Select a folder where data from selceted samples and chromatograms gets stored."):
            new_folder = get_dir()
            if new_folder:
                for file in all_files:
                    df = pd.read_feather(os.path.join(results_dir, file))[["time"]+all_chroms]
                    path = os.path.join(new_folder, file[:-4]+"_"+str(tolerance)+unit)
                    if download_as == ".tsv":
                        df.to_csv(path+".tsv", sep="\t", index=False)
                    if download_as == ".xlsx":
                        df.to_excel(path+".xlsx", index=False)
                if use_auc:
                    auc_files = [file[:-4]+"_AUC.ftr" for file in all_files]
                    for file in auc_files:
                        df = pd.read_feather(os.path.join(results_dir, file))
                        path = os.path.join(new_folder, file[:-7]+"_"+str(tolerance)+unit)+"_"+str(baseline)+"AUC"
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

                if use_auc:
                    df["AUC baseline"] = [baseline] * len(df)
                    all_chroms.append("AUC baseline")
                fig = px.line(df, x=df["time"], y=[c for c in df.columns if c in all_chroms])
                fig.update_layout(xaxis=dict(title="time"), yaxis=dict(title="intensity (cps)"))
                col.markdown(file[:-4])
                col.plotly_chart(fig)

                if use_auc:
                    auc = pd.DataFrame()
                    for chrom in all_chroms:
                        if chrom != "AUC baseline" and chrom != "BPC":
                            auc[chrom] = [int(np.trapz([x for x in df[chrom] if x > baseline]))]
                    auc.index = ["AUC"]
                    fig_auc = px.bar(x=auc.columns.tolist(), y=auc.loc["AUC", :].values.tolist())
                    fig_auc.update_traces(width=0.1)
                    fig_auc.update_layout(xaxis=dict(title=""), yaxis=dict(title="area under curve (counts)"))
                    col.plotly_chart(fig_auc)
                    auc.reset_index().to_feather(os.path.join(results_dir, file[:-4]+"_AUC.ftr"))

                col.markdown("***")