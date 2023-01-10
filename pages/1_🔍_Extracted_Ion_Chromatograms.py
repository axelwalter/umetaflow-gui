import streamlit as st
import plotly.express as px
from pyopenms import *
import os
import pandas as pd
import numpy as np
import shutil
from src.helpers import Helper
from src.plotting import Plot
from src.gnps import *
from src.dataframes import DataFrames
from pathlib import Path

results_dir = "results_extractchroms"
if not os.path.exists(results_dir):
    os.mkdir(results_dir)
# set all other viewing states to False
st.session_state.viewing_untargeted = False
# set extract specific session states
if "viewing_extract" not in st.session_state:
    st.session_state.viewing_extract = False
if "mzML_files_extract" not in st.session_state:
    st.session_state.mzML_files_extract = set()
if "masses_text_field" not in st.session_state:
    st.session_state.masses_text_field = "222.0972=GlcNAc\n294.1183=MurNAc"
with st.sidebar:
    with st.expander("info", expanded=True):
        st.markdown("""
Here you can get extracted ion chromatograms `EIC` from mzML files. A base peak chromatogram `BPC`
will be automatically generated as well. Select the mass tolerance according to your data either as
absolute values `Da` or relative to the metabolite mass in parts per million `ppm`.

As input you can add `mzML` files and select which ones to use for the chromatogram extraction.
Download the results of selected samples and chromatograms as `tsv` or `xlsx` files.

You can enter the exact masses of your metabolites each in a new line. Optionally you can label them separated by an equal sign e.g.
`222.0972=GlcNAc` or add RT limits with a further equal sign e.g. `222.0972=GlcNAc=2.4-2.6`. The specified time unit will be used for the RT limits. To store the list of metabolites for later use you can download them as a text file. Simply
copy and paste the content of that file into the input field.

The results will be displayed as a summary with all samples and EICs AUC values as well as the chromatograms as one graph per sample. Choose the samples and chromatograms to display.
""")

st.title("Extracted Ion Chromatograms (EIC/XIC)")
uploaded_mzML = st.file_uploader("mzML files", accept_multiple_files=True)

col1, col2 = st.columns(2)
masses_input = col1.text_area("masses", st.session_state.masses_text_field,
            help="Add one mass per line and optionally label it with an equal sign e.g. 222.0972=GlcNAc.",
            height=250)
unit = col2.radio("mass tolerance unit", ["ppm", "Da"])
if unit == "ppm":
    tolerance = col2.number_input("mass tolerance", 1, 100, 10)
elif unit == "Da":
    tolerance = col2.number_input("mass tolerance", 0.01, 10.0, 0.02)
time_unit = col2.radio("time unit", ["seconds", "minutes"])

col1, col2, col3= st.columns(3)
col2.markdown("##")
run_button = col2.button("**Extract Chromatograms!**")

if run_button:
    with st.spinner("Fetching uploaded data..."):
        # upload mzML files
        mzML_dir = "mzML_files"
        Helper().reset_directory(mzML_dir)
        for file in uploaded_mzML:
            with open(os.path.join(mzML_dir, file.name),"wb") as f:
                    f.write(file.getbuffer())

    Helper().reset_directory(results_dir)
    masses = []
    names = []
    times = []
    for line in [line for line in masses_input.split('\n') if line != '']:
        if len(line.split("=")) == 3:
            mass, name, time = line.split("=")
        elif len(line.split("=")) == 2:
            mass, name = line.split("=")
            time = "all"
        else:
            mass = line
            name = ''
            time = "all"
        masses.append(float(mass.strip()))
        names.append(name.strip())
        time_factor = 1.0
        if time_unit == "minutes":
            time_factor = 60.0
        if "-" in time:
            times.append([float(time.split("-")[0].strip())*time_factor, float(time.split("-")[1].strip())*time_factor])
        else:
            times.append([0,0])
    for file in Path(mzML_dir).glob("*.mzML"):
        with st.spinner("Extracting from: " + str(file)):
            exp = MSExperiment()
            MzMLFile().load(str(file), exp)
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
            for mass, name, time in zip(masses, names, times):
                intensity = []
                for spec in exp:
                    if (time == [0,0]) or (time[0] < spec.getRT() and time[1] > spec.getRT()):
                        _, intensities = spec.get_peaks()
                        if unit == "Da":
                            index_highest_peak_within_window = spec.findHighestInWindow(mass, tolerance, tolerance)
                        else:
                            index_highest_peak_within_window = spec.findHighestInWindow(mass,float((tolerance/1000000)*mass),float((tolerance/1000000)*mass))
                        if index_highest_peak_within_window > -1:
                            intensity.append(int(spec[index_highest_peak_within_window].getIntensity()))
                        else:
                            intensity.append(0)
                    else:
                        intensity.append(0)
                df[str(mass)+"_"+name] = intensity
        df.to_feather(os.path.join(results_dir, os.path.basename(file)[:-5]+".ftr"))
        # make a zip file with tables in tsv format
        tsv_dir = os.path.join(results_dir, "tsv-tables")
        Helper().reset_directory(tsv_dir)
        df.to_csv(os.path.join(tsv_dir, os.path.basename(file)[:-5]+".tsv"), sep="\t", index=False)
        shutil.make_archive(os.path.join(results_dir, "chromatograms"), 'zip', tsv_dir)
        shutil.rmtree(tsv_dir)
    st.session_state.viewing_extract = True

files = [f for f in os.listdir(results_dir) if f.endswith(".ftr") and "AUC" not in f and "summary" not in f]
if files:
    chroms = pd.read_feather(os.path.join(results_dir, files[0])).drop(columns=["time"]).columns.tolist()
    if "index" in chroms:
        chroms.remove("index")
    if "AUC baseline" in chroms:
        chroms.remove("AUC baseline")
else:
    chroms = []

if st.session_state.viewing_extract:
    all_files = sorted(st.multiselect("samples", files, files, format_func=lambda x: os.path.basename(x)[:-4]), reverse=True)
    all_chroms = st.multiselect("chromatograms", chroms, chroms) 

    col1, col2, col3, col4 = st.columns(4)
    baseline = col1.number_input("AUC baseline", 0, 1000000, 5000, 1000)
    num_cols = col2.number_input("show columns", 1, 5, 1)
    col3.markdown("##")
    with open(os.path.join(results_dir, "chromatograms.zip"), "rb") as fp:
        btn = col3.download_button(
            label="Download all Chromatograms",
            data=fp,
            file_name="chromatograms.zip",
            mime="application/zip"
        )

    for file in all_files:
        df = pd.read_feather(os.path.join(results_dir, file))
        df["AUC baseline"] = [baseline] * len(df)
        if "AUC baseline" not in all_chroms:
            all_chroms.append("AUC baseline")

        auc = pd.DataFrame()
        for chrom in all_chroms:
            if chrom != "AUC baseline" and chrom != "BPC":
                auc[chrom] = [int(np.trapz([x-baseline for x in df[chrom] if x > baseline]))]
        auc.to_feather(os.path.join(results_dir, file[:-4]+"AUC.ftr"))
        df.to_feather(os.path.join(results_dir, file))

    st.markdown("***")
    DataFrames().get_auc_summary([os.path.join(results_dir, file[:-4]+"AUC.ftr") for file in all_files], os.path.join(results_dir, "summary.ftr"))
    df_summary = pd.read_feather(os.path.join(results_dir, "summary.ftr"))
    df_summary.index = df_summary["index"]
    df_summary = df_summary.drop(columns=["index"])

    col4.markdown("##")
    col4.download_button("Download Feature Matrix", df_summary.rename(columns={col: col+".mzML" for col in df_summary.columns if col != "metabolite"}).to_csv(sep="\t", index=False), "Quantification-EIC.tsv")
    col4.download_button("Download Meta Data", pd.DataFrame({"filename": [file.replace("ftr", "mzML") for file in all_files], "ATTRIBUTE_Sample_Type": ["Sample"]*len(all_files)}).to_csv(sep="\t", index=False), "Meta-Data-EIC.tsv")

    st.markdown("Summary")
    fig = Plot().FeatureMatrix(df_summary)
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
            df = pd.read_feather(os.path.join(results_dir, file))
            auc = pd.read_feather(os.path.join(results_dir, file[:-4]+"AUC.ftr"))
            fig_chrom, fig_auc = Plot().extracted_chroms(df, chroms=all_chroms, df_auc=auc, title=file[:-4], time_unit=time_unit)
            col.plotly_chart(fig_chrom)
            col.plotly_chart(fig_auc)
            col.markdown("***")
