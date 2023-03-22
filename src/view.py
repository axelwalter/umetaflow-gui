import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px


@st.cache_data
def get_spectra_dict(mzML_df_files):
    return {file.stem: pd.read_feather(file) for file in Path(mzML_df_files).iterdir()}


@st.cache_data
def get_dfs(spectra, file):
    if spectra and file:
        return (
            spectra[file].loc[spectra[file]["mslevel"] == 1],
            spectra[file].loc[spectra[file]["mslevel"] == 2],
        )
    else:
        return pd.DataFrame(), pd.DataFrame()


@st.cache_resource
def plot_2D_map(df, cutoff):
    fig = go.Figure()
    ints = np.concatenate([df.loc[index, "intarray"] for index in df.index])
    int_filter = ints > cutoff  # show only ints over threshold
    ints = ints[int_filter]
    mzs = np.concatenate([df.loc[index, "mzarray"] for index in df.index])[int_filter]
    rts = np.concatenate(
        [
            np.full(len(df.loc[index, "mzarray"]), df.loc[index, "RT"])
            for index in df.index
        ]
    )[int_filter]

    sort = np.argsort(ints)
    ints = ints[sort]
    mzs = mzs[sort]
    rts = rts[sort]

    fig.add_trace(
        go.Scattergl(
            name="peaks",
            x=rts,
            y=mzs,
            mode="markers",
            marker_color=ints,
            marker_symbol="square",
        )
    )
    fig.update_layout(
        title="peak map 2D",
        xaxis_title="retention time",
        yaxis_title="m/z",
        plot_bgcolor="rgb(255,255,255)",
        # height=800,
        # width=1000,
    )
    fig.layout.template = "plotly_white"

    color_scale = [
        (0.00, "rgba(233, 233, 233, 1.0)"),
        (0.01, "rgba(243, 236, 166, 1.0)"),
        (0.1, "rgba(255, 168, 0, 1.0)"),
        (0.2, "rgba(191, 0, 191, 1.0)"),
        (0.4, "rgba(68, 0, 206, 1.0)"),
        (1.0, "rgba(33, 0, 101, 1.0)"),
    ]

    fig.update_traces(
        marker_colorscale=color_scale,
        hovertext=ints.round(),
        selector=dict(type="scattergl"),
    )
    st.plotly_chart(fig, use_container_width=True)
    return


@st.cache_resource
def plot_bpc(df, ms1_rt, ms2_rt=0):
    import time

    time.sleep(4)
    intensity = np.array([max(intensity_array) for intensity_array in df["intarray"]])
    fig = px.line(df, x="RT", y=intensity)
    fig.add_trace(
        go.Scatter(
            x=[ms1_rt],
            y=[intensity[np.abs(df["RT"] - ms1_rt).argmin()]],
            name="MS1 spectrum",
            text="MS1",
            textposition="top center",
            textfont=dict(color="#EF553B", size=20),
        )
    )
    fig.data[1].update(
        mode="markers+text",
        marker_symbol="x",
        marker=dict(color="#EF553B", size=12),
    )
    if ms2_rt > 0:
        fig.add_trace(
            go.Scatter(
                x=[ms2_rt],
                y=[intensity[np.abs(df["RT"] - ms2_rt).argmin()]],
                name="MS2 spectrum",
                text="MS2",
                textposition="top center",
                textfont=dict(color="#00CC96", size=20),
            )
        )
        fig.data[2].update(
            mode="markers+text",
            marker_symbol="x",
            marker=dict(color="#00CC96", size=12),
        )
    fig.update_traces(showlegend=False)
    fig.update_layout(
        showlegend=False,
        title_text="base peak chromatogram (BPC)",
        xaxis_title="retention time (s)",
        yaxis_title="intensity (cps)",
        plot_bgcolor="rgb(255,255,255)",
    )
    fig.layout.template = "plotly_white"
    return fig


@st.cache_resource
def plot_ms_spectrum(df_spectrum, title, color):
    """
    Takes a pandas Dataframe with one row (spectrum) and generates a needle plot with m/z and intensity dimension.
    """

    def create_spectra(x, y, zero=0):
        x = np.repeat(x, 3)
        y = np.repeat(y, 3)
        y[::3] = y[2::3] = zero
        return pd.DataFrame({"mz": x, "intensity": y})

    df = create_spectra(
        df_spectrum["mzarray"].tolist()[0], df_spectrum["intarray"].tolist()[0]
    )
    fig = px.line(df, x="mz", y="intensity")
    fig.update_traces(line_color=color)
    fig.update_layout(
        showlegend=False,
        title_text=title,
        xaxis_title="m/z",
        yaxis_title="intensity",
        plot_bgcolor="rgb(255,255,255)",
    )
    fig.layout.template = "plotly_white"
    fig.update_yaxes(fixedrange=True)
    st.plotly_chart(fig, use_container_width=True)
    return
