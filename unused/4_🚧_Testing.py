import streamlit as st

st.write("for testing...")

from src.helpers import FeatureMapHelper
import pandas as pd

df = pd.read_csv(
    "/home/a/dev/umetaflow-gui/default-workspace/results-metabolomics/FeatureMatrix.tsv",
    sep="\t",
)
st.dataframe(df)
FeatureMapHelper.FFMID_library_from_consensus_df(
    "/home/a/dev/umetaflow-gui/default-workspace/results-metabolomics/FeatureMatrix.tsv",
    "/home/a/dev/umetaflow-gui/default-workspace/results-metabolomics/interim/FFMID.tsv",
)
