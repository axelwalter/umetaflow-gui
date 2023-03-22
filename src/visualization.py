import streamlit as st
import pandas as pd
import numpy as np
from .plotting import *


"""
Contains all visualization blocks as modules with streamlit components.
"""


def display_feature_data(feature_maps, spectra):
    c1, c2 = st.columns(2)
    name = c1.selectbox("choose feature map", [key for key in feature_maps.keys()])
    if name:
        df = feature_maps[name]
        c1, c2, c3 = st.columns(3)
        c1.metric("number of features", df.shape[0])
        c2.metric("lowest intensity", int(min(df["intensity"])))
        c3.metric("highest intensity", int(max(df["intensity"])))
        int_cutoff = st.select_slider(
            "show features with intensity above intensity",
            range(0, int(max(df["intensity"])), 100000),
        )

        df = df[df["intensity"] > int_cutoff]
        df.sort_values(by=["intensity"], inplace=True)
        df.fillna(0, inplace=True)
        # 2D feature map
        fig = plot_feature_map(df)
        st.plotly_chart(fig)

        selected_feature = st.selectbox("detailed feature view", df["metabolite"])
        feature = df[df["metabolite"] == selected_feature]
        # get start and end RT/mz values to filter peak map
        bb = feature[["RTstart", "RTend", "MZstart", "MZend"]]

        # filter df by retention time...
        df_peaks = spectra[name][
            (spectra[name]["RT"] > bb.loc[bb.index[0], "RTstart"])
            & (spectra[name]["RT"] < (bb.loc[bb.index[0], "RTend"]))
        ]

        # and by mz...
        def filter_arrays(row):
            filter = (row["mzarray"] > bb.loc[bb.index[0], "MZstart"]) & (
                row["mzarray"] < bb.loc[bb.index[0], "MZend"]
            )
            row["mzarray"] = row["mzarray"][filter]
            row["intarray"] = row["intarray"][filter]
            return row

        df_peaks[["mzarray", "intarray"]] = df_peaks[["mzarray", "intarray"]].apply(
            filter_arrays, axis=1
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("m/z", feature["mz"].round(5))
        c2.metric("intensity", feature["intensity"].astype(int))
        c3.metric("charge", feature["charge"])
        c4.metric("adduct", feature.loc[feature.index[0], "adduct"])
        c1.metric("retention time", feature["RT"].round(2))
        c2.metric(
            "retention time range",
            np.round(feature["RTend"] - feature["RTstart"], 2),
        )
        c3.metric("FWHM", feature["fwhm"].round(2))
        if "snr" in feature.columns:
            c4.metric("S/N", feature["snr"].round(2))
        # chromatogram monoisotopic mass
        fig = plot_feature_chromatogram(df[df["metabolite"] == selected_feature])
        st.plotly_chart(fig)
        # 2D chromatogram peak map of feature area
        fig = plot_peak_map_2D(df_peaks, 0)
        st.plotly_chart(fig)


def display_map_alignemnt(feature_maps: dict):
    c1, c2, c3 = st.columns(3)
    name = c1.selectbox(
        "choose feature map",
        [
            key
            for key, value in feature_maps.items()
            if not value["original_rt"].isnull().any()
        ],
    )
    if name:
        df = feature_maps[name]
        c2.metric(
            "reference map (contains most features)",
            [
                key
                for key, value in feature_maps.items()
                if value["original_rt"].isnull().any()
            ][0],
        )
        c3.metric("mean RT deviation", np.mean(df["RT"] - df["original_rt"]).round(2))
        fig = plot_feature_map_alignment(df)
        st.plotly_chart(fig)


def display_consensus_map(df: pd.DataFrame, feature_maps: dict):
    # calculate means of intensities
    df = df.assign(
        means=df[[col for col in df.columns if col.endswith(".mzML")]].mean(axis=1)
    )

    c1, c2 = st.columns(2)
    # select a sample or all for mean intensities
    sample = c1.selectbox(
        "choose sample to highlight",
        ["Show mean intensities"]
        + [col for col in df.columns if col.endswith(".mzML")],
    )

    # select "means" column if selected
    if sample == "Show mean intensities":
        sample = "means"

    # sort df by sample value to plot high intensities on top
    df.sort_values(by=[sample], inplace=True)

    # chose a feature for comparison chromatogram plot
    feature = c2.selectbox(
        "choose metabolite for intensity comparison",
        [m for m in df["metabolite"]],
    )

    fig = plot_consensus_map(df, sample)
    st.plotly_chart(fig)

    # determine which features in which samples to plot as chromatogram
    to_plot = {
        k: v
        for k, v in df[df["metabolite"] == feature]["sample_to_id"].iloc[0].items()
        if v
    }

    fig = plot_consensus_feature_chromatograms(feature_maps, to_plot, feature)
    st.plotly_chart(fig)
