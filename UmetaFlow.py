import streamlit as st
import os
import sys

st.set_page_config(page_title="UmetaFlow", page_icon="resources/icon.png", layout="wide", initial_sidebar_state="auto", menu_items=None)

st.session_state.location = "online"

if "selected" not in st.session_state:
    st.session_state.selected = []

if "local" in sys.argv:
    st.session_state.location = "local"

# if we run the packaged windows version, we start within the Python directory -> need to change working directory to ..\umetaflow-gui-main
if "windows" in sys.argv:
    os.chdir("../umetaflow-gui-main")

try:
    st.session_state.missing_values_before = None
    st.session_state.missing_values_after = None

    if not os.path.isdir("mzML_files"):
        os.mkdir("mzML_files")

    st.markdown("""
    # UmetaFlow

    ## A universal tool for metabolomics data analysis

    ## About
    All LC-MS related analysis is done with [pyOpenMS](https://pyopenms.readthedocs.io/en/latest/index.html).
    """)

except:
    st.warning("Something went wrong.")