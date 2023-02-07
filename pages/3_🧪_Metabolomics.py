import streamlit as st
import pandas as pd
from src.core import *
from src.helpers import *
from src.dataframes import *
from src.visualization import Visualization
from src.umetaflow import run
from src.constants import METABO, WARNINGS, ERRORS
from pathlib import Path
from datetime import datetime
import json

st.set_page_config(
    page_title="UmetaFlow",
    page_icon="resources/icon.png",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None,
)

try:
    # create result dir if it does not exist already
    if "workspace" in st.session_state:
        results_dir = Path(str(st.session_state["workspace"]), "results-metabolomics")
    else:
        st.warning(WARNINGS["no-workspace"])
        st.experimental_rerun()
    if not os.path.exists(results_dir):
        os.mkdir(results_dir)

    with st.sidebar:
        # show currently available mzML files
        st.markdown("### Uploaded Files")
        for f in sorted(st.session_state["mzML_files"].iterdir()):
            if f.name in st.session_state:
                checked = st.session_state[f.name]
            else:
                checked = True
            st.checkbox(f.name[:-5], checked, key=f.name)

        st.markdown("***")
        st.image("resources/OpenMS.png", "powered by")

    st.title("Metabolomics")

    with st.expander("📖 **Help**"):
        st.markdown(METABO["main"])

    if Path(Path(st.session_state["workspace"], "metabolomics.json")).is_file():
        with open(Path(st.session_state["workspace"], "metabolomics.json")) as f:
            params = json.loads(f.read())
    else:
        with open("params/metabolomics_defaults.json") as f:
            params = json.loads(f.read())

except:
    st.error(ERRORS["general"])

try:
    st.markdown("#### 1. Pre-Processing")
    st.markdown("**Feature Detection**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        params["ffm_mass_error"] = st.number_input(
            "**mass error ppm**", 1.0, 1000.0, params["ffm_mass_error"]
        )
        params["ffm_min_fwhm"] = st.number_input(
            "min peak width at FWHM", 0.1, 60.0, params["ffm_min_fwhm"]
        )

    with col2:
        params["ffm_noise"] = float(
            st.number_input(
                "**noise threshold**", 10, 1000000000, int(params["ffm_noise"]), 100
            )
        )
        params["ffm_peak_width"] = st.number_input(
            "peak width at FWHM", 0.1, 120.0, params["ffm_peak_width"], 1.0
        )
    with col3:
        st.markdown("##")
        params["ffm_single_traces"] = st.checkbox(
            "remove single traces", params["ffm_single_traces"]
        )
        if params["ffm_single_traces"]:
            ffm_single_traces = "true"
        else:
            ffm_single_traces = "false"
        st.markdown("#####")
        params["ffm_max_fwhm"] = st.number_input(
            "max peak width at FWHM", 0.2, 60.0, params["ffm_max_fwhm"]
        )
    with col4:
        params["ffm_snr"] = st.number_input(
            "min S/N ratio", 1.0, 20.0, params["ffm_snr"], 1.0
        )
    if not (
        params["ffm_min_fwhm"] <= params["ffm_peak_width"] <= params["ffm_max_fwhm"]
    ):
        st.warning("Check your peak width settings.")

    params["use_ma"] = st.checkbox("**Map Alignment**", params["use_ma"])
    if params["use_ma"]:
        col1, col2, col3 = st.columns(3)
        with col1:
            params["ma_mz_max"] = st.number_input(
                "**mz max difference**",
                0.01,
                1000.0,
                params["ma_mz_max"],
                step=1.0,
                format="%.2f",
            )
        with col2:
            params["ma_mz_unit"] = st.radio(
                "mz distance unit",
                ["ppm", "Da"],
                ["ppm", "Da"].index(params["ma_mz_unit"]),
            )
        with col3:
            params["ma_rt_max"] = float(
                st.number_input(
                    "RT max difference", 1, 1000, int(params["ma_rt_max"]), 10
                )
            )

    if params["use_ad"]:
        use_ad = True
    else:
        use_ad = False
    params["use_ad"] = st.checkbox("**Adduct Detection**", use_ad)
    if params["use_ad"]:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            params["ad_ion_mode"] = st.radio(
                "ionization mode",
                ["positive", "negative"],
                ["positive", "negative"].index(params["ad_ion_mode"]),
                help=METABO["ad_ion_mode"],
            )
        with col2:
            params["ad_adducts"] = st.text_area(
                "potential adducts",
                params["ad_adducts"],
                help=METABO["potential_adducts"],
            )
        with col3:
            params["ad_charge_min"] = st.number_input(
                "charge min",
                -3,
                3,
                params["ad_charge_min"],
                help=METABO["ad_charge_min"],
            )
            params["ad_charge_max"] = st.number_input(
                "charge max",
                -3,
                3,
                params["ad_charge_max"],
                help=METABO["ad_charge_min"],
            )
        with col4:
            params["ad_rt_max_diff"] = float(
                st.number_input(
                    "RT max difference",
                    1,
                    60,
                    int(params["ad_rt_max_diff"]),
                    help=METABO["ad_rt_diff"],
                )
            )

    st.markdown("**Feature Linking**")
    col1, col2, col3 = st.columns(3)
    with col1:
        params["fl_mz_tol"] = float(
            st.number_input(
                "**mz tolerance**",
                0.01,
                1000.0,
                params["fl_mz_tol"],
                step=1.0,
                format="%.2f",
            )
        )
    with col2:
        params["fl_mz_unit"] = st.radio(
            "mz tolerance unit",
            ["ppm", "Da"],
            ["ppm", "Da"].index(params["fl_mz_unit"]),
        )
    with col3:
        params["fl_rt_tol"] = float(
            st.number_input("RT tolerance", 1, 200, int(params["fl_rt_tol"]))
        )

    st.markdown("#### 2. Re-Quantification")
    params["use_requant"] = st.checkbox(
        "**Re-Quantification**",
        params["use_requant"],
        help=METABO["re-quant"],
    )

    st.markdown("#### 3. Export files for SIRIUS and GNPS")
    params["use_sirius_manual"] = st.checkbox(
        "**Export files for SIRIUS**",
        params["use_sirius_manual"],
        help=METABO["sirius"],
    )
    params["use_gnps"] = st.checkbox(
        "**Export files for GNPS**",
        params["use_gnps"],
        help=METABO["gnps"],
    )
    if params["use_gnps"]:
        params["annotate_gnps_library"] = st.checkbox(
            "annotate features with GNPS library",
            True,
            help=METABO["annotate_gnps"],
        )

    st.markdown("#### 4. Annotation via in-house library")
    params["annotate_ms1"] = st.checkbox(
        "**MS1 annotation by m/z and RT**",
        value=params["annotate_ms1"],
        help=METABO["annotate_ms1"],
    )
    if params["annotate_ms1"]:
        ms1_annotation_file_upload = st.file_uploader(
            "Select library for MS1 annotations.", type=["tsv"]
        )
        if ms1_annotation_file_upload:
            params["ms1_annotation_file"] = os.path.join(
                str(st.session_state["workspace"]), ms1_annotation_file_upload.name
            )
            with open(params["ms1_annotation_file"], "wb") as f:
                f.write(ms1_annotation_file_upload.getbuffer())
        elif params["ms1_annotation_file"]:
            st.write(
                "Currently selected MS1 library: "
                + Path(params["ms1_annotation_file"]).name
            )
        else:
            st.warning("No MS1 library selected.")
            params["ms1_annotation_file"] = ""
        c1, c2 = st.columns(2)
        params["annoation_rt_window_sec"] = c1.number_input(
            "retention time window for annotation in seconds",
            1,
            240,
            60,
            10,
            help=METABO["annotate_ms1_rt"],
        )
        params["annotation_mz_window_ppm"] = c2.number_input(
            "mz window for annotation in ppm", 1, 100, 10, 1
        )

    params["annotate_ms2"] = st.checkbox(
        "**MS2 annotation via fragmentation patterns**",
        value=params["annotate_ms2"],
        help=METABO["annotate_ms2"],
    )
    if params["annotate_ms2"]:
        params["use_gnps"] = True
        ms2_annotation_file_upload = st.file_uploader(
            "Select library for MS2 annotations", type=["mgf"]
        )
        if ms2_annotation_file_upload:
            params["ms2_annotation_file"] = os.path.join(
                str(st.session_state["workspace"]), ms2_annotation_file_upload.name
            )
            with open(params["ms2_annotation_file"], "wb") as f:
                f.write(ms2_annotation_file_upload.getbuffer())
        elif params["ms2_annotation_file"]:
            st.write(
                "Currently selected MS2 library: "
                + Path(params["ms2_annotation_file"]).name
            )
        else:
            st.warning("No MS2 library selected.")
            params["ms2_annotation_file"] = ""

    st.markdown("##")
    c1, c2, _, c4 = st.columns(4)
    if c1.button("Load defaults"):
        if Path(st.session_state["workspace"], "metabolomics.json").is_file():
            Path(st.session_state["workspace"], "metabolomics.json").unlink()

    if c2.button("**Save parameters**"):
        with open(Path(st.session_state["workspace"], "metabolomics.json"), "w") as f:
            f.write(json.dumps(params, indent=4))

    run_button = c4.button("**Run Workflow!**")

except:
    st.warning(ERRORS["parameters"])

try:
    # check for mzML files
    mzML_files = [
        str(Path(st.session_state["mzML_files"], key))
        for key, value in st.session_state.items()
        if key.endswith("mzML") and value
    ]

    if run_button and mzML_files:

        results_dir = Helper().reset_directory(results_dir)

        run(params, mzML_files, results_dir)

        st.success("Complete!")

    elif run_button:
        st.warning(WARNINGS["missing-mzML"])
except:
    st.error(ERRORS["workflow"])

try:
    if any(Path(results_dir).iterdir()):

        df = pd.DataFrame()

        if Path(results_dir, "FeatureMatrix.tsv").is_file():
            df = pd.read_csv(Path(results_dir, "FeatureMatrix.tsv"), sep="\t")
            st.session_state["missing_values_before"] = sum(
                [(df[col] == 0).sum() for col in df.columns]
            )
        if Path(results_dir, "FeatureMatrixRequantified.tsv").is_file():
            df = pd.read_csv(
                Path(results_dir, "FeatureMatrixRequantified.tsv"), sep="\t"
            )
            st.session_state["missing_values_after"] = sum(
                [(df[col] == 0).sum() for col in df.columns]
            )

        if not df.empty:
            st.markdown("***")
            st.markdown("#### Feature Matrix")
            st.markdown(f"**{df.shape[0]} rows, {df.shape[1]} columns**")
            st.dataframe(df)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("number of features", df.shape[0])
            col2.metric(
                "number of samples", len([col for col in df.columns if "mzML" in col])
            )
            if "missing_values_before" in st.session_state:
                col3.metric("missing values", st.session_state.missing_values_before)
            if "missing_values_after" in st.session_state:
                col4.metric(
                    "missing values after re-quantification",
                    st.session_state.missing_values_after,
                )
            st.markdown("***")
            st.markdown("#### Downloads")
            col1, col2, col3, col4 = st.columns(4)
            col1.download_button(
                "Feature Matrix",
                df.to_csv(sep="\t", index=False),
                f"FeatureMatrix-{datetime.now().strftime('%d%m%Y-%H-%M')}.tsv",
            )
            df_md = pd.read_csv(os.path.join(results_dir, "MetaData.tsv"), sep="\t")
            col2.download_button(
                "Meta Data",
                df_md.to_csv(sep="\t", index=False),
                f"MetaData-{datetime.now().strftime('%d%m%Y-%H-%M')}.tsv",
            )
            if Path(results_dir, "interim", "ExportSirius.zip").is_file():
                with open(
                    os.path.join(results_dir, "interim", "ExportSirius.zip"), "rb"
                ) as fp:
                    btn = col3.download_button(
                        label="Files for Sirius",
                        data=fp,
                        file_name=f"ExportSirius-{datetime.now().strftime('%d%m%Y-%H-%M')}.zip",
                        mime="application/zip",
                    )
            if Path(results_dir, "interim", "ExportGNPS.zip").is_file():
                with open(
                    os.path.join(results_dir, "interim", "ExportGNPS.zip"), "rb"
                ) as fp:
                    btn = col4.download_button(
                        label="Files for GNPS",
                        data=fp,
                        file_name=f"ExportGNPS-{datetime.now().strftime('%d%m%Y-%H-%M')}.zip",
                        mime="application/zip",
                    )
        st.markdown("***")
        st.markdown("#### Inspect Details")
        # display detailed results
        options = ["mzML files"]
        try:
            path = Path(results_dir, "interim", "FFM_df")
            if path.exists():
                if any(path.iterdir()):
                    options.append("detected features")
            path = Path(results_dir, "interim", "FFM_aligned_df")
            if path.exists():
                if any(path.iterdir()):
                    options.append("feature map alignment")
            path = Path(results_dir, "interim", "FFMID_df")
            if path.exists():
                options.append("feature re-quantification")
            path = Path(results_dir, "FeatureMatrix.ftr")
            if path.is_file():
                options.append("consensus features")
        except FileNotFoundError:
            pass

        choice = st.radio("choose to view", options)

        # ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']
        if choice == "mzML files":
            Visualization.display_MS_data(
                {
                    file.stem: pd.read_feather(file)
                    for file in Path(st.session_state["mzML_dfs"]).iterdir()
                }
            )

        elif choice == "detected features":
            Visualization.display_feature_data(
                {
                    file.stem: pd.read_feather(file)
                    for file in Path(
                        results_dir,
                        "interim",
                        "FFM_df",
                    ).iterdir()
                },
                {
                    file.stem: pd.read_feather(file)
                    for file in Path(st.session_state["mzML_dfs"]).iterdir()
                },
            )

        elif choice == "feature map alignment":
            Visualization.display_map_alignemnt(
                {
                    file.stem: pd.read_feather(file)[["mz", "RT", "original_rt"]]
                    for file in Path(
                        results_dir,
                        "interim",
                        "FFM_aligned_df",
                    ).iterdir()
                }
            )

        elif choice == "feature re-quantification":
            if params["use_ma"]:
                mzML_dir = Path(results_dir, "interim", "mzML_aligned_df")
            else:
                mzML_dir = Path(st.session_state["mzML_dfs"])
            Visualization.display_feature_data(
                {
                    file.stem: pd.read_feather(file)
                    for file in Path(
                        results_dir,
                        "interim",
                        "FFMID_df",
                    ).iterdir()
                },
                {file.stem: pd.read_feather(file) for file in mzML_dir.iterdir()},
            )

        elif choice == "consensus features":
            if params["use_requant"]:
                feature_dir = Path(results_dir, "interim", "FFMID_df")
            else:
                feature_dir = Path(results_dir, "interim", "FFM_df")
            Visualization.display_consensus_map(
                pd.read_feather(Path(results_dir, "FeatureMatrix.ftr")),
                {file.stem: pd.read_feather(file) for file in feature_dir.iterdir()},
            )

except:
    st.error(ERRORS["visualization"])
