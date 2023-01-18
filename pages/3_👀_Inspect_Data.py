import streamlit as st
import pandas as pd
from pathlib import Path
from src.visualisation.graphs import *

st.set_page_config(page_title="UmetaFlow", page_icon="resources/icon.png", layout="wide", initial_sidebar_state="auto", menu_items=None)

try:
    st.title("Inspect Data")

    choice = st.radio("choose to view", ["mzML files", "Metabolomics results"])

    # ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']
    if choice == "mzML files":
        spectra = {file.stem: pd.read_pickle(file) for file in Path(st.session_state["mzML_dfs"]).iterdir()}
        
        st.markdown("#### MS data")
        view = st.radio("view MS data", ["side view", "top view"])
        sample = st.selectbox("choose sample", [key for key in spectra.keys()])

        df_ms1 = spectra[sample].loc[spectra[sample]["mslevel"] == 1]
        df_ms2 = spectra[sample].loc[spectra[sample]["mslevel"] == 2]

        if view == "side view":
            c1, c2 = st.columns(2)
            ms1_rt = c1.select_slider("MS1 spectrum (RT)", df_ms1["RT"].round(2))
            fig = plot_ms_spectrum(df_ms1[df_ms1["RT"].round(2) == ms1_rt], f"MS1 spectrum @RT {ms1_rt}", "#EF553B")
            c1.plotly_chart(fig)
            if not df_ms2.empty:
                ms2_precmz = c2.select_slider("MS2 spectrum (precursor m/z)", sorted(df_ms2["precursormz"].round(4)))
                ms2_rt = df_ms2[df_ms2["precursormz"].round(4) == ms2_precmz]["RT"].tolist()[0]
                fig = plot_ms_spectrum(df_ms2[df_ms2["precursormz"].round(4) == ms2_precmz], f"MS2 spectrum @precursor m/z {ms2_precmz} @RT {ms2_rt}", "#00CC96")
                c2.plotly_chart(fig)
            fig = px.line(df_ms1, x="RT", y=[max(intensity_array) for intensity_array in df_ms1["intarray"]], labels={"y": "intensity (cps)"})
            fig.add_trace(go.Line(x=[ms1_rt, ms1_rt], y=[0, max(fig.data[0].y)], name="MS1 spectrum"))
            fig.data[1].update(mode='lines', marker_symbol="x", marker=dict(color="#EF553B"))
            if not df_ms2.empty:
                fig.add_trace(go.Line(x=[ms2_rt, ms2_rt], y=[0, max(fig.data[0].y)], name="MS2 spectrum"))
                fig.data[2].update(mode='lines', marker_symbol="x", marker=dict(color="#00CC96"))
            fig.update_traces(showlegend=False)
            st.plotly_chart(fig)
except:
    st.warning("Something went wrong.")