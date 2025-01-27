
<img src="assets/umetaflow-app-overview.png" alt="overview"/>

[**Click to open app!**](https://abi-services.cs.uni-tuebingen.de/umetaflow/)

## What is UmetaFlow?

This app offers the powerful UmetaFlow **[1]** pipeline for untargeted metabolomics in an accessible user interface. Raw data pre-processing converts raw data to a feature quantification table by feature detection, alignment, grouping, adduct annotation and optional re-quantification of missing values. Features can be annotated by in-house libraries based on MS1 m/z and retention time matching as well as MS2 fragment spectrum similarity as well as with formula, structure and compound classes by SIRIUS [2], CSI:FingerID [3] & CANOPUS [4]. Furthermore, required input files for GNPS Feature Based Molecular Networking [5] and Ion Identity Molecular Networking [6] can be generated. Besides the untargeted pipeline, this app offers some additional features, such as an interface to explore raw data and metabolite identification and quantification via extracted ion chromatograms based on exact m/z values generated conveniently by an included m/z calculator. For downstream processing statistical analysis can be performed within the app or in the popular [FBmn STATS GUIde](https://github.com/axelwalter/streamlit-metabolomics-statistics) for statistical analyis of metabolomics data **[7]**.

**[1]** Kontou, Eftychia E., et al. "UmetaFlow: an untargeted metabolomics workflow for high-throughput data processing and analysis." Journal of Cheminformatics 15.1 (2023): 52**.

**[2]**	Dührkop K, Fleischauer M, Ludwig M, Aksenov AA, Melnik AV, Meusel M, et al. SIRIUS 4: a rapid tool for turning tandem mass spectra into metabolite structure information. Nat Methods 2019;16:299–302. https://doi.org/10.1038/s41592-019-0344-8.

**[3]**	Dührkop K, Shen H, Meusel M, Rousu J, Böcker S. Searching molecular structure databases with tandem mass spectra using CSI:FingerID. Proc Natl Acad Sci 2015;112:12580–5. https://doi.org/10.1073/pnas.1509788112.

**[4]**	Dührkop K, Nothias L-F, Fleischauer M, Reher R, Ludwig M, Hoffmann MA, et al. Systematic classification of unknown metabolites using high-resolution fragmentation mass spectra. Nat Biotechnol 2021;39:462–71. https://doi.org/10.1038/s41587-020-0740-8.

**[5]**	Nothias L-F, Petras D, Schmid R, Dührkop K, Rainer J, Sarvepalli A, et al. Feature-based molecular networking in the GNPS analysis environment. Nat Methods 2020;17:905–8. https://doi.org/10.1038/s41592-020-0933-6.

**[6]**	Schmid R, Petras D, Nothias L-F, Wang M, Aron AT, Jagels A, et al. Ion identity molecular networking for mass spectrometry-based metabolomics in the GNPS environment. Nat Commun 2021;12:3832. https://doi.org/10.1038/s41467-021-23953-9.

**[7]** Shah, Abzer K. Pakkir, et al. "The Hitchhiker’s Guide to Statistical Analysis of Feature-based Molecular Networks from Non-Targeted Metabolomics Data." (2023).

UmetaFlow is further implemented as a [snakemake pipeline](https://github.com/NBChub/snakemake-UmetaFlow) and as a Python version in [Jupyter notebooks](https://github.com/eeko-kon/pyOpenMS_UmetaFlow) based on [pyOpenMS](https://pyopenms.readthedocs.io/en/latest/index.html).

## Installation
1. Clone this repository

`git clone https://github.com/axelwalter/umetaflow-gui.git`

2. Change into the `umetaflow-gui` folder

`cd umetaflow-gui`

3. Install all Python modules specified in the requirements file with pip

`pip install -r requirements.txt --no-cache`

4. Launch the streamlit app locally in your browser

`streamlit run app.py local`

### Windows
1. Visit the [UmetaFlow web app](https://abi-services.cs.uni-tuebingen.de/umetaflow/)
2. Click on **Download for Windows** button and download zip file
3. Extract zip file
4. Run the app by executing `UmetaFlow`

## Quickstart

### Workspaces
On the left side of this page you can define a workspace where all your data including uploaded `mzML` files will be stored. Entering a workspace will switch to an existing one or create a new one if it does not exist yet. In the web app, you can share your results via the unique workspace ID. Be careful with sensitive data, anyone with access to this ID can view your data.

### 📁 File Handling
Upload `mzML` files via the **File Upload** tab. The data will be stored in your workspace. With the web app you can upload only one file at a time.
Locally there is no limit in files. However, it is recommended to upload large number of files by specifying the path to a directory containing the files.

Your uploaded files will be shown in the sidebar of all tabs dealing with the files, e.g. the **Metabolomics** tab. Checked file names will be used for analysis.

Result files are available via specified download buttons or, if run locally, within the workspace directory.

### Targeted Metabolomics

##### 📟 m/z Calculator

The m/z calculator facilitates the calculation of mass-to-charge ratios (m/z) for metabolites and includes a method to easily combine metabolites into large molecules.

This table can be used as input for the Extracted Ion Chromatograms workflow.

##### 🔍 Extracted Ion Chromatograms

Simple workflow for the extraction of chromatograms by `m/z` (and optionally `RT` range) value. Produces a **Feature Matrix** file with area under the curve intensities as well as a **Meta Data** template and the chromatogram data for each file.

Area intensities of different variants (e.g. adducts or neutral losses) of a metabolite can be combined. Put a `#` with the name first and variant second (e.g. `glucose` and `glucose#[M+Na]+`).  

#### Untargeted Metabolomics

1. **Pre-Processing**
Converting your raw data to a table of metabolic features with a series of algorithms. Produces a table of consensus metabolite intensities across your samples.

2. **Re-Quantification**
One of the unique and great features of UmetaFlow. For missing value imputation go back into the raw data and double check. Never miss a feature any more! 

3. **GNPS and SIRIUS**
Run SIRIUS and automatically annotate features with sum formula, identification and compound classes (**UmetaFlow TOPP**) or export files to run SIRIUS externally (**UmetaFlow pyOpenMS**). Export files to run GNPS externally (**both**).

4. **Annotation via in-house libraries**
Load your in-house data for MS1 (`tsv` file with metabolite `m/z` and `RT` values) and MS2 (`mgf` file) annotations.

##### 🐍 UmetaFlow pyOpenMS

Using pyOpenMS. Recommended if OpenMS TOPP tools are not installed.

##### 🚀 UmetaFlow TOPP

A high performance workflow with OpenMS TOPP tools running in parallel.

#### Downstream Processing

##### 📈 Statistics

Here, you can do basic statistics right away such as calculating mean intensities, fold changes, clustering and heatmaps all with nice visualizations.

For an advanced and complete workflow visit the [app for statistical analysis of metabolomics data](https://axelwalter-streamlit-metabol-statistics-for-metabolomics-3ornhb.streamlit.app/).
