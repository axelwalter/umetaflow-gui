import streamlit as st
import os
import sys

st.set_page_config(layout="wide")

st.session_state.location = "online"

if "local" in sys.argv:
    st.session_state.location = "local"

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