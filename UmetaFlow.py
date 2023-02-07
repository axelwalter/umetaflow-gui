import streamlit as st
import os
import shutil
import sys
import uuid
from pathlib import Path
from src.constants import QUICKSTART

st.set_page_config(
    page_title="UmetaFlow",
    page_icon="resources/icon.png",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None,
)

try:
    # default location is online (instead of local)
    st.session_state.location = "online"

    # if we run the packaged windows version, we start within the Python directory -> need to change working directory to ..\umetaflow-gui-main
    if "windows" in sys.argv:
        os.chdir("../umetaflow-gui-main")

    # check if app is run locally and set default workspace
    if "local" in sys.argv:
        st.session_state.location = "local"
        if "workspace" not in st.session_state:
            st.session_state["workspace"] = "default-workspace"
    # online we want a new key generated each time
    elif "workspace" not in st.session_state:
        st.session_state["workspace"] = str(uuid.uuid1())

    # if the selected workspace does not exist, create it
    if not os.path.exists(str(st.session_state["workspace"])):
        os.mkdir(str(st.session_state["workspace"]))

    # show the workspace options and info text
    with st.sidebar:
        st.markdown("### Workspaces")
        if st.session_state["location"] == "online":
            new_workspace = st.text_input("enter workspace", "")
            if st.button("**Enter Workspace**") and new_workspace:
                st.session_state["workspace"] = new_workspace
            st.info(
                f"""💡 Your workspace ID:

    **{st.session_state['workspace']}**

    You can share this unique workspace ID with other people.

    ⚠️ Anyone with this ID can access your data!
    """
            )
        elif st.session_state["location"] == "local":

            create_remove_workspace = st.text_input("create/remove workspace", "")
            if st.button("**Create Workspace**") and create_remove_workspace:
                st.session_state["workspace"] = create_remove_workspace
                st.experimental_rerun()

            if (
                st.button("⚠️ Delete Workspace")
                and create_remove_workspace
                and Path(create_remove_workspace).exists()
            ):
                shutil.rmtree(st.session_state["workspace"])
                st.session_state["workspace"] = "default-workspace"
                st.experimental_rerun()

            options = [
                file.name
                for file in Path(".").iterdir()
                if file.is_dir()
                and file.name
                not in (
                    ".git",
                    ".streamlit",
                    "example_data",
                    "pages",
                    "unused",
                    "src",
                    "resources",
                    "params",
                )
            ]
            chosen_workspace = st.selectbox(
                "choose existing workspace",
                options,
                index=options.index(st.session_state["workspace"]),
            )
            if chosen_workspace:
                st.session_state["workspace"] = chosen_workspace

        st.markdown("***")
        st.image("resources/OpenMS.png", "powered by")

    # define directory to store mzML files
    st.session_state["mzML_files"] = Path(st.session_state["workspace"], "mzML_files")
    if not os.path.isdir(st.session_state["mzML_files"]):
        os.mkdir(st.session_state["mzML_files"])

    # define directory to store mzML files as dataframes in ftr format
    st.session_state["mzML_dfs"] = Path(st.session_state["workspace"], "mzML_dfs")
    if not os.path.isdir(st.session_state["mzML_dfs"]):
        os.mkdir(st.session_state["mzML_dfs"])

    st.markdown(QUICKSTART)
except:
    st.warning("Something went wrong.")
