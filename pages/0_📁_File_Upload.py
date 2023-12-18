from pathlib import Path

import streamlit as st
import pandas as pd

from src.common import *
from src.fileupload import *

params = page_setup()

st.title("File Upload")

tabs = ["File Upload", "Example Data"]
if st.session_state.location == "local":
    tabs.append("Files from local folder")

tabs = st.tabs(tabs)

with tabs[0]:
    with st.form("mzML-upload", clear_on_submit=True):
        files = st.file_uploader(
            "mzML files", accept_multiple_files=(st.session_state.location == "local"))
        if st.form_submit_button("Add files to workspace", use_container_width=True, type="primary"):
            if files:
                save_uploaded_mzML(files)
            else:
                st.error("Nothing to add, please upload file.")

# Example mzML files
with tabs[1]:
    st.markdown("Example data set of bacterial cytosolic fractions. Bacillus subtilis cultures were treated with the antibiotic fosfomycin, which inhibits a step in the biosynthesis of petidoglycan (bacterial cell wall). The major accumulation product is UDP-GlcNAc.")
    if st.button("Load Example Data", type="primary", use_container_width=True):
        load_example_mzML_files()

# Local file upload option: via directory path
if st.session_state.location == "local":
    with tabs[2]:
        # with st.form("local-file-upload"):
        local_mzML_dir = st.text_input(
            "path to folder with mzML files")
        # raw string for file paths
        local_mzML_dir = r"{}".format(local_mzML_dir)
        if st.button("Copy files to workspace", type="primary", use_container_width=True, disabled=(local_mzML_dir == "")):
            copy_local_mzML_files_from_directory(local_mzML_dir)

mzML_dir = Path(st.session_state.workspace, "mzML-files")
if any(Path(mzML_dir).iterdir()):
    v_space(2)
    # Display all mzML files currently in workspace
    df = pd.DataFrame(
        {"file name": [f.name for f in Path(mzML_dir).iterdir()]})
    st.markdown("##### mzML files in current workspace:")
    show_table(df)
    v_space(1)
    # Remove files
    with st.expander("🗑️ Remove mzML files"):
        to_remove = st.multiselect("select mzML files",
                                   options=[f.stem for f in sorted(mzML_dir.iterdir())])
        c1, c2 = st.columns(2)
        if c2.button("Remove **selected**", type="primary", use_container_width=True, disabled=not any(to_remove)):
            params = remove_selected_mzML_files(to_remove, params)
            save_params(params)
            st.rerun()

        if c1.button("⚠️ Remove **all**", use_container_width=True, disabled=not any(mzML_dir.iterdir())):
            params = remove_all_mzML_files(params)
            save_params(params)
            st.rerun()

save_params(params)
