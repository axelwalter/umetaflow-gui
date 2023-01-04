# UmetaFlow
This app is based on the [UmetaFlow](https://chemrxiv.org/engage/chemrxiv/article-details/634fb68fdfbd2b6abc5c5fcd) workflow for LC-MS data analysis. UmetaFlow is implemented as a [snakemake pipeline](https://github.com/NBChub/snakemake-UmetaFlow) and as a Python version in [Jupyter notebooks](https://github.com/eeko-kon/pyOpenMS_UmetaFlow).

Simply interface for the analysis of mass spec data with pyOpenMS including chromatogram extraction, metabolomics and statistics.

## Installation
1. Clone this repository
`git clone https://github.com/axelwalter/umetaflow-gui.git`
2. From within the `umetaflow-gui` folder init and update the pymetabo submodule
`git submodule init`
`git submodule update --remote`
3. Install the [latest pyopenms version](https://pyopenms.readthedocs.io/en/latest/installation.html#nightly-ci-wheels)
4. Install all other Python modules specified in the requirements file with pip
`pip install -r requirements.txt`
5. Launch the streamlit app locally in your browser from within the `umetaflow-gui` folder
`streamlit run UmetaFlow.py`

### Windows
Download the [windows executable](https://github.com/axelwalter/umetaflow-gui/releases/download/v0.1.0/easy-MS.zip) file and unzip it. Run the `Update.exe` file once to install the tool. It is recommended to run the update once in a while to get the latest changes. To start the tool simply run `easy-MS.exe`.

## Acknowledgement

MS data anylsis is performed using pyOpenMS, check out the documentation [here](https://pyopenms.readthedocs.io/en/latest/index.html).
