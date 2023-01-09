import streamlit as st
import plotly.express as px
from pyopenms import *
import os
import pandas as pd
import numpy as np
from pymetabo.helpers import Helper
from utils.filehandler import get_files, get_dir, get_file
from pymetabo.dataframes import DataFrames
from pymetabo.gnps import GNPSExport
from pymetabo.spectralmatcher import SpectralMatcher
import pathlib
from os.path import isfile, join
from os import listdir

st.write("for testing...")

uploaded = st.file_uploader("upload files", accept_multiple_files=True)

if st.button("run"):
    for file in uploaded:
        with open(os.path.join("tempDir",file.name),"wb") as f:
                f.write(file.getbuffer())