import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import plotly.figure_factory as ff
import streamlit as st

COLORS = [
    "#636efa",
    "#ef553b",
    "#00cc96",
    "#ab63fa",
    "#ffa15a",
    "#19d3f3",
    "#ff6692",
    "#b6e880",
    "#fe9aff",
    "rgb(23, 190, 207)",
]

COLOR_SCALE = [
    (0.00, "rgba(233, 233, 233, 1.0)"),
    (0.01, "rgba(243, 236, 166, 1.0)"),
    (0.1, "rgba(255, 168, 0, 1.0)"),
    (0.2, "rgba(191, 0, 191, 1.0)"),
    (0.4, "rgba(68, 0, 206, 1.0)"),
    (1.0, "rgba(33, 0, 101, 1.0)"),
]


def cycle(my_list):
    start_at = 0
    while True:
        yield my_list[start_at]
        start_at = (start_at + 1) % len(my_list)


def extracted_chroms(df_chrom, chroms=[], df_auc=None, title="", time_unit="seconds"):
    colors = cycle(COLORS)
    traces_line = []
    traces_bar = []
    for chrom in chroms:
        if chrom == "BPC":
            color = "#CCCCCC"
        elif chrom == "AUC baseline":
            color = "#555555"
        else:
            color = next(colors)
        traces_line.append(
            go.Scatter(
                x=df_chrom["time"],
                y=df_chrom[chrom],
                name=chrom,
                mode="lines",
                line_color=color,
            )
        )
        if len(df_auc) == 1 and chrom in df_auc.columns:
            traces_bar.append(
                go.Bar(x=[chrom], y=[df_auc[chrom][0]], name=chrom, marker_color=color)
            )
    fig_chrom = go.Figure()
    fig_auc = go.Figure()
    for trace in traces_line:
        fig_chrom.add_trace(trace)
    for trace in traces_bar:
        fig_auc.add_trace(trace)
    fig_chrom.update_layout(
        title=title,
        xaxis=dict(title=f"time ({time_unit})"),
        yaxis=dict(title="intensity (counts per second)"),
    )
    fig_auc.update_layout(
        title=title,
        xaxis=dict(title=""),
        yaxis=dict(title="area under curve (counts)"),
    )
    fig_auc.update_traces(width=0.3)
    return fig_chrom, fig_auc


def FFMID(
    self,
    df_chrom,
    compounds=[],
    df_auc=None,
    df_auc_combined=None,
    title="",
    time_unit="seconds",
):
    colors = cycle(COLORS)
    if compounds:
        trace_names = compounds
    else:
        trace_names = set([c[:-5] for c in df_chrom.columns if c.endswith("RT")])
    traces_line = []
    traces_bar = []
    traces_bar_combined = []
    for name in trace_names:
        color = next(colors)
        i = 1
        while name + "_" + str(i) + "_RT" in df_chrom.columns:
            label = name + "_" + str(i)
            traces_line.append(
                go.Scatter(
                    x=df_chrom[label + "_RT"],
                    y=df_chrom[label + "_int"],
                    name=label,
                    mode="lines",
                    line_color=color,
                )
            )
            if len(df_auc) == 1 and name in df_auc.columns and i == 1:
                traces_bar.append(
                    go.Bar(x=[name], y=[df_auc[name][0]], name=name, marker_color=color)
                )
            i += 1
    if len(df_auc) == 1:
        colors = cycle(COLORS)
        for name in df_auc_combined.columns:
            color = next(colors)
            traces_bar_combined.append(
                go.Bar(
                    x=[name],
                    y=[df_auc_combined[name][0]],
                    name=name,
                    marker_color=color,
                )
            )
    fig_chrom = go.Figure()
    fig_auc = go.Figure()
    fig_auc_combined = go.Figure()
    for trace in traces_line:
        fig_chrom.add_trace(trace)
    for trace in traces_bar:
        fig_auc.add_trace(trace)
    for trace in traces_bar_combined:
        fig_auc_combined.add_trace(trace)
    fig_chrom.update_layout(
        title=title,
        xaxis=dict(title=f"time ({time_unit})"),
        yaxis=dict(title="intensity (cps)"),
    )
    for fig in (fig_auc, fig_auc_combined):
        fig.update_layout(
            title=title,
            xaxis=dict(title=""),
            yaxis=dict(title="area under curve (counts)"),
        )
        fig.update_traces(width=0.3)
    return fig_chrom, fig_auc, fig_auc_combined


def FeatureMatrix(
    self,
    df,
    df_std=pd.DataFrame(),
    samples=[],
    features=[],
    title="",
    y_title="area under curve (counts)",
):
    samples = df.columns.tolist()
    features = df.index.tolist()
    fig = go.Figure()
    for feature in features:
        if not df_std.empty:
            fig.add_trace(
                go.Bar(
                    x=samples,
                    y=df.loc[feature],
                    name=feature,
                    error_y=dict(type="data", array=df_std.loc[feature], visible=True),
                )
            )
        else:
            fig.add_trace(go.Bar(x=samples, y=df.loc[feature], name=feature))
    fig.update_layout(title=title, yaxis=dict(title=y_title))
    return fig


def FeatureMatrixHeatMap(df, title=""):
    fig = go.Figure(
        data=go.Heatmap(
            {
                "z": df.values.tolist(),
                "x": df.columns.tolist(),
                "y": df.index.tolist(),
            },
            colorscale=[
                [0, "rgba(69, 117, 180, 1.0)"],
                [
                    0 - df.min().min() / (df.max().max() - df.min().min()),
                    "rgba(255, 255, 255, 1.0)",
                ],
                [1, "rgba(215,48,39, 1.0)"],
            ],
        )
    )
    # fig.layout.width = 200+10*len(df.columns)
    # fig.layout.height = 30*len(df.index)
    fig.update_layout(title=title)
    return fig


def dendrogram(df):
    fig = ff.create_dendrogram(df, labels=list(df.index))
    fig.update_xaxes(side="top")
    return fig


def heatmap(df):
    fig = px.imshow(
        df,
        y=list(df.index),
        x=list(df.columns),
        text_auto=True,
        aspect="auto",
        color_continuous_scale="RdBu_r",
        range_color=[-3, 3],
    )

    fig.update_layout(
        autosize=False, width=700, height=1200, xaxis_title="", yaxis_title=""
    )

    # fig.update_yaxes(visible=False)
    fig.update_xaxes(tickangle=35)
    return fig


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
    return fig


def plot_bpc(df, ms1_rt, ms2_rt=0):
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
        title_text="base peak chromatogram",
        xaxis_title="retention time (s)",
        yaxis_title="intensity (cps)",
        plot_bgcolor="rgb(255,255,255)",
    )
    fig.layout.template = "plotly_white"
    return fig


@st.cache_resource
def plot_peak_map_2D(df, cutoff):
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
        title="2D peak map",
        xaxis_title="retention time",
        yaxis_title="m/z",
        plot_bgcolor="rgb(255,255,255)",
        height=800,
        width=1000,
    )
    fig.layout.template = "plotly_white"

    fig.update_traces(
        marker_colorscale=COLOR_SCALE,
        hovertext=ints.round(),
        selector=dict(type="scattergl"),
    )
    return fig


def plot_feature_map(df):
    fig = go.Figure()
    # fig.add_traces([go.Scattergl(x=[df.loc[i, "RTstart"], df.loc[i, "RTend"]], y=[df.loc[i, "mz"], df.loc[i, "mz"]], mode="lines", line=dict(color="rgba(41,55,155, 0.5)")) for i in df.index])
    fig.add_trace(
        go.Scattergl(
            name="feature",
            x=df["RT"],
            y=df["mz"],
            mode="markers",
            marker_color=df["intensity"],
            marker_symbol="square",
            marker_size=12,
            customdata=np.stack(
                (
                    df["mz"].round(5),
                    df["intensity"].astype(int),
                    df["RTstart"].astype(int),
                    df["RTend"].astype(int),
                    df["RTend"].astype(int) - df["RTstart"].astype(int),
                    df["fwhm"].round(),
                    df["charge"],
                    df["quality"],
                    df["adduct"],
                ),
                axis=-1,
            ),
            hovertemplate="<b>mz: %{customdata[0]}<br>intensity: %{customdata[1]}<br>RTstart: %{customdata[2]}<br>RTend: %{customdata[3]}<br>RTrange: %{customdata[4]}<br>FWHM: %{customdata[5]}<br>charge: %{customdata[6]}<br>quality: %{customdata[7]}<br>adduct: %{customdata[8]}<br>",
        )
    )

    fig.update_layout(
        title="feature map",
        xaxis_title="retention time",
        yaxis_title="m/z",
        plot_bgcolor="rgb(255,255,255)",
        height=800,
        width=1000,
    )
    fig.layout.template = "plotly_white"
    fig.update_traces(
        showlegend=False,
        marker_colorscale=COLOR_SCALE,
        hovertext="int: "
        + df["intensity"].astype(int).astype(str)
        + " q: "
        + df["quality"].astype(str),
        selector=dict(type="scattergl"),
    )
    return fig


def plot_feature_chromatogram(df):
    fig = px.line(
        x=df.loc[df.index[0], "chrom_rts"],
        y=df.loc[df.index[0], "chrom_intensities"],
    )
    fig.update_layout(
        title=f"monoisotopic peak chromatogram",
        xaxis_title="retention time",
        yaxis_title="intensity (counts per second)",
        plot_bgcolor="rgb(255,255,255)",
    )
    fig.layout.template = "plotly_white"
    return fig


def plot_feature_map_alignment(df):
    fig = go.Figure()
    fig.add_trace(
        go.Scattergl(
            name="before aligment",
            x=df["original_rt"],
            y=df["mz"],
            mode="markers",
            marker_symbol="circle",
            marker_size=12,
        )
    )
    fig.add_trace(
        go.Scattergl(
            name="after aligment",
            x=df["RT"],
            y=df["mz"],
            mode="markers",
            marker_symbol="circle",
            marker_size=8,
        )
    )
    fig.update_layout(
        title=f"feature map alignment",
        xaxis_title="retention time",
        yaxis_title="m/z",
        plot_bgcolor="rgb(255,255,255)",
    )
    fig.layout.template = "plotly_white"
    return fig


def plot_consensus_map(df, sample):
    fig = go.Figure()

    # define custom data for hovering
    meta_values = [
        df["metabolite"],
        df["mz"].round(5),
        df["RT"].round(),
        df[sample],
        df["charge"],
        df["quality"],
    ]

    hovertemplate = """
<b>name: %{customdata[0]}<br>
mz: %{customdata[1]}<br>
RT: %{customdata[2]}<br>
intensity: %{customdata[3]}<br>
charge: %{customdata[4]}<br>
quality: %{customdata[5]}<br>
"""

    if "adduct" in df.columns:
        meta_values.append(df["adduct"])
        hovertemplate += "adduct: %{customdata[5]}<br>"

    for s in [col for col in df.columns if col.endswith("mzML")]:
        meta_values.append(df[s])
        hovertemplate += (
            s[:-5] + ": %{customdata[" + str(len(meta_values) - 1) + "]}<br>"
        )

    customdata = np.stack(meta_values, axis=-1)

    fig.add_trace(
        go.Scattergl(
            name="feature",
            x=df["RT"],
            y=df["mz"],
            mode="markers",
            marker_color=df[sample],
            marker_symbol="square",
            marker_size=12,
            customdata=customdata,
            hovertemplate=hovertemplate,
        )
    )
    fig.update_layout(
        title=f"consensus map with intensities from {sample}",
        xaxis_title="retention time",
        yaxis_title="m/z",
        showlegend=False,
        plot_bgcolor="rgb(255,255,255)",
    )
    fig.update_traces(
        showlegend=False,
        marker_colorscale=COLOR_SCALE,
        selector=dict(type="scattergl"),
    )

    return fig


def plot_consensus_feature_chromatograms(feature_maps: dict, to_plot: dict, title: str):

    fig = go.Figure()

    for sample, id in to_plot.items():
        df = feature_maps[sample][feature_maps[sample]["feature_id"] == id]

        fig.add_trace(
            go.Scattergl(
                name=sample,
                x=df.loc[df.index[0], "chrom_rts"],
                y=df.loc[df.index[0], "chrom_intensities"],
                mode="lines",
            )
        )
    fig.update_layout(
        showlegend=True,
        title=title,
        xaxis_title="time",
        yaxis_title="intensity (counts per second)",
        legend_title="sample",
        plot_bgcolor="rgb(255,255,255)",
    )
    fig.layout.template = "plotly_white"
    return fig


@st.cache_resource
def plot_example_plot(x):
    import time

    time.sleep(5)
    return px.scatter(np.random.randn(x, 23))
