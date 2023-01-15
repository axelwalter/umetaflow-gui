import streamlit as st
from src.helpers import Helper
from pathlib import Path
import pandas as pd
import os
import shutil

st.set_page_config(page_title="UmetaFlow", page_icon="resources/icon.png", layout="wide", initial_sidebar_state="auto", menu_items=None)

# define directory to store mzML files
mzML_dir = "mzML_files"
if not os.path.isdir(mzML_dir):
    os.mkdir(mzML_dir)

with st.sidebar:
    # show currently available mzML files
    st.markdown("**choose mzML files:**")
    for f in sorted(Path("mzML_files").iterdir()):
        if f.name in st.session_state:
            checked = st.session_state[f.name]
        else:
            checked = True
        st.checkbox(f.name, checked, key=f.name)
    st.markdown("***")
    if st.button("Remove **Un**selected Files"):
        for file in [Path("mzML_files", key) for key, value in st.session_state.items() if key.endswith("mzML") and not value]:
            file.unlink()
        st.experimental_rerun()
    if st.button("⚠️ Remove All"):
        Helper().reset_directory("mzML_files")
        st.experimental_rerun()
    

st.title("File Upload")
st.info("""
    **💡 How to upload files**

    1. Browse files on your computer
    2. Click the **Add mzML files** button to use them in the workflows

    Select data for anaylsis from the uploaded files shown in the sidebar.
    """)

accept_multiple = True
if st.session_state.location == "online":
    accept_multiple = False

st.markdown("**Upload files**")
with st.form("my-form", clear_on_submit=True):
        uploaded_mzML = st.file_uploader("mzML files", accept_multiple_files=accept_multiple)
        _, c2, _ = st.columns(3)
        submitted = c2.form_submit_button("Add the uploaded mzML files")

# we need to have a list of uploaded files to copy to the mzML dir, in case of online only a single item is return, so we put it in the list
if st.session_state.location == "online":
    uploaded_mzML = [uploaded_mzML]


# option for local installation: upload files via directory path
if st.session_state.location == "local":
    st.markdown("**OR specify the path to a folder containing your mzML files**")
    c1, c2 = st.columns([0.9, 0.1])
    upload_dir = c1.text_input("path to folder with mzML files")
    upload_dir = r'{}'.format(upload_dir)
    c2.markdown("##")
    if c2.button("Upload"):
        with st.spinner("Uploading files..."):
            for file in Path(upload_dir).iterdir():
                if file.name not in Path(mzML_dir).iterdir() and file.name.endswith("mzML"):
                    shutil.copy(file, mzML_dir)
            st.success("Successfully added uploaded files!")
            st.experimental_rerun()

# upload mzML files
if submitted:
    if uploaded_mzML:
        for file in uploaded_mzML:
            if file.name not in Path(mzML_dir).iterdir() and file.name.endswith("mzML"):
                with open(Path(mzML_dir, file.name),"wb") as f:
                    f.write(file.getbuffer())
        st.success("Successfully added uploaded files!")
        st.experimental_rerun()
    else:
        st.warning("Upload some files before adding them.")

# except:
#     st.warning("Something went wrong.")