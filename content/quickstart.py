import streamlit as st
from src.common.common import page_setup
from pathlib import Path
import json

params = page_setup(page="main")

st.title("A universal metabolomics tool")
cols = st.columns([0.8, 0.1])
cols[0].markdown(
    """
This app offers the powerful UmetaFlow **[1]** pipeline for untargeted metabolomics in an accessible user interface. Raw data pre-processing converts raw data to a feature quantification table by feature detection, alignment, grouping, adduct annotation and optional re-quantification of missing values. Features can be annotated by in-house libraries based on MS1 m/z and retention time matching as well as MS2 fragment spectrum similarity as well as with formula, structure and compound classes by SIRIUS. Furthermore, required input files for GNPS Feature Based Molecular Networking can be generated. Besides the untargeted pipeline, this app offers some additional features, such as an interface to explore raw data and metabolite identification and quantification via extracted ion chromatograms based on exact m/z values generated conveniently by an included m/z calculator. For downstream processing statistical analysis can be performed within the app or in the popular [FBmn STATS GUIde](https://github.com/axelwalter/streamlit-metabolomics-statistics) for statistical analyis of metabolomics data **[2]**.

**[1]** Kontou, Eftychia E., et al. "UmetaFlow: an untargeted metabolomics workflow for high-throughput data processing and analysis." Journal of Cheminformatics 15.1 (2023): 52**.

**[2]** Shah, Abzer K. Pakkir, et al. "The Hitchhiker’s Guide to Statistical Analysis of Feature-based Molecular Networks from Non-Targeted Metabolomics Data." (2023).

UmetaFlow is further implemented as a [snakemake pipeline](https://github.com/NBChub/snakemake-UmetaFlow) and as a Python version in [Jupyter notebooks](https://github.com/eeko-kon/pyOpenMS_UmetaFlow) based on [pyOpenMS](https://pyopenms.readthedocs.io/en/latest/index.html).
    """)

cols[1].image("assets/umetaflow-logo.png")
cols[1].image("assets/pyopenms-logo.png")


if Path("UmetaFlow-App.zip").exists():
    st.markdown(
            """
## Installation

### Download for Windows

Simply download and extract the zip file. The folder contains an executable UmetaFlow file. No need to install anything.
        """)
    with open("UmetaFlow-App.zip", "rb") as file:
        st.download_button(
                    label="Download for Windows",
                    data=file,
                    file_name="UmetaFlow-App.zip",
                    mime="archive/zip",
                    type="primary"
                )
# st.image("assets/umetaflow-app-overview.png", width=800)

st.markdown(
    """
## Workspaces
On the left side of this page you can define a workspace where all your data including uploaded `mzML` files will be stored. Entering a workspace will switch to an existing one or create a new one if it does not exist yet. In the web app, you can share your results via the unique workspace ID. Be careful with sensitive data, anyone with access to this ID can view your data.

## 📁 File Handling
Upload `mzML` files via the **File Upload** tab. The data will be stored in your workspace. With the web app you can upload only one file at a time.
Locally there is no limit in files. However, it is recommended to upload large number of files by specifying the path to a directory containing the files.

Your uploaded files will be shown in the sidebar of all tabs dealing with the files, e.g. the **Metabolomics** tab. Checked file names will be used for analysis.

Result files are available via specified download buttons or, if run locally, within the workspace directory.


## UmetaFlow: Untargeted Quantification & Identification

1. **Pre-Processing**
This initial step transforms raw data into a  feature quantification matrix (FeatureMatrix) containing metabolite intensities across all samples. Includes steps such as RT alignment, adduct detection and mapping of MS2 spectra top features for subsequent annotation.

2. **Re-Quantification**
Unique to UmetaFlow, this optional step is designed to detect low-abundance features that may be missed during pre-processing (e.g. features below the noise-threshold intensity). By re-evaluating the data for subtle signals, this step enhances sensitivity, improving the quantification of minor metabolites.

3. **Annotation**
UmetaFlow offers complementary annotation methods in order to maximize meaningful biological interpretation. Best annotations are from spectral matching with in-house libraries, generated from authentic standards, followed by querying publicly available databases for metabolite identification and structure prediction by CSI:FingerID and GNPS. If no specific compound was found, analog search by MS2Query and compound class prediction by CANOPUS can still provide valuable insights.

## Targeted Quantification: Extracted Ion Chromatograms

#### 📟 m/z Calculator

The m/z calculator facilitates the calculation of mass-to-charge ratios (m/z) for metabolites and includes a method to easily combine metabolites into large molecules.

This table can be used as input for the Extracted Ion Chromatograms workflow.

#### 🔍 Extracted Ion Chromatograms

Simple workflow for the extraction of chromatograms by `m/z` (and optionally `RT` range) value. Produces a **Feature Matrix** file with area under the curve intensities as well as a **Meta Data** template and the chromatogram data for each file.

Area intensities of different variants (e.g. adducts or neutral losses) of a metabolite can be combined. Put a `#` with the name first and variant second (e.g. `glucose` and `glucose#[M+Na]+`).  

### Downstream Processing

#### 📈 Statistics

Here, you can do basic statistics right away such as calculating mean intensities, fold changes, clustering and heatmaps all with nice visualizations.

For an advanced and complete workflow visit the [app for statistical analysis of metabolomics data](https://axelwalter-streamlit-metabol-statistics-for-metabolomics-3ornhb.streamlit.app/).
    """)
