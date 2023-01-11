import streamlit as st
from src.helpers import Helper
from pathlib import Path
import pandas as pd
import os
import shutil

st.set_page_config(layout="wide")


try:
    if not os.path.isdir("mzML_files"):
        os.mkdir("mzML_files")

    st.title("File Selection")

    st.info("""
    **How to upload files**

    1. Browse files on your computer
    2. Click the **Add mzML files** button to use them in the workflows

    The currently uploaded files will be used for data analysis in both workflows.
    """)

    accept_multiple = True
    if st.session_state.location == "online":
        accept_multiple = False

    st.markdown("**Upload files**")
    with st.form("my-form", clear_on_submit=True):
            uploaded_mzML = st.file_uploader("mzML files", accept_multiple_files=accept_multiple)
            _, c2, _ = st.columns(3)
            submitted = c2.form_submit_button("Add the uploaded mzML files")

    mzML_dir = "mzML_files"

    # option for local installation: upload files via directory path
    if st.session_state.location == "local":
        st.markdown("**OR specify the path to a folder containing your mzML files**")
        c1, c2 = st.columns([0.9, 0.1])
        upload_dir = c1.text_input("path to folder with mzML files")
        c2.markdown("##")
        if c2.button("Upload"):
            for file in Path(upload_dir).iterdir():
                if file.name not in Path(mzML_dir).iterdir() and file.name.endswith("mzML"):
                    shutil.copy(file, mzML_dir)
            st.success("Successfully added uploaded files!")

    # upload mzML files
    if submitted:
        if uploaded_mzML:
            for file in uploaded_mzML:
                if file.name not in Path(mzML_dir).iterdir() and file.name.endswith("mzML"):
                    with open(Path(mzML_dir, file.name),"wb") as f:
                            f.write(file.getbuffer())
            st.success("Successfully added uploaded files!")
        else:
            st.warning("Upload some files before adding them.")


    st.markdown("##")
    c1, c2 = st.columns([0.4, 0.8])
    c2.markdown("#")
    clear_all = c2.button("Remove All Files")
    c1.markdown("**mzML files for data anaylsis**")
    c1.dataframe(pd.DataFrame({"files": [file.name for file in Path(mzML_dir).iterdir()]}))

    if clear_all:
        Helper().reset_directory("mzML_files")
        st.experimental_rerun()
except:
    st.warning("Something went wrong.")