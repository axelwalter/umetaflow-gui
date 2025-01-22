import streamlit as st
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Draw

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from itertools import cycle

from src.common.common import show_fig, load_parquet


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
    st.markdown(f"**Feature Matrix** containing {df.shape[0]} metabolites")
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


# @st.cache_data
# def get_chroms_for_each_sample(metabolite):
#     # Get index of row in df where "metabolite" is equal to metabolite
#     all_samples = [
#         col.replace(".mzML_IDs", "")
#         for col in df.columns
#         if col.endswith("mzML_IDs")
#     ]
#     dfs = []
#     samples = []
#     for sample in all_samples:
#         # Get feature ID for sample
#         fid = df.loc[metabolite, sample + ".mzML_IDs"]
#         path = Path(feature_df_dir, sample + ".parquet")
#         f_df = load_parquet(path)
#         if fid in f_df.index:
#             dfs.append(f_df.loc[[fid]])
#             samples.append(sample)
#     df = pd.concat(dfs)
#     df["sample"] = samples
#     color_cycle = cycle(px.colors.qualitative.Plotly)
#     df["color"] = [next(color_cycle) for _ in range(len(df))]

#     return df


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
        title=metabolite,
        xaxis_title="retention time (s)",
        yaxis_title="intensity (counts per second)",
        plot_bgcolor="rgb(255,255,255)",
        template="plotly_white",
        showlegend=True,
    )
    return fig


def feature_intensity_plot(metabolite):
    df = pd.DataFrame(
        {
            "sample": [i for i in metabolite.index if i.endswith(".mzML")],
            "intensity": metabolite["intensity"],
        }
    )
    fig = px.bar(df, x="sample", y="intensity", color="sample", opacity=0.8)

    fig.update_layout(
        xaxis_title="",
        yaxis_title="metabolite intensity",
        plot_bgcolor="rgb(255,255,255)",
        template="plotly_white",
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        height=300

    )
    show_fig(fig, f"AUC_{metabolite.index[0]}")
