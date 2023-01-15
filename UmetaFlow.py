import streamlit as st
import os
import sys
import uuid

st.set_page_config(page_title="UmetaFlow", page_icon="resources/icon.png", layout="wide", initial_sidebar_state="auto", menu_items=None)

try:
    st.session_state.location = "online"

    # define directory to store mzML files
    mzML_dir = "mzML_files"
    if not os.path.isdir(mzML_dir):
        os.mkdir(mzML_dir)

    if "local" in sys.argv:
        st.session_state.location = "local"
    elif "user_id" not in st.session_state:
        st.session_state["user_id"] = uuid.uuid1()

    st.write(st.session_state["user_id"])

    # if we run the packaged windows version, we start within the Python directory -> need to change working directory to ..\umetaflow-gui-main
    if "windows" in sys.argv:
        os.chdir("../umetaflow-gui-main")

    st.markdown("""
    # UmetaFlow

    ## A universal tool for metabolomics data analysis

    This app is based on the [UmetaFlow](https://chemrxiv.org/engage/chemrxiv/article-details/634fb68fdfbd2b6abc5c5fcd) workflow for LC-MS data analysis. UmetaFlow is implemented as a [snakemake pipeline](https://github.com/NBChub/snakemake-UmetaFlow) and as a Python version in [Jupyter notebooks](https://github.com/eeko-kon/pyOpenMS_UmetaFlow).

    ## About
    All LC-MS related analysis is done with [pyOpenMS](https://pyopenms.readthedocs.io/en/latest/index.html).
    """)
except:
    st.warning("Something went wrong.")