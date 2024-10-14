import streamlit as st
from src.common.common import *
from src.umetaflow import run_umetaflow, HELP
from src.viewmetabolomics import *
from pathlib import Path

params = page_setup(page="workflow")

with st.sidebar:
    st.markdown(HELP)

st.title("UmetaFlow")
st.info(
    "💡Workflow using **pyOpenMS** with limited functionality. Consider using **UmetaFlow TOPP** for complete functionality and fast execution times."
)

results_only = st.toggle("view results only")

results_dir = Path(st.session_state.workspace, "umetaflow-results")


if not results_only:
    df_path = Path(st.session_state.workspace, "mzML-files.tsv")

    if not df_path.exists():
        mzML_files = []
    else:
        df = pd.read_csv(df_path, sep="\t")

        # Filter the DataFrame for files where "use in workflow" is True
        selected_files = df[df["use in workflows"] == True]["file name"].tolist()

        # Construct full file paths
        mzML_files = [
            Path(st.session_state.workspace, "mzML-files", file_name)
            for file_name in selected_files
        ]
    if not mzML_files:
        st.warning("No mzML files selected.")
    with st.form("umetaflow-form"):
        st.markdown("**1. Pre-Processing**")
        tabs = st.tabs(
            [
                "Feature Detection",
                "Map Alignement",
                "Adduct Detection",
                "Feature Linking",
            ]
        )
        with tabs[0]:
            c1, c2, c3, c4 = st.columns(4)
            c1.number_input(
                "**mass error ppm**",
                1.0,
                1000.0,
                params["ffm_mass_error"],
                key="ffm_mass_error",
            )

            c2.number_input(
                "**noise threshold**",
                10,
                1000000000,
                int(params["ffm_noise"]),
                100,
                key="ffm_noise",
            )
            v_space(1, c3)
            c3.checkbox(
                "remove single traces",
                params["ffm_single_traces"],
                key="ffm_single_traces",
            )

            c4.number_input(
                "min S/N ratio", 1.0, 20.0, params["ffm_snr"], 1.0, key="ffm_snr"
            )
            c1, c2, c3, c4 = st.columns(4)
            c1.number_input(
                "min peak width at FWHM",
                0.1,
                60.0,
                params["ffm_min_fwhm"],
                key="ffm_min_fwhm",
            )
            c2.number_input(
                "peak width at FWHM",
                0.1,
                120.0,
                params["ffm_peak_width"],
                1.0,
                key="ffm_peak_width",
            )
            c3.number_input(
                "max peak width at FWHM",
                0.2,
                60.0,
                params["ffm_max_fwhm"],
                key="ffm_max_fwhm",
            )
            if not (
                st.session_state["ffm_min_fwhm"]
                <= st.session_state["ffm_peak_width"]
                <= st.session_state["ffm_max_fwhm"]
            ):
                c4.warning("Check your peak width settings.")

        with tabs[2]:
            st.checkbox(
                "align feature map retention times", params["use_ma"], key="use_ma"
            )
            # if st.session_state["use_ma"]:
            c1, c2, c3 = st.columns(3)
            c1.number_input(
                "**mz max difference**",
                0.01,
                1000.0,
                params["ma_mz_max"],
                step=1.0,
                format="%.2f",
                key="ma_mz_max",
            )
            c2.radio(
                "mz distance unit",
                ["ppm", "Da"],
                ["ppm", "Da"].index(params["ma_mz_unit"]),
                key="ma_mz_unit",
            )

            c3.number_input(
                "RT max difference",
                1,
                1000,
                int(params["ma_rt_max"]),
                10,
                key="ma_rt_max",
            )

        with tabs[3]:
            st.checkbox("detect adducts", params["use_ad"], key="use_ad")
            # if st.session_state["use_ad"]:
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
""",
            )
            c3.number_input(
                "charge min",
                -3,
                3,
                params["ad_charge_min"],
                key="ad_charge_min",
                help="e.g. for negative mode -3, for positive mode 1",
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

        with tabs[3]:
            st.markdown("link consensus features")
            c1, c2, c3 = st.columns(3)
            c1.number_input(
                "**mz tolerance**",
                0.01,
                1000.0,
                params["fl_mz_tol"],
                step=1.0,
                format="%.2f",
                key="fl_mz_tol",
            )
            c2.radio(
                "mz tolerance unit",
                ["ppm", "Da"],
                ["ppm", "Da"].index(params["fl_mz_unit"]),
                key="fl_mz_unit",
            )

            c3.number_input(
                "RT tolerance", 1, 200, int(params["fl_rt_tol"]), 5, key="fl_rt_tol"
            )

        st.markdown("**2. Re-Quantification**")
        st.checkbox(
            "re-quantify consensus features with missing values",
            params["use_requant"],
            key="use_requant",
            help="Go back into the raw data to re-quantify consensus features that have missing values.",
        )


        c1, c2 = st.columns(2)
        if c1.form_submit_button("💾 Save Parameters", use_container_width=True):
            save_params(params)
        run_button = c2.form_submit_button(
            "Run UmetaFlow", type="primary", use_container_width=True
        )

    if run_button:
        save_params(params)
        reset_directory(results_dir)
        run_umetaflow(params, mzML_files, results_dir)

if results_dir.exists():
    v_space(1)
    df = pd.DataFrame()

    # Determine which dataframe to use and extract metrics
    if Path(results_dir, "FeatureMatrix.tsv").is_file():
        df = pd.read_csv(Path(results_dir, "FeatureMatrix.tsv"), sep="\t")
        st.session_state["missing_values_before"] = sum(
            [(df[col] == 0).sum() for col in df.columns]
        )
    if Path(results_dir, "FeatureMatrixRequantified.tsv").is_file():
        df = pd.read_csv(Path(results_dir, "FeatureMatrixRequantified.tsv"), sep="\t")
        st.session_state["missing_values_after"] = sum(
            [(df[col] == 0).sum() for col in df.columns]
        )

    if not df.empty:
        # id number integers too large for st dataframe, convert to string
        if "id" in df.columns:
            df["id"] = df["id"].astype(str)

        if Path(results_dir, "interim", "FFM_aligned_df").exists():
            ffm_path = Path(results_dir, "interim", "FFM_aligned_df")
            mzML_path = Path(results_dir, "interim", "mzML_aligned_df")
        else:
            ffm_path = Path(results_dir, "interim", "FFM_df")
            mzML_path = Path(results_dir, "interim", "mzML_original_df")

        tab_options = ["📁 Feature matrix", "📈 Consensus Features"]
        if ffm_path.exists():
            tab_options.append("📈 Feature Detection")
        if Path(results_dir, "interim", "FFM_aligned_df").exists():
            tab_options.append("📈 Map alignement")
        if Path(results_dir, "interim", "FFMID_df").exists():
            tab_options.append("📈 Re-quantification")
        tab_options.append("📁 Download results")
        # if Path(results_dir, "FeatureMatrix.ftr").exists():
        #     tabs.append("📈 Consensus features")
        tabs = st.tabs(tab_options)

        with tabs[0]:
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

        with tabs[1]:
            if Path(results_dir, "interim", "FFMID_df").exists():
                feature_dir = Path(results_dir, "interim", "FFMID_df")
            else:
                if Path(results_dir, "interim", "FFM_df").exists():
                    feature_dir = Path(results_dir, "interim", "FFM_df")
                else:
                    feature_dir = Path(results_dir, "interim", "FFM_aligned_df")
            display_consensus_map(
                pd.read_feather(Path(results_dir, "FeatureMatrix.ftr")),
                {file.stem: pd.read_feather(file) for file in feature_dir.iterdir()},
            )

        with tabs[tab_options.index("📈 Feature Detection")]:
            display_feature_data(
                {f.stem: pd.read_feather(f) for f in ffm_path.iterdir()},
                {f.stem: pd.read_feather(f) for f in mzML_path.iterdir()},
            )

        if Path(results_dir, "interim", "FFM_aligned_df").exists():
            with tabs[tab_options.index("📈 Map alignement")]:
                display_map_alignement(
                    {
                        f.stem: pd.read_feather(f)[["mz", "RT", "original_rt"]]
                        for f in Path(
                            results_dir, "interim", "FFM_aligned_df"
                        ).iterdir()
                    }
                )

        if Path(results_dir, "interim", "FFMID_df").exists():
            if Path(results_dir, "interim", "mzML_aligned_df").exists():
                mzML_dir = Path(results_dir, "interim", "mzML_aligned_df")
            else:
                mzML_dir = Path(results_dir, "interim", "mzML_original_df")
            with tabs[tab_options.index("📈 Re-quantification")]:
                display_feature_data(
                    {
                        file.stem: pd.read_feather(file)
                        for file in Path(
                            results_dir,
                            "interim",
                            "FFMID_df",
                        ).iterdir()
                    },
                    {file.stem: pd.read_feather(file) for file in mzML_dir.iterdir()},
                    "FFMID",
                )

        with tabs[-1]:
            c1, c2 = st.columns([0.2, 0.8])
            c1.download_button(
                "Feature Matrix",
                df.to_csv(sep="\t", index=False),
                "FeatureMatrix.tsv",
            )
            df_md = pd.read_csv(os.path.join(results_dir, "MetaData.tsv"), sep="\t")
            c2.markdown(
                "**Add new attributes to meta data** (hover on bottom border to add more rows)"
            )
            md = c2.data_editor(df_md.T, use_container_width=True, num_rows="dynamic")
            c1.download_button(
                "Meta Data",
                md.T.to_csv(sep="\t", index=False),
                "MetaData.tsv",
            )
