# UmetaFlow GUI [![Open UmetaFlow!](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://axelwalter-umetaflow-gui-umetaflow-pdiomd.streamlit.app/)
**powered by:**

<img src="resources/OpenMS.png" width=20%>

This app is based on the [UmetaFlow](https://chemrxiv.org/engage/chemrxiv/article-details/634fb68fdfbd2b6abc5c5fcd) workflow for LC-MS data analysis. UmetaFlow is implemented as a [snakemake pipeline](https://github.com/NBChub/snakemake-UmetaFlow) and as a Python version in [Jupyter notebooks](https://github.com/eeko-kon/pyOpenMS_UmetaFlow) based on [pyOpenMS](https://pyopenms.readthedocs.io/en/latest/index.html).

Here, we take the powerful UmetFlow algorithms in a simple and easy graphical user interface. In contrast to the pipeline for automatic data processing,
this app is tweaked a bit to be used with smaller to medium sample sets and some manual data interpretation. For example the automatic annotation of features via SIRIUS is omitted.
Instead we export all the files necessary to run in the SIRIUS GUI tool and manually annotate the result tables via a unique identifier. This method of curated annotation can be interesting if you really want to be confident in your annotations.
The same applies for GNPS, here you can export all the files required for Feature Based Molecular Networking and Ion Identity Networking.

Besides the core UmetaFlow algorithms in the **Metabolomics** tab, you will find additional tabs for **Extracted Ion Chromatograms** and **Statistics**. The data produced here is fully compatible with the web app for [statistical analyis of metabolomics](https://github.com/axelwalter/streamlit-metabolomics-statistics) data.

## Installation
1. Clone this repository

`git clone https://github.com/axelwalter/umetaflow-gui.git`

2. Change into the `umetaflow-gui` folder

`cd umetaflow-gui`

3. Install all other Python modules specified in the requirements file with pip

`pip install -r requirements.txt`

4. Launch the streamlit app locally in your browser

`streamlit run UmetaFlow.py local`

### Windows
1. Download and extract the [UmetaFlow.zip](https://github.com/axelwalter/umetaflow-gui/releases/download/v1.0.0/UmetaFlow.zip) file
2. Run the `Update` script (also from time to time to get latest changes).
> The command prompt will close once the update is done.
3. Run the app by executing` UmetaFlow`

## Quickstart

### Workspaces
On the left side of this page you can define a workspace where all your data including uploaded `mzML` files will be stored. Entering a workspace will switch to an existing one or create a new one if it does not exist yet. In the web app, you can share your results via the unique workspace ID. Be careful with sensitive data, anyone with access to this ID can view your data.

### 📁 File Handling
Upload `mzML` files via the **File Upload** tab. The data will be stored in your workspace. With the web app you can upload only one file at a time.
Locally there is no limit in files. However, it is recommended to upload large number of files by specifying the path to a directory containing the files.

Your uploaded files will be shown in the sidebar of all tabs dealing with the files, e.g. the **Metabolomics** tab. Checked file names will be used for analysis.

Result files are available via specified download buttons or, if run locally, within the workspace directory.
### Workflows

#### 🔍 Extracted Ion Chromatograms

Simple workflow for the extraction of chromatograms by `m/z` (and optionally `RT` range) value. Produces a **Feature Matrix** file with area under the curve intensities as well as a **Meta Data** template and the chromatogram data for each file.

Area intensities of different variants (e.g. adducts or neutral losses) of a metabolite can be combined. Put a `#` with the name first and variant second (e.g. `glucose` and `glucose#[M+Na]+`).  

#### 🧪 Metabolomics (UmetaFlow)

The core UmetaFlow pipeline with some tweaks.

1. **Pre-Processing**
Converting your raw data to a table of metabolic features with a series of algorithms. Produces a table of consensus metabolite intensities across your samples.

2. **Re-Quantification**
One of the unique and great features of UmetaFlow. For missing value imputation go back into the raw data and double check. Never miss a feature any more! 

3. **GNPS and SIRIUS**
Export all files required to run GNPS Feature Based Molecular Networking and SIRIUS externally. Also offers the possibility to annotate from the complete GNPS library. For manual annotation of SIRIUS results a unique ID is provied in the **Feature Matrix**.

4. **Annotation via in-house libraries**
Load your in-house data for MS1 (`tsv` file with metabolite `m/z` and `RT` values) and MS2 (`mgf` file) annotations.

#### 📈 Statistics
Here, you can do basic statistics right away such as calculating mean intensities, fold changes, clustering and heatmaps all with nice visualizations.

For an advanced and complete workflow visit the [app for statistical analysis of metabolomics data](https://axelwalter-streamlit-metabol-statistics-for-metabolomics-3ornhb.streamlit.app/).
