import streamlit as st
from src.helpers import Helper
from src.dataframes import *
from pathlib import Path
import os
import shutil

st.set_page_config(page_title="UmetaFlow", page_icon="resources/icon.png", layout="wide", initial_sidebar_state="auto", menu_items=None)

try:
    # define directory to store mzML files
    if not os.path.isdir(st.session_state["mzML_files"]):
        os.mkdir(st.session_state["mzML_files"])

    c1, c2 = st.columns([0.8, 0.2])
    c1.title("File Upload")
    c2.markdown("##")
    if c2.button("Load Example Data"):
        example_mzML_dir = Path("example_data", "mzML")
        for file in example_mzML_dir.glob("*.mzML"):
            shutil.copy(file, Path(st.session_state["mzML_files"]))
            DataFrames.mzML_to_pkl(file, st.session_state["mzML_dfs"])

    st.info("""
        **💡 How to upload files**

        1. Browse files on your computer
        2. Click the **Add the uploaded mzML files** button to use them in the workflows

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
        c1, c2 = st.columns([0.8, 0.2])
        upload_dir = c1.text_input("path to folder with mzML files")
        upload_dir = r'{}'.format(upload_dir)
        c2.markdown("##")
        if c2.button("Upload"):
            with st.spinner("Uploading files..."):
                for file in Path(upload_dir).iterdir():
                    if file.name not in st.session_state["mzML_files"].iterdir() and file.name.endswith("mzML"):
                        shutil.copy(file, st.session_state["mzML_files"])
                        DataFrames.mzML_to_pkl(file, st.session_state["mzML_dfs"])
                st.success("Successfully added uploaded files!")

    # upload mzML files
    if submitted:
        if uploaded_mzML:
            if uploaded_mzML[0]: # opening file dialog and closing without choosing a file results in None upload
                for file in uploaded_mzML:
                    if file.name not in st.session_state["mzML_files"].iterdir() and file.name.endswith("mzML"):
                        with open(Path(st.session_state["mzML_files"], file.name),"wb") as f:
                            f.write(file.getbuffer())
                        DataFrames.mzML_to_pkl(Path(st.session_state["mzML_files"], file.name), st.session_state["mzML_dfs"])
                st.success("Successfully added uploaded files!")
        else:
            st.warning("Upload some files before adding them.")


    with st.sidebar:
        # Removing files
        st.markdown("### Remove Files")
        c1, c2 = st.columns(2)
        if c1.button("⚠️ **All**"):
            try:
                if any(st.session_state["mzML_files"].iterdir()):
                    Helper().reset_directory(st.session_state["mzML_files"])
                if any(st.session_state["mzML_dfs"].iterdir()):
                    Helper().reset_directory(st.session_state["mzML_dfs"])
                    st.experimental_rerun()
            except:
                pass
        if c2.button("**Un**selected"):
            try:
                for file in [Path(st.session_state["mzML_files"], key) for key, value in st.session_state.items() if key.endswith("mzML") and not value]:
                    file.unlink()
                for file in [Path(st.session_state["mzML_dfs"], key[:-4]+"pkl") for key, value in st.session_state.items() if key.endswith("mzML") and not value]:
                    file.unlink()
                st.experimental_rerun()
            except:
                pass

        # show currently available mzML files
        st.markdown("### Uploaded Files")
        for f in sorted(st.session_state["mzML_files"].iterdir()):
            if f.name in st.session_state:
                checked = st.session_state[f.name]
            else:
                checked = True
            st.checkbox(f.name[:-5], checked, key=f.name)

        st.markdown("***")
        st.image("resources/OpenMS.png", "powered by")
    
except:
    st.warning("Something went wrong.")