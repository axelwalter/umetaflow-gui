import streamlit as st
import pandas as pd
from pathlib import Path
from src.visualisation.graphs import *

st.set_page_config(page_title="UmetaFlow", page_icon="resources/icon.png", layout="wide", initial_sidebar_state="auto", menu_items=None)

def display_MS_data(spectra):
    c1, c2 = st.columns(2)
    name = c1.selectbox("choose peak map", [key for key in spectra.keys()])
    view = c2.radio("view data", ["spectrum view", "2D peak map"])

    if name:
        df_ms1 = spectra[name].loc[spectra[name]["mslevel"] == 1]
        if view == "2D peak map":
            cutoff = c1.number_input("intensity cutoff ⚠️ low cutoff can be slow!", 0, 1000000000, 10000, 1000)
            with st.spinner("Generating 2D peak map..."):
                peak_map = plot_peak_map_2D(df_ms1, cutoff)
                st.plotly_chart(peak_map)
        else:
            df_ms2 = spectra[name].loc[spectra[name]["mslevel"] == 2]

            c1, c2 = st.columns(2)
            ms1_rt = c1.select_slider("MS1 spectrum (RT) 💡 Scroll with the arrow keys!", df_ms1["RT"].round(2))

            ms2_rt = 0
            if not df_ms2.empty:
                ms2 = c2.selectbox("MS2 spectrum", sorted([f"{mz} m/z @ {rt} s" for mz, rt in zip(df_ms2["precursormz"].round(4), df_ms2["RT"].round(2))]))
                ms2_precmz = float(ms2.split(" m/z")[0])
                ms2_rt = df_ms2[df_ms2["precursormz"].round(4) == ms2_precmz]["RT"].tolist()[0]
                c1.plotly_chart(plot_ms_spectrum(df_ms1[df_ms1["RT"].round(2) == ms1_rt], f"MS1 spectrum @RT {ms1_rt}", "#EF553B"))
                c2.plotly_chart(plot_ms_spectrum(df_ms2[df_ms2["precursormz"].round(4) == ms2_precmz], f"MS2 spectrum @precursor m/z {ms2_precmz} @RT {round(ms2_rt, 2)}", "#00CC96"))
                st.plotly_chart(plot_bpc(df_ms1, ms1_rt, ms2_rt))
            else:
                c1.plotly_chart(plot_ms_spectrum(df_ms1[df_ms1["RT"].round(2) == ms1_rt], f"MS1 spectrum @RT {ms1_rt}", "#EF553B"))
                c2.markdown("##")
                c2.markdown("##")
                c2.markdown("##")
                c2.plotly_chart(plot_bpc(df_ms1, ms1_rt, ms2_rt))

def display_FFM_data(feature_maps):
    c1, c2 = st.columns(2)
    name = c1.selectbox("choose feature map", [key for key in feature_maps.keys()])
    if name:
        df = feature_maps[name]
        c1, c2, c3 = st.columns(3)
        c1.metric("number of features", df.shape[0])
        c2.metric("lowest intensity", int(min(df["intensity"])))
        c3.metric("highest intensity", int(max(df["intensity"])))
        int_cutoff = c1.number_input("show features with intensity above x 10e6", 0, int(max(df["intensity"])/1000000), 0, 1) * 1000000
        df = df[df["intensity"] > int_cutoff]
        df.sort_values(by=["intensity"], inplace=True)
        df.fillna("None", inplace=True)
        selected_feature = c2.selectbox("detailed feature view", df["metabolite"])

        c1, c2 = st.columns(2)
        # 2D chromatogram peak map of feature area
        fig = plot_feature_chromatogram(df[df["metabolite"] == selected_feature])
        c1.plotly_chart(fig)
        # chromatogram monoisotopic mass


        # 2D feature map
        fig = plot_feature_map(df)
        st.plotly_chart(fig)

# try:
with st.sidebar:
    st.image("resources/OpenMS.png", "powered by")

st.title("Visualization")

# determine possible options
options = ["mzML files"]
try:
    if any(Path(st.session_state["workspace"], "results-metabolomics", "interim", "FFM_dfs").iterdir()):
        options.append("metabolomics: detected features")
    if any(Path(st.session_state["workspace"], "results-metabolomics", "interim", "FFM_aligned").iterdir()):
        options.append("metabolomics: feature alignment")
    if Path(st.session_state["workspace"], "results-metabolomics", "interim", "FeatureMatrix.consensusXML").is_file():
        options.append("metabolomics: consensus features")
except FileNotFoundError:
    pass

choice = st.radio("choose to view", options)

# ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']
if choice == "mzML files":
    display_MS_data({file.stem: pd.read_feather(file) for file in Path(st.session_state["mzML_dfs"]).iterdir()})

elif choice == "metabolomics: detected features":
    display_FFM_data({file.stem: pd.read_feather(file) for file in Path(st.session_state["workspace"], "results-metabolomics", "interim", "FFM_dfs").iterdir()})
else:
    st.info("Coming soon!")

# except:
#     st.warning("Something went wrong.")