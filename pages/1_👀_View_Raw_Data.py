import streamlit as st
import pandas as pd
from pathlib import Path
from src.visualization import Visualization


st.set_page_config(page_title="UmetaFlow", page_icon="resources/icon.png", layout="wide", initial_sidebar_state="auto", menu_items=None)

try:
    with st.sidebar:
        st.image("resources/OpenMS.png", "powered by")

    st.title("View raw MS data")

    Visualization.display_MS_data({file.stem: pd.read_feather(file) for file in Path(st.session_state["mzML_dfs"]).iterdir()})

except:
    st.warning("Something went wrong.")