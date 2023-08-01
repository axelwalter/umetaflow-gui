import streamlit as st
import pandas as pd
import numpy as np
from .metabolomicsplotting import *


"""
Contains all visualization blocks as modules with streamlit components.
"""


def display_feature_data(feature_maps, spectra, feature_detection_method="FFM"):
    c1, c2 = st.columns(2)
    name = c1.selectbox("choose feature map", [
                        key for key in feature_maps.keys()], key=feature_detection_method)
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

        selected_feature = st.selectbox(
            "detailed feature view", df["metabolite"])
        feature = df[df["metabolite"] == selected_feature]
        # get start and end RT/mz values to filter peak map
        bb = feature[["RTstart", "RTend", "MZstart", "MZend"]]

        # Define the values for mzmin and mzmax
        mzmin = bb.loc[bb.index[0], "MZstart"]
        mzmax = bb.loc[bb.index[0], "MZend"]

        # # filter df by retention time...
        df_peaks = spectra[name][
            (spectra[name]["RT"] > bb.loc[bb.index[0], "RTstart"])
            & (spectra[name]["RT"] < (bb.loc[bb.index[0], "RTend"]))
        ]

        # Create a function to filter the entries based on the condition
        def filter_entries(row):
            mz_array = row['mzarray']
            int_array = row['intarray']
            filtered_indices = np.where((mz_array > mzmin) & (mz_array < mzmax))
            filtered_mz = mz_array[filtered_indices]
            filtered_int = int_array[filtered_indices]
            return filtered_mz, filtered_int

        # Apply the filter_entries function to the DataFrame and create new columns with the filtered results
        df_peaks[['filtered_mzarray', 'filtered_intarray']] = df_peaks.apply(filter_entries, axis=1, result_type='expand')

        # If you only want the entries that have some values in both 'mzarray' and 'intarray'
        # you can drop rows with empty arrays in the filtered columns
        df_peaks = df_peaks.dropna(subset=['filtered_mzarray', 'filtered_intarray'])

        # Drop the original 'mzarray' and 'intarray' columns if needed
        df_peaks = df_peaks.drop(columns=['mzarray', 'intarray'])

        # Rename to original name
        df_peaks = df_peaks.rename(columns={"filtered_mzarray": "mzarray", "filtered_intarray": "intarray"})


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
        fig = plot_feature_chromatogram(
            df[df["metabolite"] == selected_feature])
        st.plotly_chart(fig)
        # 2D chromatogram peak map of feature area
        fig = plot_peak_map_2D(df_peaks, 0)
        st.plotly_chart(fig)


def display_map_alignement(feature_maps: dict):
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
        c3.metric("mean RT deviation", np.mean(
            df["RT"] - df["original_rt"]).round(2))
        fig = plot_feature_map_alignment(df)
        st.plotly_chart(fig)


def display_consensus_map(df: pd.DataFrame, feature_maps: dict):
    # calculate means of intensities
    df = df.assign(
        means=df[[col for col in df.columns if col.endswith(".mzML")]].mean(
            axis=1)
    )


    # select a sample or all for mean intensities
    c1, _ = st.columns(2)
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

    fig = plot_consensus_map(df, sample)
    st.plotly_chart(fig)

    # chose a feature for comparison chromatogram plot
    c1, _ = st.columns(2)
    feature = c1.selectbox(
        "choose metabolite for intensity comparison",
        [m for m in df["metabolite"]],
    )

    # determine which features in which samples to plot as chromatogram
    to_plot = {
        k: v
        for k, v in df[df["metabolite"] == feature]["sample_to_id"].iloc[0].items()
        if v
    }

    fig = plot_consensus_feature_chromatograms(feature_maps, to_plot, feature)
    st.plotly_chart(fig)
