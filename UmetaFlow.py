import streamlit as st

st.set_page_config(layout="wide")
st.session_state.uploaded_mzML = []

st.markdown("""
# UmetaFlow

## A universal tool for metabolomics data analysis

## About
All LC-MS related analysis is done with [pyOpenMS](https://pyopenms.readthedocs.io/en/latest/index.html).
""")