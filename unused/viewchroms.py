import streamlit as st
import plotly.express as px
from pyopenms import *
import os
import pandas as pd
from utils.filehandler import get_files

# TODO deal with multiple file inputs (only problem on Windows?)
# TODO how to enter path in Windows? raw string? conversion? works with Linux also?


def app():
    with st.sidebar:
        with st.expander("info", expanded=False):
            st.markdown("""
Here you can view extracted ion chromatograms generated with the `Extract Chromatograms` workflow.
Simply load the `tsv` files that you stored earlier.
""")
    if "loaded" not in st.session_state:
        st.session_state.loaded = set([])
    if "chroms" not in st.session_state:
        st.session_state.chroms = set([])
    

    col1, col2 = st.columns([9,1])
    col2.markdown("##")
    load_button = col2.button("Add", help="Add tsv files with chromatogram data.")
    if load_button:
        files = get_files("Open chromatogram data", [("chromatogram data", ".xlsx"), ("chromatogram data", ".tsv")])
        for file in files:
            st.session_state.loaded.add(file)
            if file.endswith(".tsv"):
                columns = pd.read_csv(file, sep="\t").drop(columns=["time"]).columns.tolist()
            elif file.endswith(".xlsx"):
                columns = pd.read_excel(file).drop(columns=["time"]).columns.tolist()
            for column in columns:
                st.session_state.chroms.add(column)

    all_files = col1.multiselect("samples", list(st.session_state.loaded), 
                            list(st.session_state.loaded))
    all_chroms = col1.multiselect("chromatograms", list(st.session_state.chroms), list(st.session_state.chroms))
    
    col2.write("")
    num_cols = col2.number_input("columns", 1, 5, 1)
    cols = st.columns(num_cols)

    while all_files:
        for col in cols:
            try:
                file = all_files.pop()
            except IndexError:
                break
            if file.endswith(".tsv"):
                df = pd.read_csv(file, sep="\t")
            if file.endswith(".xlsx"):
                df = pd.read_excel(file)

            fig = px.line(df, x=df["time"], y=all_chroms, title=file)
            fig.update_layout(xaxis=dict(title="time"), yaxis=dict(title="intensity (cps)"))
            col.plotly_chart(fig)
