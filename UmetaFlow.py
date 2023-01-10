import streamlit as st
import os

st.set_page_config(layout="wide")

if not os.path.isdir("mzML_files"):
    os.mkdir("mzML_files")

st.markdown("""
# UmetaFlow

## A universal tool for metabolomics data analysis

## About
All LC-MS related analysis is done with [pyOpenMS](https://pyopenms.readthedocs.io/en/latest/index.html).
""")