from pathlib import Path
from .core import *
from .sirius import Sirius
from .gnps import GNPSExport
from .helpers import *
from .dataframes import DataFrames


class UmetaFlow:
    """
    Implements the steps for UmetaFlow in a reusable way.
    """

    def __init__(self, params, mzML_files, results_dir):
        self.params = params
        self.mzML_files = mzML_files
        self.results_dir = results_dir
        self.interim = Helper().reset_directory(Path(results_dir, "interim"))
        self.mzML_dir = Path(self.interim, "mzML_original")
        self.featureXML_dir = Path(self.interim, "FFM")
        self.sirius_ms_dir = ""
        self.consensusXML = Path(self.interim, "FeatureMatrix.consensusXML")
        self.consensus_tsv = Path(self.results_dir, "FeatureMatrix.tsv")
        self.mgf_file = str(Path(self.results_dir, "GNPS", "MS2.mgf"))

    def fetch_raw_data(self):
        Helper().reset_directory(self.mzML_dir)
        for file in self.mzML_files:
            shutil.copy(file, self.mzML_dir)

    def feature_detection(self):
        if self.params["ffm_single_traces"]:
            ffm_single_traces = "true"
        else:
            ffm_single_traces = "false"
        FeatureFinderMetabo().run(
            self.mzML_dir,
            os.path.join(self.interim, "FFM"),
            {
                "noise_threshold_int": self.params["ffm_noise"],
                "chrom_fwhm": self.params["ffm_peak_width"],
                "chrom_peak_snr": self.params["ffm_snr"],
                "report_chromatograms": "true",
                "mass_error_ppm": self.params["ffm_mass_error"],
                "remove_single_traces": ffm_single_traces,
                "report_convex_hulls": "true",
                "min_fwhm": self.params["ffm_min_fwhm"],
                "max_fwhm": self.params["ffm_max_fwhm"],
            },
        )
        self.featureXML_dir = Path(self.interim, "FFM")

    def adduct_detection(self):
        MetaboliteAdductDecharger().run(
            self.featureXML_dir,
            Path(self.interim, "FFM_decharged"),
            {
                "potential_adducts": [
                    line.encode() for line in self.params["ad_adducts"].split("\n")
                ],
                "charge_min": self.params["ad_charge_min"],
                "charge_max": self.params["ad_charge_max"],
                "max_neutrals": 2,
                # "negative_mode": ad_negative_mode,
                "retention_max_diff": self.params["ad_rt_max_diff"],
                "retention_max_diff_local": self.params["ad_rt_max_diff"],
            },
        )
        shutil.rmtree(self.featureXML_dir)
        Path(self.interim, "FFM_decharged").rename(Path(self.featureXML_dir))

    def align_feature_maps(self):
        MapAligner().run(
            self.featureXML_dir,
            os.path.join(self.interim, "FFM_aligned"),
            os.path.join(self.interim, "Trafo"),
            {
                "max_num_peaks_considered": -1,
                "superimposer:mz_pair_max_distance": 0.05,
                "pairfinder:distance_MZ:max_difference": self.params["ma_mz_max"],
                "pairfinder:distance_MZ:unit": self.params["ma_mz_unit"],
                "pairfinder:distance_RT:max_difference": self.params["ma_rt_max"],
            },
        )
        self.featureXML_dir = Path(self.interim, "FFM_aligned")

    def feature_maps_to_df(self):
        df_path = Path(self.featureXML_dir).name + "_df"
        Helper().reset_directory(Path(self.interim, df_path))
        requant = self.params["use_requant"]
        for file in Path(self.featureXML_dir).iterdir():
            DataFrames.featureXML_to_ftr(
                file, Path(self.interim, df_path), requant=requant
            )

    def align_peak_maps(self):
        MapAligner().run(
            self.mzML_dir,
            Path(self.interim, "mzML_aligned"),
            Path(self.interim, "Trafo"),
        )
        self.mzML_dir = Path(self.interim, "mzML_aligned")

    def map_MS2(self):
        MapID().run(
            self.mzML_dir,
            self.featureXML_dir,
            Path(self.interim, "FeatureMaps_ID_mapped"),
        )
        self.featureXML_dir = Path(self.interim, "FeatureMaps_ID_mapped")

    def link_feature_maps(self):
        FeatureLinker().run(
            self.featureXML_dir,
            str(self.consensusXML),
            {
                "link:mz_tol": self.params["fl_mz_tol"],
                "link:rt_tol": self.params["fl_rt_tol"],
                "mz_unit": self.params["fl_mz_unit"],
            },
        )

    def consensus_df(self):
        DataFrames().create_consensus_table(
            str(self.consensusXML),
            self.consensus_tsv,
            self.sirius_ms_dir,
        )

    def sirius(self):
        Sirius().run(
            self.mzML_dir,
            self.featureXML_dir,
            Path(self.results_dir, "SIRIUS"),
            "",
            True,
            {"-preprocessing:feature_only": "true"},
        )
        self.sirius_ms_dir = os.path.join(self.results_dir, "SIRIUS", "sirius_files")

    def requantify(self):
        # FeatureMapHelper.FFMID_library_from_consensus_df(
        #     self.consensus_tsv, Path(self.interim, "FFMID.tsv")
        # )
        # FeatureMapHelper().split_consensus_map(
        #     str(self.consensusXML),
        #     str(Path(self.interim, "ConsensusComplete.consensusXML")),
        #     str(Path(self.interim, "ConsensusMissing.consensusXML")),
        # )
        # FeatureMapHelper().FFMID_libraries_for_missing_features(
        #     str(Path(self.interim, "ConsensusMissing.consensusXML")),
        #     Path(self.interim, "FFMID_libraries"),
        # )
        # FeatureFinderMetaboIdent().run(
        #     self.mzML_dir,
        #     str(Path(self.interim, "FFMID_tmp")),
        #     Path(self.interim, "FFMID_libraries"),
        #     {
        #         "detect:peak_width": self.params["ffm_peak_width"],
        #         "extract:mz_window": self.params["ffm_mass_error"],
        #         "extract:n_isotopes": 2,
        #         # "extract:rt_window": self.params["ffm_peak_width"] * 4,
        #     },
        # )
        # FeatureMapHelper().consensus_to_feature_maps(
        #     str(Path(self.interim, "ConsensusComplete.consensusXML")),
        #     self.featureXML_dir,
        #     Path(self.interim, "FeatureMapsComplete"),
        # )
        # FeatureMapHelper().merge_feature_maps(
        #     Path(self.interim, "FFMID"),
        #     Path(self.interim, "FeatureMapsComplete"),
        #     Path(self.interim, "FFMID_tmp"),
        # )
        # self.consensusXML = Path(self.interim, "FeatureMatrixRequantified.consensusXML")
        # self.consensus_tsv = Path(self.results_dir, "FeatureMatrixRequantified.tsv")
        # self.featureXML_dir = Path(self.interim, "FFMID")
        Requantifier().run(
            str(self.consensusXML),
            self.consensus_tsv,
            self.mzML_dir,
            self.featureXML_dir,
            self.params["ffm_mass_error"],
        )

    def export_metadata(self):
        GNPSExport().export_metadata_table_only(
            str(self.consensusXML),
            str(Path(self.results_dir, "MetaData.tsv")),
        )

    def gnps(self):
        # create interim directory for MS2 ids later (they are based on the GNPS mgf file)
        Helper().reset_directory(Path(self.interim, "mztab_ms2"))
        GNPSExport().run(
            str(self.consensusXML),
            self.mzML_dir,
            Path(self.results_dir, "GNPS"),
        )
        output_mztab = str(Path(self.interim, "mztab_ms2", "GNPS.mzTab"))
        database = "example_data/ms2-libraries/GNPS-LIBRARY.mgf"
        SpectralMatcher().run(database, self.mgf_file, output_mztab)
        DataFrames().annotate_ms2(
            self.mgf_file,
            output_mztab,
            self.consensus_tsv,
            "GNPS library match",
        )

    def annotate_MS1(self):
        if self.params["ms1_annotation_file"]:
            DataFrames().annotate_ms1(
                self.consensus_tsv,
                self.params["ms1_annotation_file"],
                self.params["annotation_mz_window_ppm"],
                self.params["annoation_rt_window_sec"],
            )
            DataFrames().save_MS_ids(
                self.consensus_tsv,
                Path(self.results_dir, "MS1-annotations"),
                "MS1 annotation",
            )

    def annotate_MS2(self):
        if self.params["ms2_annotation_file"]:
            output_mztab = str(Path(self.interim, "mztab_ms2", "MS2.mzTab"))
            SpectralMatcher().run(
                self.params["ms2_annotation_file"], self.mgf_file, output_mztab
            )
            DataFrames().annotate_ms2(
                self.mgf_file,
                output_mztab,
                self.consensus_tsv,
                "MS2 annotation",
                overwrite_name=True,
            )
            DataFrames().save_MS_ids(
                self.consensus_tsv,
                os.path.join(self.results_dir, "MS2-annotations"),
                "MS2 annotation",
            )

    def make_zip_archives(self):
        if self.params["use_sirius_manual"]:
            shutil.make_archive(
                Path(self.interim, "ExportSirius"), "zip", self.sirius_ms_dir
            )
        if self.params["use_gnps"]:
            shutil.make_archive(
                Path(self.interim, "ExportGNPS"),
                "zip",
                Path(self.results_dir, "GNPS"),
            )

    def additional_data_for_consensus_df(self):
        DataFrames.consensus_df_additional_annotations(
            self.consensus_tsv,
            Path(self.results_dir, "FeatureMatrix.ftr"),
            self.consensusXML,
        )
