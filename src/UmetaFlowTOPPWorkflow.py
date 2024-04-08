import streamlit as st
from pathlib import Path
from .workflow.WorkflowManager import WorkflowManager

from src.common import show_fig

# tmp imports
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from itertools import cycle


class Workflow(WorkflowManager):
    # Setup pages for upload, parameter, execution and results.
    # For layout use any streamlit components such as tabs (as shown in example), columns, or even expanders.
    def __init__(self) -> None:
        # Initialize the parent class with the workflow name.
        super().__init__("UmetaFlow", st.session_state["workspace"])

    def upload(self) -> None:
        return

    def configure(self) -> None:

        tabs = st.tabs(
            [
                "**mzML files**",
                "**Pre-Processing**",
                "Re-Quantification",
                "Input Files for SIRIUS & GNPS",
                "Annotation (MS1 & MS2)",
            ]
        )
        # Create tabs for different analysis steps.
        with tabs[0]:
            self.ui.input_widget(
                "mzML-files",
                [],
                name="select mzML files",
                options=[
                    str(p)
                    for p in Path(st.session_state.workspace, "mzML-files").iterdir()
                ],
                help="Select mzML files for the analysis.",
            )
        with tabs[1]:
            t = st.tabs(
                [
                    "Precursor Mass Correction",
                    "**Feature Detection**",
                    "Adduct Detection",
                    "Map Alignement",
                    "**Feature Linking**",
                ]
            )
            with t[0]:
                self.ui.input_widget(
                    "correct-precursor",
                    True,
                    "correct precursor mass to highest intensity peak",
                    help="Correct precursor mass to highest intensity MS peak peak.",
                )
                self.ui.input_TOPP(
                    "HighResPrecursorMassCorrector",
                    include_parameters=[
                        "highest_intensity_peak:mz_tolerance",
                    ],
                    custom_defaults={"highest_intensity_peak:mz_tolerance": 100.0},
                )
            with t[1]:
                # Parameters for FeatureFinderMetabo TOPP tool.
                self.ui.input_TOPP(
                    "FeatureFinderMetabo",
                    exclude_parameters=["report_convex_hulls", "quant_method"],
                    custom_defaults={
                        "algorithm:common:noise_threshold_int": 1000.0,
                        "algorithm:ffm:remove_single_traces": "true",
                        "algorithm:ffm:report_convex_hulls": "true",
                    },
                )
            with t[2]:
                # A single checkbox widget for workflow logic.
                self.ui.input_widget(
                    "adduct-detection",
                    False,
                    "enable **adduct detection**",
                    help="Detect feature adducts using the OpenMS TOPP tool *MetaboliteAdductDecharger*.",
                )
                # Paramters for MetaboliteAdductDecharger TOPP tool.
                self.ui.input_TOPP("MetaboliteAdductDecharger")
            with t[3]:
                self.ui.input_widget(
                    "map-alignement",
                    True,
                    "enable **map alignement**",
                    help="Align features to a reference map using the OpenMS TOPP tool *MapAlignerPoseClustering*.",
                )
                self.ui.input_TOPP(
                    "MapAlignerPoseClustering", exclude_parameters=["index"]
                )
            with t[4]:
                self.ui.input_TOPP(
                    "FeatureLinkerUnlabeledKD",
                    display_full_parameter_names=True,
                )
        with tabs[2]:
            self.ui.input_widget(
                "requantify",
                False,
                "**re-quantify** features with missing values",
                help="Re-quantify missing values in consensus features using the OpenMS TOPP tool *FeatureFinderMetaboIdent*.",
            )
            self.ui.input_TOPP("FeatureFinderMetaboIdent")
        with tabs[3]:
            self.ui.input_widget(
                "export-sirius",
                False,
                "export for SIRIUS",
                help="Generate input files for SIRIUS from raw data and feature information using the OpenMS TOPP tool *SiriusExport*.",
            )
            self.ui.input_widget(
                "export-gnps",
                False,
                "export for GNPS FBMN and IIMN",
                help="Generate input files for GNPS feature based molecular networking (FBMN) and ion identity molecular networking (IIMN) from raw data and feature information using the OpenMS TOPP tool *GNPSExport*.",
            )
            t = st.tabs(["**SIRIUS**", "**GNPS**"])
            with t[0]:
                self.ui.input_TOPP("SiriusExport")
            with t[1]:
                self.ui.input_TOPP("GNPSExport")
        with tabs[4]:
            st.warning("Not implemented yet")

    def execution(self) -> None:
        # Set log levels from st.session_state
        if st.session_state["log_level"] in [
            "commands and execution times",
            "show all",
        ]:
            self.executor.log_commands = True
        if st.session_state["log_level"] in ["tool outputs", "show all"]:
            self.executor.log_tool_outputs = True
        # Get mzML input files from self.params.
        mzML = self.file_manager.get_files(self.params["mzML-files"])

        # Log any messages.
        self.logger.log(f"Number of input mzML files: {len(mzML)}")

        # Precursor m/z correction to highest intensity MS1 peak
        if self.params["correct-precursor"]:
            self.logger.log("Correcting precursor m/z to highest intensity MS1 peak.")
            mzML_pmc = self.file_manager.get_files(mzML, "mzML", "mzML-pmc")
            self.executor.run_topp(
                "HighResPrecursorMassCorrector",
                {"in": mzML, "out": mzML_pmc},
            )
            mzML = mzML_pmc

        # Feature Detection
        self.logger.log("Detecting features.")
        ffm = self.file_manager.get_files(mzML, "featureXML", "feature-detection")
        self.executor.run_topp(
            "FeatureFinderMetabo",
            input_output={
                "in": mzML,
                "out": ffm,
                "out_chrom": self.file_manager.get_files(
                    mzML, set_results_dir="ffm-chroms"
                ),
            },
        )

        # Adduct Detection
        self.logger.log("Detecting adducts.")
        if self.params["adduct-detection"]:
            # Run MetaboliteAdductDecharger for adduct detection, with disabled logs.
            self.executor.run_topp(
                "MetaboliteAdductDecharger",
                {"in": ffm, "out_fm": ffm},
            )

        # Map Alignement
        if self.params["map-alignement"]:
            self.logger.log("Aligning feature maps.")
            trafos = self.file_manager.get_files(
                ffm, "trafoXML", "trafos", collect=True
            )
            # Run MapAlignerPoseClustering for map alignement, with disabled logs.
            self.executor.run_topp(
                "MapAlignerPoseClustering",
                {
                    "in": self.file_manager.get_files(ffm, collect=True),
                    "out": self.file_manager.get_files(ffm, collect=True),
                    "trafo_out": trafos,
                },
            )
            self.logger.log("Transforming mzML files based on map alignement.")
            # Transform mzML files
            self.executor.run_topp(
                "MapRTTransformer",
                {
                    "in": mzML,
                    "out": mzML,
                    "trafo_in": self.file_manager.get_files(trafos),
                },
            )

        # Export FFM feature maps to dataframes (including chromatograms)
        self.executor.run_python("export_ffm_df", {"in": ffm})

        # Feature Linking and Export to pd.DataFrame
        self.logger.log("Linking features.")
        consensusXML = self.file_manager.get_files(
            "feature-matrix", "consensusXML", "feature-linker"
        )
        self.executor.run_topp(
            "FeatureLinkerUnlabeledKD",
            {"in": self.file_manager.get_files(ffm, collect=True), "out": consensusXML},
        )

        # Export to DataFrame
        consensus_df = self.file_manager.get_files(
            "feature-matrix", "parquet", "consensus-dfs"
        )

        self.executor.run_python(
            "export_consensus_df", {"in": consensusXML, "out": consensus_df}
        )

        # Requantify features with missing values
        if self.params["requantify"]:
            self.logger.log("Re-quantifying features with missing values.")
            # Prepare library
            ffmid_library = self.file_manager.get_files(
                "library", "tsv", "ffmid-library"
            )
            consensus_df_ffm_complete = self.file_manager.get_files(
                "consensus-df-ffm-complete", "parquet", "consensus-dfs"
            )
            self.executor.run_python(
                "generate_FFMID_library",
                {
                    "in": consensus_df,
                    "out": ffmid_library,
                    "out_ffm": consensus_df_ffm_complete,
                },
            )

            # Run FeatureFinderMetaboIdent
            ffmid = self.file_manager.get_files(mzML, "featureXML", "ffmid-features")
            self.executor.run_topp(
                "FeatureFinderMetaboIdent",
                {"in": mzML, "out": ffmid, "id": ffmid_library},
            )

            # Perform Adduct detection on re-quantified features
            self.logger.log("Detecting adducts for re-quantified features.")
            if self.params["adduct-detection"]:
                # Run MetaboliteAdductDecharger for adduct detection.
                self.executor.run_topp(
                    "MetaboliteAdductDecharger",
                    {"in": ffmid, "out_fm": ffmid},
                )

            # Export re-quantified feature maps to dataframes (including chromatograms)
            self.executor.run_python("export_ffmid_df", {"in": ffmid})

            # Link re-quantified features
            consensusXML_ffmid = self.file_manager.get_files(
                "feature-matrix-ffmid", "consensusXML", "feature-linker"
            )
            self.executor.run_topp(
                "FeatureLinkerUnlabeledKD",
                {
                    "in": self.file_manager.get_files(ffmid, collect=True),
                    "out": consensusXML_ffmid,
                },
            )

            # Export to DataFrame
            consensus_df_ffmid = self.file_manager.get_files(
                "feature-matrix-ffmid", "parquet", "consensus-dfs"
            )
            self.executor.run_python(
                "export_consensus_df",
                {"in": consensusXML_ffmid, "out": consensus_df_ffmid},
            )

            # Merge consensus_df and consensus_df_ffmid
            self.executor.run_python(
                "merge_consensus_df",
                {
                    "in": [consensus_df_ffm_complete, consensus_df_ffmid],
                    "out": consensus_df,
                },
            )

            # Merge feature maps from FFM and FFMID from merged consensus table
            self.executor.run_python(
                "merge_ffm_ffmid_df",
                {
                    "in": consensus_df,
                },
            )

            # Re-create feature maps from consensus df
            self.executor.run_python(
                "recreate_feature_maps",
                {"in": str(Path(self.file_manager.workflow_dir, "results"))},
            )

            # Ensure mzML and featureXML file paths are ordered the same for SiriusExport and GNPSExport
            ffm = sorted(
                [
                    str(p)
                    for p in Path(
                        Path(consensus_df[0]).parent.parent,
                        "feature-maps-recreated",
                    ).glob("*.featureXML")
                ]
            )
            mzML = sorted(mzML)

        # TODO: how to deal with number of masstraces??
        if self.params["export-sirius"]:
            self.logger.log("Exporting input files for SIRIUS.")
            self.executor.run_topp(
                "SiriusExport",
                {
                    "in": mzML,
                    "in_featureinfo": ffm,
                    "out": self.file_manager.get_files(mzML, "ms", "sirius-export"),
                },
            )
        if self.params["export-gnps"]:
            self.logger.log("Exporting input files for GNPS.")
            # Map MS2 specs to features
            self.executor.run_topp(
                "IDMapper",
                {
                    "in": ffm,
                    "spectra:in": mzML,
                    "out": ffm,
                    "id": self.file_manager.get_files(
                        str(Path("assets", "empty.idXML"))
                    ),
                },
            )
            # Link features with MS2 info
            gnps_consensus = self.file_manager.get_files(
                "feature-matrix", "consensusXML", "gnps-consensus"
            )
            self.executor.run_topp(
                "FeatureLinkerUnlabeledKD",
                {
                    "in": self.file_manager.get_files(ffm, collect=True),
                    "out": gnps_consensus,
                },
            )
            # Export to dataframe
            self.executor.run_python(
                "export_consensus_df",
                {"in": gnps_consensus, "out": consensus_df},
            )
            # Filter consensus features which have missing values
            self.executor.run_topp(
                "FileFilter",
                {"in": gnps_consensus, "out": gnps_consensus},
                custom_params={"id:remove_unannotated_features": ""},
            )

            # Run GNPSExport
            self.executor.run_topp(
                "GNPSExport",
                {
                    "in_cm": gnps_consensus,
                    "in_mzml": self.file_manager.get_files(mzML, collect=True),
                    "out": self.file_manager.get_files("MS2", "mgf", "gnps-export"),
                    "out_quantification": self.file_manager.get_files(
                        "feature-quantification", "txt", "gnps-export"
                    ),
                    "out_pairs": self.file_manager.get_files(
                        "pairs", "csv", "gnps-export"
                    ),
                    "out_meta_values": self.file_manager.get_files(
                        "meta-values", "tsv", "gnps-export"
                    ),
                },
            )

    def results(self) -> None:
        def load_parquet(file):
            if Path(file).exists():
                return pd.read_parquet(file)
            else:
                return pd.DataFrame()

        tabs = st.tabs(
            [
                "📁 **Feature Matrix**",
                "📊 **Chromatograms & Intensity Charts**",
                "📁 Samples",
            ]
        )

        df_matrix = load_parquet(
            self.file_manager.get_files("feature-matrix", "parquet", "consensus-dfs")[
                0
            ],
        )
        def quality_colors(value):
            # Ensure the value is within the expected range
            value = max(0, min(1, value))
            
            # Adjust the components to emphasize yellow in the middle
            if value < 0.5:
                # Increase green component towards the middle
                green = 255 * (value * 2)
                red = 255
            else:
                # Decrease red component after the middle
                green = 255
                red = 255 * ((1 - value) * 2)
                
            return f"background-color: rgba({red}, {green}, 0, 0.3);"
        
        if df_matrix.empty:
            return


        feature_df_dir = Path(self.file_manager.workflow_dir, "results", "feature-dfs")
        if not feature_df_dir.exists():
            feature_df_dir = Path(self.file_manager.workflow_dir, "results", "ffm-df")


        with tabs[0]:
            c1, c2 = st.columns(2)
            c1.metric(
                "Number of samples",
                len([col for col in df_matrix.columns if col.endswith(".mzML")]),
            )
            c2.metric("Number of features", len(df_matrix))
            sample_cols = sorted(
                [col for col in df_matrix.columns if col.endswith(".mzML")]
            )
            df_matrix.insert(
                1,
                "intensity",
                df_matrix.apply(lambda row: [row[col] for col in sample_cols], axis=1),
            )
            st.dataframe(
                df_matrix,
                column_order=[
                    "metabolite",
                    "intensity",
                    # "quality ranked",
                    "RT",
                    "mz",
                    "charge",
                    "adduct",
                    "re-quantified"
                ],
                hide_index=True,
                column_config={
                    "intensity": st.column_config.BarChartColumn(
                        width="small",
                        help=", ".join(
                            [
                                str(Path(col).stem)
                                for col in sorted(df_matrix.columns)
                                if col.endswith(".mzML")
                            ]
                        ),
                    ),
                    # "quality ranked": st.column_config.Column(width="small", help="Evenly spaced quality values between 0 and 1."),
                },
                height=700,
                use_container_width=True,
            )

        with tabs[1]:
            c1, c2 = st.columns(2)
            metabolite = c1.selectbox("Select metabolite", df_matrix["metabolite"])

            @st.cache_data
            def get_chroms_for_each_sample(metabolite):
                # Get index of row in df_matrix where "metabolite" is equal to metabolite
                index = df_matrix[df_matrix["metabolite"] == metabolite].index[0]
                all_samples = [
                    col.replace(".mzML_IDs", "")
                    for col in df_matrix.columns
                    if col.endswith("mzML_IDs")
                ]
                dfs = []
                samples = []
                for sample in all_samples:
                    # Get feature ID for sample
                    fid = df_matrix.loc[index, sample + ".mzML_IDs"]
                    path = Path(feature_df_dir, sample + ".parquet")
                    f_df = load_parquet(path)
                    if fid in f_df.index:
                        dfs.append(f_df.loc[[fid]])
                        samples.append(sample)
                df = pd.concat(dfs)
                df["sample"] = samples
                color_cycle = cycle(px.colors.qualitative.Plotly)
                df["color"] = [next(color_cycle) for _ in range(len(df))]
                return df

            @st.cache_resource
            def get_feature_chromatogram_plot(df):
                # Create an empty figure
                fig = go.Figure()
                # Loop through each row in the DataFrame and add a line trace for each
                for _, row in df.iterrows():
                    fig.add_trace(
                        go.Scatter(
                            x=row["chrom_RT"],  # Assuming chrom_RT is a list of values
                            y=row[
                                "chrom_intensity"
                            ],  # Assuming chrom_intensity is a list of values
                            mode="lines",  # Line plot
                            name=row[
                                "sample"
                            ],  # Giving each line a name based on its index
                            marker=dict(color=row["color"]),
                        )
                    )
                # Update layout of the figure
                fig.update_layout(
                    title=metabolite,
                    xaxis_title="retention time (s)",
                    yaxis_title="intensity (counts per second)",
                    plot_bgcolor="rgb(255,255,255)",
                    template="plotly_white",
                    height=700,
                    width=700,
                    showlegend=True,
                )
                return fig

            def get_feature_intensity_plot(df):
                fig = px.bar(df, x="sample", y="intensity", opacity=0.8)
                fig.data[0].marker.color = df["color"]
                # Update layout of the figure
                fig.update_layout(
                    title=metabolite,
                    xaxis_title="",
                    yaxis_title="feature intensity",
                    plot_bgcolor="rgb(255,255,255)",
                    template="plotly_white",
                    height=700,
                    width=700,
                    showlegend=False,
                )
                return fig

            df = get_chroms_for_each_sample(metabolite)
            c1, c2 = st.columns(2)
            with c1:
                fig = get_feature_chromatogram_plot(df)
                show_fig(fig, f"chromatograms_{metabolite}", container_width=False)
            with c2:
                show_fig(
                    get_feature_intensity_plot(df),
                    f"intensity_{metabolite}",
                    container_width=False,
                )

        with tabs[2]:
            c1, c2, _ = st.columns(3)
            feature_file = c1.selectbox(
                "Select feature file",
                feature_df_dir.iterdir(),
                format_func=lambda x: x.stem,
            )
            if feature_file != "None":
                df = load_parquet(feature_file).style.map(quality_colors, subset=["quality ranked"])
                st.dataframe(
                    df,
                    hide_index=True,
                    column_order=[
                        "metabolite",
                        "chrom_intensity",
                        "quality ranked",
                        "charge",
                        "RT",
                        "mz",
                        "intensity",
                        "num_of_masstraces",
                        "adduct",
                        "FWHM",
                        "re-quantified",
                    ],
                    column_config={
                        "chrom_intensity": st.column_config.LineChartColumn(
                            "chromatogram", width="small"
                        )
                    },
                    use_container_width=True,
                    height=700,
                ),
