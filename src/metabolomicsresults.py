import streamlit as st
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Draw

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from itertools import cycle

from src.common.common import show_fig, load_parquet

def add_color_column(df):
    color_cycle = cycle(px.colors.qualitative.Plotly)
    df["color"] = [next(color_cycle) for _ in range(len(df))]
    return df

@st.dialog("🔎 Filter Feature Matrix")
def filter_dialog(df):
    # ><
    st.session_state["feature-matrix-filtered"] = pd.DataFrame()
    mz = st.slider("*m/z* range", df["mz"].min(), df["mz"].max(), value=(df["mz"].min(), df["mz"].max()))
    rt = st.slider("RT range", df["RT"].min(), df["RT"].max(), value=(df["RT"].min(), df["RT"].max()))
    filter_sirius = st.toggle("keep only metabolites with SIRIUS annotation", False)
    charge = st.selectbox("charge state", ["all"]+sorted(df["charge"].unique().tolist()))
    if filter_sirius:
        df_sirius = df[[c for c in df.columns if c.startswith("CSI:FingerID_")]].dropna()
        df = df.loc[df_sirius.index, :]
    if charge != "all":
        df = df[df["charge"] == int(charge)]
    df = df[(df["mz"] > mz[0]) & (df["mz"] < mz[1])]
    df = df[(df["RT"] > rt[0]) & (df["RT"] < rt[1])]
    if df.empty:
        st.warning("⚠️ Feature Matrix is empty after filtering. Filter will not be applied.")
    _, _, c1, c2 = st.columns(4)
    if c1.button("Cancel", use_container_width=True):
        st.rerun()

    if c2.button("Apply", type="primary", use_container_width=True):
        st.session_state["feature-matrix-filtered"] = df
        st.rerun()

def metabolite_selection():
    st.session_state.results_metabolite = "none"

    df = load_parquet(
        Path(st.session_state.results_dir, "consensus-dfs", "feature-matrix.parquet")
    )

    if df.empty:
        st.error("FeatureMatrix is empty.")
        return None

    df.set_index("metabolite", inplace=True)
    sample_cols = sorted([col for col in df.columns if col.endswith(".mzML")])
    # Insert a column with normalized intensity values to display as barchart column in dataframe
    df.insert(
        1,
        "intensity",
        df.apply(lambda row: [int(row[col]) for col in sample_cols], axis=1),
    )
    df["intensity"] = df["intensity"].apply(
        lambda intensities: [i / max(intensities) for i in intensities]
    )
    c1, c2, c3 = st.columns([0.5, 0.25, 0.25])
    c1.markdown(f"**Feature Matrix** containing {df.shape[0]} metabolites")
    if "feature-matrix-filtered" in st.session_state:
        if c2.button("❌ Reset", use_container_width=True):
            del st.session_state["feature-matrix-filtered"]
            st.rerun()
    if c3.button("🔎 Filter", use_container_width=True):
        filter_dialog(df)
    if "feature-matrix-filtered" in st.session_state:
        if not st.session_state["feature-matrix-filtered"].empty:
            df = st.session_state["feature-matrix-filtered"]

    event = st.dataframe(
        df,
        column_order=["intensity", "RT", "mz", "charge", "adduct"],
        hide_index=False,
        column_config={
            "intensity": st.column_config.BarChartColumn(
                width="small",
                help=", ".join(
                    [
                        str(Path(col).stem)
                        for col in sorted(df.columns)
                        if col.endswith(".mzML")
                    ]
                ),
            ),
        },
        height=300,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
    )
    rows = event.selection.rows
    if rows:
        return df.iloc[rows[0], :]
    st.info(
        "💡 Select a row (metabolite) in the feature matrix for more information."
    )
    return None


@st.cache_data
def get_chroms_for_each_sample(metabolite):
    # Get index of row in df where "metabolite" is equal to metabolite
    all_samples = [
        i.replace(".mzML", "")
        for i in metabolite.index
        if i.endswith("mzML")
    ]
    dfs = []
    samples = []
    for sample in all_samples:
        # Get feature ID for sample
        fid = metabolite[sample + ".mzML_IDs"]
        path = Path(st.session_state.results_dir, "ffmid-df" if metabolite["re-quantified"] else "ffm-df", sample + ".parquet")
        f_df = load_parquet(path)
        if fid in f_df.index:
            dfs.append(f_df.loc[[fid]])
            samples.append(sample)
    df = pd.concat(dfs)
    df["sample"] = samples
    df = add_color_column(df)
    return df


@st.cache_resource
def get_feature_chromatogram_plot(df):
    # Create an empty figure
    fig = go.Figure()
    # Loop through each row in the DataFrame and add a line trace for each
    for _, row in df.iterrows():
        fig.add_trace(
            go.Scatter(
                x=row["chrom_RT"],  # Assuming chrom_RT is a list of values
                y=row[
                    "chrom_intensity"
                ],  # Assuming chrom_intensity is a list of values
                mode="lines",  # Line plot
                name=row["sample"],  # Giving each line a name based on its index
                marker=dict(color=row["color"]),
            )
        )
    # Update layout of the figure
    fig.update_layout(
        xaxis_title="retention time (s)",
        yaxis_title="intensity (counts)",
        plot_bgcolor="rgb(255,255,255)",
        template="plotly_white",
        showlegend=True,
                margin=dict(l=0, r=0, t=0, b=0),
        height=300
    )
    return fig

@st.cache_resource
def get_feature_intensity_plot(metabolite):
    df = pd.DataFrame(
        {
            "sample": [i for i in metabolite.index if i.endswith(".mzML")],
            "intensity": metabolite["intensity"]
        }
    )
    df = add_color_column(df)

    # Create a mapping from sample to color
    color_map = dict(zip(df["sample"], df["color"]))

    # Plot bar chart
    fig = px.bar(df, x="sample", y="intensity", color="sample", 
                color_discrete_map=color_map)

    fig.update_layout(
        xaxis_title="",
        yaxis_title="intensity (AUC)",
        plot_bgcolor="rgb(255,255,255)",
        template="plotly_white",
        showlegend=True,
        margin=dict(l=0, r=0, t=0, b=0),
        height=300
    )
    return fig

