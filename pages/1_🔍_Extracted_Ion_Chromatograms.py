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
import json
import time

st.set_page_config(page_title="UmetaFlow", page_icon="resources/icon.png", layout="wide", initial_sidebar_state="auto", menu_items=None)

# try:
# create result dir if it does not exist already
if "workspace" in st.session_state:
    results_dir = Path(str(st.session_state["workspace"]), "results-extract-chromatograms")
else:
    st.warning("No online workspace ID found, please visit the start page first (UmetaFlow tab).")
    st.experimental_rerun()
if not os.path.exists(results_dir):
    os.mkdir(results_dir)

with st.sidebar:
    st.image("resources/OpenMS.png", "powered by")
    st.markdown("***")
    # Removing files
    st.markdown("### Remove Files")
    c1, c2 = st.columns(2)
    if c1.button("⚠️ **All**"):
        try:
            if any(st.session_state["mzML_files"].iterdir()):
                Helper().reset_directory(st.session_state["mzML_files"])
                st.experimental_rerun()
        except:
            pass
    if c2.button("**Un**selected"):
        try:
            for file in [Path(st.session_state["mzML_files"], key) for key, value in st.session_state.items() if key.endswith("mzML") and not value]:
                file.unlink()
            st.experimental_rerun()
        except:
            pass

    # show currently available mzML files
    st.markdown("### Uploaded Files")
    for f in sorted(st.session_state["mzML_files"].iterdir()):
        if f.name in st.session_state:
            checked = st.session_state[f.name]
        else:
            checked = True
        st.checkbox(f.name[:-5], checked, key=f.name)


st.title("Extracted Ion Chromatograms (EIC/XIC)")

with st.expander("📖 **Help**"):
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

if Path(st.session_state["workspace"], "extract.json").is_file():
    with open(Path(st.session_state["workspace"], "extract.json")) as f:
        params = json.loads(f.read())
else:
    with open("params/extract_defaults.json") as f:
        params = json.loads(f.read())

# parameters
c1, c2 = st.columns(2)
# text area to define masses in with name, mass and optionl RT boundaries
params["masses_text"] = c1.text_area("masses", params["masses_text"], height=380,
            help="Add one mass per line and optionally label it with an equal sign e.g. 222.0972=GlcNAc.")

# define mass tolerances and their units
params["mz_unit"] =  c2.radio("mass tolerance unit", ["ppm", "Da"], index=["ppm", "Da"].index(params["mz_unit"]))

if params["mz_unit"] == "ppm":
    params["tolerance_ppm"] = c2.number_input("mass tolerance", 1, 100, params["tolerance_ppm"])
else:
    params["tolerance_da"] = c2.number_input("mass tolerance", 0.01, 10.0, params["tolerance_da"])

# time unit either seconds or minutes
params["time_unit"] = c2.radio("time unit", ["seconds", "minutes"], index=["seconds", "minutes"].index(params["time_unit"]))

# we need an AUC intensity cutoff value
params["baseline"] = c2.number_input("AUC baseline", 0, 1000000, params["baseline"], 100)

# combine variants of the same metabolite
params["combine"] = c2.checkbox("combine variants of same metabolite", params["combine"], help="Combines different variants (e.g. adducts or neutral losses) of a metabolite. Put a `#` with the name first and variant second (e.g. `glucose#[M+H]+` and `glucose#[M+Na]+`)")

st.markdown("##")
# run the workflow...
c1, c2, _, c4= st.columns(4)
if c1.button("Load defaults"):
    if Path(st.session_state["workspace"], "extract.json").is_file():
        Path(st.session_state["workspace"], "extract.json").unlink()

if c2.button("**Save parameters**"):
    with open(Path(st.session_state["workspace"], "extract.json"), "w") as f:
        f.write(json.dumps(params, indent=4))

if c4.button(label="**Extract Chromatograms!**"):

    mzML_files = [Path(st.session_state["mzML_files"], key) for key, value in st.session_state.items() if key.endswith("mzML") and value]

    if not mzML_files:
        st.warning("Upload or select some mzML files first!")

    Helper().reset_directory(results_dir)

    # to make a zip file with tables in tsv format later create a directory
    tsv_dir = os.path.join(results_dir, "tsv-tables")
    Helper().reset_directory(tsv_dir)

    # extract compound massses, names and time points for chromatogram extraction
    masses = []
    names = []
    times = []
    for line in [line for line in params["masses_text"].split('\n') if line != '']:
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
        if params["time_unit"] == "minutes":
            time_factor = 60.0
        if "-" in time:
            times.append([float(time.split("-")[0].strip())*time_factor, float(time.split("-")[1].strip())*time_factor])
        else:
            times.append([0,0])
        
    # create an empty df for AUCs with filenames as columns and mass names as indexes
    df_auc = pd.DataFrame(columns = [Path(file).name for file in mzML_files], index=names)

    # iterate over the files and extract chromatograms in a single dataframe per file
    for file in mzML_files:
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
                if params["time_unit"] == "minutes":
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
                        if params["mz_unit"] == "Da":
                            index_highest_peak_within_window = spec.findHighestInWindow(mass, params["tolerance_da"], params["tolerance_da"])
                        else:
                            index_highest_peak_within_window = spec.findHighestInWindow(mass,float((params["tolerance_ppm"]/1000000)*mass),float((params["tolerance_ppm"]/1000000)*mass))
                        # get peak intensity at highest peak index
                        peak_intensity = 0
                        if index_highest_peak_within_window > -1:
                            peak_intensity = int(spec[index_highest_peak_within_window].getIntensity())
                        # check if highet then baseline
                        if peak_intensity > params["baseline"]:
                            intensity.append(peak_intensity)
                        else:
                            intensity.append(0)
                    else:
                        intensity.append(0)
                # add intensity values to df
                df[str(mass)+"_"+name] = intensity
                # also insert the AUC in the auc dataframe
                df_auc.loc[name, Path(file).name] = sum(intensity)

            # save to feather dataframe for quick access
            df.to_feather(Path(results_dir, Path(file).stem+".ftr"))
            # save as tsv for download option
            df.to_csv(Path(tsv_dir,  Path(file).stem+".tsv"), sep="\t", index=False)

    # once all files are processed, zip the tsv files and delete their directory
    shutil.make_archive(os.path.join(results_dir, "chromatograms"), 'zip', tsv_dir)
    shutil.rmtree(tsv_dir)

    # save summary of AUC values to tsv file
    if params["combine"]:
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
    df_auc = df_auc.reindex(sorted(df_auc.columns), axis=1)
    df_auc.to_csv(Path(results_dir, "summary.tsv"), sep="\t")

if any(Path(results_dir).glob("*.ftr")):
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
    fig = px.bar(df_auc.T, barmode="group")
    fig.update_layout(
        xaxis_title="",
        yaxis_title="area under curve",
        legend_title="metabolite")
    st.plotly_chart(fig)

    # compare two files side by side
    st.markdown("#### File Comparison")
    c1, c2 = st.columns(2)
    show_bpc = c1.checkbox("show base peak chromatogram", False)
    show_baseline = c2.checkbox("show baseline for AUC calculation", False)
    for i, c in enumerate([c1, c2]):
        file = c.selectbox(f"select file {i+1}", df_auc.columns)
        df = pd.read_feather(Path(results_dir, file[:-4]+"ftr"))
        if show_baseline:
            df["AUC baseline"] = [params["baseline"]] * df.shape[0]
        if not show_bpc:
            df.drop(columns=["BPC"], inplace=True)
        fig = px.line(df, x="time", y=df.columns)
        fig.update_layout(
            title=file[:-5],
            xaxis_title=f"time ("+params["time_unit"]+")",
            yaxis_title="intensity (counts per second)",
            legend_title="metabolite")
        c.plotly_chart(fig)

# except:
#     st.warning("Something went wrong.")