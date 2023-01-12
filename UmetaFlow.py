import streamlit as st
import os
import sys
from pathlib import Path

st.set_page_config(page_title="UmetaFlow", page_icon="resources/icon.png", layout="wide", initial_sidebar_state="auto", menu_items=None)

try:
    st.session_state.location = "online"

    if "selected" not in st.session_state:
        st.session_state.selected = []

    if "local" in sys.argv:
        st.session_state.location = "local"

    # if we run the packaged windows version, we start within the Python directory -> need to change working directory to ..\umetaflow-gui-main
    if "windows" in sys.argv:
        os.chdir("../umetaflow-gui-main")

    st.session_state.missing_values_before = None
    st.session_state.missing_values_after = None

    if not os.path.isdir("mzML_files"):
        os.mkdir("mzML_files")

    st.markdown("""
    # UmetaFlow

    ## A universal tool for metabolomics data analysis

    This app is based on the [UmetaFlow](https://chemrxiv.org/engage/chemrxiv/article-details/634fb68fdfbd2b6abc5c5fcd) workflow for LC-MS data analysis. UmetaFlow is implemented as a [snakemake pipeline](https://github.com/NBChub/snakemake-UmetaFlow) and as a Python version in [Jupyter notebooks](https://github.com/eeko-kon/pyOpenMS_UmetaFlow).

    ## About
    All LC-MS related analysis is done with [pyOpenMS](https://pyopenms.readthedocs.io/en/latest/index.html).
    """)

    # define directory to store mzML files
    mzML_dir = "mzML_files"

    # with st.sidebar:
    #     st.session_state.file_chooser = st.multiselect("mzML files", [path.name for path in Path(mzML_dir).iterdir()], [])

except:
    st.warning("Something went wrong.")