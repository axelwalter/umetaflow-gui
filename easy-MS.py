from lib2to3.pgen2.tokenize import Untokenizer
import streamlit as st

st.set_page_config(layout="wide")

st.markdown("""
# easy-MS for metabolomics

This is a collection of workflows useful for LC-MS data analysis and metabolomics. Please choose your workflow.

## About

All LC-MS related analysis is done with [pyOpenMS](https://pyopenms.readthedocs.io/en/latest/index.html).
""")