import streamlit as st
from pathlib import Path
from .workflow.WorkflowManager import WorkflowManager


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
                self.ui.input_widget("correct-precursor", True, "correct precursor mass to highest intensity peak", help="Correct precursor mass to highest intensity MS peak peak.")
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
                        "algorithm:ffm:remove_single_traces": "true"
                    }
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
                self.ui.input_TOPP("MapAlignerPoseClustering", exclude_parameters=["index"])
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
        # Get mzML input files from self.params.
        mzML = self.file_manager.get_files(self.params["mzML-files"])

        # Log any messages.
        self.logger.log(f"Number of input mzML files: {len(mzML)}")

        # Precursor m/z correction to highest intensity MS1 peak
        if self.params["correct-precursor"]:
            mzML_pmc = self.file_manager.get_files(mzML, "mzML", "auto")
            self.executor.run_topp(
                "HighResPrecursorMassCorrector", {"in": mzML, "out": mzML_pmc}
            )
            mzML = mzML_pmc

        # Feature Detection
        ffm = self.file_manager.get_files(
            mzML, "featureXML", "feature-detection"
        )
        self.executor.run_topp(
            "FeatureFinderMetabo", input_output={"in": mzML, "out": ffm}, write_log=False
        )

        # Adduct Detection
        if self.params["adduct-detection"]:
            # Run MetaboliteAdductDecharger for adduct detection, with disabled logs.
            self.executor.run_topp(
                "MetaboliteAdductDecharger",
                {"in": ffm, "out_fm": ffm},
                write_log=False,
            )
        
        # Map Alignement
        if self.params["map-alignement"]:
            trafos = self.file_manager.get_files(ffm, "trafoXML", "auto", collect=True)
            # Run MapAlignerPoseClustering for map alignement, with disabled logs.
            self.executor.run_topp(
                "MapAlignerPoseClustering",
                {"in": self.file_manager.get_files(ffm, collect=True), "out": self.file_manager.get_files(ffm, collect=True), "trafo_out": trafos},
            )
            # Transform mzML files
            self.executor.run_topp(
                "MapRTTransformer",
                {"in": mzML, "out": mzML, "trafo_in": self.file_manager.get_files(trafos)},
            )

        # Feature Linking and Export to pd.DataFrame
        consensusXML = self.file_manager.get_files("feature-matrix.consensusXML", set_results_dir="feature-linker")
        self.executor.run_topp(
            "FeatureLinkerUnlabeledKD",
            {"in": self.file_manager.get_files(ffm, collect=True), "out": consensusXML},
            write_log=False,
        )
        
        consensus_df = self.file_manager.get_files(consensusXML, "parquet")
        self.executor.run_python("export_consensus_df", {"in": consensusXML, "out": consensus_df})
        
        # # Requantify features with missing values
        # if self.params["requantify"]:
        #     ffmid_library = self.file_manager.get_files(consensusXML, "tsv", "ffmid-library")
        #     self.executor.run_python("generate_FFMID_library", {"in":  consensus_df, "out": ffmid_library})

        #     self.executor.run_topp(
        #         "FeatureFinderMetaboIdent",
        #         {"in": mzML, "out": self.file_manager.get_files(ffm, "ffmid-features"), "ffmid_library": ffmid_library},
        #     )

    def results(self) -> None:
        st.warning("Not implemented yet.")
