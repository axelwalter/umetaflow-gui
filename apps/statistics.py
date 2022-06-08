import streamlit as st
from pymetabo.plotting import *
import pandas as pd
from utils.filehandler import get_file

def app():
    with st.sidebar:
        if "viewing_statistics" not in st.session_state:
            st.session_state.viewing_statistics = False
        if "statistics_matrix_file" not in st.session_state:
            st.session_state.statistics_matrix_file = "results_untargeted/FeatureMatrix_requant.tsv"
        if "statistics_cohorts":
            pass
        with st.expander("info", expanded=True):
            st.markdown("""
Here you can load a feature matrix from extracted chromatograms, targeted and untargeted metabolomics and do some post-processing.
""")
    with st.expander("settings", expanded=True):
        col1, col2 = st.columns([6,1])
        with col2:
            st.markdown("##")
            select_button = st.button("Select", help="Choose a feature matrix for statistical analysis.")
        if select_button:
            st.session_state.statistics_matrix_file = get_file("Open a feature matrix file.", type=[("Excel file", "*.xlsx"), ("Table file", "*.tsv")])
        with col1:
            matrix_file = st.text_input("mzML files folder", st.session_state.statistics_matrix_file)
        if matrix_file:
            if matrix_file.endswith("tsv"):
                df = pd.read_csv(matrix_file, sep="\t")
            elif matrix_file.endswith("xlsx"):
                df = pd.read_excel(matrix_file)
            df.index = df["Unnamed: 0"]
            df.drop(columns=[c for c in ["Unnamed: 0", "charge", "RT", "mz", "quality", "name", "adduct"] if c in df.columns], inplace=True)


        run_button = st.button("Run Analysis!")
    
    if run_button:
        st.dataframe(df)
        fig = Plot().FeatureMatrix(df)
        st.plotly_chart(fig)
        

