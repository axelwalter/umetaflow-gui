import streamlit as st
import plotly.express as px
from pyopenms import *
import os
import pandas as pd
import shutil
from src.helpers import Helper
from src.gnps import *
from pathlib import Path
from datetime import datetime

st.set_page_config(layout="wide")

try:
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
    Download the results of selected samples and chromatograms as `tsv` files.

    You can enter the exact masses of your metabolites each in a new line. Optionally you can label them separated by an equal sign e.g.
    `222.0972=GlcNAc` or add RT limits with a further equal sign e.g. `222.0972=GlcNAc=2.4-2.6`. The specified time unit will be used for the RT limits. To store the list of metabolites for later use you can download them as a text file. Simply
    copy and paste the content of that file into the input field.

    The results will be displayed as a summary with all samples and EICs AUC values as well as the chromatograms as one graph per sample. Choose the samples and chromatograms to display.
    """)

    st.title("Extracted Ion Chromatograms (EIC/XIC)")

    # parameters
    c1, c2 = st.columns(2)
    # text area to define masses in with name, mass and optionl RT boundaries
    masses_input = c1.text_area("masses", st.session_state.masses_text_field,
                help="Add one mass per line and optionally label it with an equal sign e.g. 222.0972=GlcNAc.",
                height=380)
    # define mass tolerances and their units
    unit = c2.radio("mass tolerance unit", ["ppm", "Da"])
    if unit == "ppm":
        tolerance = c2.number_input("mass tolerance", 1, 100, 10)
    elif unit == "Da":
        tolerance = c2.number_input("mass tolerance", 0.01, 10.0, 0.02)
    # time unit either seconds or minutes
    time_unit = c2.radio("time unit", ["seconds", "minutes"])
    # we need an AUC intensity cutoff value
    baseline = c2.number_input("AUC baseline", 0, 1000000, 5000, 1000)
    # combine variants of the same metabolite
    combine = c2.checkbox("combine variants of same metabolite", help="Combines different variants (e.g. adducts or neutral losses) of a metabolite. Put a `#` with the name first and variant second (e.g. `glucose#[M+H]+` and `glucose#[M+Na]+`)")

    # run the workflow...
    _, _, c3 = st.columns(3)
    run_button = c3.button("**Extract Chromatograms!**")

    # set the mzML file directory
    mzML_dir = "mzML_files"

    # run only if there are files in the mzML dir
    if run_button and any(Path(mzML_dir).iterdir()):
        Helper().reset_directory(results_dir)

        # make a zip file with tables in tsv format
        tsv_dir = os.path.join(results_dir, "tsv-tables")
        Helper().reset_directory(tsv_dir)

        # extract compound massses, names and time points for chromatogram extraction
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
        
        # create an empty df for AUCs with filenames as columns and mass names as indexes
        df_auc = pd.DataFrame(columns = [file.name for file in Path(mzML_dir).glob("*.mzML")], index=names)

        # iterate over the files and extract chromatograms in a single dataframe per file
        for file in Path(mzML_dir).glob("*.mzML"):
            with st.spinner("Extracting from: " + str(file)):
                # load mzML file into exp
                exp = MSExperiment()
                MzMLFile().load(str(file), exp)

                # create an empty dataframe to collect chromatogram data in
                df = pd.DataFrame()

                # get BPC and time always for each file
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
                            # get peak intensity at highest peak index
                            peak_intensity = 0
                            if index_highest_peak_within_window > -1:
                                peak_intensity = int(spec[index_highest_peak_within_window].getIntensity())
                            # check if highet then baseline
                            if peak_intensity > baseline:
                                intensity.append(peak_intensity)
                            else:
                                intensity.append(0)
                        else:
                            intensity.append(0)
                    # add intensity values to df
                    df[str(mass)+"_"+name] = intensity
                    # also insert the AUC in the auc dataframe
                    df_auc.loc[name, file.name] = sum(intensity)

                # save to feather dataframe for quick access
                df.to_feather(os.path.join(results_dir, os.path.basename(file)[:-5]+".ftr"))
                # save as tsv for download option
                df.to_csv(os.path.join(tsv_dir, os.path.basename(file)[:-5]+".tsv"), sep="\t", index=False)

        # once all files are processed, zip the tsv files and delete their directory
        shutil.make_archive(os.path.join(results_dir, "chromatograms"), 'zip', tsv_dir)
        shutil.rmtree(tsv_dir)
        # save summary of AUC values to tsv file
        if combine:
            # sum intensities of variants of the same metabolite
            combined = {}
            metabolite_names = list(set([c.split("#")[0] for c in df_auc.index]))
            for filename in df_auc.columns:
                aucs = []
                for a in metabolite_names:
                    auc = 0
                    for b in [b for b in df_auc.index if ((a+"#" in b and b.startswith(a)) or a == b)]:
                        auc += df_auc.loc[b, filename]
                    aucs.append(auc)
                combined[filename] = aucs
            df_auc = pd.DataFrame(combined)
            df_auc.set_index(pd.Index(metabolite_names), inplace=True)
        df_auc.index.name = "metabolite"
        df_auc.to_csv(Path(results_dir, "summary.tsv"), sep="\t")

    elif run_button:
        st.warning("Upload some mzML files first!")

    if any(Path(results_dir).iterdir()):
        # add separator for results
        st.markdown("***")
        df_auc = pd.read_csv(Path(results_dir, "summary.tsv"), sep="\t").set_index("metabolite")
        # download everything required
        st.markdown("#### Downloads")
        c1, c2, c3 = st.columns(3)
        c1.download_button("FeatureMatrix", df_auc.to_csv(sep="\t"), f"FeatureMatrix-EIC-{datetime.now().strftime('%d%m%Y-%H-%M-%S')}.tsv")
        c2.download_button("MetaData", pd.DataFrame({"filename": df_auc.columns, "ATTRIBUTE_Sample_Type": ["Sample"]*df_auc.shape[1]}).to_csv(sep="\t", index=False), f"MetaData-EIC-{datetime.now().strftime('%d%m%Y-%H-%M-%S')}.tsv")
        with open(os.path.join(results_dir, "chromatograms.zip"), "rb") as fp:
            btn = c3.download_button(
                label="Chromatograms",
                data=fp,
                file_name=f"chromatograms-{datetime.now().strftime('%d%m%Y-%H-%M-%S')}.zip",
                mime="application/zip"
            )
        # display the feature matrix and it's bar plot
        st.markdown("#### Feature Matrix")
        st.markdown(f"**{df_auc.shape[0]} rows, {df_auc.shape[1]} columns**")
        st.dataframe(df_auc)
        st.plotly_chart(px.bar(df_auc.T, barmode="group"))

        # compare two files side by side
        st.markdown("#### File Comparison")
        c1, c2 = st.columns(2)
        show_bpc = c1.checkbox("show base peak chromatogram", False)
        show_baseline = c2.checkbox("show baseline for AUC calculation", False)
        for i, c in enumerate([c1, c2]):
            file = c.selectbox(f"select file {i+1}", df_auc.columns)
            df = pd.read_feather(Path(results_dir, file[:-4]+"ftr"))
            if show_baseline:
                df["AUC baseline"] = [baseline] * df.shape[0]
            if not show_bpc:
                df.drop(columns=["BPC"], inplace=True)
            fig = px.line(df, x="time", y=df.columns)
            fig.update_layout(
                title=file[:-5],
                xaxis_title=f"time ({time_unit})",
                yaxis_title="intensity (counts per second)",
                legend_title="metabolite")
            c.plotly_chart(fig)

except:
    st.warning("Something went wrong.")