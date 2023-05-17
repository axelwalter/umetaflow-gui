import streamlit as st
from src.common import *
from src.umetaflow import run_umetaflow, HELP
from pathlib import Path


params = page_setup(page="workflow")

st.title("UmetaFlow")

with st.expander("📖 Help"):
    st.markdown(HELP)

with st.expander("Settings", expanded=True):
    st.markdown("#### 1. Pre-Processing")
    st.markdown("**Feature Detection**")
    c1, c2, c3, c4 = st.columns(4)
    c1.number_input(
        "**mass error ppm**", 1.0, 1000.0, params["ffm_mass_error"], key="ffm_mass_error"
    )

    c2.number_input(
        "**noise threshold**", 10, 1000000000, int(
            params["ffm_noise"]), 100, key="ffm_noise"
    )
    v_space(1, c3)
    c3.checkbox("remove single traces",
                params["ffm_single_traces"], key="ffm_single_traces")

    c4.number_input(
        "min S/N ratio", 1.0, 20.0, params["ffm_snr"], 1.0, key="ffm_snr"
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.number_input(
        "min peak width at FWHM", 0.1, 60.0, params["ffm_min_fwhm"],  key="ffm_min_fwhm"
    )
    c2.number_input(
        "peak width at FWHM", 0.1, 120.0, params["ffm_peak_width"], 1.0, key="ffm_peak_width"
    )
    c3.number_input(
        "max peak width at FWHM", 0.2, 60.0, params["ffm_max_fwhm"], key="ffm_max_fwhm"
    )
    if not (
        st.session_state["ffm_min_fwhm"] <= st.session_state["ffm_peak_width"] <= st.session_state["ffm_max_fwhm"]
    ):
        c4.warning("Check your peak width settings.")

    v_space(1)
    st.checkbox(
        "**Blank Removal**", params["remove_blanks"], key="remove_blanks", help="Useful to filter out features which are present in blank sample/s or e.g. for differential feature detection to remove features which are present in control, but not in treatment samples."
    )
    if st.session_state["remove_blanks"]:
        c1, c2 = st.columns(2)
        c1.multiselect(
            "select blank samples",
            st.session_state["selected-mzML-files"],
            key="blank_files",
            help="The selected samples will be used to calculate avarage feature blank intensities and will not be further processed.",
        )
        c2.number_input(
            "ratio blank/sample average intensity cutoff",
            0.05,
            0.9,
            params["blank_cutoff"],
            0.05,
            key="blank_cutoff",
            help="Features that have an intensity ratio below (avagera blank) to (average samples) will be removed. Set low for strict blank removal.",
        )

    v_space(1)
    st.checkbox("**Map Alignment**", params["use_ma"], key="use_ma")
    if st.session_state["use_ma"]:
        c1, c2, c3 = st.columns(3)
        c1.number_input(
            "**mz max difference**",
            0.01,
            1000.0,
            params["ma_mz_max"],
            step=1.0,
            format="%.2f",
            key="ma_mz_max"
        )
        c2.radio(
            "mz distance unit",
            ["ppm", "Da"],
            ["ppm", "Da"].index(params["ma_mz_unit"]),
            key="ma_mz_unit"
        )

        c3.number_input(
            "RT max difference", 1, 1000, int(params["ma_rt_max"]), 10, key="ma_rt_max"
        )

    v_space(1)
    st.checkbox("**Adduct Detection**", params["use_ad"], key="use_ad")
    if st.session_state["use_ad"]:
        c1, c2, c3, c4 = st.columns(4)
        c1.radio(
            "ionization mode",
            ["positive", "negative"],
            ["positive", "negative"].index(params["ad_ion_mode"]),
            key="ad_ion_mode",
            help="Carefully adjust settings for each mode. Especially potential adducts and negative min/max charges for negative mode.",
        )
        c2.text_area(
            "potential adducts",
            params["ad_adducts"],
            key="ad_adducts",
            help="""
Specify adducts and neutral additions/losses.\n
Format (each in a new line): adducts:charge:probability.\n
The summed up probability for all charged entries needs to be 1.0.\n

Good starting options for positive mode with sodium adduct and water loss:\n
H:+:0.9\n
Na:+:0.1\n
H-2O-1:0:0.4

Good starting options for negative mode with water loss and formic acid addition:\n
H-1:-:1\n
H-2O-1:0:0.5\n
CH2O2:0:0.5
"""
        )
        c3.number_input(
            "charge min",
            -3,
            3,
            params["ad_charge_min"],
            key="ad_charge_min",
            help="e.g. for negative mode -3, for positive mode 1"
        )
        c3.number_input(
            "charge max",
            -3,
            3,
            params["ad_charge_max"],
            key="ad_charge_max",
            help="e.g. for negative mode -1, for positive mode 3",
        )

        c4.number_input(
            "RT max difference",
            1,
            60,
            int(params["ad_rt_max_diff"]),
            key="ad_rt_max_diff",
            help="Groups features with slightly different RT.",
        )

    v_space(1)
    st.markdown("**Feature Linking**")
    c1, c2, c3 = st.columns(3)
    c1.number_input(
        "**mz tolerance**",
        0.01,
        1000.0,
        params["fl_mz_tol"],
        step=1.0,
        format="%.2f",
        key="fl_mz_tol"
    )
    c2.radio(
        "mz tolerance unit",
        ["ppm", "Da"],
        ["ppm", "Da"].index(params["fl_mz_unit"]),
        key="fl_mz_unit"
    )

    c3.number_input("RT tolerance", 1, 200, int(
        params["fl_rt_tol"]), 5, key="fl_rt_tol")

    v_space(1)
    st.markdown("#### 2. Re-Quantification")
    st.checkbox(
        "**Re-Quantification**",
        params["use_requant"],
        key="use_requant",
        help="Go back into the raw data to re-quantify consensus features that have missing values.",
    )

    v_space(1)
    st.markdown("#### 3. Export files for SIRIUS and GNPS")
    st.checkbox(
        "**Export files for SIRIUS**",
        params["use_sirius_manual"],
        key="use_sirius_manual",
        help="Export files for formula and structure predictions. Run Sirius with these pre-processed .ms files, can be found in results -> SIRIUS -> sirius_files.",
    )
    st.checkbox(
        "**Export files for GNPS**",
        params["use_gnps"],
        key="use_gnps",
        help="Run GNPS Feature Based Molecular Networking and Ion Identity Molecular Networking with these files, can be found in results -> GNPS.",
    )
    if st.session_state["use_gnps"]:
        st.checkbox(
            "annotate features with GNPS library",
            params["annotate_gnps_library"],
            key="annotate_gnps_library",
            help="UmetaFlow contains the complete GNPS library in mgf file format. Check to annotate.",
        )

    v_space(1)
    st.markdown("#### 4. Annotation via in-house library")
    st.checkbox(
        "**MS1 annotation by m/z and RT**",
        value=params["annotate_ms1"],
        key="annotate_ms1",
        help="Annotate features on MS1 level with known m/z and retention times values.",
    )
    if st.session_state["annotate_ms1"]:
        ms1_annotation_file_upload = st.file_uploader(
            "Select library for MS1 annotations.", type=["tsv"]
        )
        if ms1_annotation_file_upload:
            path = Path(st.session_state.workspace,
                        ms1_annotation_file_upload.name)
            with open(path, "wb") as f:
                f.write(ms1_annotation_file_upload.getbuffer())
            params["ms1_annotation_file"] = str(path)
        elif params["ms1_annotation_file"]:
            st.info(
                f"Currently selected MS1 library: {Path(params['ms1_annotation_file']).name}")
        else:
            st.warning("No MS1 library selected.")
            params["ms1_annotation_file"] = ""
        c1, c2 = st.columns(2)
        c1.number_input(
            "retention time window for annotation in seconds",
            1, 240, params["annoation_rt_window_sec"], 10,
            key="annoation_rt_window_sec",
            help="Checks around peak apex, e.g. window of 60 s will check left and right 30 s.",
        )
        params["annotation_mz_window_ppm"] = c2.number_input(
            "mz window for annotation in ppm", 1, 100, params["annotation_mz_window_ppm"], 1, key="annotation_mz_window_ppm"
        )

    st.checkbox(
        "**MS2 annotation via fragmentation patterns**",
        params["annotate_ms2"],
        key="annotate_ms2",
        help="Annotate features on MS2 level based on their fragmentation patterns. The library has to be in mgf file format.",
    )
    if st.session_state["annotate_ms2"]:
        ms2_annotation_file_upload = st.file_uploader(
            "Select library for MS2 annotations", type=["mgf"]
        )
        if ms2_annotation_file_upload:
            path = Path(st.session_state.workspace,
                        ms2_annotation_file_upload.name)
            with open(path, "wb") as f:
                f.write(ms2_annotation_file_upload.getbuffer())
            params["ms2_annotation_file"] = str(path)
        elif params["ms2_annotation_file"]:
            st.info(
                f"Currently selected MS2 library: {Path(params['ms2_annotation_file']).name}")
        else:
            st.warning("No MS2 library selected.")
            params["ms2_annotation_file"] = ""

    v_space(1)
    _, c2, _ = st.columns(3)
    run_button = c2.button("Run UmetaFlow", type="primary")

if run_button:
    save_params(params)
    umetaflow_params = load_params()
    # Modify paramters to have float values if necessary
    for key in ("fl_rt_tol", "ad_rt_max_diff", "ma_rt_max", "ffm_noise"):
        umetaflow_params[key] = float(umetaflow_params[key])
    mzML_files = [str(Path(st.session_state.workspace,
                           "mzML-files", f+".mzML")) for f in st.session_state["selected-mzML-files"]]

    results_dir = Path(st.session_state.workspace, "umetaflow-results")
    run_umetaflow(umetaflow_params, mzML_files, results_dir)

save_params(params)
