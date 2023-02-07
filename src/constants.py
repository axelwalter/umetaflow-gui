QUICKSTART = """
# UmetaFlow
## A universal metabolomics tool

This app is based on the [UmetaFlow](https://chemrxiv.org/engage/chemrxiv/article-details/634fb68fdfbd2b6abc5c5fcd) workflow for LC-MS data analysis. UmetaFlow is implemented as a [snakemake pipeline](https://github.com/NBChub/snakemake-UmetaFlow) and as a Python version in [Jupyter notebooks](https://github.com/eeko-kon/pyOpenMS_UmetaFlow) based on [pyOpenMS](https://pyopenms.readthedocs.io/en/latest/index.html).

Here, we take the powerful UmetFlow algorithms in a simple and easy graphical user interface. In contrast to the pipeline for automatic data processing,
this app is tweaked a bit to be used with smaller to medium sample sets and some manual data interpretation. For example the automatic annotation of features via SIRIUS is omitted.
Instead we export all the files necessary to run in the SIRIUS GUI tool and manually annotate the result tables via a unique identifier. This method of curated annotation can be interesting if you really want to be confident in your annotations.
The same applies for GNPS, here you can export all the files required for Feature Based Molecular Networking and Ion Identity Networking.

Besides the core UmetaFlow algorithms in the **Metabolomics** tab, you will find additional tabs for **Extracted Ion Chromatograms** and **Statistics**. The data produced here is fully compatible with the web app for [statistical analyis of metabolomics](https://github.com/axelwalter/streamlit-metabolomics-statistics) data.

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
"""

UPLOAD_INFO = """
    **💡 How to upload files**

    1. Browse files on your computer
    2. Click the **Add the uploaded mzML files** button to use them in the workflows

    Select data for anaylsis from the uploaded files shown in the sidebar.
"""

EIC = {
    "main": """
Here you can get extracted ion chromatograms `EIC` from mzML files. A base peak chromatogram `BPC`
will be automatically generated as well. Select the mass tolerance according to your data either as
absolute values `Da` or relative to the metabolite mass in parts per million `ppm`.

As input you can add `mzML` files and select which ones to use for the chromatogram extraction.
Download the results of selected samples and chromatograms as `tsv` files.

You can enter the exact masses of your metabolites each in a new line. Optionally you can label them separated by an equal sign e.g.
`222.0972=GlcNAc` or add RT limits with a further equal sign e.g. `222.0972=GlcNAc=2.4-2.6`. The specified time unit will be used for the RT limits. To store the list of metabolites for later use you can download them as a text file. Simply
copy and paste the content of that file into the input field.

The results will be displayed as a summary with all samples and EICs AUC values as well as the chromatograms as one graph per sample. Choose the samples and chromatograms to display.
""",
    "masses": "Add one mass per line and optionally label it with an equal sign e.g. `222.0972=GlcNAc`.",
    "combine": "Combines different variants (e.g. adducts or neutral losses) of a metabolite. Put a `#` with the name first and variant second (e.g. `glucose#[M+H]+` and `glucose#[M+Na]+`)",
}

METABO = {
    "main": """
This workflow includes the core UmetaFlow pipeline which results in a table of metabolic features.

- The most important parameter are marked as **bold** text. Adjust them according to your instrument.
- All the steps with checkboxes are optional.
""",
    "potential_adducts": """
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
    "ad_ion_mode": "Carefully adjust settings for each mode. Especially potential adducts and negative min/max charges for negative mode.",
    "ad_charge_min": "e.g. for negative mode -3, for positive mode 1",
    "ad_charge_max": "e.g. for negative mode -1, for positive mode 3",
    "ad_rt_diff": "Groups features with slightly different RT.",
    "re-quant": "Go back into the raw data to re-quantify consensus features that have missing values.",
    "sirius": "Export files for formula and structure predictions. Run Sirius with these pre-processed .ms files, can be found in results -> SIRIUS -> sirius_files.",
    "gnps": "Run GNPS Feature Based Molecular Networking and Ion Identity Molecular Networking with these files, can be found in results -> GNPS.",
    "annotate_gnps": "UmetaFlow contains the complete GNPS library in mgf file format. Check to annotate.",
    "annotate_ms1": "Annotate features on MS1 level with known m/z and retention times values.",
    "annotate_ms1_rt": "Checks around peak apex, e.g. window of 60 s will check left and right 30 s.",
    "annotate_ms2": "Annotate features on MS2 level based on their fragmentation patterns. The library has to be in mgf file format.",
}

STATISTICS = {
    "main": """
#### 💡 Important

We have developed a web app specifically for metabolomics data analyisis. 

Visit [the GitHub repository](https://github.com/axelwalter/streamlit-metabolomics-statistics) or [**open the app**](https://metabolomics-statistics.streamlit.app/) directly from here.

#### What you need from this app

Both Workflows let you download a **Feature Matrix** and a **Meta Data** table in `tsv` format. Edit the meta data by defining sample types (e.g. Sample, Blank or Pool)
and add at least one more custom attribute column to where your samples differentiate (e.g. ATTRIBUTE_Treatment: antibiotic and control).
"""
}

WARNINGS = {
    "no-workspace": "No online workspace ID found, please visit the start page first (UmetaFlow tab).",
    "missing-mzML": "Upload or select some mzML files first!",
}

ERRORS = {
    "general": "Something went wrong.",
    "parameters": "Something went wrong during parameter input.",
    "workflow": "Something went wrong during workflow execution.",
    "visualization": "Something went wrong during visualization of results.",
}
