import streamlit as st
import pandas as pd
from pathlib import Path
from src.visualisation.graphs import *

st.set_page_config(page_title="UmetaFlow", page_icon="resources/icon.png", layout="wide", initial_sidebar_state="auto", menu_items=None)

# try:

with st.sidebar:
    st.image("resources/OpenMS.png", "powered by")
    st.markdown("***")

st.title("Visualization")

choice = st.radio("choose to view", ["mzML files", "Metabolomics results"])

# ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']
if choice == "mzML files":
    spectra = {file.stem: pd.read_pickle(file) for file in Path(st.session_state["mzML_dfs"]).iterdir()}
    
    st.markdown("#### MS data")
    c1, c2 = st.columns(2)
    sample = c1.selectbox("choose sample", [key for key in spectra.keys()])

    if sample:
        c2.markdown("#")
        show_peak_map = c2.checkbox("show 2D peak map", False)

        df_ms1 = spectra[sample].loc[spectra[sample]["mslevel"] == 1]
        if show_peak_map:
            peak_map = plot_peak_map_2D(df_ms1)
            st.plotly_chart(peak_map)
        df_ms2 = spectra[sample].loc[spectra[sample]["mslevel"] == 2]

        ms1_rt = st.select_slider("MS1 spectrum (RT)", df_ms1["RT"].round(2))
        c1, c2 = st.columns(2)
        
        ms2_rt = 0
        if not df_ms2.empty:
            ms2 = c2.selectbox("MS2 spectrum", sorted([f"{mz} m/z @ {rt} s" for mz, rt in zip(df_ms2["precursormz"].round(4), df_ms2["RT"].round(2))]))
            ms2_precmz = float(ms2.split(" m/z")[0])
            ms2_rt = df_ms2[df_ms2["precursormz"].round(4) == ms2_precmz]["RT"].tolist()[0]
            c2.plotly_chart(plot_ms_spectrum(df_ms2[df_ms2["precursormz"].round(4) == ms2_precmz], f"MS2 spectrum @precursor m/z {ms2_precmz} @RT {round(ms2_rt, 2)}", "#00CC96"))
            c1.markdown("#")
            c1.markdown("#")
            st.plotly_chart(plot_ms_spectrum(df_ms1[df_ms1["RT"].round(2) == ms1_rt], f"MS1 spectrum @RT {ms1_rt}", "#EF553B"))

        else:
            c2.plotly_chart(plot_ms_spectrum(df_ms1[df_ms1["RT"].round(2) == ms1_rt], f"MS1 spectrum @RT {ms1_rt}", "#EF553B"))
        c1.plotly_chart(plot_bpc(df_ms1, ms1_rt, ms2_rt))

elif choice == "Metabolomics results":
    st.info("Coming soon!")

# except:
#     st.warning("Something went wrong.")