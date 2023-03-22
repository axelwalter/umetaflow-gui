import streamlit as st

st.write("for testing...")

import numpy as np
import pandas as pd

import time
from pathlib import Path

import plotly.express as px


# @st.cache_data
# def number(x=3):
#     time.sleep(3)
#     return np.random.randn(x, x)


# if "num" not in st.session_state:
#     st.session_state.num = 4

# st.number_input("number", 1, 10, st.session_state.num, key="num")

# st.dataframe(number(st.session_state.num))

# st.number_input("num2", 10, 20, 12)

# # st.write(st.session_state.view_spectra_dict.keys())


st.write(st.session_state)
