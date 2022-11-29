import streamlit as st

def app():
    st.markdown("""
# easy-MS

This is a collection of workflows useful for LC-MS data analysis and metabolomics. Please choose your workflow.

## About

All LC-MS related analysis is done with [pyOpenMS](https://pyopenms.readthedocs.io/en/latest/index.html).
This multi-page app is using the [streamlit-multiapps](https://github.com/upraneelnihar/streamlit-multiapps) framework.
""")