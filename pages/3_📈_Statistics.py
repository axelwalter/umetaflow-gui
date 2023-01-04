import streamlit as st
from pymetabo.plotting import *
from pymetabo.statistics import *
import pandas as pd
from utils.filehandler import get_file, save_file
import os

def download_df(df):
    path = save_file("Download Table", type=[("Excel table", "*.xlsx"), ("tab separated table", "*.tsv")])
    if path:
        if path.endswith(".tsv"):
            df.to_csv(path, sep="\t")
        elif path.endswith("xlsx"):
            df.to_excel(path)
        st.success("Download done")

st.title("Statistics")
st.warning("""**Important:** This statistics workflow gives you very basic options to calculate means and fold changes.

For advanced methods please use the [web app for metabolomics statistics](https://github.com/axelwalter/streamlit-metabolomics-statistics) by clicking on the **Open in Streamlit** badge.

You can use the Feature Matrix created by the metabolomics workflow together with the meta data table there.
""")
with st.sidebar:
    if "statistics_matrix_file" not in st.session_state:
        st.session_state.statistics_matrix_file = ""
    if "statistics_samples" not in st.session_state:
        st.session_state.statistics_samples = []
    if "statistics_features" not in st.session_state:
        st.session_state.statistics_features = []

    with st.expander("info", expanded=True):
        st.markdown("""
Here you can load a feature matrix from extracted chromatograms, targeted and untargeted metabolomics and do some post-processing.
To calculate fold changes, mean, values and standard deviations enter sample pairs in the text fields `Sample A` and `Sample B`.
You can use the suggested sample names. In order to enter replicates put them in the sample name separated with a `#`. E.g. from `sample#1.mzML` and
`sample#2.mzML` the mean and standard deviations will be calculated.
""")

col1, col2 = st.columns([6,1])
with col2:
    st.markdown("##")
    select_button = st.button("Select", help="Choose a feature matrix for statistical analysis.")
if select_button:
    st.session_state.statistics_matrix_file = get_file("Open a feature matrix file.", type=[("Table file", "*.tsv"), ("Excel file", "*.xlsx")])
with col1:
    matrix_file = st.text_input("feature matrix file", st.session_state.statistics_matrix_file)

if os.path.exists(matrix_file):
    if matrix_file.endswith("tsv"):
        df = pd.read_csv(matrix_file, sep="\t")
    elif matrix_file.endswith("xlsx"):
        df = pd.read_excel(matrix_file)
    meta_value_columns = ["id", "metabolite", "charge", "RT", "mz", "quality", "name", "adduct"]
    df.set_index("metabolite", inplace=True)
    st.session_state.statistics_samples = [col for col in df.columns if col.endswith("mzML")]
    st.session_state.statistics_features = df.index.to_list()
    samples = st.multiselect("samples", st.session_state.statistics_samples, st.session_state.statistics_samples)
    features = st.multiselect("features", st.session_state.statistics_features, st.session_state.statistics_features)
    
    df = df.loc[features, samples]
    df_meta_values = df[[c for c in meta_value_columns if c in df.columns]]
    df.drop(columns=[c for c in meta_value_columns if c in df.columns], inplace=True)
    st.write("Choose pairs for comparison from the follwing samples:")
    for name in set([c.split("#")[0] for c in df.columns]):
        st.write(name)
    col1, col2 = st.columns(2)
    with col1:
        pairs_a = st.text_area("Samples A")
    with col2:
        pairs_b = st.text_area("Samples B")
    col1, col2, col3 = st.columns(3)
    with col1:
        normalize = st.radio("normalize values", ["do not", "per sample", "across feature map"])

if os.path.exists(matrix_file):
    if normalize == "per sample":
        df_norm = Statistics().maximum_absolute_scaling_per_column(df)
    elif normalize == "across feature map":
        df_norm = Statistics().normalize_max(df)
    elif normalize == "do not":
        df_norm = df

    pairs = []
    for a, b in zip(pairs_a.split("\n"), pairs_b.split("\n")):
        a = a.strip()
        b = b.strip()
        if a and b:
            pairs.append((b, a))
    df_mean, df_std, df_change = Statistics().get_mean_std_change_df(df, pairs)
    df_summary = pd.concat([df_meta_values, df_norm, df_change], axis=1)
    if st.button("Summary"):
        download_df(df_summary)
    st.dataframe(df_summary)
    fig = Plot().FeatureMatrix(df_norm)
    st.plotly_chart(fig)
    if not df_mean.empty:
        st.markdown("***")
        if st.button("Mean intensities"):
            download_df(df_mean)
        st.dataframe(df_mean)
        if st.button("Standard deviations"):
            download_df(df_std)
        st.dataframe(df_std)
        st.plotly_chart(Plot().FeatureMatrix(df_mean, df_std, y_title="mean AUC"))
        st.markdown("***")
        if st.button("Log 2 fold changes"):
            download_df(df_change)
        st.dataframe(df_change)
        st.plotly_chart(Plot().FeatureMatrix(df_change, y_title="log 2 fold change"))
        st.plotly_chart(Plot().FeatureMatrixHeatMap(df_change, title="log 2 fold change"))
